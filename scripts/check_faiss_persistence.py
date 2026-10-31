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
