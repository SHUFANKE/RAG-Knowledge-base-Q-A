import os
import httpx

REWRITE_PROMPT = """你是一个专业的搜索查询优化助手。
你的任务是结合用户此前的【对话历史】，将用户的【当前提问】改写为一个语义完整、脱离上下文也能独立检索的【独立搜索查询】。

改写规则：
1. 【消除指代】：将“它”、“那”、“这个”等代词替换为历史中讨论的具体实体。
2. 【补全上下文】：如果当前问题省略了主语或环境（例如“内存呢？”），请结合上文补全（如“FastAPI 生产部署时的内存配置推荐”）。
3. 【无需改写直接返回】：如果当前问题本身已经是语义完整的独立问题，或者历史记录为空，请直接输出原问题。
4. 【纯文本输出】：只输出最终改写后的查询字符串，不要带任何标点解释或前缀说明。
"""

class QueryRewriter:
    """基于轻量LLM的多轮会话指代消解与查询改写器"""

    def __init__(
            self,
            api_key: str | None = None,
            model: str = "qwen-plus",
    ):
        self.api_key =(
            api_key
            or os.getenv("DASHSCOPE_API_KEY")
            or os.getenv("QWEN_API_KEY")
            or os.getenv("DASHSCOPE_KEY")
        )
        if not self.api_key:
            raise ValueError("未检测到API Key，前检查.env配置！")
        self.endpoint = (
            "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
        )
        self.model = model

    async def rewrite(self, query:str,history: list[dict]) -> str:
        """输入当前问题与对话历史，输出消解指代后的饱满检索Query"""
        #如果没有历史对话，直接跳过改写，节省开销
        if not history:
            return query
        #组织多轮历史上下文
        history_text_blocks = []
        for msg in history[-4:]: #仅截取最近2轮（最多4条），防止上下文冗长
            role_lable = "用户" if msg.get("role") == "user" else "助手"
            history_text_blocks.append(f"{role_lable}:{msg.get('content')}")

        history_summary = "\n".join(history_text_blocks)
        user_prompt = f"""【对话历史】：
{history_summary}
【当前提问】：
{query}
请输出改写后的独立查询："""

        payload = {
            "model": self.model,
            "messages":[
                {"role":"system","content":REWRITE_PROMPT},
                {"role":"user","content": user_prompt},
            ],
            "temperature":0.0,#确定性输出
            "max_tokens":100,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    self.endpoint,json=payload,headers=headers
                )
                resp.raise_for_status()
                data = resp.json()
                rewritten = (
                    data["choices"][0]["message"]["content"].strip().strip('"') 
                )
                return rewritten if rewritten else query
        except Exception as e:
            #容错降级：改写调用失败时平滑降级为原Query，绝不中断业务
            print(f"[QueryRewriter异常降级]:{e}")
            return query
        
