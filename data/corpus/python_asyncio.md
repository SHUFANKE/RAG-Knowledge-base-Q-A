# Python asyncio 调度、阻塞与并发原语

## 1. 事件循环与协作式调度

调用 async def 定义的函数会创建协程对象，不会仅因这次调用就执行协程体。可以通过 await、asyncio.create_task() 或顶层 asyncio.run() 驱动执行。

事件循环采用协作式调度：同一个事件循环一次执行一个任务。任务等待尚未完成的异步操作时，可以让其他就绪任务运行；不能认为每个 await 都一定发生任务切换。

事件循环不是整个程序全局唯一。asyncio.run() 会创建并管理一个事件循环，结束时关闭它；同一线程已经有运行中的事件循环时，不能再次调用 asyncio.run()。

来源：https://docs.python.org/3.10/library/asyncio-task.html
核验日期：2026-10-29；版本范围：Python 3.10。

## 2. 阻塞调用与线程转移

在事件循环线程中直接执行耗时的同步操作，例如 time.sleep()，会占用该线程，使其他任务无法在这段时间内正常获得调度。把函数声明为 async def 不会自动把内部同步调用变成异步调用。

asyncio.sleep() 在等待期间会挂起当前任务。对于需要复用的阻塞式IO函数，可以使用 await asyncio.to_thread(func, *args) 在线程中执行。

to_thread() 主要用于阻塞式IO。对于通常受CPython GIL限制的纯Python计算任务，不能直接假定转移到线程就能获得多核并行加速。

来源：https://docs.python.org/3.10/library/asyncio-task.html#running-in-threads
核验日期：2026-10-29；版本范围：Python 3.10。

## 3. gather、TaskGroup 与 Semaphore

asyncio.gather() 并发运行传入的可等待对象。全部成功时，结果顺序对应输入顺序，而不是完成顺序。

默认 return_exceptions=False：首个异常会立即传播给等待 gather() 的调用者，其他任务不会仅因这个异常被自动取消。设置 return_exceptions=True 时，异常会作为结果项收集。

TaskGroup 从Python 3.11开始提供，Python 3.10不能直接使用。组内任务出现非 CancelledError 异常时，TaskGroup 会取消其余任务，并等待它们结束。

asyncio.Semaphore 控制共享同一个信号量的任务同时进入指定区域的数量。它不是跨进程的全局限流器，也不直接保证每分钟请求数不超过某个值。

来源：
https://docs.python.org/3.10/library/asyncio-task.html#running-tasks-concurrently
https://docs.python.org/3.11/library/asyncio-task.html#task-groups
https://docs.python.org/3.10/library/asyncio-sync.html#semaphore
核验日期：2026-10-29；版本范围：gather与Semaphore按Python 3.10，TaskGroup按Python 3.11。