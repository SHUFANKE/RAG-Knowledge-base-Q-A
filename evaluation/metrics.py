def calculate_metrics(
        expected_ids: list[str],
        retrieved_ids: list[str],
        top_k: int,
) -> dict:
    """计算一道题的检索指标；无答案题单独记录是否被过滤"""
    if top_k <= 0:
        raise ValueError("top_k 必须大于0")

    expected = set(expected_ids)

    #只评估前k个结果，保留排名并去除重复ID
    ranked_ids = list(dict.fromkeys(retrieved_ids[:top_k]))#dict.fromkeys去重
    retrieved = set(ranked_ids)

    #无答案题不参与正向检索指标的平均
    if not expected:
        return{
            "hit":None,#有没有命中至少一个正确切片
            "recall": None,#正确切片找回了多少比例
            "complete": None,#有没有找全所有标准答案切片
            "reciprocal_rank": None,#第一个正确结果的倒数排名
            "retrieval_refusal": float(not ranked_ids),
        }

    matched = expected & retrieved

    reciprocal_rank = 0.0
    for rank, chunk_id in enumerate(ranked_ids, start=1 ):
        if chunk_id in expected:
            reciprocal_rank = 1.0 / rank
            break

    return {
        "hit": float(bool(matched)),
        "recall": len(matched) / len(expected),
        "complete": float(expected <= retrieved),#两边都是集合，<= 表示子集判断，expected中的每个元素是否都包含在retrieved中？
        "reciprocal_rank": reciprocal_rank,
        "retrieval_refusal": None,
    }

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