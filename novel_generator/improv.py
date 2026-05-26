# novel_generator/improv.py
# -*- coding: utf-8 -*-
"""
即兴写作模式（improv）专用生成器。

不依赖 Novel_directory.txt（全书蓝图）和 plot_architecture，
而是按章生成单章蓝图、单章细纲，并维护 open_threads.txt（伏笔池）。

文件布局：
  filepath/
    chapter_blueprints/chapter_{N}_blueprint.txt   单章蓝图
    chapter_outlines/chapter_{N}_outline.txt        单章细纲（可选）
    open_threads.txt                                伏笔池（全局累积）
"""
import os
import logging

from llm_adapters import create_llm_adapter
import prompt_definitions
from novel_generator.common import invoke_with_cleaning
from novel_generator.architecture import (
    read_core_seed, read_character_dynamics, read_world_building,
    read_character_state,
)
from utils import read_file, clear_file_content, save_string_to_txt


# ============================================================
# 文件路径辅助
# ============================================================

def _blueprint_dir(filepath: str) -> str:
    return os.path.join(filepath, "chapter_blueprints")


def _outline_dir(filepath: str) -> str:
    return os.path.join(filepath, "chapter_outlines")


def get_single_blueprint_path(filepath: str, chapter_number: int) -> str:
    return os.path.join(_blueprint_dir(filepath), f"chapter_{chapter_number}_blueprint.txt")


def get_single_outline_path(filepath: str, chapter_number: int) -> str:
    return os.path.join(_outline_dir(filepath), f"chapter_{chapter_number}_outline.txt")


def get_open_threads_path(filepath: str) -> str:
    return os.path.join(filepath, "open_threads.txt")


def read_single_blueprint(filepath: str, chapter_number: int) -> str:
    p = get_single_blueprint_path(filepath, chapter_number)
    return read_file(p) if os.path.exists(p) else ""


def read_single_outline(filepath: str, chapter_number: int) -> str:
    p = get_single_outline_path(filepath, chapter_number)
    return read_file(p) if os.path.exists(p) else ""


def read_open_threads(filepath: str) -> str:
    p = get_open_threads_path(filepath)
    return read_file(p) if os.path.exists(p) else ""


def save_single_blueprint(filepath: str, chapter_number: int, content: str) -> None:
    os.makedirs(_blueprint_dir(filepath), exist_ok=True)
    save_string_to_txt(content, get_single_blueprint_path(filepath, chapter_number))


def save_single_outline(filepath: str, chapter_number: int, content: str) -> None:
    os.makedirs(_outline_dir(filepath), exist_ok=True)
    save_string_to_txt(content, get_single_outline_path(filepath, chapter_number))


def save_open_threads(filepath: str, content: str) -> None:
    os.makedirs(filepath, exist_ok=True)
    save_string_to_txt(content, get_open_threads_path(filepath))


# ============================================================
# 单章蓝图生成
# ============================================================

def generate_chapter_blueprint_single(
    interface_format: str,
    api_key: str,
    base_url: str,
    model_name: str,
    filepath: str,
    chapter_number: int,
    chapter_intent: str,
    word_number: int = 7000,
    temperature: float = 0.7,
    max_tokens: int = 8192,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    progress=None,
) -> str:
    """
    基于作者口述的本章意图，生成单章蓝图。
    返回蓝图文本（不直接保存，由调用方决定是否保存）。
    """
    core_seed = read_core_seed(filepath)
    character_dynamics = read_character_dynamics(filepath)
    world_building = read_world_building(filepath)
    character_state = read_character_state(filepath)

    global_summary_file = os.path.join(filepath, "global_summary.txt")
    global_summary = read_file(global_summary_file) if os.path.exists(global_summary_file) else ""
    open_threads = read_open_threads(filepath)

    if not core_seed.strip():
        return "❌ 请先生成核心种子"
    if not character_dynamics.strip():
        return "❌ 请先生成角色动力学"

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget,
    )

    prompt = prompt_definitions.chapter_blueprint_single_prompt.format(
        core_seed=core_seed,
        world_building=world_building if world_building.strip() else "（未填写）",
        character_dynamics=character_dynamics,
        global_summary=global_summary if global_summary.strip() else "（首章·尚无前文摘要）",
        character_state=character_state if character_state.strip() else "（首章·角色状态尚未建立）",
        open_threads=open_threads if open_threads.strip() else "（首章·伏笔池为空）",
        chapter_number=chapter_number,
        chapter_intent=chapter_intent.strip() if chapter_intent.strip() else "（作者未提供意图，请基于已有素材自由发挥一章）",
        word_number=word_number,
    )

    if progress:
        progress(0.2, desc=f"正在生成第 {chapter_number} 章蓝图…")

    result = invoke_with_cleaning(llm_adapter, prompt, progress=progress)
    if not result or not result.strip():
        return "❌ 单章蓝图生成结果为空"

    if progress:
        progress(1.0, desc=f"第 {chapter_number} 章蓝图生成完成（请手动保存）")

    logging.info(f"[Improv] Single blueprint for chapter {chapter_number} generated.")
    return result.strip()


