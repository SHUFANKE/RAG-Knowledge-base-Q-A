import asyncio
import json
from pathlib import Path
from dotenv import load_dotenv

from app.embedder import QwenCloudEmbedder
from rag.bm25_retriever import BM25Retriever
from rag.dense_retriever import FAISSRetriever
from rag.hybrid_retriever import HybridRetriever
from rag.pipeline import ProductionRAGRetriever
from rag.reranker import DashScopeReranker
from rag.generator import QwenGenerator

load_dotenv()

async def main():
    chunks_path = Path("data/indexed_chunks.json")
    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    #1.组装检索流水线
    embedder = QwenCloudEmbedder()
    dense = FAISSRetriever(embedder=embedder, dimension=1024)
    bm25 = BM25Retriever()
    hybrid = HybridRetriever(dense_retriever=dense, bm25_retriever=bm25)
    await hybrid.add_documents(chunks)

    reranker = DashScopeReranker(model="qwen3-rerank")
    retriever = ProductionRAGRetriever(hybrid_retriever=hybrid,reranker=reranker)

    #2.组装生成器
    generator = QwenGenerator(model="qwen-turbo")

    #3.准备两条测试问题： 一条知识库内题，一条超纲题
    test_queries = [
        "FastAPI 生产部署时，工作进程workers的推荐计算公式是什么？",
        "如何使用Redis哨兵集群搭建高可用架构？",
    ]

    for  q in test_queries:
        print("\n"+"=" * 60)
        print(f"用户提问：{q}")
        print("-" * 60)

        #检索阶段（Top-10粗排 -> Top-3精排 -> 0.45阈值过滤）
        retrieved_docs = await retriever.retrieve(
            query=q, candidate_k=10, final_k=3,rerank_threshold=0.45
        )

        print(f"检索到及格切片数:{len(retrieved_docs)}")
        for idx ,doc in enumerate(retrieved_docs, start=1):
            print(f" [{idx}] {doc['chunk_id']}(得分：{doc['rerank_score']:.4f})")

        #生成阶段
        print("\n大模型回答：")
        answer = await generator.generate(query=q, context_docs=retrieved_docs)
        print(answer)
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
