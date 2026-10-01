import os
from typing import AsyncGenerator
import json
import httpx

SYSTEM_PROMPT = """你是一个严谨的企业级知识库问答助手。
你的任务是严格根据下方给出的【参考资料】来回答用户的提问。

回答规则与约束：
1. 【忠实原文】：回答内容必须能从【参考资料】中找到确切依据，严禁凭借模型自带的外部常识主观臆测或编造。
2. 【引文标注】：引用的事实依据必须在句末清晰标注对应的参考来源编号，格式如 [Doc 1] 或 [Doc 2]。
3. 【无依据拒答】：如果【参考资料】中的内容不足以支撑回答用户的问题，请直接明确回复：“抱歉，当前知识库资料中未包含相关信息，无法为您提供确切答案。”，切勿生搬硬套。
"""

class QwenGenerator:
    """基于DashScope兼容接口的异步文本生成器"""

    def __init__(
            self,
            api_key: str | None = None,
            model: str = "qwen-turbo",
    ):
        self.api_key = (
            api_key
            or os.getenv("DASHSCOPE_API_KEY")
            or os.getenv("QWEN_API_KEY")
        )
        if not self.api_key:
            raise ValueError("未检测刀到API key,请检查.env配置！")

        self.endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        self.model = model

    def build_user_prompt(self, query: str, context_docs: list[dict]) -> str:
        """格式化组织切片上下文与用户问题"""
        context_blocks  = []
        for rank, doc in enumerate(context_docs, start=1):
            chunk_id = doc.get("chunk_id", f"c_{rank}")
            score = doc.get("rerank_score", 0.0)
            text = doc.get("text", "").strip()
            context_blocks.append(
                f"【参考资料[Doc{rank}]】(ID:{chunk_id} | 置信度：{score:.4f})\n{text}"

            )

        full_context = "\n\n".join(context_blocks)

        user_content = f"""
【参考资料】：
{full_context}

【用户问题】：
{query}
请基于上述资料给出结构化解答：
"""
        return user_content

    async def generate(self, query:str, context_docs: list[dict]) -> str:
        """非流式全量文本生成"""
        #前置判断：若检索结果在阈值截断后为空，直接零Token拒答
        if not context_docs:
            return "抱歉，当前知识库资料中未包含相关信息，无法为您提供确切答案。"

        user_prompt = self.build_user_prompt(query, context_docs)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1, #生产级知识库设定低温度以保证严谨性
        }
        headers = {
            "Authorization": f"Bearer{self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(self.endpoint,json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return data["choices"][0]["message"]["content"]

    async def stream_generate(
            self, query:str, context_docs: list[dict]
    ) -> AsyncGenerator[str,None]:
        """打字机流式文本生成（SSE流式输出Token）"""
        if not context_docs:
            yield"抱歉，当前知识库资料中未包含相关信息，无法为您提供切确答案。"
            return
        
        user_prompt = self.build_user_prompt(query, context_docs)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "stream": True,  # 开启 SSE 流式传输
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", self.endpoint, json=payload,headers=headers
            ) as response:
                response.raise_for_status()
                #逐行读取云端发来的SSE数据
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if line.startswith("data:"):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk_json = json.loads(data_str)
                            delta = chunk_json["choices"][0].get("delta",{})
                            content = delta.get("content","")
                            if content:
                                yield content#吐出一个文字/token
                        except Exception:
                            continue
    