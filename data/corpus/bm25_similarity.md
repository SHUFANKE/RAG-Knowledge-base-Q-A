# Elasticsearch BM25 参数边界

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 词频饱和
Elasticsearch 默认 BM25 相似度基于词频与逆文档频率，并内置词频规范化。k1 控制非线性词频归一化的饱和程度，官方默认为 1.2。这里的默认值属于 Elasticsearch，不应未经核查直接视为任何 Python BM25 库或本项目的默认值。

来源：https://www.elastic.co/docs/reference/elasticsearch/index-settings/similarity

## 2. 长度归一化
Elasticsearch BM25 的 b 控制文档长度对词频归一化的影响程度，官方默认值为 0.75。它与 k1 的词频饱和作用不同，也不是向量 L2 归一化参数；文档长度和向量长度属于不同度量对象。

来源：https://www.elastic.co/docs/reference/elasticsearch/index-settings/similarity

## 3. 重叠 token 的规范化
Elasticsearch BM25 的 discount_overlaps 决定计算 norm 时是否忽略位置增量为零的重叠 token。默认值为 true，即此类 token 不计入该 norm 的长度。这里的重叠是分析器 token 位置概念，不是文档切片的 chunk_overlap。

来源：https://www.elastic.co/docs/reference/elasticsearch/index-settings/similarity
