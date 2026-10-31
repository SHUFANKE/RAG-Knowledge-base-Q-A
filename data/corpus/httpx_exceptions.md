# HTTPX 错误层级

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 请求与状态错误
RequestError 是发送请求过程中出现的错误基类；HTTPStatusError 对应调用 response.raise_for_status() 后报告的错误 HTTP 状态。二者都继承 HTTPError。应区分请求执行问题与已获得响应后的状态检查问题。

来源：https://www.python-httpx.org/exceptions/

## 2. 超时层级
TimeoutException 是超时错误基类，包含 ConnectTimeout、ReadTimeout、WriteTimeout、PoolTimeout。它属于 TransportError，进一步属于 RequestError。可捕获超时基类，也可按发生阶段捕获具体子类。

来源：https://www.python-httpx.org/exceptions/

## 3. 协议与网络错误
NetworkError 的子类包括 ConnectError、ReadError、WriteError 和 CloseError。ProtocolError 分为 LocalProtocolError 与 RemoteProtocolError，分别表示客户端或服务端违反协议。网络错误与协议错误都在传输错误体系中，不是 HTTP 状态码异常。

来源：https://www.python-httpx.org/exceptions/
