import pytest
from app.embedder import SimpleWordEmbedder,BaseEmbedder

def test_base_embedder_cannot_instantiate():
    """c测试抽象基类无法直接实例化（接口防御测试"""
    with pytest.raises(TypeError):
        BaseEmbedder()

def test_base_embedder_vocab__initialization():
    """测试词表清洗：去重、去空格、统一小写"""
    raw_vocab = ["Python","python","RAG","rag"]
    embedder = SimpleWordEmbedder(vocab=raw_vocab)

    assert embedder.dim == 2
    assert embedder.vocab == ["python","rag"]
    assert embedder.word_to_idx == {"python":0,"rag":1}

def test_embedder_empty_vocab():
    """测试空词表非法输入防御"""
    with pytest.raises(ValueError):
        SimpleWordEmbedder(vocab=[])

    with pytest.raises(ValueError):
        SimpleWordEmbedder(vocab=["   ",""])

def test_embed_text_and_batch():
    """测试单句与多句向量转换逻辑"""
    embedder = SimpleWordEmbedder(vocab=["apple","banana"])

    #1.测试单句
    vec = embedder.embed_text("Apple apple orange!")
    #apple 出现2次，banana出现0次，orange忽略
    assert vec == [2.0,0.0]

    #2.测试批量
    batch_vecs = embedder.embed_batch(["banana","peach"])
    assert len(batch_vecs) == 2
    assert batch_vecs[0] == [0.0,1.0]
    assert batch_vecs[1] == [0.0,0.0]