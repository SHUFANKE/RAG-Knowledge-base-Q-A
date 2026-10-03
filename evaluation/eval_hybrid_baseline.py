import asyncio
import json
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from app.embedder import QwenCloudEmbedder
from evaluation.metrics import calculate_metrics, summarize
from rag.bm25_retriever import BM25Retriever
from rag.dense_retriever import FAISSRetriever
from rag.hybrid_retriever import HybridRetriever


async def run_evaluation(top_k: int = 3):
    load_dotenv()

    chunks_path = Path("data/indexed_chunks.json")
    dataset_path = Path("evaluation/ground_truth.json")

    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    ground_truth = json.loads(dataset_path.read_text(encoding="utf-8"))

    if not chunks or not ground_truth:
        raise ValueError("切片和评测集不能为空")

    chunk_ids = {chunk["chunk_id"] for chunk in chunks}
    if len(chunk_ids) != len(chunks):
        raise ValueError("切片 ID 重复，请先检查数据")

    for item in ground_truth:
        expected = item.get("expected_chunks") or item.get("expected") or []
        missing = set(expected) - chunk_ids
        if missing:
            raise ValueError(
                f"题目 {item['id']} 的标注引用了不存在的切片：{missing}"
            )

    # 与当前 HybridRetriever 的默认参数保持一致。
    branch_candidate_k = 20
    rrf_k = 60

    embedder = QwenCloudEmbedder()
    dense = FAISSRetriever(embedder=embedder, dimension=1024)
    bm25 = BM25Retriever()
    retriever = HybridRetriever(
        dense_retriever=dense,
        bm25_retriever=bm25,
        rrf_k=rrf_k,
    )

    try:
        print(
            f"正在构建 Hybrid 索引："
            f"模型={embedder.model}，切片数={len(chunks)}"
        )

        start_index = time.perf_counter()
        await retriever.add_documents(chunks)
        index_build_ms = (
            time.perf_counter() - start_index
        ) * 1000.0

        rows = []

        for item in ground_truth:
            expected = (
                item.get("expected_chunks")
                or item.get("expected")
                or []
            )

            start = time.perf_counter()
            retrieved_docs = await retriever.search(
                query=item["query"],
                top_k=top_k,
                canditate_k=branch_candidate_k,
            )
            retrieval_ms = (time.perf_counter() - start) * 1000.0

            retrieved_ids = [
                doc["chunk_id"] for doc in retrieved_docs
            ]
            metrics = calculate_metrics(
                expected, retrieved_ids, top_k
            )

            rows.append({
                "id": item["id"],
                "type": item["type"],
                "query": item["query"],
                "expected_chunks": expected,
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

            if expected and not metrics["complete"]:
                print(
                    f"[证据未找全] {item['id']} "
                    f"期望={expected} 实际={retrieved_ids}"
                )

        summary = summarize(rows)
        by_type = {
            question_type: summarize([
                row for row in rows
                if row["type"] == question_type
            ])
            for question_type in sorted({
                row["type"] for row in rows
            })
        }

        now = datetime.now().astimezone()
        report = {
            "created_at": now.isoformat(),
            "config": {
                "method": "Hybrid",
                "embedding_model": embedder.model,
                "dimension": dense.dimension,
                "rrf_k": rrf_k,
                "branch_candidate_k": branch_candidate_k,
                "top_k": top_k,
                "chunk_count": len(chunks),
                "chunks_path": str(chunks_path),
                "dataset_path": str(dataset_path),
                "index_build_ms": index_build_ms,
                "latency_scope": (
                    "查询向量化、Dense 检索、BM25 检索及 RRF 融合，"
                    "不含索引构建与回答生成"
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

        print(f"\nHybrid 评测结果，Top-K={top_k}")
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        print(f"\n逐题结果已保存：{output_file.resolve()}")

    finally:
        await embedder.client.close()


if __name__ == "__main__":
    asyncio.run(run_evaluation(top_k=3))



# import sys 
# from pathlib import Path

# sys.path.append(str(Path(__file__).resolve().parent.parent))
# import asyncio
# import json
# import time
# from dotenv import load_dotenv

# from app.embedder import QwenCloudEmbedder
# from rag.bm25_retriever import BM25Retriever
# from rag.dense_retriever import FAISSRetriever
# from rag.hybrid_retriever import HybridRetriever

# load_dotenv()

# async def run_evaluation(top_k: int = 3):
#     chunks_path = Path("data/indexed_chunks.json")
#     dataset_path = Path("evaluation/ground_truth.json")

#     with open(chunks_path, "r", encoding="utf-8") as f:
#         chunks = json.load(f)
#     with open(dataset_path, "r", encoding="utf-8") as f:
#         ground_truth = json.load(f)

#     print(f">>>正在初始化双路混合检索器（Dense + BM25），切片量：{len(chunks)}...")
#     embedder = QwenCloudEmbedder()
#     dense = FAISSRetriever(embedder=embedder, dimension=1024)
#     bm25 = BM25Retriever()

#     hybrid = HybridRetriever(dense_retriever=dense, bm25_retriever=bm25)
#     await hybrid.add_documents(chunks)
#     print(">>>双路索引构建完成，开始执行混合检索评测...\n")

#     answerable_count = 0
#     hit_count = 0
#     mrr_sum = 0.0
#     total_latency_ms = 0.0
#     type_stats = {}

#     for item in ground_truth:
#         q_id =item["id"]
#         q_type = item["type"]
#         query = item["query"]
#         raw_expected = item.get("expected_chunks") or item.get("expected") or []
#         expected = set(raw_expected)

#         if q_type not in type_stats:
#             type_stats[q_type] = {"total": 0, "hits": 0, "mrr_sum": 0.0}
#         type_stats[q_type]["total"] += 1

#         start_t = time.perf_counter()
#         #双路召回，最终融合输出top—k
#         retrieved_docs =await hybrid.search(query=query,top_k=top_k)
#         cost_ms = (time.perf_counter() - start_t) * 1000.0
#         total_latency_ms += cost_ms

#         retrieved_ids = [doc["chunk_id"] for doc in retrieved_docs]

#         if q_type == "unanswerable" or len(expected) == 0:
#             continue

#         answerable_count += 1

#         is_hit = bool(expected.intersection(set(retrieved_ids)))
#         if is_hit:
#             hit_count += 1
#             type_stats[q_type]["hits"] += 1

#         reciprocal_rank = 0.0
#         for rank, rid in enumerate(retrieved_ids, start=1):
#             if rid in expected:
#                 reciprocal_rank = 1.0 / rank
#                 break
#         mrr_sum += reciprocal_rank
#         type_stats[q_type]["mrr_sum"] += reciprocal_rank

#         if not is_hit:
#             print(f"[FAIL] 题号 {q_id} ({q_type}) 召回失败!")
#             print(f"       问题: {query}")
#             print(f"       期望: {list(expected)}")
#             print(f"       实际召回: {retrieved_ids}\n")

#     overall_recall = hit_count / answerable_count if answerable_count else 0.0
#     overall_mrr = mrr_sum / answerable_count if answerable_count else 0.0
#     avg_latency = total_latency_ms / len(ground_truth)

#     print("=" * 60)
#     print("           Hybrid Baseline (Dense + BM25 + RRF) 评测报告")
#     print("=" * 60)
#     print(
#         f"评测总题数: {len(ground_truth)} (可回答: {answerable_count}, 超纲拒答: {len(ground_truth) - answerable_count})"
#     )
#     print(f"召回深度 Top-K: {top_k}")
#     print(f"平均检索延迟: {avg_latency:.2f} ms")
#     print(
#         f"综合 Recall@{top_k}: {overall_recall:.4f} ({hit_count}/{answerable_count})"
#     )
#     print(f"综合 MRR@{top_k}:    {overall_mrr:.4f}")
#     print("-" * 60)
#     print("分题型细分表现:")
#     for t, stat in type_stats.items():
#         if t == "unanswerable":
#             print(f"  - [{t:12s}] 共 {stat['total']} 题 (无答案测试用例)")
#             continue
#         t_recall = stat["hits"] / stat["total"] if stat["total"] else 0.0
#         t_mrr = stat["mrr_sum"] / stat["total"] if stat["total"] else 0.0
#         print(
#             f"  - [{t:12s}] Recall@{top_k}: {t_recall:.4f} | MRR: {t_mrr:.4f} (共 {stat['total']} 题)"
#         )
#     print("=" * 60)

# if __name__ == "__main__":
#     asyncio.run(run_evaluation(top_k=3))