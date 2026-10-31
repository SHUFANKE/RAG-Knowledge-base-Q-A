# Sentence Transformers 检索评测接口

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 评测输入映射
InformationRetrievalEvaluator 接收 queries、corpus 和 relevant_docs。前两者分别把查询 ID 映射到查询文本、文档 ID 映射到文档文本；relevant_docs 把每个查询 ID 映射到相关文档 ID 集合。需要对齐这些标识，不能把任意检索结果自动当成标准相关文档。

来源：https://sbert.net/docs/package_reference/sentence_transformer/evaluation.html

## 2. 排名指标截断
InformationRetrievalEvaluator 报告 MRR、Recall@k、NDCG 等检索指标。mrr_at_k、ndcg_at_k 和 precision_recall_at_k 可分别配置这些指标使用的截断 k 列表。同一指标比较应明确使用哪个 k；这些 k 不代表服务器线程数或训练轮数。

来源：https://sbert.net/docs/package_reference/sentence_transformer/evaluation.html

## 3. 重排正负样本
RerankingEvaluator 的每个样本包含 query、positive 和 negative。它对查询与候选文档配对打分并排序，再计算 MRR、NDCG、MAP 等排序指标。positive 和 negative 是用于判断排名质量的相关与不相关候选，区别于只包含查询文本而无相关性标注的输入。

来源：https://sbert.net/docs/package_reference/sentence_transformer/evaluation.html
