import sys 
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
import asyncio
import json
import time
from dotenv import load_dotenv

from app.embedder import QwenCloudEmbedder
from rag.bm25_retriever import BM25Retriever
from rag.dense_retriever import FAISSRetriever
from rag.hybrid_retriever import HybridRetriever

load_dotenv()

async def run_evaluation(top_k: int = 3):
    chunks_path = Path("data/indexed_chunks.json")
    dataset_path = Path("evaluation/ground_truth.json")

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    with open(dataset_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    print(f">>>正在初始化双路混合检索器（Dense + BM25），切片量：{len(chunks)}...")
    embedder = QwenCloudEmbedder()
    dense = FAISSRetriever(embedder=embedder, dimension=1024)
    bm25 = BM25Retriever()

    hybrid = HybridRetriever(dense_retriever=dense, bm25_retriever=bm25)
    await hybrid.add_documents(chunks)
    print(">>>双路索引构建完成，开始执行混合检索评测...\n")

    answerable_count = 0
    hit_count = 0
    mrr_sum = 0.0
    total_latency_ms = 0.0
    type_stats = {}

    for item in ground_truth:
        q_id =item["id"]
        q_type = item["type"]
        query = item["query"]
        raw_expected = item.get("expected_chunks") or item.get("expected") or []
        expected = set(raw_expected)

        if q_type not in type_stats:
            type_stats[q_type] = {"total": 0, "hits": 0, "mrr_sum": 0.0}
        type_stats[q_type]["total"] += 1

        start_t = time.perf_counter()
        #双路召回，最终融合输出top—k
        retrieved_docs =await hybrid.search(query=query,top_k=top_k)
        cost_ms = (time.perf_counter() - start_t) * 1000.0
        total_latency_ms += cost_ms

        retrieved_ids = [doc["chunk_id"] for doc in retrieved_docs]

        if q_type == "unanswerable" or len(expected) == 0:
            continue

        answerable_count += 1

        is_hit = bool(expected.intersection(set(retrieved_ids)))
        if is_hit:
            hit_count += 1
            type_stats[q_type]["hits"] += 1

        reciprocal_rank = 0.0
        for rank, rid in enumerate(retrieved_ids, start=1):
            if rid in expected:
                reciprocal_rank = 1.0 / rank
                break
        mrr_sum += reciprocal_rank
        type_stats[q_type]["mrr_sum"] += reciprocal_rank

        if not is_hit:
            print(f"[FAIL] 题号 {q_id} ({q_type}) 召回失败!")
            print(f"       问题: {query}")
            print(f"       期望: {list(expected)}")
            print(f"       实际召回: {retrieved_ids}\n")

    overall_recall = hit_count / answerable_count if answerable_count else 0.0
    overall_mrr = mrr_sum / answerable_count if answerable_count else 0.0
    avg_latency = total_latency_ms / len(ground_truth)

    print("=" * 60)
    print("           Hybrid Baseline (Dense + BM25 + RRF) 评测报告")
    print("=" * 60)
    print(
        f"评测总题数: {len(ground_truth)} (可回答: {answerable_count}, 超纲拒答: {len(ground_truth) - answerable_count})"
    )
    print(f"召回深度 Top-K: {top_k}")
    print(f"平均检索延迟: {avg_latency:.2f} ms")
    print(
        f"综合 Recall@{top_k}: {overall_recall:.4f} ({hit_count}/{answerable_count})"
    )
    print(f"综合 MRR@{top_k}:    {overall_mrr:.4f}")
    print("-" * 60)
    print("分题型细分表现:")
    for t, stat in type_stats.items():
        if t == "unanswerable":
            print(f"  - [{t:12s}] 共 {stat['total']} 题 (无答案测试用例)")
            continue
        t_recall = stat["hits"] / stat["total"] if stat["total"] else 0.0
        t_mrr = stat["mrr_sum"] / stat["total"] if stat["total"] else 0.0
        print(
            f"  - [{t:12s}] Recall@{top_k}: {t_recall:.4f} | MRR: {t_mrr:.4f} (共 {stat['total']} 题)"
        )
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_evaluation(top_k=3))