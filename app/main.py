from contextlib import asynccontextmanager
from fastapi import FastAPI,HTTPException
from app.embedder import SimpleWordEmbedder
from app.llm_client import MockLLMClient
from app.rag_pipeline import LocalRAGPipeline
from app.schemas import (
    IndexRequest,
    IndexResponse,
    QueryRequest,
    QueryResponse,
    SourceChunkInfo,
)

#全局单例Pipeline
pipeline:LocalRAGPipeline | None = None #定义pipeline要么是前面这个要么是None


@asynccontextmanager
async def lifespan(app:FastAPI):
    """应用生命周期管理：服务启动时初始化RAG核心组件，服务关闭时释放资源"""
    global pipeline
    vocab = ["python", "rag", "fastapi", "llm", "vector", "database", "retrieval"]
    embedder = SimpleWordEmbedder(vocab=vocab)
    llm_client = MockLLMClient(response_delay=0.1)

    pipeline = LocalRAGPipeline(embedder=embedder,llm_client=llm_client)

    #预置一条样例知识，方便开箱即测
    sample_text = "Python is great for writing RAG systems. We can connect LLM and FastAPI."
    pipeline.index_document(sample_text,source="default_intro.txt",chunk_size=20,overlap=5)
    print(">>>[System] RAG Pipeline 初始化完成，服务已就绪")

    yield

    print(">>> [System] 服务正在关闭，资源已释放。")

app = FastAPI(
    title="Minimalist RAG API Service",
    description="基于 FastAPI + 自研RAG内核的轻量化知识库问答服务",
    version="1.0.0",
    lifespan=lifespan,
)

@app.get("/health")
async def health_check():
    """健康检查探针接口"""
    return {"status":"ok","service":"rag-pipeline"}

@app.post("/api/index",response_model=IndexResponse)
async def index_knowledge(req:IndexRequest):
    """上传文档切片并写入向量知识库"""
    if pipeline is None:
        raise HTTPException(status_code=500,detail="Pipeline未初始化")

    count = pipeline.index_document(
        text=req.text,
        source=req.source,
        chunk_size=req.chunk_size,
        overlap=req.overlap,
    )
    return IndexResponse(
        message=f"成功为文档'{req.source}'建立索引",
        indexed_chunks=count,
    )

@app.post("/api/query",response_model=QueryResponse)
async def query_knowledge(req:QueryRequest):
    """基于知识库的大模型问答接口"""
    if pipeline is None:
        raise HTTPException(status_code=500,detail="Pipeline未初始化")

    #1.召回相关的切片与相似度得分
    raw_results = pipeline.retrieve(req.question,top_k=req.top_k)

    #2.转换为规范的响应模型
    sources = [
        SourceChunkInfo(
            chunk_id=chunk.chunk_id,
            text=chunk.text,
            source=chunk.source,
            score=round(score,4)

        )
        for chunk,score in raw_results
    ]

    #3.异步调用完整RAG回答
    answer =await pipeline.answer_question(req.question,top_k=req.top_k)

    return QueryResponse(
        question=req.question,
        answer=answer,
        sources=sources,
    )

