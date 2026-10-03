from _collections_abc import AsyncGenerator
from contextlib import asynccontextmanager
import json
from pathlib import Path
import time

from dotenv import load_dotenv
from fastapi import FastAPI,HTTPException
from fastapi.responses import StreamingResponse

from app.embedder import QwenCloudEmbedder
from app.schemas import ChatRequest, ChatResponse, LatencyMetrics, ReferenceDoc
from app.logger import logger
from rag.bm25_retriever import BM25Retriever
from rag.dense_retriever import FAISSRetriever
from rag.generator import QwenGenerator
from rag.hybrid_retriever import HybridRetriever
from rag.pipeline import ProductionRAGRetriever
from rag.reranker import DashScopeReranker
from rag.rewriter import QueryRewriter


load_dotenv()

#全局单例持有字典
rag_components = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：服务启动时预先装配索引与重排器，服务关闭时安全释放"""
    print("\n>>>[System Startup] 正在加载生产级RAG知识库与索引单例...")
    chunks_path = Path("data/indexed_chunks.json")
    if not chunks_path.exists():
        raise FileExistsError(
            f"未找到切片文件{chunks_path},请确认构建步骤！"
        )

    with open(chunks_path, encoding="utf-8") as f:
        chunks = json.load(f)

    #1.初始化各基础组件
    embedder = QwenCloudEmbedder()
    dense = FAISSRetriever(embedder=embedder,dimension=1024)
    bm25 = BM25Retriever()
    hybrid = HybridRetriever(dense_retriever=dense, bm25_retriever=bm25)
    await hybrid.add_documents(chunks)

    #2.组装二阶段重排检索管线
    reranker = DashScopeReranker(model="qwen3-rerank")
    retriever = ProductionRAGRetriever(
        hybrid_retriever=hybrid,reranker=reranker
    )

    #3.组装LLM生成器
    generator = QwenGenerator(model="qwen-turbo")

    #4.组装查询改写器
    rewriter = QueryRewriter(model="qwen-turbo")

    #缓存到全局生命周期字典中供接口复用
    rag_components["retriever"] = retriever
    rag_components["generator"] = generator
    rag_components["rewriter"] = rewriter #注册改写器

    print(
        f">>> [System Ready] 知识库切片转载完成({len(chunks)}条)，RAG Web 服务已就绪！"
    )
    yield
    print(">>>[System Shutdown] 正在清理与释放知识库资源...")
    rag_components.clear()#一键释放所有重度内存对象


app = FastAPI(
    title="Production Enterprise RAG API",
    version="1.0.0",
    description="基于混合检索，Cross-Encoder重排与防幻觉置信度截断的企业级知识库问答后端",
    lifespan=lifespan

)#实例化FastAPI成一个对象（app）

@app.post (
    "/api/chat",
    response_model=ChatResponse,
    summary="标准全量问答接口（非流式）",
)
async def chat_endpoint(req: ChatRequest):
    retriever: ProductionRAGRetriever = rag_components.get("retriever")
    generator: QwenGenerator = rag_components.get("generator")
    rewriter: QueryRewriter = rag_components.get("rewriter")

    if not retriever or not generator or not rewriter:
        raise HTTPException(status_code=503, detail="RAG组件尚未完全就绪")

    start_total = time.perf_counter()

    #1.多轮上下文改写阶段
    start_rewriter = time.perf_counter()
    history_dicts = [m.model_dump() for m in req.history]
    active_query = await rewriter.rewrite(
        query=req.query,history=history_dicts
    )
    rewrite_ms = (time.perf_counter() - start_rewriter) * 1000.0

    #2.二阶段检索与精排（使用改写后的active_query）
    start_retrieval = time.perf_counter()
    docs = await retriever.retrieve(
        query=active_query,#这里用改写后的active——query
        candidate_k=10,
        final_k=req.final_k,
        rerank_threshold=req.rerank_threshold,
    )
    retrieval_ms = (time.perf_counter() - start_retrieval) * 1000.0

    #3.大模型生成回答
    start_gen = time.perf_counter()
    answer = await generator.generate(query=active_query, context_docs=docs)
    gengeration_ms = (time.perf_counter()-start_gen) * 1000.0

    total_ms = (time.perf_counter() - start_total) * 1000.0

    #4.组装结构化元数据
    ref_docs = [
        ReferenceDoc(
            chunk_id=doc.get("chunk_id", ""),
            rerank_score=doc.get("rerank_score",0.0),
            text=doc.get("text",""),
        )
        for doc in docs
    ]

    logger.info(
        f"Query='{req.query}' | "
        f"Rewritten='{active_query if active_query != req.query else 'None'}' | "
        f"Hits={len(docs)} | "
        f"TopScore={round(docs[0]['rerank_score'],4) if docs else 0.0} | "
        f"Latency(Rewrite={round(rewrite_ms, 1)}ms, Retr={round(retrieval_ms, 1)}ms, Gen={round(gengeration_ms, 1)}ms, Total={round(total_ms, 1)}ms)"    
    )

    return ChatResponse(
        answer=answer,
        rewritten_query=(
            active_query if active_query != req.query else None
        ),#若发生改写则回传改写结果
        references=ref_docs,
        metrics=LatencyMetrics(
            rewrite_ms=round(rewrite_ms,2),
            retrieval_ms=round(retrieval_ms,2),
            generation_ms=round(gengeration_ms,2),
            total_ms=round(total_ms,2),
        ),
    )

@app.post("/api/chat/stram", summary="打字机流式问答接口（SSE）")
async def chat_stream_endpoint(req:ChatRequest):
    retriever : ProductionRAGRetriever = rag_components.get("retriever")
    generator: QwenGenerator = rag_components.get("generator")

    if not retriever or not generator:
        raise HTTPException(status_code=503,detail="RAG组件尚未就绪")

    #前置检索阶段
    docs = await retriever.retrieve(
        query=req.query,
        candidate_k=10,
        final_k=req.final_k,
        rerank_threshold=req.rerank_threshold,
    )

    async def sse_event_stream() -> AsyncGenerator[str,None]:
        #首先下发命中的参考切片元数据（让前端先展示参考源卡片）
        meta_info = {
            "type":"references",
            "references":[
                {
                    "chunk_id": d["chunk_id"],
                    "score":round(d.get("rerank_score",0.0)),
                }
                for d in docs
            ],
        }
        yield f"data:{json.dumps(meta_info, ensure_ascii=False)}\n\n"

        #逐字吐出LLM回复
        async for token in generator.stream_generate(
            query=req.query,context_docs=docs
        ):
            token_payload = {"type":"token","content": token}
            yield f"data:{json.dumps(token_payload,ensure_ascii=False)}\n\n"

        #发送结束信号
        yield "data:[DONE]\n\n"

    return StreamingResponse(sse_event_stream(),media_type="text/event-stream")


# #全局单例Pipeline
# pipeline:LocalRAGPipeline | None = None #定义pipeline要么是前面这个要么是None


# @asynccontextmanager
# async def lifespan(app:FastAPI):
#     """应用生命周期管理：服务启动时初始化RAG核心组件，服务关闭时释放资源"""
#     global pipeline
#     vocab = ["python", "rag", "fastapi", "llm", "vector", "database", "retrieval"]
#     embedder = QwenCloudEmbedder()
#     llm_client = OpenAILikeLLMClient()

#     pipeline = LocalRAGPipeline(embedder=embedder,llm_client=llm_client)

#     #预置一条样例知识，方便开箱即测
#     sample_text = (
#         "RAG（检索增强生成）是一种将信息检索系统与大语言模型相结合的架构。"
#         "系统首先将技术文档切片并存入向量空间，根据用户提问精准召回证据，"
#         "最后由生成模型基于参考资料给出严谨回答，有效消除幻觉。"
#     )
#     pipeline.index_document(sample_text,source="rag_architecture.txt",chunk_size=50,overlap=10)
#     print(">>>[System] RAG Pipeline 初始化完成，服务已就绪")

#     yield

#     print(">>> [System] 服务正在关闭，资源已释放。")

# app = FastAPI(
#     title="Minimalist RAG API Service",
#     description="基于 FastAPI + 自研RAG内核的轻量化知识库问答服务",
#     version="1.0.0",
#     lifespan=lifespan,
# )

# @app.get("/health")
# async def health_check():
#     """健康检查探针接口"""
#     return {"status":"ok","service":"rag-pipeline"}

# @app.post("/api/index",response_model=IndexResponse)
# async def index_knowledge(req:IndexRequest):
#     """上传文档切片并写入向量知识库"""
#     if pipeline is None:
#         raise HTTPException(status_code=500,detail="Pipeline未初始化")

#     count = await pipeline.index_document(
#         text=req.text,
#         source=req.source,
#         chunk_size=req.chunk_size,
#         overlap=req.overlap,
#     )
#     return IndexResponse(
#         message=f"成功为文档'{req.source}'建立索引",
#         indexed_chunks=count,
#     )

# @app.post("/api/query",response_model=QueryResponse)
# async def query_knowledge(req:QueryRequest):
#     """基于知识库的大模型问答接口"""
#     if pipeline is None:
#         raise HTTPException(status_code=500,detail="Pipeline未初始化")

#     #1.召回相关的切片与相似度得分
#     raw_results = await pipeline.retrieve(req.question,top_k=req.top_k)

#     #2.转换为规范的响应模型
#     sources = [
#         SourceChunkInfo(
#             chunk_id=chunk.chunk_id,
#             text=chunk.text,
#             source=chunk.source,
#             score=round(score,4)

#         )
#         for chunk,score in raw_results
#     ]

#     #3.异步调用完整RAG回答
#     answer =await pipeline.answer_question(req.question,search_results=raw_results)

#     return QueryResponse(
#         question=req.question,
#         answer=answer,
#         sources=sources,
#     )

