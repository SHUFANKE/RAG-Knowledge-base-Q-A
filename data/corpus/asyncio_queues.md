# Python 3.13 异步队列

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 容量与背压
asyncio.Queue 是先进先出队列。maxsize 大于零时，队列满后 await put() 等待，直到有元素被取走；maxsize 小于或等于零表示容量不受该参数限制。asyncio 队列不是线程安全的队列。

来源：https://docs.python.org/3.13/library/asyncio-queue.html

## 2. 任务完成计数
消费者取出并完成一个工作项后应调用 task_done()。入队增加未完成任务计数，task_done() 减少计数，计数降为零时 join() 结束等待。仅取走所有元素而不报告完成，不等于所有工作都已处理。

来源：https://docs.python.org/3.13/library/asyncio-queue.html

## 3. 操作超时
asyncio 队列的方法没有自己的 timeout 参数。若要对 get() 或 put() 设置等待时间，可用 asyncio.wait_for() 包装相应操作。get_nowait() 在无立即可取元素时抛出 QueueEmpty；put_nowait() 在队列已满时抛出 QueueFull。

来源：https://docs.python.org/3.13/library/asyncio-queue.html
