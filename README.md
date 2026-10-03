# 技术文档 RAG 知识库问答项目

基于 Python、FastAPI、FAISS、BM25 和阿里云百炼实现的学习型
RAG 知识库问答后端。

## 功能

- 按 Markdown 二级标题切分技术文档。
- 使用 Embedding 和 FAISS 进行向量检索。
- 使用 BM25 进行关键词检索，通过 RRF 融合两路排名。
- 调用重排模型重新排序候选切片，并按分数阈值过滤。
- 根据参考切片生成回答，要求模型标注引用。
- 结合客户端提供的历史消息进行查询改写。
- 提供普通问答和 SSE 流式问答接口。
- 返回引用信息，普通接口提供各阶段耗时。

重排分数表示相关性，不代表回答正确概率。
阈值过滤与提示词约束不能保证完全避免幻觉。

## 目录说明

| 目录或文件 | 用途 |
|---|---|
| `app/` | FastAPI 服务、请求响应模型、模型客户端及基础学习组件 |
| `rag/` | 检索、RRF 融合、重排、查询改写和回答生成 |
| `scripts/` | 手动连通与功能验证脚本 |
| `tests/` | pytest 自动测试 |
| `evaluation/` | 语料准备、评测集及检索评测脚本 |
| `data/corpus/` | Markdown 知识库语料 |
| `data/indexed_chunks.json` | 服务读取的切片文件 |
| `data/faiss_index/` | FAISS 持久化示例产生的本地索引 |
| `output/` | 脚本生成的结果 |

当前服务启动时会读取切片并重新构建检索索引；
不会自动加载 `data/faiss_index/` 中的历史索引。

`app/` 中保留了部分早期学习实现。
根目录 `test_faiss_pipeline.py` 依赖旧版 Pipeline，尚未同步，
暂不作为当前验证入口。

## 环境准备

当前本地验证环境使用 Python 3.10。
以下命令在 Windows PowerShell 中执行。

首次创建环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

已有可用环境时只需激活，不需要重新创建。

依赖清单记录当前环境的直接依赖版本；
独立新环境的安装复现仍需验证。

## 云端配置

在项目根目录的 `.env` 中配置自己的密钥：

```dotenv
DASHSCOPE_API_KEY=填写你自己的百炼APIKey
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v3
```

密钥、地域、业务空间和模型调用权限必须匹配。
不要提交真实 `.env` 或 API Key。

生成器、重排器和改写器的模型及接口地址目前在代码中配置。
其他用户复现时，需要核对 `rag/reranker.py` 中的业务空间端点，
不能直接假定当前地址适用于自己的账号。

已有终端环境变量可能优先于 `.env` 中的同名变量。

## 准备知识库

所有运行命令均从项目根目录执行。

当前仓库已有切片文件。修改 `data/corpus/` 后，可重新生成：

```powershell
python -m evaluation.ingest_corpus
```

此命令会覆盖 `data/indexed_chunks.json`。
普通启动和接口验证无需重复执行。

## 启动服务

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

启动时会调用云端 Embedding，为切片构建索引。

启动完成后访问接口文档：
http://127.0.0.1:8000/docs

主要接口：

- `POST /api/chat`：普通问答。
- `POST /api/chat/stream`：SSE 流式问答。

请求示例：

```json
{
  "query": "IndexFlatIP 在什么情况下等价于余弦相似度？",
  "history": [],
  "final_k": 3,
  "rerank_threshold": 0.45
}
```

多轮调用需由客户端在 `history` 中发送历史消息。
服务端目前不保存会话历史。

## 自动测试

```powershell
python -m pytest -q
```

默认收集 `tests/` 下的测试。
API 测试使用替身组件，不启动真实云端初始化。

当前本地运行记录：24 项测试通过，出现一条依赖弃用警告。
这代表已有测试覆盖的行为通过，不代表所有 RAG 效果已验证。

## 手动验证

以下脚本需要相应云端配置，可能产生 API 调用费用。

不需要先启动 Web 服务：

```powershell
python -m scripts.check_rerank
python -m scripts.check_rag_e2e
```

先启动 Web 服务，再在另一个终端运行：

```powershell
python -m scripts.check_api
python -m scripts.check_multi_turn
```

`check_api` 验证普通与流式接口。
`check_rag_e2e` 直接验证检索、重排、生成及无资料拒答。

`scripts.check_llm` 属于早期独立 LLM 客户端验证，
读取 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 和 `MODEL_NAME`，
与当前 RAG 主链路配置不同。

## 检索评测

已有 BM25、Dense、Hybrid 和 Hybrid＋重排评测脚本：

```powershell
python -m evaluation.eval_bm25_baseline
python -m evaluation.eval_dense_baseline
python -m evaluation.eval_hybrid_baseline
python -m evaluation.eval_production_pipeline
```

BM25 评测在本地执行；其他方案涉及云端调用。

当前示例语料包含 3 篇 Markdown、8 个切片；
评测集包含 25 道问题。
评测指标口径和结果保存仍待统一。

现有脚本标作 Recall 的部分计算实际为：
命中至少一个正确切片的问题比例。
暂不据此宣称多证据完整召回或性能提升。

## 当前状态

已完成本地验证：

- 云端重排连通与结果解析。
- 普通及流式问答。
- 一个有答案样例与一个无答案拒答样例。
- 手动脚本迁移后的运行验证。
- 当前自动测试套件。

待完成：

- 查询改写的真实多轮效果验证。
- 评测指标统一及逐题结果保存。
- 历史 FAISS 脚本处理。
- 独立新环境的安装复现验证。
