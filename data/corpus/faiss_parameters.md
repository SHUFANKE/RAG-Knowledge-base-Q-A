# FAISS 索引类型、检索参数与空间估算

## 1. 索引类型选型

IndexFlatL2 对全部已存向量执行 L2 距离搜索；IndexFlatIP 对全部已存向量执行内积搜索。它们属于穷举搜索，不需要训练。这里的精确指向量检索结果，不代表文档相关性或问答正确率为100%。

对数据库向量与查询向量都进行 L2 归一化后，可以用内积搜索实现余弦相似度排序。

IndexIVFFlat 将向量分配到多个倒排列表，查询时只扫描选中的列表。使用前需要训练，然后添加向量。

IndexIVFPQ 在倒排列表基础上使用乘积量化压缩向量，减少存储需求，但会引入量化误差。

来源：https://github.com/facebookresearch/faiss/wiki/Faiss-indexes
核验日期：2026-10-29；范围：官方 Wiki 所述索引行为，未绑定特定发布版本。

## 2. nlist 与 nprobe 的区别

nlist 是 IVF 索引的倒排列表或聚类单元总数；nprobe 是每次查询时访问的列表数量。

增加 nprobe 通常会扫描更多候选向量，改善召回，同时增加搜索开销。官方教程将搜索时间描述为随探查数量大致线性增加，并包含量化带来的固定开销；这不是所有数据和硬件上的严格耗时公式。

对于已经训练并添加向量的普通 IndexIVFFlat 对象，可以通过 index.nprobe = 10 设置探查数量，再调用 index.search(xq, k)。其中 xq 是查询向量，k 是希望返回的近邻数量。nprobe 与 k 控制的对象不同，不能混为一谈。

来源：https://github.com/facebookresearch/faiss/wiki/Faster-search
核验日期：2026-10-29；范围：官方 IndexIVFFlat 教程。

## 3. 原始向量数据量估算

float32 每个元素占4字节。N条、每条d维的原始向量数据量为 N × d × 4 字节。

例如100万条768维float32向量，原始数据量为：
1,000,000 × 768 × 4 = 3,072,000,000 字节，
按十进制单位约为3.072 GB，按二进制单位约为2.861 GiB。

以上数值由公式计算，不是实测内存。它不包含额外的向量ID、倒排列表、图结构、文档文本、Python对象和运行时缓存。不同索引的完整内存需求不能一律按原始向量数据量计算。

来源：https://github.com/facebookresearch/faiss/wiki/Faiss-indexes
核验日期：2026-10-29；范围：基于官方 Flat 索引4*d字节每向量的说明进行计算。