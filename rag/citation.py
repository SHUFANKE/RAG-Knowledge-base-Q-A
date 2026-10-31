import re


def validate_citations(answer: str, reference_count: int) -> dict:
    cited_numbers = sorted({
        int(number)
        for number in re.findall(r"\[Doc\s+([0-9]+)\]", answer)
    })#查找编号 → 转成整数 → 去重 → 排序

    invalid_numbers = [
        number for number in cited_numbers
        if not 1 <= number <= reference_count
    ]

    if invalid_numbers:
        status = "invalid"#存在越界编号，包括编号 0
    elif cited_numbers:
        status = "valid"#出现了引用，所有编号都存在
    elif reference_count == 0:
        status = "not_applicable"#没有资料，回答也没有引用
    else:
        status = "missing"#提供了资料，但回答没有出现标准格式引用

    return {
        "status": status,
        "reference_count": reference_count,
        "cited_numbers": cited_numbers,
        "invalid_numbers": invalid_numbers,
    }