# ============================================================
# 单章细纲生成
# ============================================================

def generate_chapter_outline_single(
    interface_format: str,
    api_key: str,
    base_url: str,
    model_name: str,
    filepath: str,
    chapter_number: int,
    word_number: int = 7000,
    temperature: float = 0.7,
    max_tokens: int = 8192,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    progress=None,
) -> str:
    """
    基于已确认的单章蓝图，生成单章细纲（分场+对话钩子）。
    """
    blueprint = read_single_blueprint(filepath, chapter_number)
    if not blueprint.strip():
        return f"❌ 第 {chapter_number} 章蓝图尚未生成或保存"

    core_seed = read_core_seed(filepath)
    character_dynamics = read_character_dynamics(filepath)
    character_state = read_character_state(filepath)
    global_summary_file = os.path.join(filepath, "global_summary.txt")
    global_summary = read_file(global_summary_file) if os.path.exists(global_summary_file) else ""
    open_threads = read_open_threads(filepath)

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget,
    )

    prompt = prompt_definitions.chapter_outline_single_prompt.format(
        core_seed=core_seed if core_seed.strip() else "（无）",
        character_dynamics=character_dynamics if character_dynamics.strip() else "（无）",
        global_summary=global_summary if global_summary.strip() else "（首章·尚无前文摘要）",
        character_state=character_state if character_state.strip() else "（首章·角色状态尚未建立）",
        open_threads=open_threads if open_threads.strip() else "（首章·伏笔池为空）",
        chapter_blueprint=blueprint,
    )

    if progress:
        progress(0.2, desc=f"正在生成第 {chapter_number} 章细纲…")

    result = invoke_with_cleaning(llm_adapter, prompt, progress=progress)
    if not result or not result.strip():
        return "❌ 单章细纲生成结果为空"

    if progress:
        progress(1.0, desc=f"第 {chapter_number} 章细纲生成完成（请手动保存）")

    logging.info(f"[Improv] Single outline for chapter {chapter_number} generated.")
    return result.strip()


# ============================================================
# 单章蓝图修订
# ============================================================

def revise_chapter_blueprint_single(
    interface_format: str,
    api_key: str,
    base_url: str,
    model_name: str,
    filepath: str,
    chapter_number: int,
    current_blueprint: str,
    revision_guidance: str,
    temperature: float = 0.7,
    max_tokens: int = 8192,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    progress=None,
) -> str:
    """基于已有单章蓝图 + 用户修订建议，重写单章蓝图。"""
    if not current_blueprint.strip():
        return "❌ 当前蓝图为空，无法修订"
    if not revision_guidance.strip():
        return "❌ 请填写修订建议"

    core_seed = read_core_seed(filepath)
    character_dynamics = read_character_dynamics(filepath)
    world_building = read_world_building(filepath)
    character_state = read_character_state(filepath)
    global_summary_file = os.path.join(filepath, "global_summary.txt")
    global_summary = read_file(global_summary_file) if os.path.exists(global_summary_file) else ""
    open_threads = read_open_threads(filepath)

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget,
    )

    prompt = prompt_definitions.chapter_blueprint_single_revise_prompt.format(
        core_seed=core_seed if core_seed.strip() else "（无）",
        world_building=world_building if world_building.strip() else "（无）",
        character_dynamics=character_dynamics if character_dynamics.strip() else "（无）",
        global_summary=global_summary if global_summary.strip() else "（首章·无前文摘要）",
        character_state=character_state if character_state.strip() else "（首章·状态尚未建立）",
        open_threads=open_threads if open_threads.strip() else "（伏笔池为空）",
        chapter_number=chapter_number,
        current_blueprint=current_blueprint,
        revision_guidance=revision_guidance.strip(),
    )

    if progress:
        progress(0.2, desc=f"正在修订第 {chapter_number} 章蓝图…")

    result = invoke_with_cleaning(llm_adapter, prompt, progress=progress)
    if not result or not result.strip():
        return "❌ 修订结果为空"

    if progress:
        progress(1.0, desc=f"第 {chapter_number} 章蓝图修订完成（请审阅后保存）")

    logging.info(f"[Improv] Single blueprint for chapter {chapter_number} revised.")
    return result.strip()


