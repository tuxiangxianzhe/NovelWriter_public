# api/routers/generate.py
# -*- coding: utf-8 -*-
"""生成路由（全部使用 SSE 流式输出）"""

import os
import glob
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, PlainTextResponse

from api.schemas import (
    GenerateArchRequest, GenerateArchStepRequest, AssembleArchRequest,
    ContinueArchRequest, ContinueArchStepRequest, AssembleContinuationRequest,
    CompressContextRequest,
    GenerateBlueprintRequest, GenerateChapterRequest,
    FinalizeChapterRequest, ExpandScenesRequest, SaveChapterRequest,
    SaveContentRequest, GenerateCharStateRequest, BatchGenerateRequest,
    SupplementCharactersRequest, HumanizerRequest, BatchHumanizerRequest,
    ReviseStepRequest, GenerateDetailedOutlineRequest,
)
from pydantic import BaseModel as _BaseModel
from api.app_state import get_web_app
from api.sse_utils import run_with_sse, cancel_operation
from utils import read_file, save_string_to_txt
from novel_generator.architecture import (
    read_core_seed, read_character_dynamics, read_world_building,
    read_plot_architecture, read_character_state,
    save_core_seed, save_character_dynamics, save_world_building,
    save_plot_architecture, regenerate_assembled_view,
)

router = APIRouter(tags=["generate"])


class _CancelRequest(_BaseModel):
    operation_id: str


@router.post("/generate/cancel")
def cancel_generation(body: _CancelRequest):
    found = cancel_operation(body.operation_id)
    return {"cancelled": found}


