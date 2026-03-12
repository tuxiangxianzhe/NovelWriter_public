#novel_generator/knowledge.py
# -*- coding: utf-8 -*-
"""
知识文件导入至向量库（advanced_split_content、import_knowledge_file）
"""
import os
import logging
import re
import traceback
import nltk
import warnings
from utils import read_file
from novel_generator.vectorstore_utils import (
    load_vector_store, init_vector_store,
    load_author_vector_store, init_author_vector_store
)
from langchain_core.documents import Document

# 禁用特定的Torch警告
warnings.filterwarnings('ignore', message='.*Torch was not compiled with flash attention.*')
os.environ["TOKENIZERS_PARALLELISM"] = "false"
logging.basicConfig(
    filename='app.log',      # 日志文件名
    filemode='a',            # 追加模式（'w' 会覆盖）
    level=logging.INFO,      # 记录 INFO 及以上级别的日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
def _split_sentences(content: str) -> list:
    """中英文混合分句：先按中文标点分句，再对长句用 nltk 处理英文。"""
    # 按中文句末标点分割（保留标点在句子末尾）
    parts = re.split(r'(?<=[。！？；…\n])', content)
    sentences = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        # 如果片段仍然很长且包含英文句子结构，用 nltk 进一步分割
        if len(part) > 1000:
            sub_sents = nltk.sent_tokenize(part)
            sentences.extend(sub_sents)
        else:
            sentences.append(part)
    return sentences


def advanced_split_content(content: str, similarity_threshold: float = 0.7, max_length: int = 500) -> list:
    """使用中文感知的分段策略：先按句分割，再按 max_length 合并。"""
    sentences = _split_sentences(content)
    if not sentences:
        return []

    final_segments = []
    current_segment = []
    current_length = 0

    for sentence in sentences:
        sentence_length = len(sentence)
        if current_length + sentence_length > max_length:
            if current_segment:
                final_segments.append("".join(current_segment))
            current_segment = [sentence]
            current_length = sentence_length
        else:
            current_segment.append(sentence)
            current_length += sentence_length

    if current_segment:
        final_segments.append("".join(current_segment))

    logging.info(f"文本分段完成: {len(content)}字 → {len(final_segments)}段 (max_length={max_length})")
    return final_segments

def import_knowledge_file(
    embedding_api_key: str,
    embedding_url: str,
    embedding_interface_format: str,
    embedding_model_name: str,
    file_path: str,
    filepath: str
):
    logging.info(f"开始导入知识库文件: {file_path}, 接口格式: {embedding_interface_format}, 模型: {embedding_model_name}")
    if not os.path.exists(file_path):
        logging.warning(f"知识库文件不存在: {file_path}")
        return
    # 尝试多种编码读取文件
    content = ""
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030", "big5", "shift_jis", "latin-1"):
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            if content.strip():
                logging.info(f"知识库文件使用编码 {enc} 读取成功，长度={len(content)}")
                break
        except (UnicodeDecodeError, UnicodeError):
            continue
    if not content.strip():
        logging.warning("知识库文件内容为空（所有编码均失败）。")
        return
    paragraphs = advanced_split_content(content)
    from embedding_adapters import create_embedding_adapter
    embedding_adapter = create_embedding_adapter(
        embedding_interface_format,
        embedding_api_key,
        embedding_url if embedding_url else "http://localhost:11434/api",
        embedding_model_name
    )
    store = load_vector_store(embedding_adapter, filepath)
    if not store:
        logging.info("Vector store does not exist or load failed. Initializing a new one for knowledge import...")
        store = init_vector_store(embedding_adapter, paragraphs, filepath)
        if store:
            logging.info("知识库文件已成功导入至向量库(新初始化)。")
        else:
            logging.warning("知识库导入失败，跳过。")
    else:
        try:
            docs = [Document(page_content=str(p)) for p in paragraphs]
            store.add_documents(docs)
            logging.info("知识库文件已成功导入至向量库(追加模式)。")
        except Exception as e:
            logging.warning(f"知识库导入失败: {e}")
            traceback.print_exc()


def import_author_reference_file(
    embedding_api_key: str,
    embedding_url: str,
    embedding_interface_format: str,
    embedding_model_name: str,
    file_path: str,
    filepath: str = "",
    style_name: str = "",
    styles_dir: str = "",
):
    """将作者原文文件导入到作者参考库向量存储中（绑定到文风）。"""
    logging.info(f"开始导入作者参考库文件: {file_path}, style={style_name}")
    if not os.path.exists(file_path):
        logging.warning(f"作者参考库文件不存在: {file_path}")
        return
    # 尝试多种编码读取文件
    content = ""
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030", "big5", "shift_jis", "latin-1"):
        try:
            with open(file_path, "r", encoding=enc) as f:
                content = f.read()
            if content.strip():
                logging.info(f"作者参考库文件使用编码 {enc} 读取成功，长度={len(content)}")
                break
        except (UnicodeDecodeError, UnicodeError):
            continue
    if not content.strip():
        logging.warning("作者参考库文件内容为空（所有编码均失败）。")
        return
    paragraphs = advanced_split_content(content)
    from embedding_adapters import create_embedding_adapter
    embedding_adapter = create_embedding_adapter(
        embedding_interface_format,
        embedding_api_key,
        embedding_url if embedding_url else "http://localhost:11434/api",
        embedding_model_name
    )
    store = load_author_vector_store(embedding_adapter, filepath=filepath,
                                     style_name=style_name, styles_dir=styles_dir)
    if not store:
        logging.info("Author vector store does not exist. Initializing a new one...")
        store = init_author_vector_store(embedding_adapter, paragraphs, filepath=filepath,
                                         style_name=style_name, styles_dir=styles_dir)
        if store:
            logging.info("作者参考库文件已成功导入(新初始化)。")
        else:
            logging.warning("作者参考库导入失败，跳过。")
    else:
        try:
            docs = [Document(page_content=str(p)) for p in paragraphs]
            store.add_documents(docs)
            logging.info("作者参考库文件已成功导入(追加模式)。")
        except Exception as e:
            logging.warning(f"作者参考库导入失败: {e}")
            traceback.print_exc()
