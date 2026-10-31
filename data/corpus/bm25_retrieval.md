# BM25 关键词检索与分词

## 1. BM25 的检索依据

BM25 是基于词项匹配的相关性排序方法。它利用查询词与文档词项的匹配，以及词频、文档频率和文档长度等信息计算排序分数。

词项匹配与语义匹配不同。对于函数名、配置名等明确标识符，保留正确的词项有助于检索；对于没有共同词项的同义表达，单纯的词项匹配可能无法召回。

来源：
https://www.elastic.co/docs/reference/elasticsearch/index-settings/similarity
https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
核验日期：2026-10-29；范围：BM25与词项检索的基本原理。

## 2. k1 与 b 的作用

BM25 中，k1 控制词频贡献的饱和程度。同一个词在文档中反复出现，其评分贡献不是无限线性增加。

b 控制文档长度归一化的程度，用于调整文档长度对词频评分的影响。

不同实现的默认参数不一定相同。例如Elasticsearch文档给出的k1默认值为1.2、b为0.75，不能直接把这些默认值当成所有Python库的配置。

来源：https://www.elastic.co/docs/reference/elasticsearch/index-settings/similarity
核验日期：2026-10-29；范围：参数含义通用，所列默认值仅对应Elasticsearch文档。

## 3. rank_bm25 的输入与预处理

rank_bm25 的 BM25Okapi 接收由词项列表组成的文档集合，即每篇文档先转换成字符串列表。

该库不会自动完成小写转换、停用词删除或词干处理。查询也需要分词，并采用与文档一致的预处理规则。

因此，使用中文文本时，调用方需要自行提供合适的分词结果；库本身不会自动选择中文分词器。

来源：https://github.com/dorianbrown/rank_bm25
核验日期：2026-10-29；范围：rank_bm25项目README说明。

## 4. 分数与返回条数

BM25Okapi.get_scores(tokenized_query) 返回查询对各篇文档的评分，get_top_n() 可以根据评分取出指定数量的文档。

工程解释：取前k名仅表示在当前集合中排名靠前，不表示这k篇都能回答问题。即使所有文档都不相关，排序操作本身仍可以产生一个前k名列表。

因此，BM25排名不能单独作为“资料足以回答问题”的证明。

来源：https://github.com/dorianbrown/rank_bm25
核验日期：2026-10-29；范围：接口行为依据README；回答充分性边界为工程解释。