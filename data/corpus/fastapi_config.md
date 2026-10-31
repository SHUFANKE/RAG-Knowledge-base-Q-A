# FastAPI 生产环境配置指南

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-29。范围：FastAPI 与 Uvicorn 官方文档，不作为所有部署环境的固定配置模板。

## 1. 核心运行参数

FastAPI 应用可以通过 Uvicorn 运行。`--workers` 指定工作进程数量，与 `--reload` 不能同时使用。不能把 `(2 * CPU核心数) + 1` 当成所有 FastAPI 应用的通用推荐值。

`--timeout-keep-alive` 控制 Keep-Alive 连接在没有收到新数据时的等待秒数，Uvicorn 文档中的默认值为5秒。它不是生成模型请求的总耗时上限，也没有适用于所有部署环境的固定65秒要求。

`--limit-concurrency` 限制允许的并发连接或任务数量，超出限制时返回 HTTP 503。它与工作进程数量、Keep-Alive 超时控制的对象不同。

来源：https://www.uvicorn.org/

## 2. 中间件与跨域规范

浏览器中的前端与后端使用不同协议、域名或端口时，属于不同来源。需要允许浏览器跨源访问时，可以使用 `CORSMiddleware` 配置允许的来源、方法、请求头和凭据。

来源应包含协议、域名以及需要时的端口，例如 `https://app.example.com`。不能仅因为系统采用微服务架构，就认定所有服务之间的 HTTP 调用都必须配置 CORS。

`allow_credentials=True` 用于允许携带凭据的跨源请求。按 FastAPI 官方文档，此时 `allow_origins`、`allow_methods` 和 `allow_headers` 应显式配置，不能使用 `["*"]` 通配符。

来源：https://fastapi.tiangolo.com/tutorial/cors/

## 3. 异常处理与状态码

可通过 `raise HTTPException(status_code=..., detail=...)` 返回明确的 HTTP 错误，例如资源不存在时使用404。`HTTPException` 应抛出而不是作为普通返回值返回；辅助函数中抛出它也会终止当前请求的后续处理。

FastAPI 已提供 `HTTPException` 和请求验证错误的默认处理器。需要自定义错误响应时，可以使用 `@app.exception_handler(...)` 注册处理器，不要求每个项目都创建名为 `AppException` 的异常类。

错误响应与服务端诊断日志用途不同。对外返回的信息应避免包含敏感内部细节；不能将包含内部位置等信息的异常直接转换成字符串返回给客户端。

来源：https://fastapi.tiangolo.com/tutorial/handling-errors/
