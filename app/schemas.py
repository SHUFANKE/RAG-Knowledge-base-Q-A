from pydantic import BaseModel,Field

class IndexRequest(BaseModel):
    """文档入库请求模型"""
    text:str = Field(...,min_length=1,description="需要入库的知识库文本内容")
    source:str = Field(default="user_upload.txt",description="文档来源标识")
    chunk_size: int = Field(default=5,ge=0,description="切片大小")
    overlap: int = Field(default=5,ge=0,description="重叠字符数")

class IndexResponse(BaseModel):
    """文档入库响应模型"""
    message:str
    indexed_chunks: int

class QueryRequest(BaseModel):
    """问答请求模型"""
    question:str = Field(...,min_length=1,description="用户提问")
    top_k: int = Field(default=2,ge=1,le=10,description="检索召回的切片数量")

class SourceChunkInfo(BaseModel):
    """召回切片的元数据信息"""
    chunk_id:int
    text:str
    source:str
    score:float

class QueryResponse(BaseModel):
    """问答响应模型"""
    question:str
    answer:str
    sources:list[SourceChunkInfo]

