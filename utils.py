# utils.py
# -*- coding: utf-8 -*-
import os
import json
import tempfile

def read_file(filename: str) -> str:
    """读取文件的全部内容，若文件不存在或异常则返回空字符串。"""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return ""
    except Exception as e:
        print(f"[read_file] 读取文件时发生错误: {e}")
        return ""

def append_text_to_file(text_to_append: str, file_path: str):
    """在文件末尾追加文本(带换行)。若文本非空且无换行，则自动加换行。"""
    if text_to_append and not text_to_append.startswith('\n'):
        text_to_append = '\n' + text_to_append

    try:
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(text_to_append)
    except IOError as e:
        print(f"[append_text_to_file] 发生错误：{e}")

def clear_file_content(filename: str):
    """清空指定文件内容。"""
    try:
        with open(filename, 'w', encoding='utf-8') as file:
            pass
    except IOError as e:
        print(f"[clear_file_content] 无法清空文件 '{filename}' 的内容：{e}")

def atomic_write_text(content: str, file_path: str):
    """原子写入文本文件：写入临时文件 → fsync → os.replace()"""
    dir_name = os.path.dirname(file_path) or '.'
    try:
        fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, file_path)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise
    except Exception as e:
        print(f"[atomic_write_text] 保存文件时发生错误: {e}")
        raise


def atomic_write_json(data, file_path: str, indent: int = 4):
    """原子写入 JSON 文件：写入临时文件 → fsync → os.replace()"""
    dir_name = os.path.dirname(file_path) or '.'
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=indent)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, file_path)
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def save_string_to_txt(content: str, filename: str):
    """将字符串保存为 txt 文件（覆盖写）。"""
    try:
        atomic_write_text(content, filename)
    except Exception as e:
        print(f"[save_string_to_txt] 保存文件时发生错误: {e}")

def save_data_to_json(data: dict, file_path: str) -> bool:
    """将数据保存到 JSON 文件。"""
    try:
        atomic_write_json(data, file_path, indent=4)
        return True
    except Exception as e:
        print(f"[save_data_to_json] 保存数据到JSON文件时出错: {e}")
        return False
