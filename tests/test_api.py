import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

from app.main import app, rag_components


@asynccontextmanager
async def offline_lifespan(application):
    """自动测试跳过真实云端初始化。"""
    yield


@pytest.fixture
def api_client(monkeypatch):
    """注入替身组件，测试接口逻辑，不调用云端 API。"""
    docs = [
        {
            "chunk_id": "test_doc_1",
            "text": "这是一段测试资料。",
            "rerank_score": 0.8764,
        }
    ]

    retriever = AsyncMock()
    retriever.retrieve.return_value = docs

    rewriter = AsyncMock()
    rewriter.rewrite.return_value = "独立测试问题"

    generator = AsyncMock()
    generator.generate.return_value = "测试回答 [Doc 1]"

    async def stream_generate(query, context_docs):
        yield "测试"
        yield "回答 [Doc 1]"

    generator.stream_generate = stream_generate

    components = {
        "retriever": retriever,
        "rewriter": rewriter,
        "generator": generator,
    }

    monkeypatch.setattr(app.router, "lifespan_context", offline_lifespan)

    # 保留进入测试前的组件状态，结束后恢复。
    original_components = rag_components.copy()
    rag_components.clear()
    rag_components.update(components)

    try:
        with TestClient(app) as client:
            yield client, components
    finally:
        rag_components.clear()
        rag_components.update(original_components)


def test_chat_response_and_rewritten_query(api_client):
    """验证响应结构，以及改写后的查询传递给检索和生成。"""
    client, components = api_client
    history = [{"role": "user", "content": "前一轮问题"}]

    response = client.post(
        "/api/chat",
        json={"query": "那它呢？", "history": history},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "测试回答 [Doc 1]"
    assert data["rewritten_query"] == "独立测试问题"
    assert data["references"][0]["chunk_id"] == "test_doc_1"
    assert data["citation_check"] == {
        "status": "valid",
        "reference_count": 1,
        "cited_numbers": [1],
        "invalid_numbers": [],
    }

    for field in (
        "rewrite_ms", "retrieval_ms", "generation_ms", "total_ms"
    ):
        assert data["metrics"][field] >= 0

    components["rewriter"].rewrite.assert_awaited_once_with(
        query="那它呢？",
        history=history,
    )
    components["retriever"].retrieve.assert_awaited_once_with(
        query="独立测试问题",
        candidate_k=20,
        final_k=3,
        rerank_threshold=0.45,
    )
    assert (
        components["generator"].generate.await_args.kwargs["query"]
        == "独立测试问题"
    )


def test_stream_events(api_client):
    """验证引用事件、文本事件、分数精度和结束信号。"""
    client, components = api_client

    response = client.post(
        "/api/chat/stream",
        json={"query": "测试问题"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith(
        "text/event-stream"
    )

    payloads = [
        line[5:].strip()
        for line in response.text.splitlines()
        if line.startswith("data:")
    ]

    assert payloads[-1] == "[DONE]"
    events = [json.loads(value) for value in payloads[:-1]]
    
    assert events[-1]["type"] == "citation_check"
    assert events[-1]["citation_check"] == {
        "status": "valid",
        "reference_count": 1,
        "cited_numbers": [1],
        "invalid_numbers": [],
    }
    assert events[0]["type"] == "references"
    assert events[0]["references"][0]["chunk_id"] == "test_doc_1"
    assert events[0]["references"][0]["score"] == 0.8764

    tokens = [
        event["content"]
        for event in events[1:]
        if event["type"] == "token"
    ]
    assert "".join(tokens) == "测试回答 [Doc 1]"
    assert (
        components["retriever"].retrieve.await_args.kwargs["query"]
        == "独立测试问题"
    )


@pytest.mark.parametrize(
    "payload",
    [
        {"query": ""},
        {"query": "测试问题", "final_k": 999},
        {"query": "测试问题", "rerank_threshold": 1.5},
    ],
)
def test_invalid_request(api_client, payload):
    """非法请求应被拦截，不能进入检索。"""
    client, components = api_client

    response = client.post("/api/chat", json=payload)

    assert response.status_code == 422
    components["retriever"].retrieve.assert_not_awaited()


@pytest.mark.parametrize("path", ["/api/chat", "/api/chat/stream"])
def test_components_not_ready(api_client, path):
    """组件未就绪时，普通与流式接口都应返回 503。"""
    client, _ = api_client
    rag_components.clear()

    response = client.post(path, json={"query": "测试问题"})

    assert response.status_code == 503
