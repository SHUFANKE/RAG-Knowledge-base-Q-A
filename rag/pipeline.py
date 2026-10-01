from rag.hybrid_retriever import HybridRetriever
from rag.reranker import DashScopeReranker

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

        #4.阈值截断（防幻觉机制：分值过低说明大概率是无答案超纲提，直接过滤）
        filtered_docs = [
            doc for doc in reranker_docs if doc.get("rerank_score", 0.0) >= rerank_threshold
        ]

        return filtered_docs[:final_k]



























# from app.llm_client import BaseLLMClient
# from rag.dense_retriever import FAISSRetriever

# class RAGPopeline:
#     def __init__(self, retriever: FAISSRetriever, llm_clinet: BaseLLMClient):
#         self.retriever = retriever
#         self.llm_client = llm_clinet

#     async def query(self,question: str, top_k: int = 3) -> dict:
#         """检索增强生成主链路，严格执行Citation输出规范"""
#         #1.稠密向量召回
#         matched_chunks = await self.retriever.search(query=question, top_k=top_k)

#         if not matched_chunks:
#             return {
#                 "question":question,
#                 "answer": "知识库中暂无可参考的文档，无法回答该问题",
#                 "sources": [],
#             }

#         #2.构建带编号的Context上下文
#         context_parts = []
#         for i, chunk in enumerate(matched_chunks, start=1):
#             context_parts.append(
#                 f"[{i}] 来源：{chunk.get('source', '未知文件')}\n内容：{chunk['text']}"
#             )
#         context_str = "\n\n".join(context_parts)

#         #3.约束Prompt: 要求必须标注引用
#         system_prompt = (
#             "你是一个专业严谨的技术助理。请严格基于给出的参考资料回答问题。\n"
#             "规则：\n"
#             "1. 仅根据参考资料陈述事实，不得随意推理未提及的内容。\n"
#             "2. 如果参考资料不足以回答，明确说明资料不足。\n"
#             "3. 在回答正文末尾，必须附上 Sources 引用列表，格式如下：\n"
#             "Sources:\n"
#             "[1] 文件名\n"
#             "[2] 文件名"
#         )

#         user_prompt = f"【参考资料】\n{context_str}\n\n【用户问题】\n{question}"

#         #4.生成回答
#         answer = await self.llm_client.chat(
#             prompt=user_prompt,system_prompt=system_prompt
#         )

#         return {
#             "question": question,
#             "answer": answer,
#             "sources": matched_chunks,
#         }

    
