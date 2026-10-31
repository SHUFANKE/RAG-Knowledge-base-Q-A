import re #正则表达式模块
from abc import ABC, abstractmethod
import os 
from openai import AsyncOpenAI

class BaseEmbedder(ABC):
    """Embedding 向量化器的抽象基类（接口定义）"""

    @abstractmethod
    async def embed_text(self,texts:str) -> list[float]:
        """将单个文本转换为高维浮点数向量"""
        pass

    @abstractmethod
    async def embed_batch(self,texts:list[str]) -> list[list[float]]:
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

    async def embed_text(self,text:str) -> list[float]:
        """将文本映射为词表维度的词频向量"""
        vector = [0.0] * self.dim
        tokens = self._tokenize(text)

        for token in tokens:
            if token in self.word_to_idx:
                idx = self.word_to_idx[token]
                vector[idx] += 1.0

        return vector

    async def embed_batch(self,texts:list[str]) -> list[list[float]]:

        """批量转换"""
        return [await self.embed_text(t) for t in texts]

class QwenCloudEmbedder(BaseEmbedder):
    """基于阿里云百炼（OpenAI兼容协议）的高质量文本向量嵌入模型"""

    def __init__(
            self,
            api_key: str | None = None,
            base_url: str |None = None,
            model: str | None = None,
    ):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY")
        self.base_url = base_url or os.getenv(
            "DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        self.model = model or os.getenv("EMBEDDING_MODEL", "text-embedding-v3")

        if not self.api_key:
            raise ValueError("未检测到有效的DASHSCOPE_API_KEY,请在.env中配置")

        #使用官方SDK建立连接
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    async def embed_text(self, text:str) -> list[float]:
        """将单条文本映射到高维语义几何空间"""
        if not text.strip():
            #防御空文本
            return [0.0] * 1024 #text-embedding-v3默认输出1024维
        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量将多条文本转换为向量（大幅度减少HTTP网络握手往返）"""
        cleaned_texts = [t if t.strip() else " " for t in texts]
        response = await self.client.embeddings.create(
            model=self.model,
            input=cleaned_texts,
        )
        #按照入参顺序提取所有向量
        return [item.embedding for item in response.data]


    
