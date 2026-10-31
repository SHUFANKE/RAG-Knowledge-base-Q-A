# Elasticsearch RRF 排名融合

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 融合公式
Reciprocal Rank Fusion 对文档在各结果列表的排名计算贡献：score(d) = sum 1 / (k + rank_i(d))。rank 从 1 开始，文档不在某列表中则该列表不贡献。RRF 使用名次融合，适合组合不同相关性指标的检索结果，无需先把原始得分统一为同一尺度。

来源：https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion

## 2. 排名常数
Elasticsearch RRF 的 rank_constant 对应公式中的 k，默认值 60，至少为 1。较大的常数使单个结果列表中较低排名的文档获得相对更大的影响。该常数不是最终返回数量，也不是对分数的直接拒答阈值。

来源：https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion

## 3. 候选窗口
Elasticsearch RRF 的 rank_window_size 控制每个子检索器参与融合的结果数量。它应至少为最终 size，并且至少为 1；默认等于 size。增大窗口通常改善相关性但增加性能开销，融合后再裁剪到最终返回数量。

来源：https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
