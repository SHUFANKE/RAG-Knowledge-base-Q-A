import jieba
from rank_bm25 import BM25Okapi#BM25Okapi是一个类

class BM25Retriever:
    """基于BM250kapi的轻量级稀疏关键词检索器"""

    def __init__(self):
        self.doc_store:  list[dict] = []
        self.corpus_tokens: list[list[str]] = []
        self.bm25: BM25Okapi | None = None

    def _tokenize(self, text:str) -> list[str]:
        """使用jieba对文本进行精确分词并过滤存空白符"""
        return [w for w in jieba.lcut(text) if w.strip()]#先分词，在判断是否是空白符

    def add_documents(self, documents:list[dict]) -> None:
        """为切片预料分词并构建BM25 倒排索引"""
        if not documents:
            return

        self.doc_store.extend(documents)
        self.corpus_tokens = [self._tokenize(doc["text"]) for doc in self.doc_store]
        self.bm25 = BM25Okapi(self.corpus_tokens)

    def search(self,query:str,top_k: int=5) -> list[dict]:
        """基于分词计算BM25相关性得分，返回Top-k切片"""
        if not self.bm25 or not self.doc_store:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        #获取所有文档相对于当前Query的BM25得分（一维数组）
        scores = self.bm25.get_scores(query_tokens)#scores里面就是一维的[0.6,0.8,0.3],根据索引来找对应的切片，里面就是对应切片的分数

        #按照分数从大到小排序，获取前Top-k的文档下标
        ranked_indices = sorted(
            range(len(scores)),key=lambda i: scores[i],reverse=True#根据里面的分数来对索引进行排序，目标是拿到分数高的切片的索引号
        )[: min(top_k,len(self.doc_store))]

        results = []
        for idx in ranked_indices:
            item = self.doc_store[idx].copy()
            item["score"] = float(scores[idx])
            results.append(item)

        return results#最后返回的results是一个list[dict],每个元素是按分数倒序排列的，每个元素是一个dict里面有一个key是scores。
    