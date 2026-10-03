from pydantic import BaseModel,Field

class Message(BaseModel):
    """历史对话单轮消息"""
    role: str = Field(...,description="角色：user或assistant")
    content: str = Field(...,min_length=1,description="对话正文")

class ChatRequest(BaseModel):
    """用户问答请求体"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="用户提问内容",
        examples=["FastApI 生产部署时，工作进程workers的推荐计算公式是什么？"]
    )#Field防御性编程，如果输入的内容不符合里面的要求，会报错，但是不会崩溃
    history:list[Message] = Field(
        default=[],
        description="历史对话记录，按时间正序排列",
    )
    final_k: int = Field(
        default=3, ge=1, le=10, description="精排最终保留切片数量"
    )
    rerank_threshold: float = Field(
        default=0.45, ge=0.0, le=1.0, description="防幻觉置信度截断及格线"
    )

class ReferenceDoc(BaseModel):
    """引用源切片元数据"""

    chunk_id:str
    rerank_score: float
    text: str

class LatencyMetrics(BaseModel):
    """全链路各阶段耗时分解（毫秒）"""

    rewrite_ms:float = 0.0 #多轮改写耗时
    retrieval_ms:float
    generation_ms: float
    total_ms: float

class ChatResponse(BaseModel):
    """全量问答响应结构"""

    answer: str
    rewritten_query: str | None = None
    references: list[ReferenceDoc]
    metrics: LatencyMetrics














# class IndexRequest(BaseModel):
#     """文档入库请求模型"""
#     text:str = Field(...,min_length=1,description="需要入库的知识库文本内容")
#     source:str = Field(default="user_upload.txt",description="文档来源标识")
#     chunk_size: int = Field(default=5,ge=0,description="切片大小")
#     overlap: int = Field(default=3,ge=0,description="重叠字符数")

# class IndexResponse(BaseModel):
#     """文档入库响应模型"""
#     message:str
#     indexed_chunks: int

# class QueryRequest(BaseModel):
#     """问答请求模型"""
#     question:str = Field(...,min_length=1,description="用户提问")
#     top_k: int = Field(default=2,ge=1,le=10,description="检索召回的切片数量")

# class SourceChunkInfo(BaseModel):
#     """召回切片的元数据信息"""
#     chunk_id:int
#     text:str
#     source:str
#     score:float

# class QueryResponse(BaseModel):
#     """问答响应模型"""
#     question:str
#     answer:str
#     sources:list[SourceChunkInfo]

