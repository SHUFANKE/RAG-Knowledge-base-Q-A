# Python 3.13 任务异常与超时

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. gather 异常语义
asyncio.gather 默认 return_exceptions=False：第一个异常立即传播给等待 gather 的调用者，其他可等待对象不会因此自动取消，仍可继续执行。return_exceptions=True 则把异常当作结果收集进列表。不能将默认行为理解为等待全部任务结束后才报告首个异常。

来源：https://docs.python.org/3.13/library/asyncio-task.html

## 2. TaskGroup 异常与取消
TaskGroup 中一个任务首次抛出非 CancelledError 异常时，组内剩余任务被取消；上下文退出会等待任务结束。通常将非取消异常组合为 ExceptionGroup 或 BaseExceptionGroup；KeyboardInterrupt 和 SystemExit 有特殊重抛规则。

来源：https://docs.python.org/3.13/library/asyncio-task.html

## 3. wait_for 超时
asyncio.wait_for(aw, timeout) 带超时等待可等待对象。发生超时时取消 aw 并抛出内置 TimeoutError。函数会等待取消实际完成，因此总等待时间可能超过 timeout；用 shield 包装可阻止 aw 因此次超时被取消。

来源：https://docs.python.org/3.13/library/asyncio-task.html
