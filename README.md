# 技术文档 RAG 知识库问答项目

基于 Python、FastAPI、FAISS、BM25 和阿里云百炼实现的 RAG
知识库问答后端。

面向技术文档的知识库问答系统，支持文档切片、索引持久化、
混合检索、重排过滤、多轮追问和流式回答。
通过分组检索评测与人工生成审阅，记录系统效果及能力边界。

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

正常启动时，服务读取当前切片并核对构建指纹，
加载已经保存的FAISS索引，在本地重新建立BM25。
本过程不重新调用文档Embedding；用户问题仍需在线向量化。

索引不存在、切片内容或Embedding配置发生变化时，
服务会提示显式重建，不会自动重新向量化全部文档。

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
| qwen-plus | 查询改写与回答生成 |
| SSE | 流式返回引用与回答文本 |
| pytest / pytest-asyncio | 自动测试 |

## 4. 项目结构

```text
dev-env-practice/
├── app/
│   ├── main.py                 # FastAPI 服务与组件初始化
│   ├── schemas.py              # 请求、响应与历史消息模型
│   ├── embedder.py             # 云端及本地向量器
│   └── logger.py               # 控制台日志
├── rag/
│   ├── index_loader.py         # 显式构建、指纹校验与启动加载
│   ├── citation.py             # 回答引用编号检查
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
│   ├── check_rerank.py         # 重排连通验证
│   └── check_faiss_persistence.py # 本地持久化验证
├── tests/                     # pytest 自动测试
├── evaluation/
│   ├── metrics.py             # 公共指标计算与汇总
│   ├── ingest_corpus.py        # Markdown 语料切片
│   ├── eval_dev.json           # 54道调参题
│   ├── eval_test.json          # 36道测试题
│   ├── eval_manifest.json      # 当前题集与切片版本记录
│   ├── eval_bm25_baseline.py
│   ├── eval_dense_baseline.py
│   ├── eval_hybrid_baseline.py
│   └── eval_production_pipeline.py
├── data/
│   ├── corpus/                # Markdown 知识库
│   ├── indexed_chunks.json    # 切片文件
│   └── faiss_index/           # 当前持久化索引、切片快照与构建指纹
├── output/
│   └── evaluation/            # 按时间命名的评测报告
├── README.md
├── requirements.txt
├── pyproject.toml
├── .env.example
└── .gitignore
```

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
RERANK_ENDPOINT=https://your-workspace-host/compatible-api/v1/reranks
```

以上 Embedding 地址对应当前实现的默认配置；
应按实际账号、地域和业务空间核对。

注意：

- 密钥、业务空间、地域和模型调用权限必须匹配。
- 重排完整请求地址通过RERANK_ENDPOINT配置，需要填写自己账号可调用、
  且与当前重排请求协议匹配的URL，包括路径。
  该配置独立于Embedding使用的DASHSCOPE_BASE_URL。
- 生成器与改写器的模型和接口地址目前也在代码中配置。
- `DASHSCOPE_BASE_URL` 只用于当前云端向量器，不会统一覆盖所有组件地址。
- 已存在的终端环境变量可能优先于 `.env` 中的同名变量。
- 真实 `.env` 与 API Key 不应提交到 GitHub。
- 云端 Embedding、改写、重排和生成调用可能产生费用。


## 7. 准备知识库

语料位于data/corpus/，当前共26篇Markdown文档、82个切片，
覆盖FAISS、FastAPI、HTTPX、asyncio及检索评测等主题。

切分器主要按二级标题组织切片，并保留来源、标题、
来源URL和核验日期；对长正文补充切分，尽量保持代码块完整。

新增或修改语料后，从项目根目录依次执行：

```powershell
& .\.venv\Scripts\python.exe -X utf8 -m evaluation.ingest_corpus
& .\.venv\Scripts\python.exe -X utf8 -m rag.index_loader --rebuild
```

第一条命令生成data/indexed_chunks.json。
第二条调用文档Embedding，重建并保存：

- data/faiss_index/index.faiss：文档向量索引。
- data/faiss_index/metadata.json：与向量位置对应的切片记录。
- data/faiss_index/manifest.json：切片内容、模型和维度的构建指纹。

重建后重启服务，加载新索引。
已有匹配的索引时，普通启动无需重复执行上述命令。

评测入口还会核对题集与切片版本。
修改语料后应同时检查标注是否仍然有效，不能只更新指纹来绕过检查。

## 8. 启动与接口

启动：

```powershell
& .\.venv\Scripts\python.exe -X utf8 -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

