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
from rag.pipeline import ProductionRAGRetriever
from rag.reranker import DashScopeReranker

load_dotenv()

async def run_evaluation(final_k: int=3, rerank_threshold: float = 0.2):
    chunks_path = Path("data/indexed_chunks.json")
    ddataset_path = Path("evaluation/ground_truth.json")

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    with open(ddataset_path, "r",encoding="utf-8") as f:
        ground_truth = json.load(f)

    print (f">>>正在初始化生产级RAG检索管线（切片量：{len(chunks)}...")
    embedder = QwenCloudEmbedder()
    dense = FAISSRetriever(embedder=embedder , dimension=1024)
    bm25 = BM25Retriever()
    hybrid = HybridRetriever(dense_retriever=dense,bm25_retriever=bm25)
    reranker = DashScopeReranker(model="qwen3-rerank")

    pipeline = ProductionRAGRetriever(hybrid_retriever=hybrid, reranker=reranker)
    await hybrid.add_documents(chunks)
    print(">>>索引构建与重排器装载完毕，开始执行全链路基准评测...\n")

    answerable_count = 0
    hit_count = 0
    mrr_sum = 0.0
    unanswerable_total = 0
    correct_refusal_count = 0
    total_latency_ms = 0.0
    type_stats = {}

    for item in ground_truth:
        q_id = item["id"]
        q_type = item["type"]
        query = item["query"]
        raw_expected = item.get("expected_chunks") or item.get("expected") or []
        expected = set(raw_expected)

        if q_type not in type_stats:
            type_stats[q_type] = {"total":0, "hits": 0, "mrr_sum": 0.0}
        type_stats[q_type]["total"] += 1

        start_t = time.perf_counter()
        #执行二阶段检索：粗排Top-10 -> Cross-Encoder 精排Top-3 -> 0.2阈值过滤
        retrieved_docs = await pipeline.retrieve(
            query=query,candidate_k=10, final_k=final_k, rerank_threshold=rerank_threshold
        )
        cost_ms = (time.perf_counter() - start_t) * 1000.0
        total_latency_ms += cost_ms

        retrieved_ids = [doc["chunk_id"] for doc in retrieved_docs]
        scores = [f"{doc['chunk_id']}: {doc.get('rerank_score', 0.0):.4f}" for doc in retrieved_docs]
        print(f"       切片及得分: {scores}\n")

        #超纲拒答题测试（评估防幻觉阈值过滤机制）
        if q_type == "unanswerable" or len(expected) ==  0:
            unanswerable_total += 1
            if len(retrieved_ids) == 0:
                correct_refusal_count += 1
            else:
                
                print(f"[WARN]超纲题未被阈值过滤：{query}(仍召回：{retrieved_ids})")
                
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
            print(f"[FAIL] 题号 {q_id} ({q_type}) 召回失败! 期望: {list(expected)}, 实际: {retrieved_ids}")

    overall_recall = hit_count / answerable_count if answerable_count else 0.0
    overall_mrr = mrr_sum / answerable_count if answerable_count else 0.0
    refusal_rate = correct_refusal_count / unanswerable_total if unanswerable_total else 0.0
    avg_latency = total_latency_ms / len(ground_truth)

    print("=" * 60)
    print("      Production Pipeline (Hybrid + Qwen3-Rerank) 评测报告")
    print("=" * 60)
    print(f"评测总题数: {len(ground_truth)} (可回答: {answerable_count}, 超纲拒答: {unanswerable_total})")
    print(f"精排截断深度 Top-K: {final_k} | 拒答置信度门槛: {rerank_threshold}")
    print(f"平均端到端检索耗时: {avg_latency:.2f} ms")
    print(f"综合 Recall@{final_k}: {overall_recall:.4f} ({hit_count}/{answerable_count})")
    print(f"综合 MRR@{final_k}:    {overall_mrr:.4f}")
    print(f"超纲拒答准确率:     {refusal_rate:.4f} ({correct_refusal_count}/{unanswerable_total})")
    print("-" * 60)
    print("分题型细分表现:")
    for t, stat in type_stats.items():
        if t == "unanswerable":
            continue
        t_recall = stat["hits"] / stat["total"] if stat["total"] else 0.0
        t_mrr = stat["mrr_sum"] / stat["total"] if stat["total"] else 0.0
        print(f"  - [{t:12s}] Recall@{final_k}: {t_recall:.4f} | MRR: {t_mrr:.4f} (共 {stat['total']} 题)")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_evaluation(final_k=3, rerank_threshold=0.45))