# ============================================================
# 单章细纲修订
# ============================================================

def revise_chapter_outline_single(
    interface_format: str,
    api_key: str,
    base_url: str,
    model_name: str,
    filepath: str,
    chapter_number: int,
    current_outline: str,
    revision_guidance: str,
    temperature: float = 0.7,
    max_tokens: int = 8192,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    progress=None,
) -> str:
    """基于已有单章细纲 + 用户修订建议，重写单章细纲。"""
    if not current_outline.strip():
        return "❌ 当前细纲为空，无法修订"
    if not revision_guidance.strip():
        return "❌ 请填写修订建议"

    blueprint = read_single_blueprint(filepath, chapter_number)
    if not blueprint.strip():
        return f"❌ 第 {chapter_number} 章蓝图未保存——细纲必须基于已保存的蓝图"

    core_seed = read_core_seed(filepath)
    character_dynamics = read_character_dynamics(filepath)
    character_state = read_character_state(filepath)
    global_summary_file = os.path.join(filepath, "global_summary.txt")
    global_summary = read_file(global_summary_file) if os.path.exists(global_summary_file) else ""
    open_threads = read_open_threads(filepath)

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget,
    )

    prompt = prompt_definitions.chapter_outline_single_revise_prompt.format(
        core_seed=core_seed if core_seed.strip() else "（无）",
        character_dynamics=character_dynamics if character_dynamics.strip() else "（无）",
        character_state=character_state if character_state.strip() else "（无）",
        global_summary=global_summary if global_summary.strip() else "（无）",
        open_threads=open_threads if open_threads.strip() else "（无）",
        chapter_blueprint=blueprint,
        current_outline=current_outline,
        revision_guidance=revision_guidance.strip(),
    )

    if progress:
        progress(0.2, desc=f"正在修订第 {chapter_number} 章细纲…")

    result = invoke_with_cleaning(llm_adapter, prompt, progress=progress)
    if not result or not result.strip():
        return "❌ 修订结果为空"

    if progress:
        progress(1.0, desc=f"第 {chapter_number} 章细纲修订完成（请审阅后保存）")

    logging.info(f"[Improv] Single outline for chapter {chapter_number} revised.")
    return result.strip()


# ============================================================
# 即兴模式章节正文生成
# ============================================================

