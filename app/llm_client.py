import asyncio
from abc import ABC,abstractmethod
import httpx
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

class BaseLLMClient(ABC):
    """LLM客户端抽象基类，定义大模型调用的标准契约"""

    @abstractmethod
    async def chat(self,prompt:str,system_prompt: str ="You are a helpful assistant.") -> str:
        """异步单轮对话接口，返回大模型的文本回答"""
        pass

class RomoteLLMClient(BaseLLMClient):
    """
    通用远端大模型HTTP客户端
    兼容OpenAI、Deepseek、智谱、Ollama等标准API格式
    """

    def __init__(
            self,
            api_key:str,
            base_url:str = "https://api.openai.com/v1",
            model: str = "gpt-3.5-turbo",
            timeout: float = 30.0,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    async def chat(self,prompt:str,system_prompt:str = "You are a helpful assistant") -> str:
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer{self.api_key}",
            "Content-Type":"application/json",
        }
        payload = {
            "model": self.model,
            "messages":[
                {"role": "system","content":system_prompt},
                {"role":"user","content":prompt},
            ],
            "temperature":0.7,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url,json=payload,headers=headers)
            response.raise_for_status()
            data = response.json()
            #从OpenAI标准响应格式中解析最终文本
            return data["choices"][0]["message"]['content']

class MockLLMClient(BaseLLMClient):
    """
    离线模拟大模型客户端
    无需API key 与网络连接，用于本地单测、无网开发及CI/CD流程
    """

    def __init__(self,response_delay: float = 0.5) -> None:
        self.response_delay = response_delay
    async def chat(self,prompt:str,system_prompt:str = "You are a helpful assist") -> str:
        #模拟真实网络与模拟吐字耗时
        await asyncio.sleep(self.response_delay)
        return f"[Mock大模型回复]针对问题'{prompt}',基于检索到的知识库，系统运行正常！"

class OpenAILikeLLMClient(BaseLLMClient):
    """支持OpenAI兼容格式的真实云端大模型客户端(适配Qwen/deepseek)"""

    def __init__(
            self,
            api_key:str | None = None,
            base_url: str | None = None,
            model: str | None = None,
            timeout: float = 30.0,
    ):
        #优先使用传入参数，未传则从系统的环境变量获取
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL","https://api.deepseek.com")
        self.model = model or os.getenv("MODEL_NAME","deepseek-chat")
        self.timeout = timeout
        if not self.api_key:
            raise ValueError("未检测到有效的API Key,请在.env文件中配置OPENAI_API_KEY")

        #初始化官方异步客户端
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout,
        )

    # def chat (self,prompt: str,system_prompt: str | None = None) ->str:
    #     """同步方法占位（现代web API 推荐全面拥抱异步）"""
    #     raise NotImplementedError("生产环境请使用异步achat方法")

    async def chat(self,prompt: str,system_prompt: str | None = None) -> str:
        """异步调用云端大模型生成回答"""
        messages = []
        if system_prompt:
            messages.append({"role": "system","content": system_prompt})
        messages.append({"role": "user","content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.3, #RAG场景通常调低采样温度以保证真实性
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            #捕获网络抖动、超时或鉴权异常
            raise RuntimeError(f"调用云端LLM失败： {str(e)}") from e

async def main():
    print("===测试异步Mock LLM 客户端 ===")
    mock_client = MockLLMClient(response_delay=0.3)

    #模拟同时并发处理两个用户的问题
    question1 = "RAG的全称是什么？"
    question2 = "什么是余弦相似度"

    print("正在并发发送2个问题....")
    t1 = asyncio.create_task(mock_client.chat(question1))#asyncio.create_task()把这个协程立刻包装成一个正式任务直接扔进操作系统的事件循环传送带中，让它立刻在后台开始跑
    t2 = asyncio.create_task(mock_client.chat(question2))

    #并发等待结果返回
    ans1,ans2 = await asyncio.gather(t1,t2)#这里的await是要等两个答案都收集到
    print(f"回答1：{ans1}")
    print(f"回答2:{ans2}\n")

if __name__ == "__main__":
    asyncio.run(main())





























# import httpx

# class SimpleHttpClient:
#     """封装基于httpx的基础网络客户端"""

#     def __init__(self,timeout: float = 10.0) -> None:
#         self.timeout = timeout

#     def get_public_ip(self) -> dict:
#         """
#         发送GET请求:调用公开的httpbin 测试接口获取当前公网信息
#         """
#         url = "https://httpbin.org/get"
#         with httpx.Client(timeout=self.timeout) as client:
#             response = client.get(url)
#             #如果状态码时4xx或5xx，直接抛出HTTPStatusError异常防御
#             response.raise_for_status()
#             return response.json()

#     def simulate_mock_llm_call(self,prompt:str) -> dict:
#         """
#         发送POST请求:向测试接口发送JSON数据，模拟调用大模型API的网络交互
#         """
#         url = "https://httpbin.org/post"
#         payload = {
#             "model": "mock_llm-v1",
#             "messages": [{"role": "user", "content": prompt}],
#             "temperature":0.7,
#             }
#         headers = {
#             "Authrization": "Bearer mock-api-key-123446",
#             "Content-Type": "application/json",
#         }

#         with httpx.Client(timeout=self.timeout) as  client:
#             response = client.post(url,json=payload,headers=headers)
#             response.raise_for_status()
#             data = response.json()
#             #httpbin 会原样把收到的json字段放在'json'属性里返回给我们
#             return data.get("json",{})

# if __name__ == "__main__":
#     client = SimpleHttpClient(timeout=5.0)

#     print("1.正在测试GET请求...")
#     try:
#         get_res = client.get_public_ip()
#         print(f"GET 成功,你的公网IP/请求源：{get_res.get('origin')}\n")
#     except Exception as e:
#         print(f"GET请求失败:{e}\n")

#     print("2.正在模拟POST请求(向大模型发送Prompt)....")
#     test_prompt = "什么是RAG技术?"
#     try:
#         post_res = client.simulate_mock_llm_call(prompt=test_prompt)
#         print("POST模拟调用成功,远程服务器收到的参数载荷：")
#         print(post_res)
#     except Exception as e:
#         print(f"POST请求失败:{e}")
