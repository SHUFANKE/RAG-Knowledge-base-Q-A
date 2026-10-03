# 技术文档 RAG 知识库问答项目

基于 Python、FastAPI、FAISS、BM25 和阿里云百炼实现的 RAG
知识库问答后端。

项目从基础 Python 工程练习逐步发展而来，主要用于学习大模型应用开发，
理解文档切片、向量检索、混合检索、重排、查询改写和流式接口，
并通过自动测试与检索评测检查实现效果。

## 1. 功能概览

- 按 Markdown 二级标题切分文档，并保留切片 ID 和来源信息。
- 使用云端 Embedding 和 FAISS 实现向量检索。
- 使用 BM25 实现关键词检索。
- 使用 RRF 融合向量检索与关键词检索的排名。
- 使用重排模型重新排序候选切片，并进行分数阈值过滤。
- 根据参考资料生成回答，要求模型标注引用。
- 结合客户端提供的历史消息，将追问改写为独立检索问题。
- 提供普通问答与 SSE 流式问答接口。
- 返回引用切片，普通接口记录改写、检索、生成及总耗时。
- 支持 FAISS 索引和元数据的保存、加载。

重排分数表示模型给出的相关性，不是回答正确的概率。
阈值过滤和提示词约束可以减少部分无依据回答，但不能保证完全避免幻觉。

## 2. 技术流程

### 知识库准备

```text
Markdown 文档
    ↓
按二级标题切片
    ↓
保存 indexed_chunks.json
```

### 在线问答

```text
用户问题 + 客户端提供的历史消息
    ↓
查询改写：将依赖上下文的追问补全为独立问题
    ↓
FAISS 向量检索 + BM25 关键词检索
    ↓
RRF 排名融合
    ↓
重排模型打分
    ↓
Top-K 截断与分数阈值过滤
    ↓
参考资料上下文
    ↓
普通回答 / SSE 流式回答
```

历史消息为空时，改写器直接返回原问题，不调用改写模型。
检索过滤后没有参考资料时，生成器直接返回预设拒答，不调用生成模型。

当前服务启动时读取切片文件并构建检索索引，
不会自动加载历史保存的 FAISS 索引。

## 3. 主要技术

| 技术 | 用途 |
|---|---|
| Python / asyncio | 模块组织、异步模型调用 |
| FastAPI / Pydantic | HTTP 接口、请求校验与响应模型 |
| HTTPX / OpenAI SDK | 云端模型调用 |
| text-embedding-v3 | 文本向量化 |
| FAISS IndexFlatIP | 对归一化向量进行相似度检索 |
| jieba / BM25 | 中文分词与关键词检索 |
| RRF | 融合两路检索排名 |
| qwen3-rerank | 候选切片重排 |
| qwen-turbo | 查询改写与回答生成 |
| SSE | 流式返回引用与回答文本 |
| pytest / pytest-asyncio | 自动测试 |

## 4. 项目结构

```text
dev-env-practice/
├── app/
│   ├── main.py                 # FastAPI 服务与组件初始化
│   ├── schemas.py              # 请求、响应与历史消息模型
│   ├── embedder.py             # 云端及本地向量器
│   ├── logger.py               # 控制台日志
│   ├── llm_client.py           # 独立 LLM 客户端及 Mock
│   └── ...                     # 基础与早期学习实现
├── rag/
│   ├── dense_retriever.py      # FAISS 检索与持久化
│   ├── bm25_retriever.py       # BM25 检索
│   ├── hybrid_retriever.py     # RRF 融合
│   ├── reranker.py             # 云端重排
│   ├── pipeline.py             # 混合检索、重排与阈值过滤
│   ├── rewriter.py             # 多轮查询改写
│   └── generator.py            # 普通与流式生成
├── scripts/
│   ├── check_api.py            # 普通与流式接口验证
│   ├── check_multi_turn.py     # 多轮查询改写验证
│   ├── check_rag_e2e.py        # 直接 RAG 链路验证
│   ├── check_rerank.py         # 重排连通验证
│   ├── check_faiss_persistence.py # 本地持久化验证
│   └── check_llm.py            # 早期独立 LLM 连通脚本
├── tests/                     # pytest 自动测试
├── evaluation/
│   ├── metrics.py             # 公共指标计算与汇总
│   ├── ground_truth.json      # 评测问题及标准切片标注
│   ├── ingest_corpus.py        # Markdown 语料切片
│   ├── eval_bm25_baseline.py
│   ├── eval_dense_baseline.py
│   ├── eval_hybrid_baseline.py
│   └── eval_production_pipeline.py
├── data/
│   ├── corpus/                # Markdown 知识库
│   ├── indexed_chunks.json    # 切片文件
│   ├── faiss_index/            # 历史持久化示例文件
│   └── ...                    # 基础练习数据
├── output/
│   └── evaluation/            # 按时间命名的评测报告
├── README.md
├── requirements.txt
├── pyproject.toml
├── .env.example
└── .gitignore
```

