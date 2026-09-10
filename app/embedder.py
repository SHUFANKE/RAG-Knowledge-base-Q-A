import re #正则表达式模块
from abc import ABC, abstractmethod

class BaseEmbedder(ABC):
    """Embedding 向量化器的抽象基类（接口定义）"""

    @abstractmethod
    def embed_text(self,texts:str) -> list[float]:
        """将单个文本转换为高维浮点数向量"""
        pass

    @abstractmethod
    def embed_batch(self,texts:list[str]) -> list[list[float]]:
        """批量将文本列表转换为向量列表"""
        pass

class SimpleWordEmbedder(BaseEmbedder):
    """
    基于固定词表的轻量级词频 Embedding 转换器
    适合本地离线学习、单测与无依赖闭环运行
    """

    def __init__(self, vocab: list[str]) -> None:
        if not vocab:
            raise ValueError("词表不能为空")
        #统一转为小写并去重保持顺序
        cleaned_vocab = []
        seen = set()
        for w in vocab:
            w_lower = w.strip().lower()
            if w_lower and w_lower not in seen:
                cleaned_vocab.append(w_lower)
                seen.add(w_lower)

        if not cleaned_vocab:
            raise ValueError("有效词表不能为空")

        self.vocab = cleaned_vocab
        #单词到索引的映射字典，实现o(1)查找速度
        self.word_to_idx: dict[str,int] = {word: i for i,word in enumerate(self.vocab)}
        self.dim = len(self.vocab)

    def _tokenize(self,text:str) -> list[str]:
        """简单的分词与文本清洗：提取英文单词或汉字"""
        #使用正则提取单词/汉字，统一转小写
        words = re.findall(r"\b\w+\b",text.lower())
        return words

    def embed_text(self,text:str) -> list[float]:
        """将文本映射为词表维度的词频向量"""
        vector = [0.0] * self.dim
        tokens = self._tokenize(text)

        for token in tokens:
            if token in self.word_to_idx:
                idx = self.word_to_idx[token]
                vector[idx] += 1.0

        return vector

    def embed_batch(self,texts:list[str]) -> list[list[float]]:

        """批量转换"""
        return [self.embed_text(t) for t in texts]

if __name__ == "__main__":
    #建立一个微型领域知识词表
    domain_vocab = ["python","rag","retrieval","vector","llm","database"]
    embedder = SimpleWordEmbedder(vocab=domain_vocab)

    print(f"词表维度：{embedder.dim}")
    print(F"词表映射：{embedder.word_to_idx}\n")

    #测试两个句子的向量化
    s1 = "Python and RAG are great for LLM retrieval"
    s2 = "Vector database store data"

    v1 = embedder.embed_text(s1)
    V2 = embedder.embed_text(s2)

    print(f"句子1: '{s1}'")
    print(f"向量1: {v1}\n")

    print(f"句子: '{s2}'")
    print(f"向量2: {V2}\n")