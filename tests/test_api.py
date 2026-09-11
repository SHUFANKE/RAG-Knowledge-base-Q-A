from fastapi.testclient import TestClient
from app.main import app


def test_health_check_endpoint():
    """验证探针接口健康状态"""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status":"ok","service":"rag-pipeline"}

def test_index_and_query_flow():
    """验证文档入库与问答检索的完整端到端链路"""
    with TestClient(app) as client:
        #1.测试入库接口
        index_payload = {
            "text": "FastAPI enables high performance web APIs for AI models.",
            "source": "api_test_doc.txt",
            "chunk_size": 20,
            "overlap": 5,
        }
        index_res = client.post("/api/index",json=index_payload)
        assert index_res.status_code == 200
        index_data = index_res.json()
        assert index_data["indexed_chunks"] > 0

        #2.测试问答接口
        query_playload ={
            "question": "What is FastAPI?",
            "top_k": 2,
        }
        query_res = client.post("/api/query",json=query_playload)
        assert query_res.status_code == 200
        query_data = query_res.json()
        assert "answer" in query_data
        assert len(query_data["sources"]) > 0

def test_query_validation_error():
    """验证非法入参时Pydantic的422自动拦截机制"""
    with TestClient(app) as client:
    #传入空问题或超限的top_k
        invalid_payload = {
            "question": "",
            "top_k": 999,
        }
        response = client.post("/api/query",json=invalid_payload)
        assert response.status_code == 422
