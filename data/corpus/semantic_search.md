# 语义检索与查询编码

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 向量检索机制
语义检索将语料条目与查询嵌入同一向量空间，再寻找语义相近的语料向量。它关注含义，能够处理同义表达、缩写或拼写变化；这类能力不意味着任何问题都能在知识库中找到答案。

来源：https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html

## 2. 对称与非对称检索
对称语义检索中，查询与候选通常长度和信息量相近，例如相似问题匹配。非对称检索中，查询通常较短而候选段落较长，例如用问题寻找回答段落；两者的角色不能简单互换，应选择适合任务的模型。

来源：https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html

## 3. 查询和文档编码接口
Sentence Transformers 对非对称检索建议使用 encode_query 编码查询，encode_document 编码语料。模型存在相应提示或任务路由时，这些接口可应用对应配置；没有预定义提示和任务类型时，其行为可以与通用 encode 相同。

来源：https://sbert.net/examples/sentence_transformer/applications/semantic-search/README.html
