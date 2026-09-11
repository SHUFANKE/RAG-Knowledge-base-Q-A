import pytest
from app.llm_client import BaseLLMClient,MockLLMClient

def test_base_llm_cannot_instantiate():
    """验证抽象基类不能被直接实例化（接口契约测试）"""
    with pytest.raises(TypeError):
        BaseLLMClient()

@pytest.mark.asyncio#说明这是一个异步测试函数
async def test_mock_llm_client_chat():
    """验证MockLLMClient 能够正常响应异步chat请求"""
    client = MockLLMClient(response_delay=0.01)
    prompt = "测试问题"
    result = await client.chat(prompt)

    assert isinstance(result,str)