def _sse_response(gen):
    return StreamingResponse(
        gen,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── 完整架构生成 ──────────────────────────────────────────────────────────────

@router.post("/generate/architecture")
def generate_architecture(body: GenerateArchRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.generate_architecture,
            body.llm_config_name, body.topic, body.genre,
            body.num_chapters, body.word_number, body.filepath,
            body.user_guidance, body.arch_style_name, body.xp_type,
            body.num_characters,
        ):
            yield chunk

    return _sse_response(_gen())


# ── 分步架构生成 ──────────────────────────────────────────────────────────────

@router.post("/generate/architecture/step/core_seed")
def generate_step_core_seed(body: GenerateArchStepRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.generate_step_core_seed,
            body.llm_config_name, body.topic, body.genre,
            body.num_chapters, body.word_number,
            body.step_guidance, body.global_guidance, body.xp_type,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/generate/architecture/step/characters")
def generate_step_characters(body: GenerateArchStepRequest):
    """仅生成角色动力学"""
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.generate_step_char_dynamics,
            body.llm_config_name, body.seed_text,
            body.step_guidance, body.global_guidance, body.xp_type,
            body.num_characters,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/generate/architecture/supplement_characters")
def supplement_characters_endpoint(body: SupplementCharactersRequest):
    """基于已有角色补充生成新角色"""
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.supplement_characters_gen,
            body.llm_config_name, body.existing_characters,
            body.supplement_guidance, body.num_characters,
            body.core_seed, body.world_building, body.filepath,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/generate/architecture/step/char_state")
def generate_step_char_state(body: GenerateCharStateRequest):
    """根据角色动力学生成角色状态"""
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.generate_step_char_state,
            body.llm_config_name, body.char_dynamics_text,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/generate/architecture/step/world")
def generate_step_world(body: GenerateArchStepRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.generate_step_world,
            body.llm_config_name, body.seed_text,
            body.step_guidance, body.global_guidance, body.xp_type,
            body.char_text,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/generate/architecture/step/plot")
def generate_step_plot(body: GenerateArchStepRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.generate_step_plot,
            body.llm_config_name, body.seed_text, body.char_text, body.world_text,
            body.step_guidance, body.global_guidance, body.num_chapters,
            body.arch_style_name, body.xp_type,
        ):
            yield chunk

    return _sse_response(_gen())


# ── 修订步骤内容 ──────────────────────────────────────────────────────────────

@router.post("/generate/architecture/step/revise")
def revise_step_content(body: ReviseStepRequest):
    """基于已有内容 + 修改建议，让 LLM 修订内容"""
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.revise_step_content,
            body.llm_config_name, body.original_content,
            body.revision_guidance, body.step_type,
            body.filepath,
            body.include_core_seed, body.include_characters,
            body.include_world_building, body.include_plot,
        ):
            yield chunk

    return _sse_response(_gen())


# ── 组装架构 ──────────────────────────────────────────────────────────────────

@router.post("/generate/architecture/assemble")
def assemble_architecture(body: AssembleArchRequest):
    app = get_web_app()
    status, content = app.assemble_and_save_architecture(
        body.filepath, body.topic, body.genre, body.num_chapters,
        body.word_number, body.seed_text, body.char_text,
        body.char_state_text, body.world_text, body.plot_text
    )
    if status.startswith("❌"):
        raise HTTPException(status_code=400, detail=status)
    return {"message": status, "content": content}


# ── 加载分步缓存 ──────────────────────────────────────────────────────────────

@router.get("/generate/architecture/partial")
def load_partial_steps(filepath: str):
    app = get_web_app()
    status, seed, char, world, plot = app.load_partial_steps(filepath)
    return {
        "message": status,
        "seed_text": seed,
        "char_text": char,
        "world_text": world,
        "plot_text": plot,
    }


# ── 续写章节弧 ────────────────────────────────────────────────────────────────

@router.post("/generate/architecture/continue")
def continue_architecture(body: ContinueArchRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.continue_architecture,
            body.llm_config_name, body.filepath,
            body.new_chapters, body.user_guidance,
            body.arch_style_name, body.xp_type,
            body.num_characters,
        ):
            yield chunk

    return _sse_response(_gen())


# ── 续写分步 ──────────────────────────────────────────────────────────────────

@router.post("/generate/architecture/continue/step/seed")
def continue_step_seed(body: ContinueArchStepRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.continue_step_seed,
            body.llm_config_name, body.filepath,
            body.new_chapters, body.user_guidance,
            body.arch_style_name, body.xp_type,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/generate/architecture/continue/step/world")
def continue_step_world(body: ContinueArchStepRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.continue_step_world,
            body.llm_config_name, body.filepath,
            body.continuation_seed, body.new_chapters,
            body.user_guidance, body.arch_style_name, body.xp_type,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/generate/architecture/continue/step/characters")
def continue_step_characters(body: ContinueArchStepRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.continue_step_characters,
            body.llm_config_name, body.filepath,
            body.new_chapters, body.user_guidance, body.step_guidance,
            body.arch_style_name, body.xp_type,
            body.continuation_seed, body.world_expansion,
            body.num_characters,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/generate/architecture/continue/step/arcs")
def continue_step_arcs(body: ContinueArchStepRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.continue_step_arcs,
            body.llm_config_name, body.filepath,
            body.new_characters_text, body.new_chapters,
            body.user_guidance, body.step_guidance,
            body.arch_style_name, body.xp_type,
            body.continuation_seed, body.world_expansion,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/generate/architecture/continue/step/char_state")
def continue_step_char_state(body: ContinueArchStepRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.continue_step_char_state,
            body.llm_config_name, body.filepath,
            body.new_characters_text,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/generate/architecture/continue/assemble")
def assemble_continuation(body: AssembleContinuationRequest):
    app = get_web_app()
    status, content = app.assemble_and_save_continuation(
        body.filepath, body.new_chapters, body.new_characters_text,
        body.new_arcs_text, body.new_char_state_text,
        body.continuation_seed, body.world_expansion,
    )
    if status.startswith("❌"):
        raise HTTPException(status_code=400, detail=status)
    # 从已更新的项目数据中读取新总章节数
    new_total = None
    active = app.get_active_project_name()
    if active and active in app.projects_data.get("projects", {}):
        new_total = app.projects_data["projects"][active].get("num_chapters")
    resp = {"message": status, "content": content}
    if new_total:
        resp["new_total_chapters"] = new_total
    return resp


# ── 压缩摘要/角色状态 ─────────────────────────────────────────────────────────

@router.post("/generate/compress-context")
def compress_context(body: CompressContextRequest):
    app = get_web_app()
    result = app.compress_context(body.llm_config_name, body.filepath, body.include_world_building)
    if result.startswith("❌"):
        raise HTTPException(status_code=400, detail=result)
    return {"message": result}


# ── 蓝图生成 ──────────────────────────────────────────────────────────────────

@router.post("/generate/blueprint")
def generate_blueprint(body: GenerateBlueprintRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.generate_blueprint,
            body.llm_config_name, body.filepath, body.num_chapters,
            body.user_guidance, body.bp_style_name, body.xp_type,
        ):
            yield chunk

    return _sse_response(_gen())


# ── 详细细纲 ──────────────────────────────────────────────────────────────────

@router.post("/generate/detailed_outline")
def generate_detailed_outline(body: GenerateDetailedOutlineRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.generate_detailed_outline,
            body.llm_config_name, body.filepath,
            body.start_chapter, body.end_chapter, body.num_chapters,
            body.user_guidance, body.xp_type, body.outline_mode,
        ):
            yield chunk

    return _sse_response(_gen())


@router.get("/generate/detailed_outline")
def get_detailed_outline(filepath: str = "./output"):
    outline_file = os.path.join(filepath, "Novel_detailed_outline.txt")
    if os.path.exists(outline_file):
        content = read_file(outline_file)
        return {"content": content}
    return {"content": ""}


@router.put("/generate/detailed_outline")
def save_detailed_outline(body: SaveContentRequest):
    outline_file = os.path.join(body.filepath, "Novel_detailed_outline.txt")
    os.makedirs(os.path.dirname(outline_file) if os.path.dirname(outline_file) else ".", exist_ok=True)
    save_string_to_txt(body.content, outline_file)
    return {"message": "✅ 章节细纲已保存"}


# ── 章节生成 ──────────────────────────────────────────────────────────────────

@router.post("/generate/chapter")
def generate_chapter(body: GenerateChapterRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.generate_chapter,
            body.llm_config_name, body.emb_config_name, body.filepath,
            body.chapter_num, body.word_number, body.user_guidance,
            body.characters_involved, body.key_items,
            body.scene_location, body.time_constraint,
            body.style_name, body.narrative_style_name, body.xp_type,
            body.inject_world_building, body.scene_by_scene,
        ):
            yield chunk

    return _sse_response(_gen())


@router.put("/generate/chapter/{num}")
def save_chapter(num: int, body: SaveChapterRequest, filepath: str = "./output"):
    chapter_file = os.path.join(filepath, "chapters", f"chapter_{num}.txt")
    os.makedirs(os.path.dirname(chapter_file), exist_ok=True)
    save_string_to_txt(body.content, chapter_file)
    return {"message": f"✅ 第 {num} 章已保存"}


@router.put("/generate/architecture")
def save_architecture(body: SaveContentRequest):
    """已废弃：架构文件现在是只读组装副本，请编辑各独立组件。"""
    raise HTTPException(status_code=405, detail="架构文件现在是只读的，请编辑各独立组件（PUT /generate/architecture/component/{name}）。")


@router.put("/generate/architecture/component/{component_name}")
def save_architecture_component(component_name: str, body: SaveContentRequest):
    """保存单个架构组件到独立文件，然后重新组装 Novel_architecture.txt。"""
    filepath = body.filepath
    os.makedirs(filepath, exist_ok=True)

    save_funcs = {
        "core_seed": lambda: save_core_seed(filepath, body.content),
        "character_dynamics": lambda: save_character_dynamics(filepath, body.content),
        "world_building": lambda: save_world_building(filepath, body.content),
        "plot_architecture": lambda: save_plot_architecture(filepath, body.content),
        "character_state": lambda: save_string_to_txt(
            body.content,
            os.path.join(filepath, "character_state.txt"),
        ),
    }

    if component_name not in save_funcs:
        raise HTTPException(
            status_code=400,
            detail=f"未知组件: {component_name}。可用: {', '.join(save_funcs.keys())}",
        )

    save_funcs[component_name]()
    assembled = regenerate_assembled_view(filepath)
    return {"message": f"✅ {component_name} 已保存", "assembled_content": assembled}


@router.put("/generate/blueprint")
def save_blueprint(body: SaveContentRequest):
    bp_file = os.path.join(body.filepath, "Novel_directory.txt")
    os.makedirs(os.path.dirname(bp_file), exist_ok=True)
    save_string_to_txt(body.content, bp_file)
    return {"message": "✅ 蓝图已保存"}


@router.get("/generate/chapter/{num}")
def get_chapter(num: int, filepath: str = "./output"):
    chapter_file = os.path.join(filepath, "chapters", f"chapter_{num}.txt")
    if not os.path.exists(chapter_file):
        raise HTTPException(status_code=404, detail=f"未找到第 {num} 章文件")
    return {"content": read_file(chapter_file), "chapter_num": num}


# ── 章节列表 ──────────────────────────────────────────────────────────────────

@router.get("/generate/chapters")
def list_chapters(filepath: str = "./output"):
    chapters_dir = os.path.join(filepath, "chapters")
    if not os.path.exists(chapters_dir):
        return {"chapters": []}

    all_files = glob.glob(os.path.join(chapters_dir, "chapter_*.txt"))
    chapter_nums = set()
    for f in all_files:
        match = re.search(r'chapter_(\d+)', os.path.basename(f))
        if match:
            chapter_nums.add(int(match.group(1)))

    result = []
    for num in sorted(chapter_nums):
        draft_file = os.path.join(chapters_dir, f"chapter_{num}_draft.txt")
        final_file = os.path.join(chapters_dir, f"chapter_{num}.txt")
        result.append({
            "num": num,
            "has_draft": os.path.exists(draft_file),
            "has_final": os.path.exists(final_file),
        })
    return {"chapters": result}


# ── 精炼章节 ──────────────────────────────────────────────────────────────────

@router.post("/generate/finalize")
def finalize_chapter(body: FinalizeChapterRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.finalize_chapter_web,
            body.llm_config_name, body.emb_config_name, body.filepath,
            body.chapter_num, body.word_number,
        ):
            yield chunk

    return _sse_response(_gen())


# ── 场景扩写 ──────────────────────────────────────────────────────────────────

@router.post("/generate/expand")
def expand_scenes(body: ExpandScenesRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.expand_scenes_web,
            body.llm_config_name, body.filepath, body.chapter_num,
            body.style_name, body.narrative_style_name, body.xp_type,
            body.polish_guidance, body.polish_mode,
            body.include_outline, body.include_character_state,
            body.include_summary, body.include_world_building,
        ):
            yield chunk

    return _sse_response(_gen())


# ── 去 AI 痕迹 ──────────────────────────────────────────────────────────────

@router.post("/generate/humanize")
def humanize_chapter(body: HumanizerRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.humanize_chapter_web,
            body.llm_config_name, body.filepath, body.chapter_num,
            body.enable_r8, body.user_focus, body.depth,
        ):
            yield chunk

    return _sse_response(_gen())


@router.post("/generate/humanize/batch")
def batch_humanize(body: BatchHumanizerRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.batch_humanize_web,
            body.llm_config_name, body.filepath,
            body.start_chapter, body.end_chapter,
            body.enable_r8, body.user_focus, body.depth,
        ):
            yield chunk

    return _sse_response(_gen())


# ── 一键生成全部章节 ──────────────────────────────────────────────────────────

@router.post("/generate/batch")
def batch_generate(body: BatchGenerateRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.batch_generate_all,
            body.llm_config_name, body.emb_config_name, body.filepath,
            body.word_number, body.user_guidance,
            body.style_name, body.narrative_style_name, body.xp_type,
            body.inject_world_building,
        ):
            yield chunk

    return _sse_response(_gen())


# ── 生成状态 ──────────────────────────────────────────────────────────────────

@router.get("/generate/status")
def get_generate_status(filepath: str = "./output"):
    arch_exists = os.path.exists(os.path.join(filepath, "Novel_architecture.txt"))
    bp_exists = os.path.exists(os.path.join(filepath, "Novel_directory.txt"))
    cd_exists = os.path.exists(os.path.join(filepath, "character_dynamics.txt"))

    arch_content = ""
    bp_content = ""
    cd_content = ""
    if arch_exists:
        arch_content = read_file(os.path.join(filepath, "Novel_architecture.txt"))
    if bp_exists:
        bp_content = read_file(os.path.join(filepath, "Novel_directory.txt"))
    if cd_exists:
        cd_content = read_file(os.path.join(filepath, "character_dynamics.txt"))

    # 读取各独立文件内容
    core_seed_content = read_core_seed(filepath)
    world_building_content = read_world_building(filepath)
    plot_architecture_content = read_plot_architecture(filepath)
    character_state_content = read_character_state(filepath)

    return {
        "architecture_exists": arch_exists or bool(core_seed_content),
        "blueprint_exists": bp_exists,
        "architecture_content": arch_content,
        "blueprint_content": bp_content,
        "character_dynamics_exists": cd_exists,
        "character_dynamics_content": cd_content,
        "core_seed_content": core_seed_content,
        "world_building_content": world_building_content,
        "plot_architecture_content": plot_architecture_content,
        "character_state_content": character_state_content,
    }


@router.put("/generate/character_dynamics")
def save_character_dynamics_endpoint(body: SaveContentRequest):
    cd_file = os.path.join(body.filepath, "character_dynamics.txt")
    os.makedirs(os.path.dirname(cd_file), exist_ok=True)
    save_string_to_txt(body.content, cd_file)
    return {"message": "✅ 角色动力学已保存"}


# ── 合并导出小说 ────────────────────────────────────────────────────────────

@router.get("/generate/export")
def export_novel(filepath: str = "./output"):
    """将所有章节合并为一个完整文本，供下载。"""
    from chapter_directory_parser import parse_chapter_blueprint

    chapters_dir = os.path.join(filepath, "chapters")
    if not os.path.exists(chapters_dir):
        raise HTTPException(status_code=404, detail="未找到章节目录")

    # 收集所有章节文件
    all_files = glob.glob(os.path.join(chapters_dir, "chapter_*.txt"))
    chapter_nums = set()
    for f in all_files:
        match = re.search(r'chapter_(\d+)\.txt$', os.path.basename(f))
        if match:
            chapter_nums.add(int(match.group(1)))

    if not chapter_nums:
        raise HTTPException(status_code=404, detail="未找到任何已保存的章节")

    # 尝试从蓝图获取章节标题
    bp_file = os.path.join(filepath, "Novel_directory.txt")
    chapter_titles = {}
    if os.path.exists(bp_file):
        bp_text = read_file(bp_file)
        try:
            parsed = parse_chapter_blueprint(bp_text)
            for ch in parsed:
                chapter_titles[ch["chapter_number"]] = ch.get("chapter_title", "")
        except Exception:
            pass

    # 合并：优先使用章节内容自带的标题，没有时才补上
    parts = []
    for num in sorted(chapter_nums):
        chapter_file = os.path.join(chapters_dir, f"chapter_{num}.txt")
        if not os.path.exists(chapter_file):
            continue
        content = read_file(chapter_file).strip()
        # 检查内容前几行是否已包含章节标题（如"第N章"、"第N章 标题"等）
        first_line = content.split('\n', 1)[0].strip() if content else ""
        has_title = bool(re.match(r'^第\s*\d+\s*章', first_line))
        if has_title:
            parts.append(content)
        else:
            title = chapter_titles.get(num, "")
            header = f"第{num}章" + (f" - {title}" if title else "")
            parts.append(f"{header}\n\n{content}")

    if not parts:
        raise HTTPException(status_code=404, detail="未找到任何已保存的章节")

    merged = "\n\n\n".join(parts)
    return PlainTextResponse(
        content=merged,
        headers={
            "Content-Disposition": "attachment; filename=novel_export.txt",
        },
    )
