# HTTPX 超时类型与配置

## 1. 默认超时与总耗时的区别

HTTPX 默认在网络操作持续不活动5秒后触发超时，而不是要求整个请求从开始到结束必须在5秒内完成。

读取响应时，read timeout 约束的是等待下一块数据的时间。如果响应持续分块到达，整个响应的总耗时可能超过这个数值。

因此，不能把 timeout=30.0 描述为严格的整条业务流程30秒截止时间。RAG中的检索、重排和生成如果是独立请求，也不能把某一个HTTP请求的超时值当成整条流程的时间上限。

来源：https://www.python-httpx.org/advanced/timeouts/
核验日期：2026-10-29；范围：HTTPX官方文档所述超时语义。

## 2. connect 与 read 超时

connect timeout 控制等待建立套接字连接的最长时间，超出时抛出 ConnectTimeout。

read timeout 控制等待接收下一块响应数据的最长时间，超出时抛出 ReadTimeout。

建立连接失败与连接建立后迟迟收不到响应数据属于不同阶段，不能只看“超时”两个字就认定原因相同。

来源：https://www.python-httpx.org/advanced/timeouts/
核验日期：2026-10-29；范围：HTTPX官方文档所述超时语义。

## 3. write 与 pool 超时

write timeout 控制发送一块请求数据时允许等待的最长时间，超出时抛出 WriteTimeout。

pool timeout 控制从客户端连接池获取连接时允许等待的最长时间，超出时抛出 PoolTimeout。

PoolTimeout 可能发生在请求尚未获得可用连接时，不能据此判断远端模型已经收到并开始处理请求。

来源：https://www.python-httpx.org/advanced/timeouts/
核验日期：2026-10-29；范围：HTTPX官方文档所述超时语义。

## 4. 客户端默认配置与分项配置

httpx.Client(timeout=10.0) 为客户端请求设置默认超时；AsyncClient也支持超时配置。

httpx.Timeout(10.0, connect=60.0) 表示连接阶段允许等待60秒，其他超时类型使用10秒。可将该Timeout对象传给客户端。

timeout=None 表示禁用相应配置范围内的超时限制，不是“立即超时”。

来源：https://www.python-httpx.org/advanced/timeouts/
核验日期：2026-10-29；范围：HTTPX官方文档所述超时配置。