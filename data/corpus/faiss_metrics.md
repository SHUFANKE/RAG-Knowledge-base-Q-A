# FAISS 官方距离度量说明

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 平方欧氏距离
FAISS 的 METRIC_L2 返回平方欧氏距离，以避免开平方；它与欧氏距离的排序关系一致。若需要欧氏距离的实际数值，应对返回值开平方。该度量对正交旋转保持不变。

来源：https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances

## 2. 余弦归一化
用内积索引做余弦检索时，数据库向量在入库前、查询向量在搜索前都应归一化，可使用 faiss.normalize_L2。仅选择 METRIC_INNER_PRODUCT 并不自动得到余弦相似度；向量必须归一化到单位长度。

来源：https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances

## 3. 归一化后的度量关系
当两个向量都归一化到单位长度时，平方 L2 距离等于 2 - 2 * 内积。内积越大，平方 L2 越小，因此在相同归一化条件下，最大内积搜索与最小 L2 距离搜索可对应相同的排序。

来源：https://github.com/facebookresearch/faiss/wiki/MetricType-and-distances
