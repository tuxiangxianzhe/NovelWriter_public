# api/sse_utils.py
# -*- coding: utf-8 -*-
"""SSE 流式工具：替代 gr.Progress() 的进度回调"""

import asyncio
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import AsyncGenerator, Callable, Any
from uuid import uuid4

logger = logging.getLogger(__name__)

# 共享线程池，避免每次 SSE 请求都新建
_executor = ThreadPoolExecutor(max_workers=4)

# 活跃操作注册表，用于取消支持
_active_operations: dict[str, "ProgressQueue"] = {}


def cancel_operation(operation_id: str) -> bool:
    """取消指定的操作。返回是否找到该操作。"""
    pq = _active_operations.get(operation_id)
    if pq is not None:
        pq.cancelled = True
        return True
    return False


def cancel_all_operations():
    """取消所有活跃操作。"""
    for pq in _active_operations.values():
        pq.cancelled = True


class ProgressQueue:
    """替换 gr.Progress() 的轻量回调队列。

    调用方式与 gr.Progress 相同：
        progress(value, desc="...")
    其中 value 为 0~1 的浮点数（可忽略），desc 为进度描述文字。
    """

    def __init__(self):
        self._queue: asyncio.Queue = None  # 延迟初始化，绑定到调用协程的事件循环
        self.cancelled = False
        self.operation_id = str(uuid4())

    def _ensure_queue(self):
        if self._queue is None:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
            self._queue = asyncio.Queue()

    def __call__(self, value=None, desc: str = "", total=None):
        """由同步线程调用，将进度放入队列"""
        self._ensure_queue()
        event = {"type": "progress", "message": desc}
        if value is not None:
            try:
                event["value"] = float(value)
            except (TypeError, ValueError):
                pass
        try:
            loop = asyncio.get_event_loop()
            loop.call_soon_threadsafe(self._queue.put_nowait, event)
        except Exception as e:
            logger.debug(f"ProgressQueue put failed: {e}")

    def empty(self) -> bool:
        return self._queue is None or self._queue.empty()

    async def drain(self) -> list:
        """取出队列中所有当前消息"""
        items = []
        while self._queue and not self._queue.empty():
            try:
                items.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        return items


def _sse_data(event: dict) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


async def run_with_sse(
    sync_fn: Callable,
    *args,
    progress_index: int = -1,
) -> AsyncGenerator[str, None]:
    """
    在线程池中运行同步生成函数，将进度作为 SSE 发送。

    参数说明
    --------
    sync_fn : 同步函数，其参数列表的最后一项（或 progress_index 指定位置）
              期望接收一个 progress 可调用对象。
    *args   : 传给 sync_fn 的所有参数（不含 progress）。
    progress_index : 将 progress 插入到 args 的哪个位置。
                     -1 表示追加到末尾（默认）。

    SSE 事件格式
    ------------
    {"type": "started",  "operation_id": "..."}
    {"type": "progress", "message": "...", "value": 0.5}
    {"type": "result",   "content": "..."}
    {"type": "error",    "message": "..."}
    {"type": "done"}
    """
    progress = ProgressQueue()
    progress._ensure_queue()

    # 注册到活跃操作表
    op_id = progress.operation_id
    _active_operations[op_id] = progress

    # 将 progress 插入参数列表
    args_list = list(args)
    if progress_index == -1:
        args_list.append(progress)
    else:
        args_list.insert(progress_index, progress)

    loop = asyncio.get_event_loop()
    future = loop.run_in_executor(_executor, sync_fn, *args_list)

    try:
        # 先发出 started 事件，告知前端 operation_id
        yield _sse_data({"type": "started", "operation_id": op_id})

        while not future.done():
            # 检查是否被取消
            if progress.cancelled:
                future.cancel()
                yield _sse_data({"type": "error", "message": "操作已取消"})
                return

            # 先把队列里积攒的进度消息全部发出去
            for event in await progress.drain():
                yield _sse_data(event)
            await asyncio.sleep(0.05)

        # future 完成后，再把剩余进度消息清空
        for event in await progress.drain():
            yield _sse_data(event)

        # 最终检查取消状态（可能在 future 完成后才设置）
        if progress.cancelled:
            yield _sse_data({"type": "error", "message": "操作已取消"})
            return

        result = await future

        # 根据返回值类型决定如何发送结果
        if isinstance(result, str):
            content = result
        elif isinstance(result, tuple):
            # 某些方法返回 (status_msg, content)
            content = result[1] if len(result) >= 2 else str(result[0])
        else:
            content = str(result) if result is not None else ""

        yield _sse_data({"type": "result", "content": content})

    except Exception as e:
        logger.error(f"run_with_sse error: {e}", exc_info=True)
        yield _sse_data({"type": "error", "message": str(e)})

    finally:
        _active_operations.pop(op_id, None)
        yield _sse_data({"type": "done"})
