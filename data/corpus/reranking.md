# 检索候选与 Cross-Encoder 重排

## 1. 为什么分为检索与重排

两阶段检索先使用高效检索器，从文档集合中选出一批可能相关的候选，再使用重排模型评估这些候选。

第一阶段可以采用词项检索，也可以采用向量检索。第二阶段进一步区分候选与问题的相关程度，调整顺序。

这种设计把计算较贵的重排限制在较小的候选集合上，而不是对整个大型文档库逐篇评分。

来源：https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
核验日期：2026-10-29；范围：Retrieve & Re-Rank基本流程。

## 2. Bi-Encoder 与 Cross-Encoder

Bi-Encoder分别编码问题和文档，生成各自的向量，再通过向量比较进行检索。文档向量可以提前计算。

Cross-Encoder把问题与一篇候选文档共同输入模型，让二者在模型内部交互，并输出相关性分数。

因此，Cross-Encoder重排不等于重新比较两条已经缓存好的独立向量。

来源：https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
核验日期：2026-10-29；范围：两种编码方式的区别。

## 3. 候选数量与最终返回数量

候选数量决定本次交给重排器评分的文档范围；最终返回数量决定从重排结果中取出多少篇。

工程推论：如果必要证据没有进入候选集合，重排器不能通过重新排序找回它。遇到漏证据，应先检查候选召回，再检查重排顺序。

对更多问题与文档组合进行评分会增加计算工作量，因此候选集合大小需要结合召回效果和耗时选择。

来源：https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
核验日期：2026-10-29；范围：候选重排机制；漏召回边界由两阶段流程推得。

## 4. 重排分数与答案正确性的边界

Cross-Encoder重排输出的是问题与候选文档的相关性评分。相关文档不一定包含用户所需的具体结论、参数值或操作步骤。

工程推论：不能仅凭高重排分数就认定回答正确，也不能把某个分数直接解释成回答正确概率。

最终回答仍需要检查证据是否支持相应陈述；设置过滤阈值时，也需要评估是否误删必要证据。

来源：https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html
核验日期：2026-10-29；范围：相关性评分依据官方说明；回答与阈值边界为工程解释。