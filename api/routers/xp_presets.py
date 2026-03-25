# api/routers/xp_presets.py
# -*- coding: utf-8 -*-
"""XP 类型预设管理：增删改查"""

import os
import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(tags=["xp_presets"])

XP_PRESETS_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "xp_presets.json")


def _load_presets() -> list[dict]:
    if not os.path.exists(XP_PRESETS_FILE):
        return []
    try:
        with open(XP_PRESETS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save_presets(presets: list[dict]):
    with open(XP_PRESETS_FILE, "w", encoding="utf-8") as f:
        json.dump(presets, f, ensure_ascii=False, indent=2)


class XPPresetCreate(BaseModel):
    name: str
    content: str


class XPPresetUpdate(BaseModel):
    name: str | None = None
    content: str | None = None


@router.get("/xp-presets")
def list_xp_presets():
    return {"presets": _load_presets()}


@router.post("/xp-presets")
def create_xp_preset(body: XPPresetCreate):
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="名称不能为空")
    presets = _load_presets()
    if any(p["name"] == body.name.strip() for p in presets):
        raise HTTPException(status_code=400, detail=f"预设 '{body.name}' 已存在")
    presets.append({"name": body.name.strip(), "content": body.content.strip()})
    _save_presets(presets)
    return {"message": f"✅ XP 预设 '{body.name}' 已创建"}


@router.put("/xp-presets/{name}")
def update_xp_preset(name: str, body: XPPresetUpdate):
    presets = _load_presets()
    for p in presets:
        if p["name"] == name:
            if body.name is not None:
                # 检查新名称是否冲突
                new_name = body.name.strip()
                if new_name != name and any(pp["name"] == new_name for pp in presets):
                    raise HTTPException(status_code=400, detail=f"预设 '{new_name}' 已存在")
                p["name"] = new_name
            if body.content is not None:
                p["content"] = body.content.strip()
            _save_presets(presets)
            return {"message": f"✅ XP 预设已更新"}
    raise HTTPException(status_code=404, detail=f"未找到预设 '{name}'")


@router.delete("/xp-presets/{name}")
def delete_xp_preset(name: str):
    presets = _load_presets()
    new_presets = [p for p in presets if p["name"] != name]
    if len(new_presets) == len(presets):
        raise HTTPException(status_code=404, detail=f"未找到预设 '{name}'")
    _save_presets(new_presets)
    return {"message": f"✅ XP 预设 '{name}' 已删除"}
