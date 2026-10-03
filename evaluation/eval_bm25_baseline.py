import json
import time
from datetime import datetime
from pathlib import Path

from evaluation.metrics import calculate_metrics,summarize
from rag.bm25_retriever import BM25Retriever


def summarize(rows: list[dict]) -> dict:
    """正向指标只对有答案题取平均，无答案题单独统计。"""
    answerable = [row for row in rows if row["expected_chunks"]]
    unanswerable = [row for row in rows if not row["expected_chunks"]]

    def average(selected_rows, field):
        if not selected_rows:
            return None
        return sum(row["metrics"][field] for row in selected_rows) / len(
            selected_rows
        )

    return {
        "total_questions": len(rows),
        "answerable_questions": len(answerable),
        "unanswerable_questions": len(unanswerable),
        "hit_at_k": average(answerable, "hit"),
        "recall_at_k": average(answerable, "recall"),
        "complete_evidence_rate": average(answerable, "complete"),
        "mrr_at_k": average(answerable, "reciprocal_rank"),
        "retrieval_refusal_rate": average(
            unanswerable, "retrieval_refusal"
        ),
        "avg_retrieval_ms": (
            sum(row["retrieval_ms"] for row in rows) / len(rows)
            if rows else None
        ),
    }


def run_evaluation(top_k: int = 3):
    chunks_path = Path("data/indexed_chunks.json")
    dataset_path = Path("evaluation/ground_truth.json")

    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    ground_truth = json.loads(dataset_path.read_text(encoding="utf-8"))

    if not chunks or not ground_truth:
        raise ValueError("切片和评测集不能为空")

    chunk_ids = {chunk["chunk_id"] for chunk in chunks}
    if len(chunk_ids) != len(chunks):
        raise ValueError("切片 ID 重复，请先检查数据")

    # 先检查标注，避免不存在的切片 ID 影响评测。
    for item in ground_truth:
        expected = item.get("expected_chunks") or item.get("expected") or []
        missing = set(expected) - chunk_ids
        if missing:
            raise ValueError(
                f"题目 {item['id']} 的标注引用了不存在的切片：{missing}"
            )

    retriever = BM25Retriever()
    retriever.add_documents(chunks)
    rows = []

    for item in ground_truth:
        expected = item.get("expected_chunks") or item.get("expected") or []

        start = time.perf_counter()
        retrieved_docs = retriever.search(
            query=item["query"],
            top_k=top_k,
        )
        retrieval_ms = (time.perf_counter() - start) * 1000.0

        retrieved_ids = [doc["chunk_id"] for doc in retrieved_docs]
        metrics = calculate_metrics(expected, retrieved_ids, top_k)

        rows.append({
            "id": item["id"],
            "type": item["type"],
            "query": item["query"],
            "expected_chunks": expected,
            "retrieved_chunks": retrieved_ids,
            "scores": [
                {
                    "chunk_id": doc["chunk_id"],
                    "score": float(doc.get("score", 0.0)),
                }
                for doc in retrieved_docs
            ],
            "retrieval_ms": retrieval_ms,
            "metrics": metrics,
        })

        # 不仅关注完全漏召回，也记录多证据未找全的题。
        if expected and not metrics["complete"]:
            print(
                f"[证据未找全] {item['id']} "
                f"期望={expected} 实际={retrieved_ids}"
            )

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
            "method": "BM25",
            "top_k": top_k,
            "chunk_count": len(chunks),
            "chunks_path": str(chunks_path),
            "dataset_path": str(dataset_path),
            "latency_scope": "仅检索，不含索引构建与回答生成",
        },
        "summary": summary,
        "by_type": by_type,
        "questions": rows,
    }

    output_dir = Path("output/evaluation")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / (
        f"bm25_{now.strftime('%Y%m%d_%H%M%S_%f')}.json"
    )
    output_file.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\nBM25 评测结果，Top-K={top_k}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n逐题结果已保存：{output_file.resolve()}")


if __name__ == "__main__":
    run_evaluation(top_k=3)

# import sys
# from pathlib import Path

# sys.path.append(str(Path(__file__).resolve().parent.parent))

# import json
# import time
# from rag.bm25_retriever import BM25Retriever

# def run_evaluation(top_k: int = 3):
#     chunks_path = Path("data/indexed_chunks.json")
#     datastes_path = Path("evaluation/ground_truth.json")

#     with open(chunks_path,"r",encoding='utf-8') as f:
#         chunks = json.load(f)
#     with open(datastes_path,"r",encoding="utf-8") as f:
#         ground_truth = json.load(f)

#     print(f">>>正在对{len(chunks)}个切片进行中文分词并构建BM25索引...")
#     retriever = BM25Retriever()#构造实例对象要加括号
#     retriever.add_documents(documents=chunks)
#     print(">>>BM25索引构建完成，开始执行评测...\n")

#     answerable_count = 0
#     hit_count = 0
#     mrr_sum = 0.0
#     total_latency_ms = 0.0
#     type_stats = {}

#     for item in ground_truth:
#         q_id = item["id"]
#         q_type = item["type"]
#         query = item["query"]
#         raw_expected = item.get("expected_chunks")  or item.get("expected") or []
#         expected = set(raw_expected)

#         if q_type not in type_stats:
#             type_stats[q_type] = {"total":0,"hits": 0,"mrr_sum": 0.0}
#         type_stats[q_type]["total"] += 1

#         #测算纯本地BM25检索耗时
#         start_t = time.perf_counter()
#         retrieved_docs = retriever.search(query=query, top_k=top_k)
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
#         for rank,rid in enumerate(retrieved_ids,start=1):
#             if rid in expected:
#                 reciprocal_rank = 1.0/ rank
#                 break

#         mrr_sum += reciprocal_rank
#         type_stats[q_type]["mrr_sum"] += reciprocal_rank

#         if not is_hit:
#             print(f"[FALL]题号{q_id}({q_type})召回失败！")
#             print(f"      问题：{query}")
#             print(f"      期望：{list(expected)}")
#             print(f"      实际召回：{retrieved_ids}\n")

#     overall_recall = hit_count / answerable_count if answerable_count else 0.0
#     overall_mrr = mrr_sum / answerable_count if answerable_count else 0.0
#     avg_latency = total_latency_ms /len(ground_truth)

#     print("=" * 60)
#     print("       BM25 Baseline (Sparse)检索评测报告")
#     print("=" * 60)
#     print(
#         f"评测总题数：{len(ground_truth)}(可回答：{answerable_count}，超纲拒答：{len(ground_truth) - answerable_count})"
#     )
#     print(f"召回深度Top-k:{top_k}")
#     print(f"平均检索延迟：{avg_latency:.2f}ms")
#     print(
#         f"综合Recall@{top_k}:{overall_recall:.4f}({hit_count}/{answerable_count})"
#     )
#     print(f"综合MRR@{top_k}: {overall_mrr:.4f}")
#     print("-" * 60)
#     print("分题型细分表现：")
#     for t, stat in type_stats.items():
#         if t == "unanswerable":
#             print(f" -[{t:12s}]共{stat['total']}题（无答案测试用例）")
#             continue
#         t_recall = stat["hits"] /stat["total"] if stat["total"] else 0.0
#         t_mrr = stat["mrr_sum"] / stat["total"] if stat["total"] else 0.0
#         print(
#             f"  - [{t:12s}] Recall@{top_k}:{t_recall:.4f} | MRR:{t_mrr:.4f}(共{stat['total']}题)"
#         )
#         print("=" * 60)

# if __name__ == "__main__" :
#     run_evaluation(top_k=3)