`app/` 中保留了词频向量、内存向量库、本地 Pipeline 等早期学习实现。
当前 Web 服务入口为 `app/main.py`，当前检索与生成主线位于 `rag/`。

目录职责：

- `tests/`：自动测试，默认不调用云端 API。
- `scripts/`：手动验证，按脚本需要启动服务或配置云端。
- `evaluation/`：检索方案效果评测与数据准备。

## 5. 环境与依赖

当前本地验证环境使用 Python 3.10 和 Windows PowerShell。
直接依赖及当前版本记录在 `requirements.txt`。

首次创建环境：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

已有可用环境时只需激活，不需要重新创建。

检查当前环境的依赖冲突：

```powershell
python -m pip check
```

当前本地检查结果为：

```text
No broken requirements found.
```

所有下述命令均从项目根目录执行。

## 6. 云端配置

在项目根目录 `.env` 中配置自己的百炼 API Key：

```dotenv
DASHSCOPE_API_KEY=填写你自己的百炼APIKey
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL=text-embedding-v3
```

以上 Embedding 地址对应当前实现的默认配置；
应按实际账号、地域和业务空间核对。

注意：

- 密钥、业务空间、地域和模型调用权限必须匹配。
- 重排器的业务空间端点目前配置在 `rag/reranker.py` 中。
- 生成器与改写器的模型和接口地址目前也在代码中配置。
- `DASHSCOPE_BASE_URL` 只用于当前云端向量器，不会统一覆盖所有组件地址。
- 已存在的终端环境变量可能优先于 `.env` 中的同名变量。
- 真实 `.env` 与 API Key 不应提交到 GitHub。
- 云端 Embedding、改写、重排和生成调用可能产生费用。

`scripts/check_llm.py` 属于早期独立客户端验证，
读取 `OPENAI_API_KEY`、`OPENAI_BASE_URL` 和 `MODEL_NAME`，
与当前 RAG 主链路配置不同。

## 7. 准备知识库

当前示例语料位于 `data/corpus/`，主题包括：

- FastAPI 配置；
- FAISS 索引与参数；
- Python asyncio。

切片按照 Markdown 二级标题组织。
当前共有 3 篇文档、8 个切片。

修改语料后，可重新生成切片：

```powershell
python -m evaluation.ingest_corpus
```

此命令会覆盖：

```text
data/indexed_chunks.json
```

当前仓库已有切片文件，普通启动和接口验证无需重复生成。
语料变化后应重启服务，重新构建索引。

## 8. 启动与接口

启动：

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

服务启动时会调用云端 Embedding，为知识库切片构建索引。
修改代码或密钥配置后，需要重启服务加载修改。

接口文档：

