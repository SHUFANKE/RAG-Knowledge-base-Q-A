import os 
import httpx

class DashScopeReranker:
    """基于Cross-Encoder的云端重排器"""

    def __init__(
            self,
            api_key: str | None = None,
            model:str = "qwen3-rerank",
    ):
        self.api_key = api_key or os.getenv("") or os.getenv("DASHSCOPE_API_KEY")
        if not self.api_key:
            raise ValueError("未检测到DASHSCOPE_API_KEY,请检查.env配置！")

        self.endpoint = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"
        self.model = model

    async def reranker(
            self, query:str, documents: list[dict], top_k: int = 3
    ) -> list[dict]:
        """
        对粗排返回的候选切片进行跨注意力交叉打分并重新排序
        :param query:检索问题
        :param documents:粗排召回的候选文档切片列表
        :param top_k:精排最终保留的切片数量
        """

        if not documents:
            return []

        doc_texts = [doc["text"] for doc in documents]

        #构造重排请求
        payload = {
            "model":self.model,
            "input":{
                "query":query,
                "documents": doc_texts,
            },
            "parameters":{
                "top_n":min(top_k,len(documents)),
                "return_documnets": False,
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(self.endpoint,json=payload,headers=headers)
            if resp.status_code != 200:
                #打印百炼官方返回的精准错误详情
                print(f"\n[DashScope接口报错响应]：{resp.text}\n")
            resp.raise_for_status()
            data = resp.json()
            #print("\n[DEBUG 真实返回结构]:", data, "\n")

        #根据重排返回的下标和分数重构结果
        results = []
        for item in data.get("output",{}).get("results",[]):
            idx = item.get("index")
            if idx is not None and idx < len(documents):
                original_doc = documents[idx].copy()
                original_doc["rerank_score"] = float(item.get("relevance_score",0.0))
                results.append(original_doc)

        return results
