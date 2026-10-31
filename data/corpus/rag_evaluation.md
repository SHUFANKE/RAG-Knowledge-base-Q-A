# RAG 检索与回答评测维度

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 回答忠实性
Faithfulness 检查生成回答的声明能否由检索上下文支持。将回答拆为声明，逐条判断是否可从上下文推得，再以被支持声明数除以回答声明总数。该指标范围为 0 到 1；它评估回答与给定证据的一致性，不是简单比较字符串。

来源：https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/faithfulness/

## 2. 上下文召回
LLM 方式的 Context Recall 以参考答案为比较依据，将参考答案拆为声明，检查哪些声明能由检索上下文支持。支持的参考声明数除以参考声明总数得到比例。它关注是否漏掉必要证据，区别于对生成回答声明计算的 Faithfulness。

来源：https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_recall/

## 3. 上下文排序精度
Context Precision 检查检索上下文中相关切片是否排在不相关切片之前。Ragas 的该维度以相关性标记与各排名位置的 Precision@k 计算排序质量；仅找全证据却把大量不相关材料排在前面，不能说明排序精度良好。

来源：https://docs.ragas.io/en/stable/concepts/metrics/available_metrics/context_precision/
