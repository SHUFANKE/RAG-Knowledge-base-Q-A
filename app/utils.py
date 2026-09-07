def add(a: int, b: int) -> int:
    """计算两数之和"""
    return a+b

def clean_text(text: str) -> str:
    """去除首尾空格并转换为小写（模拟最简单的数据清洗）"""
    return text.strip().lower()
