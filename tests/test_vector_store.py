import pytest
from app.rag_splitter import Chunk
from app.vector_store import cosine_similarity,InMemoryVectorStore

def test_cosine_similarity_identical_and_orthogonal():
    """测试完全相同（相似度=1）与完全正交垂直（相似度=0）"""
    vec_a = [1.0,2.0,3.0]
    #同向向量（方向相同，长度翻倍），余弦值也必须是1.0
    vec_b = [2.0,4.0,6.0]
    assert pytest.approx(cosine_similarity(vec_a,vec_b)) == 1.#因为计算机做浮点数乘除（比如开根号、除法）
    #存在精度舍入误差，算出来的可能不是精确的 1.0 而是 0.9999999999999999。pytest.approx(1.0) 会自动允许极微小的浮点误差，防止测试因机器精度误报失败。
    #approximately（近似地、大约） 的缩写

    #正交向量：[1,0]与[0,1]夹角90度，相似度必须是0.0
    assert pytest.approx(cosine_similarity([1.0,0.0],[0.0,1.0])) == 0.0

def test_cosine_similarity_invalid_inputs():
    """测试维度不匹配与空向量拦截"""
    with pytest.raises(ValueError):
        cosine_similarity([1.0,2.0],[1.0])

    with pytest.raises(ValueError):
        cosine_similarity([],[])

def test_vector_store_search():
    """测试向量库存入与Top-k排序检索"""
    store = InMemoryVectorStore()
    c1 = Chunk(text="Chunk 1", source="test.txt", chunk_id=0)
    c2 = Chunk(text="Chunk 2", source="test.txt", chunk_id=1)

    store.add_chunk(c1,[1.0,0.0])
    store.add_chunk(c2,[0.0,1.0])

    #查询向量及其贴近c1
    query = [0.99,0.1]
    results = store.similarity_search(query,top_k=2)

    assert len(results) == 2
    #第一名必须是c1
    assert results[0][0].chunk_id == 0
    assert results[0][1] > results[1][1]

    #非法top_k拦截
    with pytest.raises(ValueError):
        store.similarity_search(query,top_k=0)
