#novel_generator/common.py
# -*- coding: utf-8 -*-
"""
通用重试、清洗、日志工具
"""
import json
import logging
import os
import re
import time
import traceback
from datetime import datetime

logging.basicConfig(
    filename='app.log',      # 日志文件名
    filemode='a',            # 追加模式（'w' 会覆盖）
    level=logging.INFO,      # 记录 INFO 及以上级别的日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ── Prompt 历史记录文件（JSON Lines 格式） ─────────────────────────────────────
# 路径在工作目录下，与 app.log 同级
_PROMPT_HISTORY_FILE = "prompt_history.jsonl"
_prompt_history_lock = None  # 延迟初始化（避免 import 时创建线程对象）


def _get_lock():
    global _prompt_history_lock
    if _prompt_history_lock is None:
        import threading
        _prompt_history_lock = threading.Lock()
    return _prompt_history_lock


def _append_prompt_history(prompt: str, response: str, model: str = "",
                           reasoning: str = "", call_id: str = "",
                           status: str = "done", elapsed: float = 0) -> None:
    """将一次 LLM 调用追加到 prompt_history.jsonl

    status: "pending"(已发送等待返回) / "done"(成功) / "error"(失败)
    call_id: 用于关联 pending 和 done 记录
    """
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model": model,
        "prompt": prompt,
        "response": response,
        "prompt_len": len(prompt),
        "response_len": len(response),
        "status": status,
    }
    if call_id:
        record["call_id"] = call_id
    if elapsed:
        record["elapsed"] = round(elapsed, 1)
    if reasoning:
        record["reasoning"] = reasoning
        record["reasoning_len"] = len(reasoning)
    try:
        with _get_lock():
            with open(_PROMPT_HISTORY_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception as e:
        logging.warning(f"[prompt_history] 写入失败: {e}")


def call_with_retry(func, max_retries=3, sleep_time=2, fallback_return=None, **kwargs):
    """
    通用的重试机制封装。
    :param func: 要执行的函数
    :param max_retries: 最大重试次数
    :param sleep_time: 重试前的等待秒数
    :param fallback_return: 如果多次重试仍失败时的返回值
    :param kwargs: 传给func的命名参数
    :return: func的结果，若失败则返回 fallback_return
    """
    for attempt in range(1, max_retries + 1):
        try:
            return func(**kwargs)
        except Exception as e:
            logging.warning(f"[call_with_retry] Attempt {attempt} failed with error: {e}")
            traceback.print_exc()
            if attempt < max_retries:
                time.sleep(sleep_time)
            else:
                logging.error("Max retries reached, returning fallback_return.")
                return fallback_return

def remove_think_tags(text: str) -> str:
    """移除 <think>...</think> 包裹的内容"""
    return re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

def debug_log(prompt: str, response_content: str):
    logging.info(
        f"\n[#########################################  Prompt  #########################################]\n{prompt}\n"
    )
    logging.info(
        f"\n[######################################### Response #########################################]\n{response_content}\n"
    )

def invoke_with_cleaning(llm_adapter, prompt: str, max_retries: int = 3,
                         system_message: str = "", progress=None,
                         enable_streaming: bool = True) -> str:
    """调用 LLM 并清理返回结果，同时将 prompt+response 写入 prompt_history.jsonl

    当 progress 不为 None 且 enable_streaming=True 时，使用流式调用（invoke_stream），
    实时通过 progress 回调推送已生成的文本。流式中途失败时返回已收集的部分文本。
    """
    import uuid

    # 估算 prompt token 数（中文约 1.5-2 token/字符）
    prompt_chars = len(prompt)
    prompt_tokens_est = int(prompt_chars * 1.8)
    _timeout = getattr(llm_adapter, 'timeout', '?')
    _max_tokens = getattr(llm_adapter, 'max_tokens', '?')

    print("\n" + "="*50)
    print(f"发送到 LLM 的提示词 (字符数={prompt_chars}, 估算tokens≈{prompt_tokens_est}, "
          f"max_tokens={_max_tokens}, timeout={_timeout}s):")
    print("-"*50)
    print(prompt)
    print("="*50 + "\n")

    logging.info(f"[invoke] 开始调用 LLM: prompt字符数={prompt_chars}, "
                 f"估算tokens≈{prompt_tokens_est}, max_tokens={_max_tokens}, timeout={_timeout}s")

    # 尝试从 adapter 获取模型名（兼容不同 adapter 实现）
    _model = getattr(llm_adapter, 'model_name', '') or getattr(llm_adapter, 'model', '')

    # 是否启用流式
    use_stream = (enable_streaming and progress is not None
                  and hasattr(llm_adapter, 'invoke_stream'))

    # 立即写入 pending 记录，让前端可以先看到 prompt
    call_id = uuid.uuid4().hex[:12]
    _append_prompt_history(prompt, "", model=str(_model), call_id=call_id, status="pending")

    result = ""
    retry_count = 0

    while retry_count < max_retries:
        attempt_start = time.time()
        try:
            logging.info(f"[invoke] 第 {retry_count + 1}/{max_retries} 次调用, "
                         f"model={_model}, stream={use_stream}...")

            if use_stream:
                # 流式调用：逐片段接收，实时推送进度
                chunks = []
                char_count = 0
                try:
                    for chunk in llm_adapter.invoke_stream(prompt, system_message=system_message):
                        chunks.append(chunk)
                        char_count += len(chunk)
                        elapsed_so_far = time.time() - attempt_start
                        if progress is not None:
                            accumulated = "".join(chunks)
                            progress(None,
                                     desc=f"LLM 生成中… 已输出 {char_count} 字 ({elapsed_so_far:.0f}s)",
                                     content=accumulated)
                except Exception as stream_err:
                    # 流式中途失败：保留已收集的部分文本
                    partial = "".join(chunks)
                    elapsed = time.time() - attempt_start
                    err_type = type(stream_err).__name__
                    logging.warning(f"[invoke] 流式输出中断: {err_type}: {stream_err}, "
                                    f"已收集 {len(partial)} 字, 耗时={elapsed:.1f}s")
                    if partial.strip():
                        # 有部分内容：清理后标记为不完整并返回
                        partial = partial.replace("```", "").strip()
                        warning_tag = f"\n\n⚠️ 【生成中断】LLM 输出在 {elapsed:.0f}s 后中断（{err_type}），以上为已生成的部分内容（{len(partial)} 字）。"
                        _append_prompt_history(prompt, f"[PARTIAL:{len(partial)}字] {partial[:500]}...",
                                               model=str(_model), call_id=call_id,
                                               status="partial", elapsed=elapsed)
                        if progress is not None:
                            progress(None, desc=f"⚠️ 生成中断，已保留 {len(partial)} 字部分内容")
                        return partial + warning_tag
                    else:
                        # 没有任何内容，当作普通失败处理
                        raise stream_err
                result = "".join(chunks)
            else:
                # 非流式调用
                result = llm_adapter.invoke(prompt, system_message=system_message) if system_message else llm_adapter.invoke(prompt)

            elapsed = time.time() - attempt_start
            result_len = len(result) if result else 0
            logging.info(f"[invoke] LLM 返回, 耗时={elapsed:.1f}s, 返回字符数={result_len}")

            print("\n" + "="*50)
            print(f"LLM 返回的内容 (耗时={elapsed:.1f}s, 字符数={result_len}):")
            print("-"*50)
            print(result)
            print("="*50 + "\n")

            # 清理结果中的特殊格式标记
            result = result.replace("```", "").strip()
            if result:
                # 记录到 prompt 历史（含思考过程）
                reasoning = getattr(llm_adapter, 'last_reasoning', '') or ''
                debug_log(prompt, result)
                _append_prompt_history(prompt, result, model=str(_model),
                                       reasoning=reasoning, call_id=call_id,
                                       status="done", elapsed=elapsed)
                return result
            logging.warning(f"[invoke] 第 {retry_count + 1}/{max_retries} 次调用返回空结果, "
                            f"耗时={elapsed:.1f}s, 将重试...")
            retry_count += 1
        except Exception as e:
            elapsed = time.time() - attempt_start
            err_type = type(e).__name__
            logging.error(f"[invoke] 第 {retry_count + 1}/{max_retries} 次调用失败, "
                          f"耗时={elapsed:.1f}s, 错误类型={err_type}: {str(e)}")
            print(f"调用失败 ({retry_count + 1}/{max_retries}), 耗时={elapsed:.1f}s: [{err_type}] {str(e)}")
            retry_count += 1
            if retry_count >= max_retries:
                _append_prompt_history(prompt, f"[ERROR] {err_type}: {str(e)}",
                                       model=str(_model), call_id=call_id,
                                       status="error", elapsed=elapsed)
                logging.error(f"[invoke] 已达最大重试次数 {max_retries}, 抛出异常")
                raise e

    _append_prompt_history(prompt, "[EMPTY] 所有重试均返回空结果",
                           model=str(_model), call_id=call_id, status="error")
    logging.warning(f"[invoke] {max_retries} 次调用均返回空结果")
    return result

