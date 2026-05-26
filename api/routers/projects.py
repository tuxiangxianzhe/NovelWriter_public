# api/routers/projects.py
# -*- coding: utf-8 -*-
"""项目管理路由"""

import os
import shutil
from datetime import datetime
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
        workflow_mode=body.workflow_mode,
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


# ── 项目备份与还原 ────────────────────────────────────────────────────────────

def _get_backup_dir(filepath: str) -> str:
    return os.path.join(filepath, ".backups")


@router.get("/projects/{name}/backups")
def list_backups(name: str):
    """列出指定项目的所有备份"""
    app = get_web_app()
    proj = app.projects_data.get("projects", {}).get(name)
    if not proj:
        raise HTTPException(status_code=404, detail=f"项目 '{name}' 不存在")
    filepath = proj.get("filepath", "./output")
    backup_dir = _get_backup_dir(filepath)
    if not os.path.isdir(backup_dir):
        return {"backups": []}
    backups = []
    for entry in sorted(os.listdir(backup_dir), reverse=True):
        entry_path = os.path.join(backup_dir, entry)
        if os.path.isdir(entry_path):
            # 解析备份名中的时间和备注
            # 格式：20260327_143052 或 20260327_143052_用户备注
            parts = entry.split("_", 2)
            ts_str = ""
            note = ""
            if len(parts) >= 2:
                try:
                    ts_str = datetime.strptime(parts[0] + parts[1], "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
                except ValueError:
                    ts_str = entry
            if len(parts) >= 3:
                note = parts[2]
            # 计算大小
            total_size = 0
            for dirpath, _dirnames, filenames in os.walk(entry_path):
                for f in filenames:
                    total_size += os.path.getsize(os.path.join(dirpath, f))
            backups.append({
                "id": entry,
                "timestamp": ts_str,
                "note": note,
                "size_mb": round(total_size / 1024 / 1024, 2),
            })
    return {"backups": backups}


@router.post("/projects/{name}/backups")
def create_backup(name: str, note: str = ""):
    """创建项目备份"""
    app = get_web_app()
    proj = app.projects_data.get("projects", {}).get(name)
    if not proj:
        raise HTTPException(status_code=404, detail=f"项目 '{name}' 不存在")
    filepath = proj.get("filepath", "./output")
    if not os.path.isdir(filepath):
        raise HTTPException(status_code=400, detail="项目目录不存在")

    backup_dir = _get_backup_dir(filepath)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{ts}_{note}" if note else ts
    # 清理备份名中的非法字符
    backup_name = "".join(c for c in backup_name if c not in r'\/:*?"<>|')
    dest = os.path.join(backup_dir, backup_name)

    try:
        # 复制项目目录到备份位置，排除 .backups 和 vectorstore 目录
        def _ignore(directory, contents):
            ignored = set()
            if os.path.abspath(directory) == os.path.abspath(filepath):
                if ".backups" in contents:
                    ignored.add(".backups")
                if "vectorstore" in contents:
                    ignored.add("vectorstore")
            return ignored

        shutil.copytree(filepath, dest, ignore=_ignore)
        return {"message": f"✅ 备份成功: {backup_name}", "backup_id": backup_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"备份失败: {str(e)}")


@router.post("/projects/{name}/backups/{backup_id}/restore")
def restore_backup(name: str, backup_id: str):
    """从备份还原项目"""
    app = get_web_app()
    proj = app.projects_data.get("projects", {}).get(name)
    if not proj:
        raise HTTPException(status_code=404, detail=f"项目 '{name}' 不存在")
    filepath = proj.get("filepath", "./output")
    backup_dir = _get_backup_dir(filepath)
    backup_path = os.path.join(backup_dir, backup_id)
    if not os.path.isdir(backup_path):
        raise HTTPException(status_code=404, detail=f"备份 '{backup_id}' 不存在")

    try:
        # 先备份当前状态（自动备份，防止误操作）
        auto_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        auto_backup = os.path.join(backup_dir, f"{auto_ts}_还原前自动备份")

        def _ignore(directory, contents):
            ignored = set()
            if os.path.abspath(directory) == os.path.abspath(filepath):
                if ".backups" in contents:
                    ignored.add(".backups")
                if "vectorstore" in contents:
                    ignored.add("vectorstore")
            return ignored

        shutil.copytree(filepath, auto_backup, ignore=_ignore)

        # 清除当前项目文件（保留 .backups 和 vectorstore）
        for item in os.listdir(filepath):
            if item in (".backups", "vectorstore"):
                continue
            item_path = os.path.join(filepath, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

        # 从备份复制文件回来
        for item in os.listdir(backup_path):
            src = os.path.join(backup_path, item)
            dst = os.path.join(filepath, item)
            if os.path.isdir(src):
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        return {"message": f"✅ 已从备份 '{backup_id}' 还原，还原前状态已自动备份为 '{auto_ts}_还原前自动备份'"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"还原失败: {str(e)}")


@router.delete("/projects/{name}/backups/{backup_id}")
def delete_backup(name: str, backup_id: str):
    """删除指定备份"""
    app = get_web_app()
    proj = app.projects_data.get("projects", {}).get(name)
    if not proj:
        raise HTTPException(status_code=404, detail=f"项目 '{name}' 不存在")
    filepath = proj.get("filepath", "./output")
    backup_path = os.path.join(_get_backup_dir(filepath), backup_id)
    if not os.path.isdir(backup_path):
        raise HTTPException(status_code=404, detail=f"备份 '{backup_id}' 不存在")
    try:
        shutil.rmtree(backup_path)
        return {"message": f"✅ 备份 '{backup_id}' 已删除"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


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