服务启动时加载已保存的FAISS索引，并在本地建立BM25。
修改代码或配置后，需要重启服务加载修改。

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
- `citation_check`：引用编号检查结果，包含状态、资料数量、
  已引用编号及越界编号；不判断资料是否支持对应事实。

### 流式问答

```text
POST /api/chat/stream
```

请求结构与普通接口一致，返回 `text/event-stream`。
事件顺序为：

1. `references`：引用切片元数据。
2. `token`：连续返回的回答文本片段。
3. `citation_check`：全文拼接后的引用编号检查结果。
4. `[DONE]`：流式结束信号。

引用检查发生在全文发送结束后，属于事后检查。

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

## 9. 离线测试

从项目根目录执行，测试进程跳过.env加载：

```powershell
@'
import os
os.environ['PYTHON_DOTENV_DISABLED'] = '1'

import pytest
raise SystemExit(pytest.main(['-q']))
'@ | & .\.venv\Scripts\python.exe -X utf8 -
```

当前保留tests/test_api.py和tests/test_embedder.py，覆盖：

- 普通接口响应及改写后的查询传递。
- SSE资料、文本和结束事件。
- 非法请求及组件未就绪处理。
- 本地向量器初始化、单条及批量向量化。

2026-10-31本地验证结果：

```text
11 passed, 1 warning
```

接口测试使用替身组件，不调用云端模型。
警告来自Starlette/AnyIO的弃用提示。
离线测试通过不代表检索或生成质量全部正确，效果见第11节。

## 10. 手动验证

### 本地索引持久化

```powershell
& .\.venv\Scripts\python.exe -X utf8 -m scripts.check_faiss_persistence
```

使用本地向量器和临时目录，验证索引与元数据保存、
新对象加载，以及加载前后排名和分数一致。
不调用云端，不覆盖data/faiss_index/。

### 云端重排连通性

```powershell
& .\.venv\Scripts\python.exe -X utf8 -m scripts.check_rerank
```

检查重排接口是否返回候选及相关性分数。

### 普通、流式及多轮接口

先启动服务，再在另一个终端按需运行：

```powershell
& .\.venv\Scripts\python.exe -X utf8 -m scripts.check_api
& .\.venv\Scripts\python.exe -X utf8 -m scripts.check_multi_turn
```

Web接口验证会调用当前配置的云端模型。
具体检索指标、生成审阅结果和失败样例见第11节。

## 11. 检索评测与生成抽查

记录日期：2026-10-30。

当前语料为26篇Markdown文档、82个切片。
单轮评测集共90题，划分为dev 54题、test 36题，
按group_id分组，两个集合无group_id重叠。

dev用于配置比较；test使用固定配置评测。
以下表格报告test结果：30道有答案题、6道无答案题。

### 运行方式

从项目根目录执行：

```powershell
& .\.venv\Scripts\python.exe -X utf8 -m evaluation.eval_bm25_baseline --dataset evaluation/eval_test.json --top-k 3
& .\.venv\Scripts\python.exe -X utf8 -m evaluation.eval_dense_baseline --dataset evaluation/eval_test.json --top-k 3
& .\.venv\Scripts\python.exe -X utf8 -m evaluation.eval_hybrid_baseline --dataset evaluation/eval_test.json --top-k 3
& .\.venv\Scripts\python.exe -X utf8 -m evaluation.eval_production_pipeline --dataset evaluation/eval_test.json --top-k 3 --threshold 0.45
```

四组使用相同题集、切片和最终Top-3。
Hybrid每路召回20条，RRF排名常数为60。
重排方案保留融合后的20条候选，再重排返回前三条，
按主阈值0.45、次阈值0.225过滤。

### 测试集结果

| 指标 | BM25 | Dense | Hybrid-RRF | Hybrid＋重排＋过滤 |
|---|---:|---:|---:|---:|
| Hit@3 | 0.9667 | 0.9667 | 1.0000 | 1.0000 |
| Recall@3 | 0.9167 | 0.8778 | 0.9444 | 0.9556 |
| 完整证据率 | 26/30 | 24/30 | 27/30 | 27/30 |
| MRR@3 | 0.9056 | 0.8722 | 0.9056 | 0.9667 |
| 无答案题检索拒答率 | 0/6 | 0/6 | 0/6 | 4/6 |
| 有答案题误拒答率 | 0/30 | 0/30 | 0/30 | 0/30 |
| 平均检索耗时/ms | 0.70 | 193.17 | 194.33 | 519.81 |

