import asyncio
import json
import httpx

async def test_non_streaming():
    """测试标准全量接口（/api/chat）"""
    url = "http://127.0.0.1:8000/api/chat"
    payload = {
        "query" : "HTTPX 的 read timeout 设置为30秒，是否要求整个响应30秒内接收完成？",
        "final_k": 3,
        "rerank_threshold": 0.45,
    }

    print("\n" + "=" * 60)
    print(">>>[测试 1]正在请求全量问答接口（/api/chat）...")
    print("="* 60)

    async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    print(f"【回答内容】:\n{data['answer']}\n")
    print("【引用切片】:")
    for ref in data["references"]:
        print(f"  - 切片ID: {ref['chunk_id']} | 重排得分: {ref['rerank_score']:.4f}")
    print("\n【耗时指标】:")
    print(f"  - 检索耗时: {data['metrics']['retrieval_ms']} ms")
    print(f"  - 生成耗时: {data['metrics']['generation_ms']} ms")
    print(f"  - 总耗时:   {data['metrics']['total_ms']} ms")

async def test_streaming():
    """测试打字机流式接口（/api/chat/stream）"""
    url = "http://127.0.0.1:8000/api/chat/stream"
    payload ={
        "query":"HTTPX 的 read timeout 设置为30秒，是否要求整个响应30秒内接收完成？",
        "final_k":3,
        "rerank_threshold": 0.45,
    }

    print("\n" + "=" * 60)
    print(">>> [测试 2] 正在请求 SSE 流式打字机接口 (/api/chat/stream)...")
    print("=" * 60)
    print("【流式实时输出】: ", end="", flush=True)

    async with httpx.AsyncClient(timeout=60.0, trust_env=False) as client:
        async with client.stream("POST", url, json=payload) as response:
            if response.is_error:
                await response.aread()
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    print("\n\n>>>[流式传输结束]")
                    break

                event_data = json.loads(data_str)
                event_type = event_data.get("type")

                if event_type == "token":
                    #模拟打字机逐字输出
                    print(event_data["content"], end = "",flush=True)

async def main():
    failed = False
    for test in (test_non_streaming, test_streaming):
        try:
            await test()
        except httpx.HTTPStatusError as exc:
            failed = True
            print(f"\n【接口失败】HTTP {exc.response.status_code}: {exc.request.url}")
            print(f"【服务端响应】{exc.response.text[:2000]}")
        except httpx.RequestError as exc:
            failed = True
            print(f"\n【请求失败】{type(exc).__name__}: {exc}")
            print("请确认本地 API 服务已启动并监听 127.0.0.1:8000。")
    if failed:
        raise SystemExit(1)

if __name__ == "__main__":
    asyncio.run(main())

