# api/routers/presets.py
# -*- coding: utf-8 -*-
"""提示词预设路由"""

from fastapi import APIRouter, HTTPException
from api.schemas import PresetCreate, PromptUpdate
from api.app_state import get_web_app
import prompt_definitions

router = APIRouter(tags=["presets"])


@router.get("/presets")
def list_presets():
    app = get_web_app()
    name, desc = app.get_current_preset_info()
    return {
        "presets": app.get_preset_choices(),
        "active_preset": name,
        "active_description": desc
    }


@router.post("/presets/{name}/activate")
def activate_preset(name: str):
    app = get_web_app()
    active, desc, msg = app.activate_preset(name)
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    return {"active_preset": active, "description": desc, "message": msg}


@router.post("/presets")
def save_preset(body: PresetCreate):
    app = get_web_app()
    _, msg = app.save_as_new_preset(body.name, body.description)
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.delete("/presets/{name}")
def delete_preset(name: str):
    app = get_web_app()
    _, msg = app.delete_preset_web(name)
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.get("/presets/prompts")
def get_all_prompts():
    prompts = prompt_definitions.get_all_prompts()
    keys = prompt_definitions.PROMPT_KEYS
    display_names = prompt_definitions.PROMPT_DISPLAY_NAMES
    return {
        "prompts": prompts,
        "keys": keys,
        "display_names": display_names
    }


@router.put("/presets/prompts/{key}")
def update_prompt(key: str, body: PromptUpdate):
    app = get_web_app()
    if key not in prompt_definitions.PROMPT_KEYS:
        raise HTTPException(status_code=404, detail=f"未知的 prompt key: {key}")
    # Build a fake selection string like the web app expects
    selection = f"{prompt_definitions.PROMPT_DISPLAY_NAMES.get(key, key)} ({key})"
    msg = app.save_prompt_to_current_preset(selection, body.content)
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.post("/presets/prompts/{key}/reset")
def reset_prompt(key: str):
    app = get_web_app()
    if key not in prompt_definitions.PROMPT_KEYS:
        raise HTTPException(status_code=404, detail=f"未知的 prompt key: {key}")
    selection = f"{prompt_definitions.PROMPT_DISPLAY_NAMES.get(key, key)} ({key})"
    content, msg = app.reset_prompt_to_default(selection)
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "content": content}
