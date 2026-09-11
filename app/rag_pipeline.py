import asyncio
from app.embedder import BaseEmbedder,SimpleWordEmbedder
from app.llm_client import BaseLLMClient,MockLLMClient
from app.rag_splitter import split_document,Document,Chunk
from app.vector_store import InMemoryVectorStore

class LocalRAGPipeline:
    """本地纯内存版RAG 离线问答/检索流水线"""

    def __init__(self,embedder:BaseEmbedder,llm_client:BaseLLMClient) -> None:
        #依赖注入：只依赖抽象的BaseEmbedder和 BaseLLMClient
        self.embedder = embedder
        self.llm_client = llm_client
        self.vector_store = InMemoryVectorStore()

    def index_document(self, text: str, source: str, chunk_size: int = 15,overlap: int = 5) -> int:
        """
        文档切片与入库构建索引流水线
        流程： 文本-> 封装为Document->切片(Chunks) ->批量向量化(Vectors)-> 写入向量库
    
        """
        doc = Document(text=text,source=source)
        chunks = split_document(doc, chunk_size=chunk_size, chunk_overlap=overlap )
        if not chunks:
            return 0

        #提取切片文本并批量转为向量
        chunk_texts = [c.text for c in chunks]
        vectors = self.embedder.embed_batch(chunk_texts)

        #写入向量存储
        for chunk, vector in zip(chunks,vectors):
            self.vector_store.add_chunk(chunk,vector)

        return len(chunks)

    def retrieve(self, question: str,top_k: int = 2) -> list[tuple[Chunk,float]]:
        """
        用户问答检索流水线
        流程： 用户提问 -> 向量化 ->相似度计算与Top—K检索
        """
        #1.把用户的问题转换为同一坐标小的向量
        query_vector = self.embedder.embed_text(question)

        #2.去向量数据库进行相似度比对
        return self.vector_store.similarity_search(query_vector,top_k=top_k)

    async def answer_question(self,question:str,top_k:int = 2) ->str:
        """
        端到端RAG问答链路（Retrieval-Augmented Generation）
        流程：检索召回相关上下文 ->构建增强Prompt ->异步调用LLM生成回答
        """
        #1.召回与问题最相似的知识库切片
        search_results = self.retrieve(question,top_k=top_k)

        #2.组装上下文背景文本(Context)
        context_texts = [f"-{chunk.text}(来自：{chunk.source})" for chunk,_ in search_results]
        context_str = "\n".join(context_texts) if context_texts else "无相关参考知识"

        #3.构造喂给大模型得到增强Prompt
        augmented_prompt = (
            f"请根据以下参考资料回答用户问题：\n"
            f"【参考资料】\n{context_str}\n\n"
            f"【用户问题】\n{question}\n\n"
            f"请给出严谨真实的回答："
        )

        #4.异步请求大模型
        System_prompt = "你是一个专业的知识库问答助手，必须完全基于给定的参考资料作答。"
        answer = await self.llm_client.chat(
            prompt=augmented_prompt,system_prompt=System_prompt
        )
        return answer
    




async def main():
    #1.准备专业词表与向量器
    vocab = ["python", "rag", "fastapi", "llm", "vector", "database", "retrieval"]
    embedder = SimpleWordEmbedder(vocab=vocab)

    #2.准备大模型客户端（本地开发先用Mock保证零成本与高稳定性）
    llm_client = MockLLMClient(response_delay=0.2)

    #3.组装Pipline
    pipeline = LocalRAGPipeline(embedder=embedder,llm_client=llm_client)

    #4.录入知识库文档
    doc_text = (
        "Python is great for writing RAG systems. "
        "We can build vector search from scratch. "
        "Later we will connect LLM and FastAPI for production."
    )
    indexed_count = pipeline.index_document(doc_text,source="rag_guide.txt",chunk_size=20,overlap=5)
    print(f"成功切分并建立索引{indexed_count}个切片!\n")

    #5.模拟端到端提问
    user_q = "How does Python RAG work?"
    print(f"用户提问：'{user_q}'")
    print("正在通过RAG流水线生成回答...")

    final_answer = await pipeline.answer_question(user_q,top_k=2)
    print("\n=== 大模型最终生成回答...")
    print(final_answer)

if __name__ == "__main__":
    asyncio.run(main())
    