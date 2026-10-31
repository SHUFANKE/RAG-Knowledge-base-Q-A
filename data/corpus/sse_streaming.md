# SSE 事件格式与连接状态

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 编码与事件边界
SSE 响应采用 text/event-stream 类型，事件流按 UTF-8 解码。消息由空行分隔，data 字段承载文本；连续多个 data 行用换行拼接。单个 HTTP 接收数据块不必等于完整 SSE 事件，应按事件格式识别消息边界。

来源：https://html.spec.whatwg.org/multipage/server-sent-events.html

## 2. 命名事件与注释
SSE 的 event 字段指定事件类型，未指定时默认类型为 message。客户端可用 addEventListener 监听命名事件。以冒号开始的行是注释，不作为消息数据；服务端可定期发送注释作为保活内容。

来源：https://html.spec.whatwg.org/multipage/server-sent-events.html

## 3. 重连和终止
EventSource 在连接结束后通常尝试重连，retry 字段以整数毫秒指定重连等待；非整数值会被忽略。调用 EventSource.close() 可终止连接，HTTP 204 响应可告知客户端停止重连。id 字段用于记录最后事件 ID，重连时可通过 Last-Event-ID 传给服务端。

来源：https://html.spec.whatwg.org/multipage/server-sent-events.html
