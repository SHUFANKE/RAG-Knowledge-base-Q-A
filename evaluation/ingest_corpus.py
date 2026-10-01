import json 
from pathlib import Path

#模拟切分参数:按Markdown二级标题段落切分,保持语义独立
def chunk_markdown(file_path: Path) -> list[dict]:
    content = file_path.read_text(encoding="utf-8")
    sections = content.split("\n##")
    doc_title = sections[0].split("\n")[0].replace("#","").strip()

    chunks = []
    for idx,sec in enumerate(sections[1:],start=1):
        lines = sec.strip().split("\n")
        sub_title = lines[0].strip()
        body = "\n".join(lines[1:]).strip()

        chunk_id = f"{file_path.stem}_sec{idx}"
        full_text = f"[{doc_title}-{sub_title}]\n{body}"

        chunks.append({
            "chunk_id": chunk_id,
            "source":file_path.name,
            "title": f"{doc_title}-{sub_title}",
            "text": full_text
        })

    return chunks
def main():
    corpus_dir = Path("data/corpus")
    all_chunks = []

    for doc in sorted(corpus_dir.glob("*.md")):
        chunks = chunk_markdown(doc)
        all_chunks.extend(chunks) #注意是exte不是append,extend会把列表里的每个切片"倒进"总容器中,保持all_chunks是单层平面列表
        print(f"解析{doc.name}:产生{len(chunks)}个切片")

    output_path = Path("data/indexed_chunks.json")
    with open(output_path, "w",encoding="utf-8") as f:
        json.dump(all_chunks,f ,ensure_ascii=False,indent=2)

    print(f"\n切片生成完毕,共{len(all_chunks)}个切片,已写入{output_path}")

if __name__ == "__main__":
    main()
