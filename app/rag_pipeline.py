from app.embedder import BaseEmbedder,SimpleWordEmbedder
from app.rag_splitter import split_document,Document,Chunk
from app.vector_store import InMemoryVectorStore

class LocalRAGPipeline:
    """本地纯内存版RAG 离线问答/检索流水线"""

    def __init__(self,embedder:BaseEmbedder) -> None:
        #依赖注入：只依赖抽象的BaseEmbedder
        self.embedder = embedder
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

    def query(self, question: str,top_k: int = 2) -> list[tuple[Chunk,float]]:
        """
        用户问答检索流水线
        流程： 用户提问 -> 向量化 ->相似度计算与Top—K检索
        """
        #1.把用户的问题转换为同一坐标小的向量
        query_vector = self.embedder.embed_text(question)

        #2.去向量数据库进行相似度比对
        return self.vector_store.similarity_search(query_vector,top_k=top_k)

if __name__ == "__main__":
    #1.准备专业词表与向量器
    vocab = ["python", "rag", "fastapi", "llm", "vector", "database", "retrieval"]
    embedder = SimpleWordEmbedder(vocab=vocab)

    #2.注入依赖，实例化RAG流水线
    pipeline = LocalRAGPipeline(embedder=embedder)

    #3.模拟录入一篇技术知识库文档
    doc_text = (
        "Python is great for writing RAG systems. "
        "We can build vector search from scratch. "
        "Later we will connect LLM and FastAPI for production."
    )
    indexed_count = pipeline.index_document(doc_text,source="rag_guide.txt",chunk_size=20,overlap=5)
    print(f"成功切分并建立索引{indexed_count}个切片!\n")

    #4.模拟用户提问
    user_q = "How does Python RAG work?"
    print(f"用户提问：'{user_q}'")
    results = pipeline.query(user_q,top_k=2)

    for rank, (chunk,score) in enumerate(results,start=1):
        print(f"Top {rank} [得分；{score:.4f}]:'{chunk.text}' (来源：{chunk.source},切片ID: {chunk.chunk_id})")