正向指标只对有答案题计算。
expected_chunk_sets中的每个内部列表表示一套完整、可接受的证据：
找全任意一套即为完整；
Recall取各套证据覆盖率的最大值，再对题目平均；
MRR按首个属于任一可接受证据集合的片段排名计算。

无答案题检索拒答率表示最终返回空列表的比例，越高越好；
有答案题误拒答率表示有答案题返回空列表的比例，越低越好。
两者均不是生成回答准确率。

### 结果解释与耗时范围

Hybrid相对BM25多找全1道有答案题，相对Dense多找全3道。

重排过滤提高了MRR，并拒绝4/6道无答案题；
但完整证据题数仍为27/30。
它补回了Hybrid的q414，同时丢失了q427，
因此不能声称重排在所有问题上都更好。

重排后的q402、q393、q427所需证据已进入融合候选，
但未同时进入重排Top-3，且过滤前后结果相同。
这三题的缺失不能归因于阈值误删。

BM25耗时为本地查询分词、评分和排序。
Dense、Hybrid包含查询Embedding网络请求，
重排方案还包含云端重排。
全部均不含回答生成，不应将平均检索耗时当作端到端问答耗时或P95。

报告保存在output/evaluation/，包含配置、题集与切片SHA256、
分题型指标及逐题结果。原始失败样例保留。

### 人工生成抽查

另行审阅20个场景：
12个dev单轮问题、4个部分回答场景、4个真实两轮场景，
共24条当前版本响应。多轮场景单独报告，不混入单轮检索指标。

4个部分回答场景均未编造线上配置、超时次数、
本机文件大小或浏览器连接数。
4组多轮的指代补全、上下文补全及话题切换符合预期。

同时发现并保留以下问题：

- 回答在缺失信息说明中加入资料之外的API或知识。
- 使用非约定引用格式，或引用片段未支持对应陈述。
- 将特定条件下的结论扩大为一般规则。
- 主问题已经回答后，仍追加冗余的缺失信息。

citation_check只检查[Doc N]的格式及编号范围，
不判断片段是否支持对应事实。
SSE在全文输出结束后返回检查事件，属于事后检查。

上述场景属于定向人工诊断，部分用于提示词调整，
不据此宣称整体生成准确率或完全避免幻觉。


## 12. 关键取舍

### 多轮检索

客户端提供上一轮真实问答，改写器将依赖上下文的追问补全为独立查询。
例如先询问SSE的event字段，再追问“如果省略它，默认事件类型是什么”，
实际改写为“SSE中省略event字段时的默认事件类型是什么”。

### 排序质量与证据完整性

测试集中，重排补回了Hybrid未找全的q414，同时丢失了q427，
完整证据题数仍为27/30，但MRR与无答案题拒答得到改善。
系统保留逐题结果，用于分析排序、候选截断和过滤的不同影响。

### 引用编号与事实依据

引用编号存在，不代表对应片段支持回答中的每项事实。
人工审阅发现，回答可能在缺失说明中列出资料外API，
或者将限定条件扩大为一般结论。
项目保留这些失败样例，引用检查仅声明编号检查能力。

## 13. 当前状态与局限

当前版本已接通语料切片、索引持久化加载、混合检索、
重排过滤、普通/SSE问答、多轮查询改写和引用编号检查。

已完成90题dev/test四组检索对比，以及20个场景的人工生成审阅。
项目具备演示与复盘所需的运行证据，同时保留生成依据方面的已知问题。
当前离线测试和本地索引验证说明见第9、10节。

当前局限：

- 语料与评测集规模较小，结果不代表大型知识库表现。
- 自动测试尚未覆盖全部检索组件和边界情况。
- 查询改写和回答依据约束已有样例验证，
  仍可能产生错误改写或资料外回答。
- 固定重排阈值不保证适用于不同语料、问题和模型。
- 服务端不保存会话，历史由客户端提供。
- 云端地址和部分模型配置仍在代码中维护。
- 语料变化后需要显式重建索引，当前没有自动增量更新。
- 服务未经过并发负载或长期稳定性验证，
  当前定位为学习与展示用后端原型。
- 引用编号合法不代表引用片段支持回答中的事实。
- 生成回答仍可能在缺失说明中补充资料外API，
  或把限定条件下的结论过度泛化；原始失败样例已保留。