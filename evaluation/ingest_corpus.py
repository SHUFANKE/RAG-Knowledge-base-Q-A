import json
import re
from pathlib import Path


def fence_after(line, fence):
    """跟踪 Markdown 代码围栏，fence=None 表示当前在代码块外。"""
    match = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
    if not match:
        return fence

    marker = match.group(1)
    if fence is None:
        return marker

    if marker[0] == fence[0] and len(marker) >= len(fence):
        if not line.strip()[len(marker):]:
            return None

    return fence


def split_body(lines, max_chars):
    """按正文长度合并或拆分，代码块作为整体保留。"""
    units, code = [], []
    fence = None

    for line in lines:
        next_fence = fence_after(line, fence)

        if fence is not None or next_fence is not None:
            code.append(line)
            if fence is not None and next_fence is None:
                units.append("\n".join(code))
                code = []
        else:
            # 优先在后半段的句末或空格处切开过长的一行。
            while len(line) > max_chars:
                cut = max(
                    line.rfind(p, 0, max_chars)
                    for p in "。！？； "
                )
                cut = cut + 1 if cut >= max_chars // 2 else max_chars
                units.append(line[:cut])
                line = line[cut:]

            units.append(line)

        fence = next_fence

    if code:
        units.append("\n".join(code))

    parts, current = [], ""

    for unit in units:
        combined = f"{current}\n{unit}" if current else unit

        if current and len(combined) > max_chars:
            parts.append(current.strip())
            current = unit
        else:
            current = combined

    if current.strip():
        parts.append(current.strip())

    return [part for part in parts if part]


def chunk_markdown(file_path: Path, max_chars=1000) -> list[dict]:
    if max_chars < 1:
        raise ValueError("max_chars must be positive")

    content = file_path.read_text(encoding="utf-8-sig")
    doc_title = content.splitlines()[0].lstrip("# ").strip()

    preamble, sections, body = [], [], []
    section_title = None
    fence = None

    for line in content.splitlines():
        heading = (
            re.match(r"^##\s+(.+)$", line)
            if fence is None
            else None
        )

        if heading:
            if section_title is not None:
                sections.append((section_title, body))

            section_title = heading.group(1).strip()
            body = []
        else:
            target = preamble if section_title is None else body
            target.append(line)

        fence = fence_after(line, fence)

    if section_title is not None:
        sections.append((section_title, body))

    if not sections:
        raise ValueError(
            f"{file_path.name}: missing Markdown H2 sections"
        )

    document_note = " ".join(
        line.strip()
        for line in preamble[1:]
        if line.strip()
    )

    chunks = []

    for idx, (sub_title, lines) in enumerate(sections, start=1):
        section_text = "\n".join(lines)
        source_text = section_text + "\n" + document_note

        urls = list(dict.fromkeys(
            url.rstrip(".,，。；;)]）")
            for url in re.findall(r"https?://[^\s<>]+", source_text)
        ))

        date = re.search(
            r"核验日期[:：]\s*(\d{4}-\d{2}-\d{2})",
            source_text,
        )

        parts = split_body(lines, max_chars)
        title = f"{doc_title}-{sub_title}"

        for part_idx, part in enumerate(parts, start=1):
            chunk_id = f"{file_path.stem}_sec{idx}"
            if len(parts) > 1:
                chunk_id += f"_part{part_idx}"

            text = f"[{title}]\n"
            if document_note:
                text += document_note + "\n"
            text += part

            # 长章节拆开后，每个片段仍能追溯整节的来源。
            missing_urls = [url for url in urls if url not in part]
            if missing_urls:
                text += "\n来源：" + " ".join(missing_urls)

            chunks.append({
                "chunk_id": chunk_id,
                "source": file_path.name,
                "title": title,
                "text": text,
                "source_urls": urls,
                "verified_at": date.group(1) if date else None,
                "document_note": document_note,
            })

    return chunks


def main():
    project_root = Path(__file__).resolve().parents[1]
    corpus_dir = project_root / "data" / "corpus"
    output_path = project_root / "data" / "indexed_chunks.json"

    all_chunks = []
    files = sorted(corpus_dir.glob("*.md"))

    for path in files:
        chunks = chunk_markdown(path)
        all_chunks.extend(chunks)
        print(f"{path.name}: {len(chunks)} chunks")

    if not all_chunks:
        raise ValueError(
            "No chunks generated; output was not overwritten"
        )

    output_path.write_text(
        json.dumps(all_chunks, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"TOTAL: {len(files)} documents, {len(all_chunks)} chunks")
    print(
        "Missing source URLs:",
        sum(not c["source_urls"] for c in all_chunks),
    )
    print(
        "Missing verification dates:",
        sum(not c["verified_at"] for c in all_chunks),
    )
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()