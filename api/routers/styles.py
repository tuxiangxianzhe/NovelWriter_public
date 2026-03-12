# api/routers/styles.py
# -*- coding: utf-8 -*-
"""文风 + 叙事DNA 路由"""

import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from api.schemas import (
    StyleAnalyzeRequest, StyleAnalyzeDNARequest,
    StyleMergeRequest, StyleSaveRequest, StyleCalibrateRequest,
)
from api.app_state import get_web_app
from api.sse_utils import run_with_sse

router = APIRouter(tags=["styles"])


def _sse_response(gen):
    return StreamingResponse(
        gen,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/styles")
def list_styles():
    app = get_web_app()
    return {"styles": app.list_styles()}


@router.post("/styles/analyze")
def analyze_style(body: StyleAnalyzeRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.analyze_style,
            body.llm_config_name, body.sample_text, body.style_name,
            body.unlock,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/styles/analyze-dna")
def analyze_narrative_dna(body: StyleAnalyzeDNARequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.analyze_narrative_dna,
            body.llm_config_name, body.sample_text, body.style_name,
            body.unlock,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/styles/merge")
def merge_styles(body: StyleMergeRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.merge_styles,
            body.llm_config_name, body.selected_styles,
            body.merge_name, body.user_preference,
            body.unlock,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/styles/calibrate")
def calibrate_style(body: StyleCalibrateRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.calibrate_style,
            body.llm_config_name, body.style_name, body.max_iterations,
            body.unlock,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/styles/calibrate-narrative")
def calibrate_narrative(body: StyleCalibrateRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.calibrate_narrative,
            body.llm_config_name, body.style_name, body.max_iterations,
            body.unlock,
        ):
            yield chunk

    return _sse_response(_gen())


@router.get("/styles/{name}")
def get_style(name: str):
    app = get_web_app()
    instruction, analysis, msg = app.load_style(name)
    if msg.startswith("❌"):
        raise HTTPException(status_code=404, detail=msg)
    narrative = app.get_narrative_instructions(name)
    # 读取额外字段供前端展示/编辑
    import os, json
    style_file = os.path.join(app.get_styles_dir(), f"{name}.json")
    source_sample = ""
    calibration_reference = ""
    has_calibration_snapshot = False
    snapshot_timestamp = ""
    if os.path.exists(style_file):
        with open(style_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        source_sample = data.get("source_sample", "")
        calibration_reference = data.get("calibration_reference", "")
        snapshot = data.get("pre_calibration_snapshot")
        if snapshot:
            has_calibration_snapshot = True
            snapshot_timestamp = snapshot.get("timestamp", "")
    return {
        "style_name": name,
        "style_instruction": instruction,
        "analysis_result": analysis,
        "source_sample": source_sample,
        "calibration_reference": calibration_reference,
        "has_calibration_snapshot": has_calibration_snapshot,
        "snapshot_timestamp": snapshot_timestamp,
        "narrative_for_architecture": narrative.get("for_architecture", ""),
        "narrative_for_blueprint": narrative.get("for_blueprint", ""),
        "narrative_for_chapter": narrative.get("for_chapter", ""),
        "message": msg,
    }


@router.put("/styles/{name}")
def save_style(name: str, body: StyleSaveRequest):
    app = get_web_app()
    msg = app.save_style(
        name, body.analysis_result, body.style_instruction,
        source_sample=body.source_sample,
        calibration_reference=body.calibration_reference,
        narrative_for_architecture=body.narrative_for_architecture,
        narrative_for_blueprint=body.narrative_for_blueprint,
        narrative_for_chapter=body.narrative_for_chapter,
    )
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.post("/styles/{name}/rollback-calibration")
def rollback_calibration(name: str):
    app = get_web_app()
    msg = app.rollback_calibration(name)
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.delete("/styles/{name}")
def delete_style(name: str):
    app = get_web_app()
    _, msg = app.delete_style(name)
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


# ── 作者参考库（绑定到文风）──────────────────────────────────────────────────

@router.post("/styles/{name}/author-reference/import")
async def import_author_reference(
    name: str,
    emb_config_name: str = Form(...),
    file: UploadFile = File(...),
):
    app = get_web_app()

    if not emb_config_name or emb_config_name not in app.config.get("embedding_configs", {}):
        raise HTTPException(status_code=400, detail="❌ 请先选择有效的 Embedding 配置")

    # 验证文风存在
    style_file = os.path.join(app.get_styles_dir(), f"{name}.json")
    if not os.path.exists(style_file):
        raise HTTPException(status_code=404, detail=f"❌ 文风「{name}」不存在")

    emb_conf = app.config["embedding_configs"][emb_config_name]

    import tempfile, logging
    await file.seek(0)
    file_bytes = await file.read()
    logging.info(f"作者参考库上传文件大小: {len(file_bytes)} bytes, filename={file.filename}")
    if not file_bytes:
        raise HTTPException(status_code=400, detail="❌ 上传的文件内容为空")

    suffix = os.path.splitext(file.filename)[1] if file.filename else ".txt"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="wb") as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        from novel_generator.knowledge import import_author_reference_file
        import_author_reference_file(
            embedding_api_key=emb_conf["api_key"],
            embedding_url=emb_conf["base_url"],
            embedding_interface_format=emb_conf.get("interface_format", emb_config_name),
            embedding_model_name=emb_conf["model_name"],
            file_path=tmp_path,
            style_name=name,
            styles_dir=app.get_styles_dir(),
        )
        return {"message": f"✅ 作者参考库已导入到文风「{name}」!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ 导入失败: {str(e)}")
    finally:
        os.unlink(tmp_path)


@router.delete("/styles/{name}/author-reference")
def clear_author_reference(name: str):
    app = get_web_app()
    from novel_generator.vectorstore_utils import clear_author_vector_store
    try:
        clear_author_vector_store(style_name=name, styles_dir=app.get_styles_dir())
        return {"message": f"✅ 文风「{name}」的作者参考库已清空"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ 清空失败: {str(e)}")


@router.get("/styles/{name}/author-reference/status")
def author_reference_status(name: str):
    """检查文风是否有作者参考库"""
    app = get_web_app()
    from novel_generator.vectorstore_utils import get_author_vectorstore_dir
    store_dir = get_author_vectorstore_dir(style_name=name, styles_dir=app.get_styles_dir())
    exists = os.path.exists(store_dir) and os.listdir(store_dir)
    return {"has_author_reference": bool(exists)}
