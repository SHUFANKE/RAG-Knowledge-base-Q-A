import json
import time
import argparse#用于接收命令行中的题集路径和Top-K
import hashlib#用于记录这次实际使用的数据指纹。
import asyncio

from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from app.embedder import QwenCloudEmbedder
from rag.index_loader import prepare_hybrid
from evaluation.metrics import calculate_metrics,summarize




async def run_evaluation(
        top_k: int = 3,
        dataset_path: str = "evaluation/eval_dev.json",
    ):
    load_dotenv()

    chunks_path = Path("data/indexed_chunks.json")
    dataset_path = Path(dataset_path)

    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    ground_truth = json.loads(dataset_path.read_text(encoding="utf-8"))

    manifest = json.loads(
        Path("evaluation/eval_manifest.json").read_text(encoding="utf-8")
    )
    chunks_hash = hashlib.sha256(chunks_path.read_bytes()).hexdigest()
    dataset_hash = hashlib.sha256(dataset_path.read_bytes()).hexdigest()

    if (
        chunks_hash != manifest["chunks_sha256"]
        or dataset_hash != manifest["dataset_sha256"].get(dataset_path.name)
    ):
        raise ValueError("题集或切片与记录的版本不一致，请先核对数据")
    
    if not chunks or not ground_truth:
        raise ValueError("切片和评测集不能为空")

    chunk_ids = {chunk["chunk_id"] for chunk in chunks}
    if len(chunk_ids) != len(chunks):
        raise ValueError("切片 ID 重复，请先检查数据")

    # 检查所有可接受证据组合，而不只检查第一套。
    for item in ground_truth:
        expected_ids = {
            cid
            for group in item["expected_chunk_sets"]
            for cid in group
        }
        missing = expected_ids - chunk_ids#找出“在左边集合里，但不在右边集合里”的元素

        if missing:
            raise ValueError(
                f"题目 {item['id']} 引用了不存在的切片：{missing}"
            )

    embedder = QwenCloudEmbedder()
    hybrid = await prepare_hybrid(chunks, embedder)
    retriever = hybrid
    candidate_k = 20

    rows = []

    for item in ground_truth:
        expected = item["expected_chunks"]
        expected_sets = item["expected_chunk_sets"]

        print(
            f"[Hybrid] {len(rows) + 1}/{len(ground_truth)} {item['id']}",
            flush=True,
        )

        start = time.perf_counter()
        retrieved_docs = await retriever.search(
            query=item["query"],
            top_k=top_k,
            canditate_k=candidate_k,
        )
        retrieval_ms = (time.perf_counter() - start) * 1000.0

        retrieved_ids = [doc["chunk_id"] for doc in retrieved_docs]
        metrics = calculate_metrics(
            expected_chunk_sets=expected_sets,
            retrieved_ids=retrieved_ids,
            top_k=top_k,
        )

        rows.append({
            "id": item["id"],
            "type": item["type"],
            "query": item["query"],
            "expected_chunks": expected,
            "expected_chunk_sets": expected_sets,
            "retrieved_chunks": retrieved_ids,
            "scores": [
                {
                    "chunk_id": doc["chunk_id"],
                    "rrf_score": float(doc["rrf_score"]),
                }
                for doc in retrieved_docs
            ],
            "retrieval_ms": retrieval_ms,
            "metrics": metrics,
        })

        # 不仅关注完全漏召回，也记录多证据未找全的题。
        if expected_sets and not metrics["complete"]:
            print(
                f"[证据未找全] {item['id']} "
                f"可接受组合={expected_sets} 实际={retrieved_ids}"
            )

    await embedder.client.close()

    summary = summarize(rows)
    by_type = {
        question_type: summarize([
            row for row in rows if row["type"] == question_type
        ])
        for question_type in sorted({row["type"] for row in rows})
    }

    now = datetime.now().astimezone()
    report = {
        "created_at": now.isoformat(),
        "config": {
            "method": "Hybrid-RRF",
            "candidate_k_per_retriever": candidate_k,
            "rrf_k": hybrid.rrf_k,
            "embedding_model": embedder.model,
            "dimension": hybrid.dense.dimension,
            "dense_index_type": "IndexFlatIP",
            "dense_l2_normalized": True,
            "top_k": top_k,
            "chunk_count": len(chunks),
            "chunks_path": str(chunks_path),
            "dataset_path": str(dataset_path),
            "chunks_sha256": chunks_hash,
            "dataset_sha256": dataset_hash,
            "latency_scope": (
                "查询Embedding网络请求、FAISS、BM25与RRF融合，"
                "不含索引加载、重排与回答生成"
            ),
        },
        "summary": summary,
        "by_type": by_type,
        "questions": rows,
    }

    output_dir = Path("output/evaluation")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / (
        f"hybrid_{now.strftime('%Y%m%d_%H%M%S_%f')}.json"
    )
    output_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nHybrid-RRF 评测结果，Top-K={top_k}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n逐题结果已保存：{output_file.resolve()}")

#命令中的 --dataset 会传给 dataset_path，--top-k 会传给 top_k，随后进入刚才的评测流程。
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="evaluation/eval_dev.json")
    parser.add_argument("--top-k", type=int, default=3)
    args = parser.parse_args()

    asyncio.run(run_evaluation(
        top_k=args.top_k,
        dataset_path=args.dataset,
    ))
