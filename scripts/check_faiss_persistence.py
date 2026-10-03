import asyncio
import math
from pathlib import Path
from tempfile import TemporaryDirectory

from app.embedder import SimpleWordEmbedder
from rag.dense_retriever import FAISSRetriever


async def main():
    # 使用本地词频向量器，验证持久化，不评估语义检索质量。
    embedder = SimpleWordEmbedder(
        vocab=["python", "vector", "database", "food"]
    )

    chunks = [
        {
            "chunk_id": "python_doc",
            "source": "python.txt",
            "text": "python python",
        },
        {
            "chunk_id": "vector_doc",
            "source": "vector.txt",
            "text": "python vector database",
        },
        {
            "chunk_id": "food_doc",
            "source": "food.txt",
            "text": "food",
        },
    ]

    retriever = FAISSRetriever(
        embedder=embedder,
        dimension=embedder.dim,
    )
    await retriever.add_documents(chunks)

    query = "python"
    before = await retriever.search(query=query, top_k=3)

    assert before[0]["chunk_id"] == "python_doc", (
        "保存前检索结果不符合预期"
    )
    print("1. 本地索引构建与检索通过")

    # 临时目录与真实 data/faiss_index 隔离，退出后自动清理。
    with TemporaryDirectory(prefix="rag_faiss_check_") as directory:
        retriever.save_to_disk(directory)

        assert (Path(directory) / "index.faiss").is_file()
        assert (Path(directory) / "metadata.json").is_file()
        print("2. 索引与元数据保存通过")

        # 新建对象，模拟重启后加载。
        restored = FAISSRetriever(
            embedder=embedder,
            dimension=embedder.dim,
        )

        assert restored.index.ntotal == 0
        assert restored.load_from_disk(directory), "索引加载失败"
        assert restored.index.ntotal == len(chunks)
        assert restored.index.d == embedder.dim
        assert restored.doc_store == chunks, "元数据加载不一致"
        print("3. 新对象加载索引与元数据通过")

        after = await restored.search(query=query, top_k=3)

        before_ids = [doc["chunk_id"] for doc in before]
        after_ids = [doc["chunk_id"] for doc in after]
        assert before_ids == after_ids, "加载后检索排名发生变化"

        for old_doc, new_doc in zip(before, after):
            assert math.isclose(
                old_doc["score"],
                new_doc["score"],
                rel_tol=1e-6,
                abs_tol=1e-6,
            ), "加载后检索分数发生变化"

        print("4. 保存前后检索排名与分数一致")

    print("\nFAISS 持久化验证通过，临时文件已清理。")


if __name__ == "__main__":
    asyncio.run(main())


# import asyncio
# import os
# from dotenv import load_dotenv
# from app.embedder import QwenCloudEmbedder
# from app.llm_client import OpenAILikeLLMClient
# from rag.dense_retriever import FAISSRetriever
# from rag.pipeline import RAGPopeline

# load_dotenv()

# async def main():
#     print(">>> 1.初始化Qwen Embedder 与 deepseek Client...")
#     embedder = QwenCloudEmbedder()
#     llm = OpenAILikeLLMClient(
#         api_key=os.getenv("DEEPSEEK_API_KEY"),
#         base_url=os.getenv("DEEPSEEK_BASE_URL","https://api.deepseek.com"),
#         model=os.getenv("DEEPSEEK_MODEL","deepseek-chat"),

#     )

#     retriever = FAISSRetriever(embedder=embedder, dimension=1024)

#     #模拟切片数据
#     test_chunks = [
#         {
#             "text": "FAISS (Facebook AI Similarity Search) 是专为高效密集向量相似度检索和聚类设计的开源库。",
#             "source": "faiss_intro.md",
#             "chunk_id": 1,
#         },
#         {
#             "text": "BM25 是一种基于词频和逆文档频率的经典稀疏检索算法，在精确关键词匹配场景下表现优异。",
#             "source": "bm25_intro.md",
#             "chunk_id": 2,
#         },
#         {
#             "text": "混合检索 (Hybrid Retrieval) 通常结合 BM25 和 Dense 向量检索，兼顾关键词精准度和语义泛化能力。",
#             "source": "hybrid_search.md",
#             "chunk_id": 3,
#         },
#     ]

#     print(">>> 2. 向量化切片并写入FAISS索引...")
#     await retriever.add_documents(test_chunks)

#     print(">>>3.持久化索引至 data/faiss_index 目录...")
#     retriever.save_to_disk()
#     print(" 已成功落盘!")

#     print(">>>4.模拟重启服务:重新从磁盘加载索引...")
#     new_retriver = FAISSRetriever(embedder=embedder,dimension=1024)
#     loaded = new_retriver.load_from_disk()
#     assert loaded, "FAISS 索引从磁盘加载失败!"
#     print("   成功从磁盘恢复,当前索引中向量总数:",new_retriver.index.ntotal)

#     print("\n>>>5.发起端到端问答测试...")
#     pipeline = RAGPopeline(retriever=new_retriver,llm_clinet=llm)
#     question = "什么是FAISS?它在向量检索中有什么用?"
#     result = await pipeline.query(question=question,top_k=2)

#     print("\n=============RAG回复结果===========")
#     print(result["answer"])


# if __name__ == "__main__":
#     asyncio.run(main())
