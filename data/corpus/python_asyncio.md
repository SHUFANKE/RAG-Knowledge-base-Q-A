# Python 协程与 Asyncio 底层机制

## 1. 事件循环与协作式调度
Python 的 `asyncio` 基于单线程协作式多任务调度器，其核心是全局唯一的 Event Loop（事件循环）。
协程函数使用 `async def` 声明，调用时返回一个协程对象，该对象必须通过 `await` 或调度进事件循环才能实际执行。
协程切换的触发条件是当前任务主动让出控制权，例如遇到 `asyncio.sleep()` 或异步网络 IO 操作。

## 2. 阻塞与防坑指南
在协程函数中严禁调用耗时的大计算量操作或同步阻塞调用（例如 `time.sleep()`、`requests.get()`、原生同步文件读写）。
任何同步阻塞操作都会直接卡死当前的 Event Loop，导致该线程上的所有其他并发并发任务停滞。
如必须运行阻塞调用，应使用 `asyncio.to_thread()` 将任务分发至独立的系统线程池执行。

## 3. 常见并发原语
- `asyncio.gather(*tasks)`: 并发调度多个可等待对象，保留原有顺序返回聚合结果；如果其中一个任务报错，默认仍会等待其余任务执行完毕。
- `asyncio.TaskGroup`: Python 3.11 引入的上下文管理器，提供结构化并发（Structured Concurrency）支持。一旦任意子任务抛出异常，其余任务会立即自动取消。
- `asyncio.Semaphore`: 信号量，用于对下游有限资源（如高并发 LLM API 调用）进行全局限流。