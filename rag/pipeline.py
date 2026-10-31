from rag.hybrid_retriever import HybridRetriever
from rag.reranker import DashScopeReranker

def filter_reranked_docs(docs, threshold: float, final_k: int):
    """首位达到主阈值后，保留达到半阈值的片段。"""
    if not docs or docs[0].get("rerank_score", 0.0) < threshold:
        return []

    return [
        doc for doc in docs
        if doc.get("rerank_score", 0.0) >= threshold * 0.5
    ][:final_k]

class ProductionRAGRetriever:
    """生产二阶段检索管线：双路混合召回（Top-10）->交叉编码器精排（Top-3）"""

    def __init__(
          self,
          hybrid_retriever:HybridRetriever,
          reranker:DashScopeReranker | None = None,
    ):
        self.hybrid = hybrid_retriever
        self.reranker = reranker

    async def retrieve(
            self,
            query: str,
            candidate_k: int = 10,
            final_k: int = 3,
            rerank_threshold: float = 0.2,
    ) -> list[dict]:
        """
        :param qurey:用户问题
        :param candidate_k:粗排漏斗放行容量
        :param final_k:精排输出给LLM的切片数量
        :param rerank_threshold:语义置信度截断阈值（过滤超纲/完全无关候选）
        """

        #1.粗排：双路召回candidate_k个候选
        candidates = await self.hybrid.search(query=query, top_k=candidate_k)
        if not candidates:
            return[]

        #2.如果未配置重排器，直接回退未粗排截断
        if not self.reranker:
            return candidates[:final_k]

        #3.精排：Cross-Encoder打分重排
        reranker_docs = await self.reranker.reranker(
            query=query, documents=candidates,top_k=final_k
        )

        return filter_reranked_docs(
            reranker_docs,
            threshold=rerank_threshold,
            final_k=final_k,
        )

