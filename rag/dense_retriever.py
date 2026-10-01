import json
import os
from pathlib import Path
import faiss
import numpy as np
from app.embedder import BaseEmbedder

class FAISSRetriever:
    """基于FAISS的高维稠密向量索引与持久化检索器"""

    def __init__(self,embedder:BaseEmbedder,dimension: int = 1024):
        self.embedder = embedder
        self.dimension = dimension

        #采用Inner Product（内积），配合L2 归一化即等价于余弦相似度.里面存向量
        self.index = faiss.IndexFlatIP(self.dimension)

        #存储对应文本和元数据，下标与FAISS的ID严格一一对应；里面存文本
        self.doc_store: list[dict] = []

    async def add_documents(self,chunks: list[dict]) -> None:
        """异步批量向量化切片并加入FAISS索引"""
        if not chunks:
            return
        texts = [chunk["text"] for chunk in chunks]
        embeddings = await self.embedder.embed_batch(texts)

        #转换维numpy float32 数组并进行L2归一化
        vectors = np.array(embeddings,dtype=np.float32)
        faiss.normalize_L2(vectors)

        #写入FAISS索引与文档存储
        self.index.add(vectors)
        self.doc_store.extend(chunks)

    async def search(self,query: str, top_k: int = 5) -> list[dict]:
        """输入用户问题，召回Top—k及相关切片及溯源信息"""
        if self.index.ntotal == 0:
            return []

        query_vec = await self.embedder.embed_text(query)
        q_arr = np.array([query_vec],dtype=np.float32)
        faiss.normalize_L2(q_arr)

        actual_k = min(top_k, self.index.ntotal)
        scores,indices = self.index.search(q_arr,actual_k)#这两个是二维的numpy数组


        results = []
        for score, idx in zip(scores[0],indices[0]):
            if idx == -1:#什么情况索引是-1,-1是一个特殊的占位符，代表没有找到有效结果或空槽位
                continue
            item = self.doc_store[idx].copy()
            item["score"] = float(score)
            results.append(item)
        return results#最后返回的results是一个list[dict],每个元素是按分数倒序排列的，每个元素是一个dict里面有一个key是scores。
    

    def save_to_disk(self, directory: str = "data/faiss_index") -> None:
        """持久化保存索引和元数据到磁盘"""
        path = Path(directory)
        path.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, str(path / "index.faiss"))
        with open(path / "metadata.json","w",encoding="utf-8") as f:
            json.dump(self.doc_store, f, ensure_ascii=False, indent=2)

    def load_from_disk(self,directory:str = "data/faiss_index") -> bool:
        """从磁盘加载持久化索引与元数据"""
        path = Path(directory)
        index_file = path / "index.faiss"
        meta_file = path / "metadata.json"

        if not index_file.exists() or not meta_file.exists():
            return False
        self.index = faiss.read_index(str(index_file))
        with open(meta_file, "r", encoding="utf-8") as f:
            self.doc_store = json.load(f)
        return True

    