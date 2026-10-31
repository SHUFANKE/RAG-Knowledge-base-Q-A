from pydantic import BaseModel,Field
from typing import Literal

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
        default=0.45, ge=0.0, le=1.0, description="重排相关性阈值",
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

class CitationCheck(BaseModel):
    """只检查引用编号，不判断资料是否支持回答内容。"""

    status: Literal["valid", "invalid", "missing", "not_applicable"]
    reference_count: int
    cited_numbers: list[int]
    invalid_numbers: list[int]
    
class ChatResponse(BaseModel):
    """全量问答响应结构"""

    answer: str
    rewritten_query: str | None = None
    references: list[ReferenceDoc]
    metrics: LatencyMetrics
    citation_check: CitationCheck