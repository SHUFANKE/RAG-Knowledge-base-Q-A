import json
from pathlib import Path
import pytest
from app.file_loader import count_txt_files,save_to_json

def test_count_txt_files_success():
    """测试正常读取data目录下的文件统计"""
    stats = count_txt_files("data")
    assert "doc1.txt" in stats
    assert stats["doc1.txt"] == 34
    assert len(stats) == 3


def  test_count_txt_files_not_found():
    """测试传入不存在的路径时，能否正确触发FileNotFoundError异常"""
    #pytest.raises的作用是：断言下面包裹的代码必须抛出该异常，如果不抛错，测试反而失败！
    with pytest.raises(FileNotFoundError):
        count_txt_files("non_existent_folder")

def test_save_to_json(tmp_path:Path):
    """测试 JSON 文件的持久化存储与反序列化解析

    tmp_path 是 pytest 内置的神级夹具（Fixture），它会自动为你提供一个测试专用的临时目录，
    测试结束后自动清理，避免污染真实工作区。
    """
    test_data = {"test_file.txt":100}
    test_output_file =tmp_path/"sub_folder"/"test_result.json"

    #执行保存函数
    save_to_json(test_data,str(test_output_file))

    #验证文件是否真实落盘
    assert test_output_file.exists()

    #读取并验证解析内容
    loaded_data = json.loads(test_output_file.read_text(encoding="utf-8"))
    assert loaded_data == test_data