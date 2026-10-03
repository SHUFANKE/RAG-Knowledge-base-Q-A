import asyncio
from app.llm_client import OpenAILikeLLMClient

async def main ():
    print(">>>正在连接云端大模型API...")
    try:
        client = OpenAILikeLLMClient()
        prompt = "你好！请用一句话解释什么是RAG技术。"
        response = await client.chat(prompt=prompt)
        print(response)
    except Exception as e:
        print(f"\n[Error]连接失败：{e}")

if __name__ == "__main__":
    asyncio.run(main())
