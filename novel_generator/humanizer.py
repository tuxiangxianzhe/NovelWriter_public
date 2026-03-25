# novel_generator/humanizer.py
# -*- coding: utf-8 -*-
"""
去 AI 痕迹模块：基于船板叙事空间创作系统 humanizer-xiaoshuo 的规则，
通过 LLM 对小说章节执行 AI 痕迹清除。

支持三种处理深度：
  quick（快速）：单轮处理全部 R1-R7 规则，速度快但漏改多
  standard（标准）：两轮——R1+R2 → R3+R4+R5，兼顾效果和速度
  deep（深度）：三轮——R1+R2 → R3+R4+R5 → R6+R7，效果最好
  R8（可选）：任何深度下都可额外追加一轮无用细节清除
"""
import re
import logging

from llm_adapters import create_llm_adapter
from novel_generator.common import invoke_with_cleaning
import prompt_definitions

logging.basicConfig(
    filename='app.log',
    filemode='a',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 深度级别对应的轮次 prompt 列表
_DEPTH_ROUNDS = {
    "quick": [
        ("R1-R7", "humanizer_prompt"),
    ],
    "standard": [
        ("R1+R2 句式与排版", "humanizer_round1_prompt"),
        ("R3+R4+R5 AI词汇", "humanizer_round2_prompt"),
    ],
    "deep": [
        ("R1+R2 句式与排版", "humanizer_round1_prompt"),
        ("R3+R4+R5 AI词汇", "humanizer_round2_prompt"),
        ("R6+R7 节奏结构", "humanizer_round3_prompt"),
    ],
}


def humanize_chapter(
    chapter_text: str,
    enable_r8: bool = False,
    depth: str = "standard",
    outline_context: str = "",
    character_context: str = "",
    user_focus: str = "",
    prev_tail: str = "",
    next_head: str = "",
    api_key: str = "",
    base_url: str = "",
    model_name: str = "",
    temperature: float = 0.7,
    interface_format: str = "OpenAI",
    max_tokens: int = 8192,
    timeout: int = 600,
    progress=None,
) -> str:
    """
    对单章文本执行去 AI 痕迹处理。

    depth: "quick" / "standard" / "deep"
    返回包含修改后文本和修改清单的完整结果。
    """
    if not chapter_text or not chapter_text.strip():
        return ""

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )

    context_section = _build_context_section(prev_tail, next_head)
    rounds = list(_DEPTH_ROUNDS.get(depth, _DEPTH_ROUNDS["standard"]))

    # R8 作为额外轮次追加
    if enable_r8:
        rounds.append(("R8 无用细节清除", "humanizer_round4_prompt"))

    total_rounds = len(rounds)
    all_changes = []
    current_text = chapter_text

    for i, (round_name, prompt_attr) in enumerate(rounds):
        round_num = i + 1
        logging.info(f"[Humanizer] 开始第 {round_num}/{total_rounds} 轮: {round_name}")
        if progress:
            progress(round_num / (total_rounds + 1),
                     desc=f"去 AI 第 {round_num}/{total_rounds} 轮: {round_name}...")

        # 获取本轮 prompt 模板
        prompt_template = getattr(prompt_definitions, prompt_attr, None)
        if not prompt_template:
            logging.warning(f"[Humanizer] 未找到 prompt: {prompt_attr}，跳过")
            continue

        # 构建 format 参数
        format_kwargs = {
            "chapter_text": current_text,
            "context_section": context_section,
        }
        # R8 轮需要 r8_section
        if prompt_attr == "humanizer_round4_prompt":
            format_kwargs["r8_section"] = _build_r8_section(
                True, outline_context, character_context, user_focus)
        # 旧的单轮 prompt 需要 r8_section
        if prompt_attr == "humanizer_prompt":
            format_kwargs["r8_section"] = _build_r8_section(
                enable_r8, outline_context, character_context, user_focus)

        prompt = prompt_template.format(**format_kwargs)

        # 调用 LLM
        result = invoke_with_cleaning(llm_adapter, prompt, progress=progress)
        if not result or not result.strip():
            logging.warning(f"[Humanizer] 第 {round_num} 轮返回空结果，保留上一轮文本")
            continue

        # 分离文本和修改清单
        round_text, round_changes = _split_result(result)

        if round_text:
            current_text = round_text
        if round_changes:
            all_changes.append(f"### 第 {round_num} 轮: {round_name}\n\n{round_changes}")

        logging.info(f"[Humanizer] 第 {round_num} 轮完成, "
                     f"文本={len(current_text)}字, 改动={len(round_changes)}字")

    # 合并所有轮次的修改清单
    combined_changes = "\n\n".join(all_changes) if all_changes else "（无改动）"

    return f"{current_text}\n\n---\n\n## 修改清单\n\n{combined_changes}"


def _split_result(result: str) -> tuple:
    """从 LLM 结果中分离修改后文本和修改清单"""
    # 用正则匹配分隔线
    split_match = re.split(r'\n-{3,}\n', result, maxsplit=1)
    if len(split_match) == 2:
        return split_match[0].strip(), split_match[1].strip()
    # 回退：用"## 修改清单"
    if '## 修改清单' in result:
        idx = result.index('## 修改清单')
        return result[:idx].strip(), result[idx:].strip()
    # 都没找到：整个结果当文本，无修改清单
    return result.strip(), ""


def _build_r8_section(enable_r8: bool, outline_context: str,
                      character_context: str, user_focus: str) -> str:
    """构建 R8 规则段落"""
    if not enable_r8:
        return "【R8 无用细节清除：已关闭，跳过此规则】"

    parts = ["【R8 无用细节清除：已开启】"]
    parts.append("请额外执行无用细节清除（R8），判定标准见上方规则。")

    context_parts = []
    if outline_context and outline_context.strip():
        context_parts.append(f"大纲/场景规划（本章主旨来源）：\n{outline_context.strip()}")
    if character_context and character_context.strip():
        context_parts.append(f"人物设定：\n{character_context.strip()}")
    if user_focus and user_focus.strip():
        context_parts.append(f"用户指定的本章重点：\n{user_focus.strip()}")

    if context_parts:
        parts.append("以下为副文本，用于判断细节是否有用：")
        parts.extend(context_parts)
    else:
        parts.append("无副文本提供，请基于正文自行推断主旨，并在修改清单中标注「主旨为推断，非明确来源」。")

    return "\n".join(parts)


def _build_context_section(prev_tail: str, next_head: str) -> str:
    """构建前后章衔接段"""
    if not prev_tail and not next_head:
        return ""

    parts = ["【前后章衔接校验】请确保修改不破坏章节间的过渡："]
    if prev_tail:
        parts.append(f"前章末尾（约200字）：\n{prev_tail.strip()}")
    if next_head:
        parts.append(f"后章开头（约200字）：\n{next_head.strip()}")
    return "\n".join(parts)
