# FastAPI 生命周期与资源管理

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 启动时初始化
FastAPI 的 lifespan 参数接收异步上下文管理器，可由 asynccontextmanager 装饰的异步函数提供。yield 之前的代码在应用开始接收请求前运行，适合加载共享模型或建立长期使用的资源。

来源：https://fastapi.tiangolo.com/advanced/events/

## 2. 关闭时清理
lifespan 中 yield 之后的代码在应用结束处理请求、关闭时运行。该阶段用于释放启动时持有的模型、内存或其他共享资源，与 yield 之前的初始化形成资源生命周期。

来源：https://fastapi.tiangolo.com/advanced/events/

## 3. 与旧事件机制的关系
官方推荐用 lifespan 管理启动和关闭。提供 lifespan 参数后，旧 startup 和 shutdown 事件处理器不再被调用。应选择完整的 lifespan 机制或旧事件机制，不能期待两套机制同时执行。

来源：https://fastapi.tiangolo.com/advanced/events/
