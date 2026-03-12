# api/routers/logs.py
# -*- coding: utf-8 -*-
"""运行日志 + Prompt 历史路由"""

import json
import os
from fastapi import APIRouter, HTTPException
from api.app_state import get_web_app

router = APIRouter(tags=["logs"])

_PROMPT_HISTORY_FILE = "prompt_history.jsonl"


# ── 运行日志 ──────────────────────────────────────────────────────────────────

@router.get("/logs")
def get_logs(tail: int = 200):
    app = get_web_app()
    content = app.get_log_tail(tail)
    return {"content": content}


@router.delete("/logs")
def clear_logs():
    app = get_web_app()
    msg, _ = app.clear_app_log()
    return {"message": msg}


# ── Prompt 历史 ───────────────────────────────────────────────────────────────

@router.get("/logs/prompts")
def get_prompt_history(tail: int = 50, search: str = ""):
    """
    返回最近 N 条 prompt 历史记录（来自 prompt_history.jsonl）。
    可选 `search` 参数：对 prompt/response 内容做关键词过滤（大小写不敏感）。
    """
    if not os.path.exists(_PROMPT_HISTORY_FILE):
        return {"records": [], "total": 0}

    try:
        with open(_PROMPT_HISTORY_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取失败: {e}")

    raw_records = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            raw_records.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # 合并同一 call_id 的 pending/done 记录：done 覆盖 pending
    merged = {}  # call_id -> record
    no_id_records = []
    for r in raw_records:
        cid = r.get("call_id")
        if cid:
            existing = merged.get(cid)
            if not existing or r.get("status") != "pending":
                merged[cid] = r
        else:
            no_id_records.append(r)

    records = no_id_records + list(merged.values())
    # 按 timestamp 排序
    records.sort(key=lambda r: r.get("timestamp", ""))

    # 关键词过滤
    if search.strip():
        kw = search.strip().lower()
        records = [
            r for r in records
            if kw in r.get("prompt", "").lower()
            or kw in r.get("response", "").lower()
            or kw in r.get("model", "").lower()
        ]

    total = len(records)
    # 取最后 N 条（最新的在后面）
    records = records[-tail:]
    # 倒序返回（最新的排最前）
    records = list(reversed(records))

    return {"records": records, "total": total}


@router.delete("/logs/prompts")
def clear_prompt_history():
    """清空 prompt 历史记录文件"""
    try:
        with open(_PROMPT_HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write("")
        return {"message": "✅ Prompt 历史已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清空失败: {e}")
