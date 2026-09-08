import pytest
from app.rag_splitter import Document,Chunk,split_document

def test_split_document_basic():
    """测试常规文本切分和重叠效果"""
    doc = Document(text="abcdefghijklmnopqrstuvwxyz",source="alphabet.txt")
    # 总长 26，每块 10，重叠 2，步长 = 10 - 2 = 8
    # 块0: [0:10], 块1: [8:18], 块2: [16:26], 块3: [24:34]（实际到26）
    chunks = split_document(doc,chunk_size=10,chunk_overlap=2)

    assert len(chunks) == 4
    assert chunks[0].text == "abcdefghij"
    assert chunks[1].text == "ijklmnopqr"#重叠了ij
    assert chunks[0].source == "alphabet.txt"
    assert chunks[0].chunk_id == 0
    assert chunks[1].chunk_id == 1

def test_split_document_empty_text():
    """测试空文本或纯空格文本的安全返回"""
    doc  = Document(text="    \n\t   ",source="empty.txt")
    chunks = split_document(doc,chunk_size=10,chunk_overlap=2)
    assert chunks == []

def test_split_document_invalid_params():
    """测试非法参数的异常拦截(failk Fast)"""
    doc = Document(text="Valid text",source="test.txt")

    #chunk_overlap不能小于等于0
    with pytest.raises(ValueError):
        split_document(doc,chunk_size=0,chunk_overlap=0)

    #chunk_overlap 不能大于等于chunk_size
    with pytest.raises(ValueError):
        split_document(doc,chunk_size=10,chunk_overlap=10)

    #chunk_overlap不能为负数
    with pytest.raises(ValueError):
        split_document(doc,chunk_size=10,chunk_overlap=-1)
        
