from dataclasses import dataclass

@dataclass
class Document:
   text :str
   source :str

@dataclass
class Chunk:
   text :str 
   source :str
   chunk_id :int

def split_document(
      document : Document,
      chunk_size: int = 20,
      chunk_overlap: int = 5
) -> list[Chunk] :
   
   
    """将Document 按照固定字符窗口和重叠长度切分为多个Chunk"""
    #防御性校验
    if chunk_size <= 0:
        raise ValueError("chunk_size必须大于0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap不能为负数")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap必须严格小于chunk_size")

    text = document.text
    if not text.strip():#.strip()去掉开头结尾的空白字符串
        return []

    chunks:list[Chunk] = []
    start = 0
    chunk_id = 0
    step = chunk_size - chunk_overlap

    #滑动窗口切分
    while start < len(text):
        end =start + chunk_size
        chunk_text = text[start:end]

        chunks.append(
            Chunk(
            text=chunk_text,
            source=document.source,
            chunk_id=chunk_id
            )
        )

        chunk_id += 1
        start += step

    return chunks


if __name__ == "__main__":
   raw_doc = Document(
      text="Retrieval-Augmented Generation impro ves LLm accuracy by retrieving external knowledge",
      source="rag_intro.txt"
   )
   result_chunks = split_document(raw_doc,chunk_size=30,chunk_overlap=10)

   print(f"原始文本长度：{len(raw_doc.text)}")
   print(f"切分出{len(result_chunks)}个Chunk:\n")
   for c in result_chunks:
      print(f"ID={c.chunk_id} | 来源={c.source} | 内容：'{c.text}'")


