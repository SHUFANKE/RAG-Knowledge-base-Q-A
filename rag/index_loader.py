import argparse#识别命令中有没有 --rebuild
import asyncio
import hashlib
import json
from pathlib import Path

from app.embedder import QwenCloudEmbedder
from rag.bm25_retriever import BM25Retriever
from rag.dense_retriever import FAISSRetriever
from rag.hybrid_retriever import HybridRetriever

#data/faiss_index/ 会有下面3个文件
# index.faiss	文档向量索引，里面就是切片变成的向量
# metadata.json	与向量位置对应的完整切片记录
# manifest.json	切片内容哈希、Embedding模型名、维度


# 从项目根目录运行，避免当前Windows环境下FAISS中文绝对路径问题。
INDEX_DIR = Path("data/faiss_index")
REBUILD_COMMAND = "python -m rag.index_loader --rebuild"


async def prepare_hybrid(chunks, embedder, *, rebuild=False):
    if not chunks:
        raise ValueError("切片为空，请先运行 evaluation.ingest_corpus")

    dense = FAISSRetriever(embedder=embedder, dimension=1024)
    manifest_path = INDEX_DIR / "manifest.json"

    signature = {
        "chunks_sha256": hashlib.sha256(
            json.dumps(
                chunks, ensure_ascii=False, sort_keys=True
            ).encode("utf-8")
        ).hexdigest(),
        "embedding_model": embedder.model,
        "dimension": dense.dimension,
    }

    if rebuild:
        # 复用原来的add_documents，每次最多向量化10条。
        for start in range(0, len(chunks), 10):
            batch = chunks[start:start + 10]
            await dense.add_documents(batch)
            print(
                f"[Index Build] 已向量化 "
                f"{start + len(batch)}/{len(chunks)} 条",
                flush=True,
            )

        dense.save_to_disk(str(INDEX_DIR))

        # 向量与元数据保存成功后，再记录对应的构建指纹。
        manifest_path.write_text(
            json.dumps(signature, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"[Index Saved] {dense.index.ntotal} 条 → {INDEX_DIR}")

    else:
        if not manifest_path.exists():
            raise RuntimeError(
                f"尚无新版索引，请在项目根目录执行：{REBUILD_COMMAND}"
            )

        saved_signature = json.loads(
            manifest_path.read_text(encoding="utf-8")
        )
        if saved_signature != signature:
            raise RuntimeError(
                f"切片或Embedding模型已变化，请重建：{REBUILD_COMMAND}"
            )

        if not dense.load_from_disk(str(INDEX_DIR)):
            raise RuntimeError(
                f"索引文件缺失，请重建：{REBUILD_COMMAND}"
            )

        if (
            dense.index.ntotal != len(chunks)
            or len(dense.doc_store) != len(chunks)
            or dense.index.d != dense.dimension
        ):
            raise RuntimeError(
                f"索引数量或维度不匹配，请重建：{REBUILD_COMMAND}"
            )

        print(
            f"[Index Loaded] {dense.index.ntotal} 条，"
            "本次未调用文档Embedding"
        )

    # 使用与FAISS对应的同一批切片建立BM25。
    bm25 = BM25Retriever()
    bm25.add_documents(dense.doc_store)
    print(f"[BM25 Ready] {len(bm25.doc_store)} 条")

    return HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
    )


async def main():
    from dotenv import load_dotenv

    #这部分就是识别命令中是否有rebuild
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    load_dotenv(project_root / ".env")

    chunks = json.loads(
        Path("data/indexed_chunks.json").read_text(encoding="utf-8")
    )

    embedder = QwenCloudEmbedder()
    try:
        await prepare_hybrid(
            chunks,
            embedder,
            rebuild=args.rebuild,
        )
    finally:
        await embedder.client.close()


if __name__ == "__main__":
    asyncio.run(main())