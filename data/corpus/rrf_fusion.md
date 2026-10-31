# RRF 多路检索排名融合

## 1. 为什么使用排名融合

Reciprocal Rank Fusion，简称RRF，用于把多个检索结果列表融合成一个列表。

不同检索器的原始评分可能采用不同的尺度，直接相加需要考虑尺度与权重。RRF使用文档在各列表中的名次计算贡献，不要求原始分数具有相同含义。

例如，BM25结果与Dense结果可以通过RRF融合，而不必先把两种原始评分转换成同一种分数。

来源：https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
核验日期：2026-10-29；范围：RRF算法原理，不要求项目使用Elasticsearch。

## 2. RRF 计算公式

对于候选文档d，等权RRF分数为：

score(d) = Σ 1 / (c + rank_i(d))

rank_i(d) 表示文档d在第i个结果列表中的名次，从1开始；c是排名常数。文档没有出现在某个列表中时，该列表不为它贡献分数。

示例：文档在两路中分别排名第1和第4，c=60，则融合分数为1/61 + 1/64。这里使用的是名次，不是两路检索器的原始分数。

来源：https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
核验日期：2026-10-29；范围：公式依据官方说明，示例为公式代入。

## 3. 排名常数与候选窗口

排名常数c控制不同名次之间的贡献差异。较大的c会减弱头部名次相对于后部名次的优势。

排名常数不是最终返回条数。各路候选窗口决定哪些文档能够参与融合；最终输出条数决定融合排序后保留多少结果。

工程推论：在所有输入列表中都未出现的文档，无法通过RRF凭空进入结果。因此，扩大候选窗口与增大最终返回条数不是同一件事。

来源：https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
核验日期：2026-10-29；范围：参数含义依据官方说明，候选边界由公式推得。

## 4. RRF 与语义重排的区别

RRF读取的是多个结果列表及其名次，不需要读取文档正文来重新判断问题与文档的语义关系。

Cross-Encoder重排则把问题与候选正文一起交给模型，重新计算相关性。两者可以前后组合：先融合候选列表，再对融合结果进行重排。

RRF分数由排名公式计算，不能解释为答案正确概率；融合后排名靠前，也不能替代对证据内容的检查。

来源：
https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
核验日期：2026-10-29；范围：两类方法的输入和作用对比；概率边界由计算方式推得。