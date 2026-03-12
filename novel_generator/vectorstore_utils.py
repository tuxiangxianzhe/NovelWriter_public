#novel_generator/vectorstore_utils.py
# -*- coding: utf-8 -*-
"""
向量库相关操作（初始化、更新、检索、清空、文本切分等）
"""
import os
import logging
import traceback
import nltk
import numpy as np
import re
import ssl
import requests
import warnings
from langchain_chroma import Chroma
logging.basicConfig(
    filename='app.log',      # 日志文件名
    filemode='a',            # 追加模式（'w' 会覆盖）
    level=logging.INFO,      # 记录 INFO 及以上级别的日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# 禁用特定的Torch警告
warnings.filterwarnings('ignore', message='.*Torch was not compiled with flash attention.*')
os.environ["TOKENIZERS_PARALLELISM"] = "false"  # 禁用tokenizer并行警告

from chromadb.config import Settings
from langchain_core.documents import Document
from sklearn.metrics.pairwise import cosine_similarity
from .common import call_with_retry

def get_vectorstore_dir(filepath: str) -> str:
    """获取 vectorstore 路径"""
    return os.path.join(filepath, "vectorstore")

def clear_vector_store(filepath: str) -> bool:
    """清空 清空向量库"""
    import shutil
    store_dir = get_vectorstore_dir(filepath)
    if not os.path.exists(store_dir):
        logging.info("No vector store found to clear.")
        return False
    try:
        shutil.rmtree(store_dir)
        logging.info(f"Vector store directory '{store_dir}' removed.")
        return True
    except Exception as e:
        logging.error(f"无法删除向量库文件夹，请关闭程序后手动删除 {store_dir}。\n {str(e)}")
        traceback.print_exc()
        return False

def init_vector_store(embedding_adapter, texts, filepath: str):
    """
    在 filepath 下创建/加载一个 Chroma 向量库并插入 texts。
    如果Embedding失败，则返回 None，不中断任务。
    """
    from langchain.embeddings.base import Embeddings as LCEmbeddings

    store_dir = get_vectorstore_dir(filepath)
    os.makedirs(store_dir, exist_ok=True)
    documents = [Document(page_content=str(t)) for t in texts]

    try:
        class LCEmbeddingWrapper(LCEmbeddings):
            def embed_documents(self, texts):
                return call_with_retry(
                    func=embedding_adapter.embed_documents,
                    max_retries=3,
                    fallback_return=[],
                    texts=texts
                )
            def embed_query(self, query: str):
                res = call_with_retry(
                    func=embedding_adapter.embed_query,
                    max_retries=3,
                    fallback_return=[],
                    query=query
                )
                return res

        chroma_embedding = LCEmbeddingWrapper()
        vectorstore = Chroma.from_documents(
            documents,
            embedding=chroma_embedding,
            persist_directory=store_dir,
            client_settings=Settings(anonymized_telemetry=False),
            collection_name="novel_collection"
        )
        return vectorstore
    except Exception as e:
        logging.warning(f"Init vector store failed: {e}")
        traceback.print_exc()
        return None

def load_vector_store(embedding_adapter, filepath: str):
    """
    读取已存在的 Chroma 向量库。若不存在则返回 None。
    如果加载失败（embedding 或IO问题），则返回 None。
    """
    from langchain.embeddings.base import Embeddings as LCEmbeddings
    store_dir = get_vectorstore_dir(filepath)
    if not os.path.exists(store_dir):
        logging.info("Vector store not found. Will return None.")
        return None

    try:
        class LCEmbeddingWrapper(LCEmbeddings):
            def embed_documents(self, texts):
                return call_with_retry(
                    func=embedding_adapter.embed_documents,
                    max_retries=3,
                    fallback_return=[],
                    texts=texts
                )
            def embed_query(self, query: str):
                res = call_with_retry(
                    func=embedding_adapter.embed_query,
                    max_retries=3,
                    fallback_return=[],
                    query=query
                )
                return res

        chroma_embedding = LCEmbeddingWrapper()
        return Chroma(
            persist_directory=store_dir,
            embedding_function=chroma_embedding,
            client_settings=Settings(anonymized_telemetry=False),
            collection_name="novel_collection"
        )
    except Exception as e:
        logging.warning(f"Failed to load vector store: {e}")
        traceback.print_exc()
        return None

def split_by_length(text: str, max_length: int = 500):
    """按照 max_length 切分文本"""
    segments = []
    start_idx = 0
    while start_idx < len(text):
        end_idx = min(start_idx + max_length, len(text))
        segment = text[start_idx:end_idx]
        segments.append(segment.strip())
        start_idx = end_idx
    return segments

def split_text_for_vectorstore(chapter_text: str, max_length: int = 500, similarity_threshold: float = 0.7):
    """
    对新的章节文本进行分段后,再用于存入向量库。
    使用 embedding 进行文本相似度计算。
    """
    if not chapter_text.strip():
        return []
    
    # nltk.download('punkt', quiet=True)
    # nltk.download('punkt_tab', quiet=True)
    sentences = nltk.sent_tokenize(chapter_text)
    if not sentences:
        return []
    
    # 直接按长度分段,不做相似度合并
    final_segments = []
    current_segment = []
    current_length = 0
    
    for sentence in sentences:
        sentence_length = len(sentence)
        if current_length + sentence_length > max_length:
            if current_segment:
                final_segments.append(" ".join(current_segment))
            current_segment = [sentence]
            current_length = sentence_length
        else:
            current_segment.append(sentence)
            current_length += sentence_length
    
    if current_segment:
        final_segments.append(" ".join(current_segment))
    
    return final_segments

def update_vector_store(embedding_adapter, new_chapter: str, filepath: str):
    """
    将最新章节文本插入到向量库中。
    若库不存在则初始化；若初始化/更新失败，则跳过。
    """
    from utils import read_file, clear_file_content, save_string_to_txt
    splitted_texts = split_text_for_vectorstore(new_chapter)
    if not splitted_texts:
        logging.warning("No valid text to insert into vector store. Skipping.")
        return

    store = load_vector_store(embedding_adapter, filepath)
    if not store:
        logging.info("Vector store does not exist or failed to load. Initializing a new one for new chapter...")
        store = init_vector_store(embedding_adapter, splitted_texts, filepath)
        if not store:
            logging.warning("Init vector store failed, skip embedding.")
        else:
            logging.info("New vector store created successfully.")
        return

    try:
        docs = [Document(page_content=str(t)) for t in splitted_texts]
        store.add_documents(docs)
        logging.info("Vector store updated with the new chapter splitted segments.")
    except Exception as e:
        logging.warning(f"Failed to update vector store: {e}")
        traceback.print_exc()

def get_relevant_context_from_vector_store(
    embedding_adapter, query: str, filepath: str, k: int = 2,
    score_threshold: float = 0.35,
) -> str:
    """
    从向量库中检索与 query 最相关的 k 条文本，拼接后返回。
    如果向量库加载/检索失败，则返回空字符串。
    最终只返回最多2000字符的检索片段。

    score_threshold: 相关度下限 (0~1, 越高越严格)。
                     低于该阈值的结果将被丢弃，避免注入无关内容。
    """
    store = load_vector_store(embedding_adapter, filepath)
    if not store:
        logging.info("No vector store found or load failed. Returning empty context.")
        return ""

    try:
        # 使用带相关度评分的检索，过滤低质量结果
        docs_with_scores = store.similarity_search_with_relevance_scores(query, k=k)
        if not docs_with_scores:
            logging.info(f"No relevant documents found for query '{query}'. Returning empty context.")
            return ""

        filtered = [(doc, score) for doc, score in docs_with_scores if score >= score_threshold]
        if not filtered:
            logging.info(
                f"All {len(docs_with_scores)} results below threshold {score_threshold} "
                f"(best={docs_with_scores[0][1]:.3f}). Returning empty context."
            )
            return ""

        if len(filtered) < len(docs_with_scores):
            logging.info(
                f"Knowledge retrieval: kept {len(filtered)}/{len(docs_with_scores)} results "
                f"(threshold={score_threshold}, scores={[f'{s:.3f}' for _, s in docs_with_scores]})"
            )

        combined = "\n".join([doc.page_content for doc, _ in filtered])
        if len(combined) > 2000:
            combined = combined[:2000]
        return combined
    except Exception as e:
        logging.warning(f"Similarity search failed: {e}")
        traceback.print_exc()
        return ""

def import_knowledge_to_vectorstore(embedding_adapter, knowledge_text: str, filepath: str):
    """
    将知识库文本导入到向量库中。
    若库不存在则初始化；若初始化/更新失败，则跳过。
    """
    splitted_texts = split_text_for_vectorstore(knowledge_text)
    if not splitted_texts:
        logging.warning("No valid text to import into vector store. Skipping.")
        return

    store = load_vector_store(embedding_adapter, filepath)
    if not store:
        logging.info("Vector store does not exist or failed to load. Initializing a new one for knowledge import...")
        store = init_vector_store(embedding_adapter, splitted_texts, filepath)
        if not store:
            logging.warning("Init vector store failed, skip knowledge import.")
        else:
            logging.info("Knowledge imported successfully (new vector store created).")
        return

    try:
        docs = [Document(page_content=str(t)) for t in splitted_texts]
        store.add_documents(docs)
        logging.info("Knowledge imported successfully (appended to existing vector store).")
    except Exception as e:
        logging.warning(f"Failed to import knowledge: {e}")
        traceback.print_exc()

def get_author_vectorstore_dir(filepath: str = "", style_name: str = "", styles_dir: str = "") -> str:
    """获取作者参考库 vectorstore 路径。
    优先使用 style_name + styles_dir（文风绑定模式）；
    如果未指定 style_name，回退到 filepath（兼容旧逻辑）。
    """
    if style_name and styles_dir:
        return os.path.join(styles_dir, f"{style_name}_author_vectorstore")
    # 兼容旧的 project-bound 模式
    return os.path.join(filepath, "author_vectorstore")


def init_author_vector_store(embedding_adapter, texts: list, filepath: str = "",
                             style_name: str = "", styles_dir: str = ""):
    """
    创建/加载一个作者参考库 Chroma 向量库并插入 texts。
    使用独立的 collection name: author_reference_collection。
    """
    from langchain.embeddings.base import Embeddings as LCEmbeddings

    store_dir = get_author_vectorstore_dir(filepath=filepath, style_name=style_name, styles_dir=styles_dir)
    os.makedirs(store_dir, exist_ok=True)
    documents = [Document(page_content=str(t)) for t in texts]

    try:
        class LCEmbeddingWrapper(LCEmbeddings):
            def embed_documents(self, texts):
                return call_with_retry(
                    func=embedding_adapter.embed_documents,
                    max_retries=3,
                    fallback_return=[],
                    texts=texts
                )
            def embed_query(self, query: str):
                return call_with_retry(
                    func=embedding_adapter.embed_query,
                    max_retries=3,
                    fallback_return=[],
                    query=query
                )

        chroma_embedding = LCEmbeddingWrapper()
        vectorstore = Chroma.from_documents(
            documents,
            embedding=chroma_embedding,
            persist_directory=store_dir,
            client_settings=Settings(anonymized_telemetry=False),
            collection_name="author_reference_collection"
        )
        return vectorstore
    except Exception as e:
        logging.warning(f"Init author vector store failed: {e}")
        traceback.print_exc()
        return None


def load_author_vector_store(embedding_adapter, filepath: str = "",
                             style_name: str = "", styles_dir: str = ""):
    """
    读取已存在的作者参考库 Chroma 向量库。若不存在则返回 None。
    """
    from langchain.embeddings.base import Embeddings as LCEmbeddings

    store_dir = get_author_vectorstore_dir(filepath=filepath, style_name=style_name, styles_dir=styles_dir)
    if not os.path.exists(store_dir):
        logging.info("Author vector store not found. Will return None.")
        return None

    try:
        class LCEmbeddingWrapper(LCEmbeddings):
            def embed_documents(self, texts):
                return call_with_retry(
                    func=embedding_adapter.embed_documents,
                    max_retries=3,
                    fallback_return=[],
                    texts=texts
                )
            def embed_query(self, query: str):
                return call_with_retry(
                    func=embedding_adapter.embed_query,
                    max_retries=3,
                    fallback_return=[],
                    query=query
                )

        chroma_embedding = LCEmbeddingWrapper()
        return Chroma(
            persist_directory=store_dir,
            embedding_function=chroma_embedding,
            client_settings=Settings(anonymized_telemetry=False),
            collection_name="author_reference_collection"
        )
    except Exception as e:
        logging.warning(f"Failed to load author vector store: {e}")
        traceback.print_exc()
        return None


def get_author_reference_context(
    embedding_adapter, query: str, filepath: str = "", k: int = 3,
    score_threshold: float = 0.3,
    style_name: str = "", styles_dir: str = "",
    max_chars: int = 2000,
) -> str:
    """
    从作者参考库中检索文风参考片段，采用混合策略：
    - 语义检索：取与当前章节主题最相关的片段（对话/动作/描写等场景匹配）
    - 随机采样：从全库随机抽取片段，确保覆盖作者多种写作手法

    最终返回不超过 max_chars 字符的参考文本，以 \\n---\\n 分隔。
    """
    import random

    store = load_author_vector_store(embedding_adapter, filepath=filepath,
                                     style_name=style_name, styles_dir=styles_dir)
    if not store:
        logging.info("No author vector store found. Returning empty context.")
        return ""

    try:
        collection = store._collection
        total_count = collection.count()
        if total_count == 0:
            logging.info("Author vector store is empty.")
            return ""

        selected_texts = []
        used_ids = set()

        # ── 第一部分：语义检索（取与章节主题相关的片段）──
        semantic_k = min(max(k // 2, 1), total_count)  # 至少1条语义结果
        try:
            docs_with_scores = store.similarity_search_with_relevance_scores(query, k=semantic_k + 3)
            for doc, score in docs_with_scores:
                if score >= score_threshold and len(selected_texts) < semantic_k:
                    doc_id = hash(doc.page_content)
                    if doc_id not in used_ids:
                        selected_texts.append(doc.page_content)
                        used_ids.add(doc_id)
            logging.info(
                f"Author ref semantic: {len(selected_texts)}/{len(docs_with_scores)} hits "
                f"(threshold={score_threshold}, query='{query[:50]}...')"
            )
        except Exception as e:
            logging.warning(f"Author ref semantic search failed: {e}")

        # ── 第二部分：随机采样（覆盖不同写作风格片段）──
        random_k = k - len(selected_texts)  # 剩余名额给随机
        if random_k > 0 and total_count > len(selected_texts):
            try:
                all_docs = collection.get()
                all_contents = all_docs.get("documents", [])
                # 排除已选中的片段
                candidates = [t for t in all_contents if hash(t) not in used_ids]
                if candidates:
                    sample_n = min(random_k, len(candidates))
                    random_picks = random.sample(candidates, sample_n)
                    selected_texts.extend(random_picks)
                    logging.info(f"Author ref random: sampled {sample_n} from {len(candidates)} candidates")
            except Exception as e:
                logging.warning(f"Author ref random sampling failed: {e}")

        if not selected_texts:
            logging.info("Author ref: no texts selected after both strategies.")
            return ""

        combined = "\n---\n".join(selected_texts)
        if len(combined) > max_chars:
            # 按片段截断而非硬切字符串，避免截断到半句话
            result_parts = []
            current_len = 0
            for text in selected_texts:
                if current_len + len(text) + 5 > max_chars:  # 5 for "\n---\n"
                    break
                result_parts.append(text)
                current_len += len(text) + 5
            combined = "\n---\n".join(result_parts) if result_parts else selected_texts[0][:max_chars]

        logging.info(f"Author ref final: {len(selected_texts)} fragments, {len(combined)} chars")
        return combined
    except Exception as e:
        logging.warning(f"Author reference search failed: {e}")
        traceback.print_exc()
        return ""


def clear_author_vector_store(filepath: str = "", style_name: str = "", styles_dir: str = "") -> None:
    """清空作者参考库向量库"""
    import shutil
    store_dir = get_author_vectorstore_dir(filepath=filepath, style_name=style_name, styles_dir=styles_dir)
    if not os.path.exists(store_dir):
        logging.info("No author vector store found to clear.")
        return
    try:
        shutil.rmtree(store_dir)
        logging.info(f"Author vector store directory '{store_dir}' removed.")
    except Exception as e:
        logging.error(f"无法删除作者参考库文件夹 {store_dir}。\n {str(e)}")
        traceback.print_exc()


def _get_sentence_transformer(model_name: str = 'paraphrase-MiniLM-L6-v2'):
    """获取sentence transformer模型，处理SSL问题"""
    try:
        # 设置torch环境变量
        os.environ["TORCH_ALLOW_TF32_CUBLAS_OVERRIDE"] = "0"
        os.environ["TORCH_CUDNN_V8_API_ENABLED"] = "0"
        
        # 禁用SSL验证
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # ...existing code...
    except Exception as e:
        logging.error(f"Failed to load sentence transformer model: {e}")
        traceback.print_exc()
        return None
