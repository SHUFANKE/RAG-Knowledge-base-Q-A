# FAISS 索引读写与完整性

资料类型：根据一手资料编写的中文学习摘要，非官方原文全文。
核验日期：2026-10-04。Python 内容以 3.13 文档为边界；其他资料为当日网页快照摘要。

## 1. 索引保存和恢复
FAISS 使用 write_index 将索引写入文件，read_index 从文件读取索引。这些读写操作产生深拷贝。向量索引保存与项目自己的外部文本元数据保存不是同一个接口保证，应分别管理需要恢复的数据。

来源：https://github.com/facebookresearch/faiss/wiki/Index-IO,-cloning-and-hyper-parameter-tuning

## 2. GPU 写入限制
FAISS 不支持直接把 GPU 索引写入文件，应先转为 CPU 索引。index_gpu_to_cpu 用于从 GPU 复制到 CPU，随后可以使用 write_index。CPU 与 GPU 复制属于索引转换，不能将 GPU 对象直接写盘当作受支持流程。

来源：https://github.com/facebookresearch/faiss/wiki/Index-IO,-cloning-and-hyper-parameter-tuning

## 3. 加载安全边界
FAISS 索引读取接口不检查文件内容是否正确。错误或恶意文件可能造成内存耗尽，精心构造时甚至可能导致代码执行。读取前由使用者确认 write_index 生成的文件未被篡改，不能把可读取当成可信来源的证明。

来源：https://github.com/facebookresearch/faiss/wiki/Index-IO,-cloning-and-hyper-parameter-tuning
