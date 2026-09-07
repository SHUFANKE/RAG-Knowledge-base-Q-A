import json
from pathlib import Path

def count_txt_files(directory_path:str) -> dict[str,int]:
    """读取指定目录下所有 .txt 文件，统计每个文件的字符数

    返回格式如: {"doc1.txt": 36, "doc2.txt": 46}
    """
    target_dir = Path(directory_path)

    #防御1：如果目录不存在，抛出异常
    if not target_dir.exists():
        raise FileNotFoundError(f"目录不存在：{directory_path}")

    #防御2：检查是否确实是一个目录（而不是一个普通文件）
    if not target_dir.is_dir():
        raise NotADirectoryError(f"指定的路径不是文件夹：{directory_path}")


    results ={}
    #使用glob遍历所有以.txt结尾的文件
    for file_path in target_dir.glob("*.txt"):
        text = file_path.read_text(encoding="utf-8")
        results[file_path.name] = len(text)

    #防御3：如果目录下没有任.txt文件，给出明确提示
    if not results:
        print(f"警告：目录{directory_path}中未找到任何.txt文件！")

    return results

def save_to_json(data:dict,output_path:str) ->None:
    """将数据安全保存为格式化的JSON文件"""
    out_file = Path(output_path)

    #保证输出文件的父级目录一定存在
    out_file.parent.mkdir(parents=True,exist_ok=True)

    #使用json.dumps转换为漂亮的JSON字符串(indent=2代表缩进2格，中文不转义)
    json_str = json.dumps(data,indent=2,ensure_ascii=False)
    out_file.write_text(json_str,encoding="utf-8")
    print(f"成功保存数据到：{out_file.resolve()}")#.resolve() 的作用是：把“相对路径”解析成操作系统的“绝对路径”（完整物理路径）


if __name__ == "__main__":
    #1.统计
    stats = count_txt_files("data")
    print("统计结果：",stats)

    #2.导出
    save_to_json(stats,"output/result.json")