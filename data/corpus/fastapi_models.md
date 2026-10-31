# FastAPI 请求验证与响应模型

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 请求体模型
请求体可用继承 Pydantic BaseModel 的类声明，并把该模型作为路径操作函数的参数类型。FastAPI 读取 JSON，按类型转换并验证数据，错误时指出数据问题的位置；同时生成 JSON Schema 并纳入 OpenAPI。

来源：https://fastapi.tiangolo.com/tutorial/body/

## 2. 响应字段过滤
响应模型通过返回类型或 response_model 声明。FastAPI 验证、序列化返回数据，并按模型限制输出字段。输入模型包含密码时，应使用不含密码的输出模型，避免把该字段返回给客户端。

来源：https://fastapi.tiangolo.com/tutorial/response-model/

## 3. 抛出 HTTP 异常
HTTPException 应通过 raise 抛出，而不是 return 返回。辅助函数中抛出的 HTTPException 也会终止当前请求的后续路径操作代码。可通过 status_code 和 detail 指定错误状态及信息，资源不存在的官方示例使用 404。

来源：https://fastapi.tiangolo.com/tutorial/handling-errors/
