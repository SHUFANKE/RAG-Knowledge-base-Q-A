# 两阶段检索与重排

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 召回阶段
两阶段搜索先用高效检索器从大规模文档集合产生候选，再用更昂贵的重排器重新排序。初始召回可使用词法检索或 Bi-Encoder 向量检索。检索器追求高效，仍可能返回不相关候选，重排阶段处理这个候选集合。

来源：https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html

## 2. Cross-Encoder 联合打分
Cross-Encoder 同时接收查询与一个候选文档，通过二者之间的注意力进行相关性打分。相比独立编码，它对查询和文档有联合建模能力，但逐对评估海量文档较慢，所以通常只用于候选重排。

来源：https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html

## 3. 候选边界
在先检索再重排的流程中，重排器只给已经召回的候选打分。若需要的段落不在候选集合中，单纯调整候选内部排序无法把它补回；必须回查初始召回。最终输出再从重排候选中选取较少的高排名段落。

来源：https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
