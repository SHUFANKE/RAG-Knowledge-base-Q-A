import asyncio
from dotenv import load_dotenv
from rag.reranker import DashScopeReranker

load_dotenv()

async def main():
    reranker = DashScopeReranker()
    test_docs = [
        {"chunk_id": "c1", "text": "Python 异步编程中，asyncio.gather 用于并发调度任务。"},
        {"chunk_id": "c2", "text": "FastAPI 生产部署建议将 workers 设为 (2 * CPU核数) + 1。"},
    ]
    query = "FastAPI 应该配置几个工作流程？"
    results = await reranker.reranker(query=query,documents=test_docs, top_k=2)

    if not results:
        raise RuntimeError("重排结果为空，请检查接口地址、请求协议和响应结构。")
    
    print(">>>阿里云百炼重排接口连通成功！结果如下：")
    for doc in results:
        print(f"切片ID：{doc['chunk_id']} | 相关度得分：{doc['rerank_score']:.4f} | 内容：{doc['text']}")
if __name__ == "__main__":
    asyncio.run(main())
    