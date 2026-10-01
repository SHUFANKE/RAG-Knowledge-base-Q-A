# FastAPI 生产环境配置指南

## 1. 核心运行参数
FastAPI 应用在生产环境中推荐通过 Uvicorn 或 Gunicorn 配合 UvicornWorker 启动。
核心参数配置规范如下：
- `workers`: 推荐设置为 `(2 * CPU核心数) + 1`，用于充分利用多核并发能力。
- `timeout_keep_alive`: 生产环境建议设为 65 秒，需略高于前端反向代理（如 Nginx）的 keep-alive 超时时间，防止出现 502 错误。
- `limit_concurrency`: 限制最大并发连接数，防止突发流量打垮单节点内存，默认不限制。

## 2. 中间件与跨域规范
在微服务架构下，跨域请求必须显式配置 `CORSMiddleware`。
严禁在生产环境中将 `allow_origins` 设为 `["*"]` 且同时开启 `allow_credentials=True`，这会导致浏览器跨域策略拦截并引发严重安全漏洞。
正确的做法是指定精确的安全域名白名单，例如 `allow_origins=["https://api.example.com"]`。

## 3. 异常处理与状态码
全局异常捕获必须挂载 `HTTPException` 和自定义的 `AppException`。
对于未捕获的内部错误，必须统一返回 HTTP 500 状态码，并在响应体中隐藏敏感的堆栈调用栈，防止内部代码结构泄露。