def calculate_metrics(
        expected_chunk_sets: list[list[str]],
        retrieved_ids: list[str],
        top_k: int,
) -> dict:
    """计算一道题的检索指标；无答案题单独记录是否被过滤"""
    if top_k <= 0:
        raise ValueError("top_k 必须大于0")

    if any(not group for group in expected_chunk_sets):
        raise ValueError("证据组合不能是空列表；无答案题使用 []")

    groups = [set(group) for group in expected_chunk_sets]

    #只评估前k个结果，保留排名并去除重复ID
    ranked_ids = list(dict.fromkeys(retrieved_ids[:top_k]))#dict.fromkeys去重
    retrieved = set(ranked_ids)

    # retrieval_refusal_rate：无答案题中，没有返回任何片段的比例。
    # answerable_refusal_rate：有答案题中，却没有返回任何片段的比例。
    #无答案题不参与正向检索指标的平均
    if not groups:
        return{
            "hit":None,#有没有命中至少一个正确切片
            "recall": None,#正确切片找回了多少比例
            "complete": None,#有没有找全所有标准答案切片
            "reciprocal_rank": None,#第一个正确结果的倒数排名
            "retrieval_refusal": float(not ranked_ids),
            "answerable_refusal":None,
        }

    relevant_ids = set().union(*groups)

    reciprocal_rank = 0.0
    for rank, chunk_id in enumerate(ranked_ids, start=1 ):
        if chunk_id in relevant_ids:
            reciprocal_rank = 1.0 / rank
            break

    return {
        "hit": float(bool(relevant_ids & retrieved)),
        "recall": max(
            len(group & retrieved) / len(group)
            for group in groups
        ),
        "complete": float(
            any(group <= retrieved for group in groups)
        ),
        "reciprocal_rank": reciprocal_rank,
        "retrieval_refusal": None,
        "answerable_refusal": float(not ranked_ids),
    }

def summarize(rows: list[dict]) -> dict:
    """正向指标只对有答案题取平均，无答案题单独统计。"""
    #这个函数对有预期回答的问题返回True，没有预期回答的返回flase
    def has_answer(row):
        return bool(row["expected_chunk_sets"])

    answerable = [row for row in rows if has_answer(row)]
    unanswerable = [row for row in rows if not has_answer(row)]

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
        "complete_evidence_rate": average(answerable, "complete"),#判断是否至少找齐了一整套可接受的证据，[A,C]同时找到AC为1，否则为0
        "mrr_at_k": average(answerable, "reciprocal_rank"),#平均倒数排名
        "retrieval_refusal_rate": average(
            unanswerable, "retrieval_refusal"
        ),
        "answerable_refusal_rate": average(
            answerable, "answerable_refusal"
        ),
        "avg_retrieval_ms": (
            sum(row["retrieval_ms"] for row in rows) / len(rows)
            if rows else None
        ),
    }