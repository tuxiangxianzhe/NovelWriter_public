# api/routers/projects.py
# -*- coding: utf-8 -*-
"""项目管理路由"""

from fastapi import APIRouter, HTTPException
from api.schemas import ProjectCreate, ProjectUpdate
from api.app_state import get_web_app

router = APIRouter(tags=["projects"])


@router.get("/projects")
def list_projects():
    app = get_web_app()
    data = app.projects_data
    return {
        "projects": list(data.get("projects", {}).keys()),
        "active_project": data.get("active_project", "")
    }


@router.post("/projects")
def create_project(body: ProjectCreate):
    app = get_web_app()
    _, msg = app.create_project(body.name, body.filepath)
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg, "name": body.name}


@router.post("/projects/{name}/activate")
def activate_project(name: str):
    app = get_web_app()
    results = app.switch_project(name)
    # last element is the status message
    msg = results[-1] if isinstance(results, list) else str(results)
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    proj = app.projects_data["projects"].get(name, {})
    # 返回完整配置（含 project_config.json 扩展字段）
    fp = proj.get("filepath", "./output")
    full_config = app._load_project_config(fp)
    full_config["filepath"] = fp
    full_config["name"] = proj.get("name", name)
    full_config["created_at"] = proj.get("created_at", "")
    full_config["updated_at"] = proj.get("updated_at", "")
    return {"message": msg, "project": full_config}


@router.put("/projects/{name}")
def update_project(name: str, body: ProjectUpdate):
    app = get_web_app()
    if name not in app.projects_data.get("projects", {}):
        raise HTTPException(status_code=404, detail=f"项目 '{name}' 不存在")
    # Switch to this project first
    app.projects_data["active_project"] = name
    msg = app.save_current_project(
        body.topic, body.genre, body.num_chapters,
        body.word_number, body.filepath, body.user_guidance,
        body.xp_type,
        llm_config_name=body.llm_config_name,
        emb_config_name=body.emb_config_name,
        arch_style=body.arch_style,
        bp_style=body.bp_style,
        ch_style=body.ch_style,
        ch_narrative_style=body.ch_narrative_style,
        expand_style=body.expand_style,
        expand_narrative_style=body.expand_narrative_style,
        cont_style=body.cont_style,
        cont_xp_type=body.cont_xp_type,
        step_seed_text=body.step_seed_text,
        step_char_text=body.step_char_text,
        step_char_state_text=body.step_char_state_text,
        step_world_text=body.step_world_text,
        step_plot_text=body.step_plot_text,
        continue_guidance=body.continue_guidance,
        cont_step_chars_text=body.cont_step_chars_text,
        cont_step_arcs_text=body.cont_step_arcs_text,
        cont_step_char_state_text=body.cont_step_char_state_text,
        xp_selected_presets=body.xp_selected_presets,
    )
    return {"message": msg}


@router.delete("/projects/{name}")
def delete_project(name: str):
    app = get_web_app()
    _, msg = app.delete_project(name)
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.post("/projects/discover")
def discover_projects():
    app = get_web_app()
    discovered, msg = app.discover_projects()
    return {"discovered": discovered, "message": msg}


@router.get("/projects/active")
def get_active_project():
    app = get_web_app()
    name = app.get_active_project_name()
    if not name:
        return {"active_project": None, "project": None}
    proj = app.projects_data["projects"].get(name, {})
    # 返回完整配置（含 project_config.json 扩展字段）
    fp = proj.get("filepath", "./output")
    full_config = app._load_project_config(fp)
    full_config["filepath"] = fp
    full_config["name"] = proj.get("name", name)
    full_config["created_at"] = proj.get("created_at", "")
    full_config["updated_at"] = proj.get("updated_at", "")
    return {"active_project": name, "project": full_config}
