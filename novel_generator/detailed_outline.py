# novel_generator/detailed_outline.py
# -*- coding: utf-8 -*-
"""
章节细纲生成（分批生成，每批由用户手动触发）
"""
import os
import re
import logging

from novel_generator.common import invoke_with_cleaning
from llm_adapters import create_llm_adapter
import prompt_definitions
from utils import read_file, clear_file_content, save_string_to_txt
from novel_generator.architecture import build_full_architecture


def get_chapter_outline(outline_text: str, chapter_number: int) -> str:
    """从细纲全文中提取指定章节的细纲内容。找不到返回空字符串。"""
    if not outline_text or not outline_text.strip():
        return ""
    # 匹配 【第N章细纲】 格式
    pattern = r'【第\s*(\d+)\s*章细纲】'
    parts = re.split(pattern, outline_text)
    # parts: [前导文本, 章节号1, 内容1, 章节号2, 内容2, ...]
    for i in range(1, len(parts) - 1, 2):
        if int(parts[i]) == chapter_number:
            return f"【第{parts[i]}章细纲】{parts[i+1].strip()}"
    return ""


def get_max_outline_chapter(outline_text: str) -> int:
    """获取细纲中已有的最大章节号"""
    if not outline_text or not outline_text.strip():
        return 0
    pattern = r'【第\s*(\d+)\s*章细纲】'
    chapter_numbers = [int(x) for x in re.findall(pattern, outline_text)]
    return max(chapter_numbers) if chapter_numbers else 0


def extract_blueprint_range(blueprint_text: str, start: int, end: int) -> str:
    """从蓝图中提取指定章节范围的内容"""
    if not blueprint_text:
        return ""
    # 按"第N章"分割
    pattern = r'(第\s*\d+\s*章.*?)(?=第\s*\d+\s*章|$)'
    chapters = re.findall(pattern, blueprint_text, flags=re.DOTALL)
    result = []
    for ch in chapters:
        match = re.match(r'第\s*(\d+)\s*章', ch)
        if match:
            num = int(match.group(1))
            if start <= num <= end:
                result.append(ch.strip())
    return "\n\n".join(result) if result else ""


def generate_detailed_outline_batch(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    filepath: str,
    start_chapter: int,
    end_chapter: int,
    number_of_chapters: int,
    user_guidance: str = "",
    temperature: float = 0.7,
    max_tokens: int = 4096,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    outline_mode: str = "concise",
    narrative_instruction: str = "",
    progress=None,
) -> str:
    """
    生成一批章节的详细细纲（start_chapter ~ end_chapter）。
    结果追加到 Novel_detailed_outline.txt，返回本批生成的内容。
    """
    architecture_text = build_full_architecture(filepath).strip()
    if not architecture_text:
        logging.warning("架构文件不存在或为空，请先生成架构。")
        return "❌ 请先生成小说架构"

    blueprint_file = os.path.join(filepath, "Novel_directory.txt")
    blueprint_text = read_file(blueprint_file).strip()
    if not blueprint_text:
        logging.warning("蓝图文件不存在或为空，请先生成蓝图。")
        return "❌ 请先生成章节蓝图"

    outline_file = os.path.join(filepath, "Novel_detailed_outline.txt")
    existing_outlines = read_file(outline_file).strip() if os.path.exists(outline_file) else ""

    # 提取当前批次对应的蓝图内容
    chapter_range_blueprints = extract_blueprint_range(blueprint_text, start_chapter, end_chapter)
    if not chapter_range_blueprints:
        return f"❌ 蓝图中未找到第{start_chapter}-{end_chapter}章的内容"

    # 额外提取下一章蓝图，供结尾钩子衔接参考
    next_chapter_blueprint = extract_blueprint_range(blueprint_text, end_chapter + 1, end_chapter + 1)
    if next_chapter_blueprint:
        chapter_range_blueprints += f"\n\n===== 下一章蓝图预览（第{end_chapter + 1}章，仅供本批最后一章的结尾钩子衔接参考，不要为此章生成细纲） =====\n{next_chapter_blueprint}"

    # 已有细纲只取最后3章作为衔接上下文
    context_outlines = ""
    if existing_outlines:
        pattern = r'(【第\s*\d+\s*章细纲】.*?)(?=【第\s*\d+\s*章细纲】|$)'
        all_outlines = re.findall(pattern, existing_outlines, flags=re.DOTALL)
        if all_outlines:
            context_outlines = "\n\n".join(all_outlines[-3:]).strip()

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget,
    )

    # 根据模式选择 prompt：concise（精简）或 detailed（详细，适合官能占比高的剧情）
    prompt_key = "detailed_outline_prompt_detailed" if outline_mode == "detailed" else "detailed_outline_prompt"
    prompt = prompt_definitions.get_all_prompts().get(
        prompt_key,
        prompt_definitions._DEFAULT_PROMPTS.get(prompt_key, prompt_definitions._DEFAULT_PROMPTS["detailed_outline_prompt"])
    ).format(
        novel_architecture=architecture_text,
        chapter_range_blueprints=chapter_range_blueprints,
        existing_outlines=context_outlines if context_outlines else "（无，这是第一批细纲）",
        user_guidance=user_guidance if user_guidance else "无特殊指导",
        n=start_chapter,
        m=end_chapter,
    )

    if narrative_instruction:
        prompt = f"\n【叙事风格指导】\n{narrative_instruction}\n\n" + prompt

    if progress:
        progress(0.2, desc=f"正在生成第{start_chapter}-{end_chapter}章细纲...")

    result = invoke_with_cleaning(llm_adapter, prompt, progress=progress)

    if not result or not result.strip():
        return "❌ 细纲生成结果为空"

    # 不再自动追加保存，由前端手动触发保存
    logging.info(f"Detailed outline for chapters [{start_chapter}..{end_chapter}] generated (not yet saved).")
    if progress:
        progress(1.0, desc=f"第{start_chapter}-{end_chapter}章细纲生成完成（请手动保存）")

    return result.strip()
