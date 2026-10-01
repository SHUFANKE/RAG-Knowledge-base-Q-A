from collections import defaultdict#defaultdict 允许在实例化时传入一个默认工厂函数（Default Factory）。当访问或修改一个不存在的键时，它会自动调用这个工厂函数来生成初始值，而不会报错。
from typing import Any#Any 代表“任意类型”。
from rag.bm25_retriever import BM25Retriever
from rag.dense_retriever import FAISSRetriever

class HybridRetriever:
    """结合Dense向量检索与BM25稀疏检索的双路召回融合器（基于RRF算法）"""

    def __init__(
            self,
            dense_retriever:FAISSRetriever,
            bm25_retriever:BM25Retriever,
            rrf_k: int = 60,
    ):
        self.dense = dense_retriever
        self.bm25 = bm25_retriever
        self.rrf_k = rrf_k#RRF平滑常数，业界通常设为60

    async def add_documents(self,documents: list[dict]) -> None:
        """为双路检索系统同时灌入切片并构建各自索引"""
        await self.dense.add_documents(documents)
        self.bm25.add_documents(documents)

    async def search(
            self,query:str, top_k: int = 5, canditate_k: int = 20
    ) -> list[dict]:
        """
        双路并发召回 -> RRF排名倒数加权融合 -> 截断输出 Top-k
        :param query: 搜索问题
        :param top_k: 最终输出的最优切片数
        :param candidate_k: 单路粗召回的候选池深度（粗排扩大召回面）
        """
        #1.分别从Dense 和BM25获取各自的候选列表（按名次先后排序）
        dense_docs = await self.dense.search(query=query, top_k=canditate_k)
        bm25_docs = self.bm25.search(query=query, top_k=canditate_k)

        #2.建立实体切片映射池，确保能按ID还原完整文档信息
        chunk_map: dict[str, dict[str,Any]] = {}
        rrf_scores: dict[str,float] = defaultdict(float)

        #3.统计Dense分支的RRF分数
        for rank, doc in enumerate(dense_docs,start=1):
            cid = doc["chunk_id"]
            chunk_map[cid] = doc
            rrf_scores[cid] += 1.0 / (self.rrf_k + rank)

        #4.叠加BM25分支RRF分数
        for rank, doc in enumerate(bm25_docs, start=1):
            cid = doc["chunk_id"]
            chunk_map[cid] = doc
            rrf_scores[cid] += 1.0 / (self.rrf_k + rank)

        #5.按最终RRF融合总分从大到小降序排列
        sorted_chunk_ids = sorted(
            rrf_scores.keys(),key=lambda cid: rrf_scores[cid],reverse=True
        )[:min(top_k, len(chunk_map))]

        #6.装配返回结果
        results = []
        for cid in sorted_chunk_ids:
            item = chunk_map[cid].copy()
            item["rrf_score"] = rrf_scores[cid]
            results.append(item)

        return results

    