# HTTPX 客户端复用与异步流

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 连接池复用
HTTPX 顶层请求 API 每次建立新连接。Client 使用连接池，对同一主机可复用底层 TCP 连接，降低重复握手开销。多个请求还可共享配置与 Cookie；同步 Client 可用 with 管理，并在退出时清理连接。

来源：https://www.python-httpx.org/advanced/clients/

## 2. 异步客户端生命周期
异步 HTTP 请求使用 AsyncClient，请求方法需要 await。可通过 async with 管理客户端，或显式 await client.aclose()。为了发挥连接池作用，应复用合适作用域的客户端，避免在高频循环内不断创建新实例。

来源：https://www.python-httpx.org/async/

## 3. 流式响应清理
AsyncClient.stream 返回异步上下文块，可以用 aiter_bytes、aiter_text 或 aiter_lines 增量读取响应。退出 stream 上下文会关闭响应；若手动 send(..., stream=True)，开发者必须最终调用 Response.aclose()，否则可能泄露连接资源。

来源：https://www.python-httpx.org/async/