def generate_chapter_improv(
    interface_format: str,
    api_key: str,
    base_url: str,
    model_name: str,
    filepath: str,
    chapter_number: int,
    user_guidance: str = "",
    word_number: int = 7000,
    temperature: float = 0.7,
    max_tokens: int = 16384,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    style_instruction: str = "",
    narrative_instruction: str = "",
    progress=None,
) -> str:
    """
    即兴模式·章节正文生成。
    依赖：单章蓝图（必须）+ 单章细纲（可选）+ 累积摘要 + 角色状态 + 伏笔池。
    """
    blueprint = read_single_blueprint(filepath, chapter_number)
    if not blueprint.strip():
        return f"❌ 第 {chapter_number} 章蓝图尚未生成。请先生成单章蓝图。"

    core_seed = read_core_seed(filepath)
    character_dynamics = read_character_dynamics(filepath)
    world_building = read_world_building(filepath)
    character_state = read_character_state(filepath)

    global_summary_file = os.path.join(filepath, "global_summary.txt")
    global_summary = read_file(global_summary_file) if os.path.exists(global_summary_file) else ""
    open_threads = read_open_threads(filepath)
    outline = read_single_outline(filepath, chapter_number)

    # 前章结尾段（约 800 字）
    previous_excerpt = ""
    if chapter_number > 1:
        prev_path = os.path.join(filepath, "chapters", f"chapter_{chapter_number - 1}.txt")
        if os.path.exists(prev_path):
            prev_text = read_file(prev_path).strip()
            previous_excerpt = prev_text[-800:] if len(prev_text) > 800 else prev_text

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget,
    )

    prompt = prompt_definitions.next_chapter_draft_improv_prompt.format(
        core_seed=core_seed,
        world_building=world_building if world_building.strip() else "（无）",
        character_dynamics=character_dynamics,
        global_summary=global_summary if global_summary.strip() else "（首章·无前文摘要）",
        character_state=character_state if character_state.strip() else "（首章·角色状态尚未建立）",
        open_threads=open_threads if open_threads.strip() else "（首章·伏笔池为空）",
        previous_chapter_excerpt=previous_excerpt if previous_excerpt else "（无·这是第一章或前章未保存）",
        chapter_blueprint=blueprint,
        chapter_outline=outline if outline.strip() else "（未生成细纲，请直接按蓝图执行）",
        user_guidance=user_guidance if user_guidance.strip() else "（无额外指导）",
        chapter_number=chapter_number,
    )

    # 拼接文风/叙事指导（与现有章节生成保持一致）
    prefix_blocks = []
    if style_instruction:
        prefix_blocks.append(f"【文风指导】\n{style_instruction}")
    if narrative_instruction:
        prefix_blocks.append(f"【叙事DNA指导】\n{narrative_instruction}")
    if prefix_blocks:
        prompt = "\n\n".join(prefix_blocks) + "\n\n" + prompt

    if progress:
        progress(0.1, desc=f"正在生成第 {chapter_number} 章正文…")

    result = invoke_with_cleaning(llm_adapter, prompt, progress=progress)
    if not result or not result.strip():
        return "❌ 章节正文生成结果为空"

    # 保存为 draft（与现有 chapter.py 行为一致）
    chapters_dir = os.path.join(filepath, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)
    draft_path = os.path.join(chapters_dir, f"chapter_{chapter_number}_draft.txt")
    save_string_to_txt(result.strip(), draft_path)

    if progress:
        progress(1.0, desc=f"第 {chapter_number} 章正文已生成（保存为草稿）")

    logging.info(f"[Improv] Chapter {chapter_number} draft generated.")
    return result.strip()


# ============================================================
# 伏笔池更新（finalize 时调用）
# ============================================================

def update_open_threads(
    interface_format: str,
    api_key: str,
    base_url: str,
    model_name: str,
    filepath: str,
    chapter_number: int,
    chapter_text: str,
    temperature: float = 0.5,
    max_tokens: int = 4096,
    timeout: int = 600,
    progress=None,
) -> str:
    """
    finalize 流程中调用：基于本章正文 + 本章蓝图，更新 open_threads.txt。
    返回更新后的全文。
    """
    old_open_threads = read_open_threads(filepath)
    blueprint = read_single_blueprint(filepath, chapter_number)

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )

    prompt = prompt_definitions.open_threads_update_prompt.format(
        old_open_threads=old_open_threads if old_open_threads.strip() else "（首章·伏笔池为空，请初始化）",
        chapter_text=chapter_text,
        chapter_blueprint=blueprint if blueprint.strip() else "（无对应单章蓝图）",
    )

    result = invoke_with_cleaning(llm_adapter, prompt, progress=progress)
    if not result or not result.strip():
        logging.warning("[Improv] open_threads update returned empty; keeping old version.")
        return old_open_threads

    save_open_threads(filepath, result.strip())
    logging.info(f"[Improv] open_threads.txt updated after chapter {chapter_number}.")
    return result.strip()
