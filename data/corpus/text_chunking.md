# 文本切片的长度单位与重叠

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 递归分隔与长度
RecursiveCharacterTextSplitter 按分隔符列表顺序尝试切分，直到片段足够小，尽量保留段落等相邻内容。默认依次考虑双换行、单换行、空格和空字符串。chunk_size 的长度单位由 length_function 决定；使用 len 时通常按字符计数。

来源：https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter

## 2. 重叠与中文分隔
chunk_overlap 是相邻片段的目标重叠，用于减轻上下文在切片边界被割裂造成的信息损失。中文等没有明显词间空格的语言可增加句号、逗号、顿号等分隔符，避免只依赖空格切分。目标重叠不等于所有实际片段必定重叠完全相同的长度。

来源：https://docs.langchain.com/oss/python/integrations/splitters/recursive_text_splitter

## 3. token 预算与 Unicode
模型有 token 上限，估算切片长度应使用与目标模型相同的 tokenizer，字符数不能直接替代 token 数。直接 TokenTextSplitter 可能把中文字符的多 token 编码拆到不同片段，造成无效 Unicode；文档建议使用相应字符切分器的 from_tiktoken_encoder 方式保持字符串有效。

来源：https://docs.langchain.com/oss/python/integrations/splitters/split_by_token
