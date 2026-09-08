import math
from dataclasses import dataclass
from app.rag_splitter import Chunk

def cosine_similarity(vec_a:list[float],vec_b:list[float]) -> float:
    """计算两个向量之间的余弦相似度"""
    if len(vec_a) != len(vec_b):
        raise ValueError(
            f"向量维度不匹配：向量A为{len(vec_a)}维，向量B为{len(vec_b)}维"
        )
    if not vec_a:
        raise ValueError("向量不能为空列表")

    #1.计算点积（Dot Product）
    dot_product = sum(a*b for a,b in zip(vec_a,vec_b))

    #计算两个向量各自的模长（Norm）
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    #防御性判断：全零向量模长为0，防止除以0崩溃
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


@dataclass
class VectorRecord:
    """存储在向量库内部的数据节点"""
    chunk :Chunk
    vector : list[float]

class InMemoryVectorStore:
    """内存级微型向量数据库"""

    def __init__(self)-> None:
        self.records: list[VectorRecord] = []

    def add_chunk(self,chunk:Chunk,vector:list[float]) ->None:
        """向向量库写入一条切片及其对应向量"""
        self.records.append(VectorRecord(chunk=chunk,vector=vector))

    def similarity_search(
            self,query_vector: list[float],top_k:int = 2
    ) -> list[tuple[Chunk,float]] :
        """根据查询向量，检索相似度最高的前top_k个Chunk及相似度得分"""
        if top_k <= 0:
            raise ValueError("top_k必须大于0")
        if not self.records:
            return []

        #1.计算query_vector与库中所有切片的相似度
        scores: list[tuple[Chunk,float]] = []
        for record in self.records:
            score = cosine_similarity(query_vector,record.vector)
            scores.append((record.chunk,score))

        #2.按相似度从高到低排序（sort by score descending)
        scores.sort(key=lambda item: item[1],reverse=True)

        #3.返回得分最高的前top_k个
        return scores[:top_k]

if __name__ == "__main__":
    #模拟切片数据
    chunk1 = Chunk(text="大模型与 RAG 检索技术", source="doc.txt", chunk_id=0)
    chunk2 = Chunk(text="今天晚饭去吃麻辣烫", source="life.txt", chunk_id=1)

    #假设有3个语义维度[科技,编程,美食]
    vec_chunk1 = [0.9, 0.8, 0.1]
    vec_chunk2 = [0.05, 0.0, 0.95]

    #初始化向量库并存入
    store = InMemoryVectorStore()
    store.add_chunk(chunk1,vec_chunk1)
    store.add_chunk(chunk2,vec_chunk2)

    #模拟用户提问："什么是大语言模型？" ->向量大致偏向科技和编程
    query_vec = [0.85,0.75,0.0]

    #检索最相似的Top-1结果
    top_results = store.similarity_search(query_vec,top_k=1)
    best_chunk, best_score = top_results[0]

    print(f"最匹配切片：'{best_chunk.text}'")
    print(f"相似度得分：{best_score:.4f}")
