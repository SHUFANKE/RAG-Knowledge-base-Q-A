import asyncio
import httpx

async def run_multi_turn_test():
    url = "http://127.0.0.1:8000/api/chat"

    async with httpx.AsyncClient(timeout=30.0,trust_env=False) as client:
        #第一轮提问
        q1 = "FastAPI 生产部署时，工作进程 workers 的推荐计算公式是什么？"
        print("=" * 60)
        print(f"【用户第 1 轮提问】: {q1}")
        resp1 = await client.post(url,json={"query": q1,"history":[]})
        print(f"【HTTP状态码】：{resp1.status_code}")
        if resp1.is_error:
            print(f"【错误响应】：{resp1.text}")
        resp1.raise_for_status()
        data1 = resp1.json()
        print(f"【助手回答 1】: {data1['answer'][:80]}...\n")

        #构造带历史上下文的第二轮提问
        history = [
            {"role": "user","content":q1},
            {"role":"assistant","content":data1["answer"]},
        ]
        q2 = "那如何通过启动命令设置这个参数呢？"  # 极度依赖上文指代
        print("=" * 60)
        print(f"【用户第 2 轮模糊提问】: {q2}")
        print(f"【发送的历史消息】：{history}")

        resp2 = await client.post(url, json={"query":q2,"history":history})
        print(f"【HTTP 状态码】: {resp2.status_code}")
        if resp2.is_error:
            print(f"【错误响应】: {resp2.text}")
        resp2.raise_for_status()
        data2 = resp2.json()

        print(f"【识别改写后的 Query】: {data2['rewritten_query']}")
        print(f"【改写耗时】: {data2['metrics']['rewrite_ms']} ms")
        print(f"【命中切片】: {[r['chunk_id'] for r in data2['references']]}")
        print(f"【助手最终回答 2】:\n{data2['answer']}")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_multi_turn_test())