[本地接口文档](http://127.0.0.1:8000/docs)

### 普通问答

```text
POST /api/chat
```

请求示例：

```json
{
  "query": "IndexFlatIP 在什么情况下等价于余弦相似度？",
  "history": [],
  "final_k": 3,
  "rerank_threshold": 0.45
}
```

主要响应字段：

- `answer`：回答文本；
- `rewritten_query`：发生改写时返回改写结果，否则为 null；
- `references`：引用切片的 ID、文本及重排分数；
- `metrics`：改写、检索、生成及总耗时，单位为毫秒。

### 流式问答

```text
POST /api/chat/stream
```

请求结构与普通接口一致，返回 `text/event-stream`。
事件顺序为：

1. `references`：引用切片元数据；
2. `token`：回答文本片段；
3. `[DONE]`：流式结束信号。

客户端需要按 SSE 事件读取，不能直接把整段响应作为普通 JSON 解析。

### 多轮问答

客户端在 `history` 中按时间顺序提供历史消息：

```json
{
  "query": "那这个参数有什么影响？",
  "history": [
    {
      "role": "user",
      "content": "FAISS 的 nprobe 参数是什么？"
    },
    {
      "role": "assistant",
      "content": "上一轮实际返回的回答"
    }
  ],
  "final_k": 3,
  "rerank_threshold": 0.45
}
```

改写器使用最近最多 4 条历史消息。
服务端目前不保存会话历史，由客户端负责维护。

## 9. 自动测试

运行：

```powershell
python -m pytest -q
```

默认只收集 `tests/` 下的测试。
API 测试使用替身组件并跳过真实云端初始化。

当前已有测试覆盖：

- 基础工具与文件处理；
- 文档切片；
- 本地词频向量器；
- 内存向量相似度检索；
- Mock LLM 客户端；
- 普通接口的响应与查询传递；
- SSE 引用、文本和结束事件；
- 非法请求校验；
- 组件未就绪时的响应。

本地运行记录：

```text
24 passed, 1 warning
```

警告来自 Starlette 与 AnyIO 的弃用接口提示。
已有测试通过不代表全部检索效果或回答质量已经验证。

## 10. 手动验证

### 本地 FAISS 持久化验证

不需要 Web 服务、API Key 或云端调用：

```powershell
python -m scripts.check_faiss_persistence
```

使用本地词频向量器和临时目录，验证：

- 索引与元数据保存；
- 新对象加载索引和元数据；
- 保存前后检索排名一致；
- 保存前后检索分数一致。

临时目录退出后自动清理，不覆盖已有 `data/faiss_index/`。

### 云端重排与直接 RAG 验证

不需要先启动 Web 服务，需要云端配置：

```powershell
python -m scripts.check_rerank
python -m scripts.check_rag_e2e
```

直接 RAG 脚本验证知识库内问题及一个无答案问题的处理。

### Web 接口与多轮验证

先启动服务，在另一个终端运行：

```powershell
python -m scripts.check_api
python -m scripts.check_multi_turn
```

已完成样例验证：

- 普通与流式问答正常返回；
- 无资料时返回预设拒答；
- 根据历史将模糊追问改写为独立问题；
- 提示词调整后，原失败样例不再补充资料未提供的启动命令。

这些是具体样例的运行证据，不代表所有问题均正确。

## 11. 检索评测

评测集共 25 道题：

| 题型 | 数量 |
|---|---:|
| 关键词问题 | 12 |
| 语义改写问题 | 6 |
| 多证据问题 | 2 |
| 无答案问题 | 5 |

运行四种方案：

```powershell
python -m evaluation.eval_bm25_baseline
python -m evaluation.eval_dense_baseline
python -m evaluation.eval_hybrid_baseline
python -m evaluation.eval_production_pipeline
```

BM25 在本地执行。
Dense 和 Hybrid 调用云端 Embedding。
最后一种方案还调用云端重排模型。
评测不调用回答生成模型，也不包含多轮查询改写。

### 指标定义

正向指标仅对 20 道有答案题计算：

| 指标 | 定义 |
|---|---|
| Hit@K | 命中至少一个正确切片的问题比例 |
| Recall@K | 每题召回正确切片的比例，再对问题取平均 |
| 完整证据召回率 | 找全全部标准切片的问题比例 |
| MRR@K | 第一个正确切片的倒数排名均值 |

其他指标：

- 无答案题检索拒答率：5 道无答案题中，最终结果为空的比例。
- 有答案题空结果率：有答案题中，最终结果为空的比例。
- 平均检索耗时：包含该方案在线检索阶段，不含索引构建或回答生成。

检索拒答率不是生成回答的正确率。

### 当前结果

记录日期：2026-10-03。

四种方案使用相同语料、评测题和最终 Top-3。
重排方案使用融合候选上限 10、最终 Top-3、阈值 0.45。

| 指标 | BM25 | Dense | Hybrid | Hybrid＋重排＋过滤 |
|---|---:|---:|---:|---:|
| Hit@3 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| Recall@3 | 1.0000 | 1.0000 | 1.0000 | 0.9750 |
| 完整证据召回率 | 1.0000 | 1.0000 | 1.0000 | 0.9500 |
| MRR@3 | 1.0000 | 0.9667 | 0.9750 | 1.0000 |
| 无答案题检索拒答率 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |
| 平均检索耗时 / ms | 0.406 | 161.89 | 156.65 | 461.98 |

重排与过滤方案的有答案题空结果率为 0。

结果解读：

- 在当前小型示例集上，BM25 的正向检索指标已达到满分。
- Hybrid 的 MRR 略高于 Dense，但未超过 BM25。
- 重排与过滤组合过滤了全部 5 道无答案题。
- 该组合在 q19 中只保留了两个所需切片中的一个，
  因而降低了 Recall 和完整证据召回率。
- 当前最终结果报告不足以确定 q19 的缺失切片
  是在候选融合、重排截断还是阈值过滤阶段丢失。
- 这些结果没有单独分离重排与阈值过滤的贡献。

耗时来自各方案的一次运行。
Dense、Hybrid 与重排方案包含云端请求和网络等待；
不能直接将耗时差解释为本地检索算法的速度差，
也不能据单次结果认定 Hybrid 比 Dense 更快。

### 结果文件

每次评测生成新的时间戳 JSON，不覆盖已有报告：

```text
output/evaluation/
```

报告包括：

- 运行配置；
- 总体指标；
- 分题型指标；
- 逐题问题与标准切片；
- 实际返回切片及分数；
- 逐题检索耗时。

## 12. 项目复盘

### 多轮追问

验证问题：

```text
第一轮：FastAPI 生产部署时，workers 的推荐计算公式是什么？
第二轮：那如何通过启动命令设置这个参数呢？
```

第二轮能够结合历史改写为包含 FastAPI、workers 和启动命令的独立问题，
并召回相关切片。

### 资料外回答

原回答在资料没有具体启动命令时，自行补出了命令示例。
通过加强提示词中的资料依据约束，
原样例复测后明确说明资料未提供具体命令。

这说明命中相关资料不等于回答中的每项内容都有依据。
引用标注也不能自动保证回答忠实于资料。

### 多证据覆盖与过滤

重排及阈值过滤提高了当前无答案题的检索拒答率，
同时出现一道多证据题资料不完整的情况。

项目保留该结果，用于分析过滤与证据覆盖之间的取舍，
不将复杂检索方案预设为一定优于简单方案。

## 13. 当前状态与局限

当前 V1 已完成约定的代码收尾、自动测试、
手动样例验证和四种检索方案评测，
可用于项目学习、演示与复盘。

当前局限：

- 语料与评测集规模较小，结果不代表大型知识库表现。
- 自动测试尚未覆盖全部检索组件和边界情况。
- 查询改写和回答依据约束已有样例验证，
  仍可能产生错误改写或资料外回答。
- 固定重排阈值不保证适用于不同语料、问题和模型。
- 服务端不保存会话，历史由客户端提供。
- 云端地址和部分模型配置仍在代码中维护。
- 主服务启动时重新构建索引，持久化能力尚未接入启动流程。
- 服务未经过并发负载或长期稳定性验证，
  当前定位为学习与展示用后端原型。