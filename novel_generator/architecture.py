#novel_generator/architecture.py
# -*- coding: utf-8 -*-
"""
小说总体架构生成（Novel_architecture_generate 及相关辅助函数）
"""
import os
import json
import logging
import traceback
from novel_generator.common import invoke_with_cleaning
from llm_adapters import create_llm_adapter
import prompt_definitions
logging.basicConfig(
    filename='app.log',      # 日志文件名
    filemode='a',            # 追加模式（'w' 会覆盖）
    level=logging.INFO,      # 记录 INFO 及以上级别的日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
from utils import clear_file_content, save_string_to_txt, atomic_write_json
import re as _re


def read_character_dynamics(filepath: str) -> str:
    """
    读取角色动力学内容（向后兼容）。
    1. 优先从 character_dynamics.txt 读取
    2. 回退：从 Novel_architecture.txt 提取 Section 2（旧项目兼容）
    3. 都没有则返回空字符串
    """
    dynamics_file = os.path.join(filepath, "character_dynamics.txt")
    if os.path.exists(dynamics_file):
        with open(dynamics_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return content

    # 回退：从旧架构文件中提取 Section 2
    arch_file = os.path.join(filepath, "Novel_architecture.txt")
    if os.path.exists(arch_file):
        with open(arch_file, "r", encoding="utf-8") as f:
            arch_text = f.read()
        start_marker = "#=== 2) 角色动力学 ==="
        end_marker = "#=== 3) 世界观 ==="
        start_idx = arch_text.find(start_marker)
        end_idx = arch_text.find(end_marker)
        if start_idx != -1 and end_idx != -1:
            extracted = arch_text[start_idx + len(start_marker):end_idx].strip()
            if extracted:
                return extracted

    return ""


def save_character_dynamics(filepath: str, content: str) -> None:
    """保存角色动力学内容到 character_dynamics.txt。"""
    os.makedirs(filepath, exist_ok=True)
    dynamics_file = os.path.join(filepath, "character_dynamics.txt")
    clear_file_content(dynamics_file)
    save_string_to_txt(content, dynamics_file)
    logging.info("character_dynamics.txt saved successfully.")


def read_core_seed(filepath: str) -> str:
    """
    读取核心种子内容（向后兼容）。
    1. 优先从 core_seed.txt 读取
    2. 回退：从 Novel_architecture.txt 提取 Section 1
    3. 都没有则返回空字符串
    """
    seed_file = os.path.join(filepath, "core_seed.txt")
    if os.path.exists(seed_file):
        with open(seed_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return content

    arch_file = os.path.join(filepath, "Novel_architecture.txt")
    if os.path.exists(arch_file):
        with open(arch_file, "r", encoding="utf-8") as f:
            arch_text = f.read()
        start_marker = "#=== 1) 核心种子 ==="
        start_idx = arch_text.find(start_marker)
        if start_idx != -1:
            content_start = start_idx + len(start_marker)
            # 结束于 Section 2 或 Section 3（角色动力学已独立后直接跳到3）
            end_idx = -1
            for end_marker in ["#=== 2)", "#=== 3)"]:
                pos = arch_text.find(end_marker, content_start)
                if pos != -1 and (end_idx == -1 or pos < end_idx):
                    end_idx = pos
            extracted = arch_text[content_start:end_idx].strip() if end_idx != -1 else arch_text[content_start:].strip()
            if extracted:
                return extracted

    return ""


def read_world_building(filepath: str) -> str:
    """
    读取世界观内容（向后兼容）。
    1. 优先从 world_building.txt 读取
    2. 回退：从 Novel_architecture.txt 提取 Section 3
    3. 都没有则返回空字符串
    """
    wb_file = os.path.join(filepath, "world_building.txt")
    if os.path.exists(wb_file):
        with open(wb_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return content

    arch_file = os.path.join(filepath, "Novel_architecture.txt")
    if os.path.exists(arch_file):
        with open(arch_file, "r", encoding="utf-8") as f:
            arch_text = f.read()
        start_marker = "#=== 3) 世界观 ==="
        end_marker = "#=== 4)"
        start_idx = arch_text.find(start_marker)
        end_idx = arch_text.find(end_marker, start_idx + 1) if start_idx != -1 else -1
        if start_idx != -1:
            content_start = start_idx + len(start_marker)
            extracted = arch_text[content_start:end_idx].strip() if end_idx != -1 else arch_text[content_start:].strip()
            if extracted:
                return extracted

    return ""


def read_plot_architecture(filepath: str) -> str:
    """
    读取情节架构内容（向后兼容）。
    1. 优先从 plot_architecture.txt 读取
    2. 回退：从 Novel_architecture.txt 提取 Section 4 到末尾
    3. 都没有则返回空字符串
    """
    pa_file = os.path.join(filepath, "plot_architecture.txt")
    if os.path.exists(pa_file):
        with open(pa_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return content

    arch_file = os.path.join(filepath, "Novel_architecture.txt")
    if os.path.exists(arch_file):
        with open(arch_file, "r", encoding="utf-8") as f:
            arch_text = f.read()
        start_marker = "#=== 4) 三幕式情节架构 ==="
        start_idx = arch_text.find(start_marker)
        if start_idx != -1:
            extracted = arch_text[start_idx + len(start_marker):].strip()
            if extracted:
                return extracted

    return ""


def save_core_seed(filepath: str, content: str) -> None:
    """保存核心种子到 core_seed.txt。"""
    os.makedirs(filepath, exist_ok=True)
    seed_file = os.path.join(filepath, "core_seed.txt")
    clear_file_content(seed_file)
    save_string_to_txt(content, seed_file)
    logging.info("core_seed.txt saved successfully.")


def save_world_building(filepath: str, content: str) -> None:
    """保存世界观到 world_building.txt。"""
    os.makedirs(filepath, exist_ok=True)
    wb_file = os.path.join(filepath, "world_building.txt")
    clear_file_content(wb_file)
    save_string_to_txt(content, wb_file)
    logging.info("world_building.txt saved successfully.")


def save_plot_architecture(filepath: str, content: str) -> None:
    """保存情节架构到 plot_architecture.txt。"""
    os.makedirs(filepath, exist_ok=True)
    pa_file = os.path.join(filepath, "plot_architecture.txt")
    clear_file_content(pa_file)
    save_string_to_txt(content, pa_file)
    logging.info("plot_architecture.txt saved successfully.")


def read_novel_setting(filepath: str) -> str:
    """
    读取小说设定（Section 0）。
    1. 优先从 novel_setting.txt 读取
    2. 回退：从 Novel_architecture.txt 提取 Section 0（兼容旧项目）
    3. 都没有则返回空字符串
    """
    setting_file = os.path.join(filepath, "novel_setting.txt")
    if os.path.exists(setting_file):
        with open(setting_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if content:
            return content

    arch_file = os.path.join(filepath, "Novel_architecture.txt")
    if os.path.exists(arch_file):
        with open(arch_file, "r", encoding="utf-8") as f:
            arch_text = f.read()
        marker = "#=== 1) 核心种子 ==="
        idx = arch_text.find(marker)
        if idx != -1:
            extracted = arch_text[:idx].strip()
            # 去掉 Section 0 标题行（如果有）
            if extracted.startswith("#=== 0)"):
                lines = extracted.split("\n", 1)
                extracted = lines[1].strip() if len(lines) > 1 else ""
            if extracted:
                return extracted

    return ""


def save_novel_setting(filepath: str, topic: str, genre: str, num_chapters: int, word_number: int) -> None:
    """保存小说设定到 novel_setting.txt。"""
    os.makedirs(filepath, exist_ok=True)
    content = f"主题：{topic},类型：{genre},篇幅：约{num_chapters}章（每章{word_number}字）"
    setting_file = os.path.join(filepath, "novel_setting.txt")
    clear_file_content(setting_file)
    save_string_to_txt(content, setting_file)
    logging.info("novel_setting.txt saved successfully.")


def read_character_state(filepath: str) -> str:
    """读取角色状态内容。"""
    cs_file = os.path.join(filepath, "character_state.txt")
    if os.path.exists(cs_file):
        with open(cs_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def regenerate_assembled_view(filepath: str) -> str:
    """
    从所有独立文件组装并写入 Novel_architecture.txt（只读副本），返回组装内容。
    """
    novel_setting = read_novel_setting(filepath)
    core_seed = read_core_seed(filepath)
    char_dynamics = read_character_dynamics(filepath)
    world_building = read_world_building(filepath)
    plot_arch = read_plot_architecture(filepath)
    char_state = read_character_state(filepath)

    parts = []
    if novel_setting:
        parts.append(f"#=== 0) 小说设定 ===\n{novel_setting}")
    if core_seed:
        parts.append(f"#=== 1) 核心种子 ===\n{core_seed}")
    if char_dynamics:
        parts.append(f"#=== 2) 角色动力学 ===\n{char_dynamics}")
    if world_building:
        parts.append(f"#=== 3) 世界观 ===\n{world_building}")
    if plot_arch:
        parts.append(f"#=== 4) 三幕式情节架构 ===\n{plot_arch}")
    if char_state:
        parts.append(f"#=== 5) 角色状态 ===\n{char_state}")

    assembled = "\n\n".join(parts)

    if assembled:
        arch_file = os.path.join(filepath, "Novel_architecture.txt")
        clear_file_content(arch_file)
        save_string_to_txt(assembled, arch_file)
        logging.info("Novel_architecture.txt regenerated from independent files.")

    return assembled


def build_full_architecture(filepath: str) -> str:
    """
    从独立文件组装完整架构文本（用于续写、蓝图、章节生成等需要全量的场景）。
    独立文件是唯一数据源，不再回退到 Novel_architecture.txt。
    """
    novel_setting = read_novel_setting(filepath)
    core_seed = read_core_seed(filepath)
    world_building = read_world_building(filepath)
    plot_arch = read_plot_architecture(filepath)
    char_dynamics = read_character_dynamics(filepath)

    parts = []
    if novel_setting:
        parts.append(f"#=== 0) 小说设定 ===\n{novel_setting}")
    if core_seed:
        parts.append(f"#=== 1) 核心种子 ===\n{core_seed}")
    if char_dynamics:
        parts.append(f"#=== 2) 角色动力学 ===\n{char_dynamics}")
    if world_building:
        parts.append(f"#=== 3) 世界观 ===\n{world_building}")
    if plot_arch:
        parts.append(f"#=== 4) 三幕式情节架构 ===\n{plot_arch}")

    return "\n\n".join(parts)


def _route_continuation_result(filepath: str, result_text: str) -> None:
    """
    解析一键续写 LLM 输出，将内容分别路由到不同文件：
    - 「一、新增角色设定」→ 追加到 character_dynamics.txt
    - 「二、新增剧情弧」→ 追加到 Novel_architecture.txt
    - 「三、新角色初始状态」→ 追加到 character_state.txt
    """
    # 定义段落标记
    char_markers = ["一、新增角色设定", "新增角色设定"]
    arc_markers = ["二、新增剧情弧", "新增剧情弧"]
    state_markers = ["三、新角色初始状态", "新角色初始状态", "新增角色初始状态"]

    # 提取各段落
    new_characters = ""
    new_arcs = ""
    new_char_state = ""

    # 使用所有标记构建正则拆分
    all_markers = char_markers + arc_markers + state_markers
    # 按文本中出现的位置定位各段
    sections = []
    for marker in all_markers:
        idx = result_text.find(marker)
        if idx != -1:
            marker_type = (
                "char" if marker in char_markers else
                "arc" if marker in arc_markers else
                "state"
            )
            sections.append((idx, idx + len(marker), marker_type))

    sections.sort(key=lambda x: x[0])

    for i, (start, content_start, mtype) in enumerate(sections):
        end = sections[i + 1][0] if i + 1 < len(sections) else len(result_text)
        segment = result_text[content_start:end].strip()
        if mtype == "char" and not new_characters:
            new_characters = segment
        elif mtype == "arc" and not new_arcs:
            new_arcs = segment
        elif mtype == "state" and not new_char_state:
            new_char_state = segment

    # 路由到各独立文件（不再直接写 Novel_architecture.txt）
    if new_characters:
        dynamics_file = os.path.join(filepath, "character_dynamics.txt")
        with open(dynamics_file, "a", encoding="utf-8") as f:
            f.write("\n\n#=== 续写新增角色设定 ===\n")
            f.write(new_characters)
        logging.info("New character dynamics appended to character_dynamics.txt.")

    if new_arcs:
        pa_file = os.path.join(filepath, "plot_architecture.txt")
        with open(pa_file, "a", encoding="utf-8") as f:
            f.write("\n\n#=== 续写新增剧情弧 ===\n")
            f.write(new_arcs)
        logging.info("New arcs appended to plot_architecture.txt.")

    if new_char_state:
        char_state_file = os.path.join(filepath, "character_state.txt")
        with open(char_state_file, "a", encoding="utf-8") as f:
            f.write("\n\n#=== 续写新增角色 ===\n")
            f.write(new_char_state)
        logging.info("New character states appended to character_state.txt.")

    # 重新组装只读副本
    regenerate_assembled_view(filepath)


def load_partial_architecture_data(filepath: str) -> dict:
    """
    从 filepath 下的 partial_architecture.json 读取已有的阶段性数据。
    如果文件不存在或无法解析，返回空 dict。
    """
    partial_file = os.path.join(filepath, "partial_architecture.json")
    if not os.path.exists(partial_file):
        return {}
    try:
        with open(partial_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logging.warning(f"Failed to load partial_architecture.json: {e}")
        return {}

def save_partial_architecture_data(filepath: str, data: dict):
    """
    将阶段性数据写入 partial_architecture.json。
    """
    partial_file = os.path.join(filepath, "partial_architecture.json")
    try:
        atomic_write_json(data, partial_file, indent=2)
    except Exception as e:
        logging.warning(f"Failed to save partial_architecture.json: {e}")

def Novel_architecture_generate(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    topic: str,
    genre: str,
    number_of_chapters: int,
    word_number: int,
    filepath: str,
    user_guidance: str = "",  # 新增参数
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    num_characters: str = "3-6",
    thinking_budget: int = 0,
    narrative_instruction: str = ""
) -> dict:
    """
    依次调用:
      1. core_seed_prompt
      2. character_dynamics_prompt
      3. world_building_prompt
      4. plot_architecture_prompt
    若在中间任何一步报错且重试多次失败，则将已经生成的内容写入 partial_architecture.json 并退出；
    下次调用时可从该步骤继续。
    最终保存到各独立文件 + 组装只读 Novel_architecture.txt。
    返回包含各部分内容的 dict。
    """
    os.makedirs(filepath, exist_ok=True)
    partial_data = load_partial_architecture_data(filepath)
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget
    )
    # Step1: 核心种子
    if "core_seed_result" not in partial_data:
        logging.info("Step1: Generating core_seed_prompt (核心种子) ...")
        prompt_core = prompt_definitions.core_seed_prompt.format(
            topic=topic,
            genre=genre,
            number_of_chapters=number_of_chapters,
            word_number=word_number,
            user_guidance=user_guidance  # 修复：添加内容指导
        )
        core_seed_result = invoke_with_cleaning(llm_adapter, prompt_core)
        if not core_seed_result.strip():
            logging.warning("core_seed_prompt generation failed and returned empty.")
            save_partial_architecture_data(filepath, partial_data)
            return
        partial_data["core_seed_result"] = core_seed_result
        save_partial_architecture_data(filepath, partial_data)
    else:
        logging.info("Step1 already done. Skipping...")
    # Step2: 角色动力学
    if "character_dynamics_result" not in partial_data:
        logging.info("Step2: Generating character_dynamics_prompt ...")
        prompt_character = prompt_definitions.character_dynamics_prompt.format(
            core_seed=partial_data["core_seed_result"].strip(),
            user_guidance=user_guidance,
            num_characters=num_characters
        )
        character_dynamics_result = invoke_with_cleaning(llm_adapter, prompt_character)
        if not character_dynamics_result.strip():
            logging.warning("character_dynamics_prompt generation failed.")
            save_partial_architecture_data(filepath, partial_data)
            return
        partial_data["character_dynamics_result"] = character_dynamics_result
        save_partial_architecture_data(filepath, partial_data)
    else:
        logging.info("Step2 already done. Skipping...")
    # 生成初始角色状态
    if "character_dynamics_result" in partial_data and "character_state_result" not in partial_data:
        logging.info("Generating initial character state from character dynamics ...")
        prompt_char_state_init = prompt_definitions.create_character_state_prompt.format(
            character_dynamics=partial_data["character_dynamics_result"].strip()
        )
        character_state_init = invoke_with_cleaning(llm_adapter, prompt_char_state_init)
        if not character_state_init.strip():
            logging.warning("create_character_state_prompt generation failed.")
            save_partial_architecture_data(filepath, partial_data)
            return
        partial_data["character_state_result"] = character_state_init
        character_state_file = os.path.join(filepath, "character_state.txt")
        clear_file_content(character_state_file)
        save_string_to_txt(character_state_init, character_state_file)
        save_partial_architecture_data(filepath, partial_data)
        logging.info("Initial character state created and saved.")
    # Step3: 世界观
    if "world_building_result" not in partial_data:
        logging.info("Step3: Generating world_building_prompt ...")
        prompt_world = prompt_definitions.world_building_prompt.format(
            core_seed=partial_data["core_seed_result"].strip(),
            user_guidance=user_guidance  # 修复：添加用户指导
        )
        world_building_result = invoke_with_cleaning(llm_adapter, prompt_world)
        if not world_building_result.strip():
            logging.warning("world_building_prompt generation failed.")
            save_partial_architecture_data(filepath, partial_data)
            return
        partial_data["world_building_result"] = world_building_result
        save_partial_architecture_data(filepath, partial_data)
    else:
        logging.info("Step3 already done. Skipping...")
    # Step4: 三幕式情节
    if "plot_arch_result" not in partial_data:
        logging.info("Step4: Generating plot_architecture_prompt ...")
        prompt_plot = prompt_definitions.plot_architecture_prompt.format(
            core_seed=partial_data["core_seed_result"].strip(),
            character_dynamics=partial_data["character_dynamics_result"].strip(),
            world_building=partial_data["world_building_result"].strip(),
            user_guidance=user_guidance,
            number_of_chapters=number_of_chapters
        )
        if narrative_instruction:
            prompt_plot = f"\n【叙事风格指导-架构层】\n{narrative_instruction}\n\n" + prompt_plot
        plot_arch_result = invoke_with_cleaning(llm_adapter, prompt_plot)
        if not plot_arch_result.strip():
            logging.warning("plot_architecture_prompt generation failed.")
            save_partial_architecture_data(filepath, partial_data)
            return
        partial_data["plot_arch_result"] = plot_arch_result
        save_partial_architecture_data(filepath, partial_data)
    else:
        logging.info("Step4 already done. Skipping...")

    core_seed_result = partial_data["core_seed_result"]
    character_dynamics_result = partial_data["character_dynamics_result"]
    character_state_result = partial_data.get("character_state_result", "")
    world_building_result = partial_data["world_building_result"]
    plot_arch_result = partial_data["plot_arch_result"]

    # 保存到各独立文件
    save_novel_setting(filepath, topic, genre, number_of_chapters, word_number)
    save_core_seed(filepath, core_seed_result)
    save_character_dynamics(filepath, character_dynamics_result)
    save_world_building(filepath, world_building_result)
    save_plot_architecture(filepath, plot_arch_result)

    # 组装只读副本
    assembled = regenerate_assembled_view(filepath)
    logging.info("Architecture generated and assembled from independent files.")

    partial_arch_file = os.path.join(filepath, "partial_architecture.json")
    if os.path.exists(partial_arch_file):
        os.remove(partial_arch_file)
        logging.info("partial_architecture.json removed (all steps completed).")

    return {
        "core_seed": core_seed_result,
        "character_dynamics": character_dynamics_result,
        "character_state": character_state_result,
        "world_building": world_building_result,
        "plot_architecture": plot_arch_result,
        "assembled": assembled,
    }


def generate_core_seed(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    topic: str,
    genre: str,
    number_of_chapters: int,
    word_number: int,
    user_guidance: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0
) -> str:
    """仅生成核心种子，返回结果文本。"""
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget
    )
    prompt_core = prompt_definitions.core_seed_prompt.format(
        topic=topic,
        genre=genre,
        number_of_chapters=number_of_chapters,
        word_number=word_number,
        user_guidance=user_guidance
    )
    result = invoke_with_cleaning(llm_adapter, prompt_core)
    if not result.strip():
        raise RuntimeError("核心种子生成失败，LLM 返回为空。")
    return result


def generate_character_dynamics(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    core_seed: str,
    user_guidance: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    num_characters: str = "3-6"
) -> tuple:
    """根据种子生成角色动力学 + 角色状态，返回 (character_dynamics, character_state) 元组。"""
    character_dynamics = generate_character_dynamics_only(
        interface_format=interface_format, api_key=api_key, base_url=base_url,
        llm_model=llm_model, core_seed=core_seed, user_guidance=user_guidance,
        temperature=temperature, max_tokens=max_tokens, timeout=timeout,
        enable_thinking=enable_thinking, thinking_budget=thinking_budget,
        num_characters=num_characters
    )
    character_state = generate_character_state_only(
        interface_format=interface_format, api_key=api_key, base_url=base_url,
        llm_model=llm_model, character_dynamics=character_dynamics,
        temperature=temperature, max_tokens=max_tokens, timeout=timeout,
        enable_thinking=enable_thinking, thinking_budget=thinking_budget
    )
    return (character_dynamics, character_state)


def generate_character_dynamics_only(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    core_seed: str,
    user_guidance: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    num_characters: str = "3-6"
) -> str:
    """仅生成角色动力学，返回动力学文本。"""
    llm_adapter = create_llm_adapter(
        interface_format=interface_format, base_url=base_url, model_name=llm_model,
        api_key=api_key, temperature=temperature, max_tokens=max_tokens,
        timeout=timeout, enable_thinking=enable_thinking, thinking_budget=thinking_budget
    )
    prompt_character = prompt_definitions.character_dynamics_prompt.format(
        core_seed=core_seed.strip(),
        user_guidance=user_guidance,
        num_characters=num_characters
    )
    character_dynamics = invoke_with_cleaning(llm_adapter, prompt_character)
    if not character_dynamics.strip():
        raise RuntimeError("角色动力学生成失败，LLM 返回为空。")
    return character_dynamics


def supplement_characters(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    existing_characters: str,
    supplement_guidance: str,
    num_characters: str = "1-2",
    core_seed: str = "",
    world_building: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0
) -> str:
    """基于已有角色，复用当前预设的 character_dynamics_prompt 补充生成新角色。"""
    llm_adapter = create_llm_adapter(
        interface_format=interface_format, base_url=base_url, model_name=llm_model,
        api_key=api_key, temperature=temperature, max_tokens=max_tokens,
        timeout=timeout, enable_thinking=enable_thinking, thinking_budget=thinking_budget
    )
    # 将已有角色、世界观、补充要求拼入 user_guidance，复用预设的角色动力学 prompt
    guidance_parts = []
    if supplement_guidance.strip():
        guidance_parts.append(f"补充要求：{supplement_guidance.strip()}")
    if world_building.strip():
        guidance_parts.append(f"世界观设定：\n{world_building.strip()}")
    guidance_parts.append(
        f"以下是已有角色，请勿重复，仅输出新增角色：\n{existing_characters.strip()}"
    )
    combined_guidance = "\n\n".join(guidance_parts)

    seed = core_seed.strip() if core_seed.strip() else "（请参考已有角色推断故事背景）"

    prompt = prompt_definitions.character_dynamics_prompt.format(
        core_seed=seed,
        user_guidance=combined_guidance,
        num_characters=num_characters,
    )
    result = invoke_with_cleaning(llm_adapter, prompt)
    if not result.strip():
        raise RuntimeError("补充角色生成失败，LLM 返回为空。")
    return result


def generate_character_state_only(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    character_dynamics: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0
) -> str:
    """根据角色动力学生成角色状态，返回状态文本。"""
    llm_adapter = create_llm_adapter(
        interface_format=interface_format, base_url=base_url, model_name=llm_model,
        api_key=api_key, temperature=temperature, max_tokens=max_tokens,
        timeout=timeout, enable_thinking=enable_thinking, thinking_budget=thinking_budget
    )
    prompt_char_state = prompt_definitions.create_character_state_prompt.format(
        character_dynamics=character_dynamics.strip()
    )
    character_state = invoke_with_cleaning(llm_adapter, prompt_char_state)
    if not character_state.strip():
        raise RuntimeError("角色状态生成失败，LLM 返回为空。")
    return character_state


def generate_world_building(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    core_seed: str,
    user_guidance: str = "",
    character_dynamics: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0
) -> str:
    """根据种子生成世界观，可选注入角色动力学。"""
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget
    )
    effective_guidance = user_guidance
    if character_dynamics.strip():
        effective_guidance = f"{user_guidance}\n\n以下是已有角色设定，请确保世界观与角色背景相契合：\n{character_dynamics.strip()}"
    prompt_world = prompt_definitions.world_building_prompt.format(
        core_seed=core_seed.strip(),
        user_guidance=effective_guidance
    )
    result = invoke_with_cleaning(llm_adapter, prompt_world)
    if not result.strip():
        raise RuntimeError("世界观生成失败，LLM 返回为空。")
    return result


def generate_plot_architecture(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    core_seed: str,
    character_dynamics: str,
    world_building: str,
    user_guidance: str = "",
    number_of_chapters: int = 0,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    narrative_instruction: str = ""
) -> str:
    """根据前三步生成情节架构，返回结果文本。"""
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget
    )
    prompt_plot = prompt_definitions.plot_architecture_prompt.format(
        core_seed=core_seed.strip(),
        character_dynamics=character_dynamics.strip(),
        world_building=world_building.strip(),
        user_guidance=user_guidance,
        number_of_chapters=number_of_chapters
    )
    if narrative_instruction:
        prompt_plot = f"\n【叙事风格指导-架构层】\n{narrative_instruction}\n\n" + prompt_plot
    result = invoke_with_cleaning(llm_adapter, prompt_plot)
    if not result.strip():
        raise RuntimeError("情节架构生成失败，LLM 返回为空。")
    return result


def assemble_architecture(
    filepath: str,
    topic: str,
    genre: str,
    num_chapters: int,
    word_number: int,
    core_seed: str,
    character_dynamics: str,
    character_state: str,
    world_building: str,
    plot_architecture: str
) -> str:
    """组装所有部分：保存到各独立文件 + 组装只读 Novel_architecture.txt。返回组装后的内容字符串。"""
    os.makedirs(filepath, exist_ok=True)

    # 保存到各独立文件
    save_novel_setting(filepath, topic, genre, int(num_chapters), int(word_number))
    if core_seed.strip():
        save_core_seed(filepath, core_seed)
    if character_dynamics.strip():
        save_character_dynamics(filepath, character_dynamics)
    if world_building.strip():
        save_world_building(filepath, world_building)
    if plot_architecture.strip():
        save_plot_architecture(filepath, plot_architecture)

    if character_state.strip():
        character_state_file = os.path.join(filepath, "character_state.txt")
        clear_file_content(character_state_file)
        save_string_to_txt(character_state, character_state_file)
        logging.info("character_state.txt saved successfully.")

    # 组装只读副本
    assembled = regenerate_assembled_view(filepath)
    logging.info("Architecture assembled and saved from independent files.")

    # Clean up partial file if exists
    partial_arch_file = os.path.join(filepath, "partial_architecture.json")
    if os.path.exists(partial_arch_file):
        os.remove(partial_arch_file)

    return assembled


def continue_novel_architecture(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    filepath: str,
    new_chapters: int,
    user_guidance: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    narrative_instruction: str = "",
    num_characters: str = "1-3"
) -> str:
    """
    在已有小说架构基础上生成续写扩展方案。

    1. 读取 Novel_architecture.txt（必须存在）
    2. 读取 global_summary.txt（可选）
    3. 读取 character_state.txt（可选）
    4. 调用 LLM 生成续写架构
    5. 将结果追加到 Novel_architecture.txt
    6. 如果生成内容中包含角色状态信息，追加到 character_state.txt
    7. 返回生成的续写内容
    """
    existing_architecture = build_full_architecture(filepath)
    if not existing_architecture:
        raise FileNotFoundError(f"架构文件不存在，请先执行 Step 1 生成小说架构。")

    global_summary = ""
    summary_file = os.path.join(filepath, "global_summary.txt")
    if os.path.exists(summary_file):
        with open(summary_file, "r", encoding="utf-8") as f:
            global_summary = f.read()

    character_state = ""
    char_state_file = os.path.join(filepath, "character_state.txt")
    if os.path.exists(char_state_file):
        with open(char_state_file, "r", encoding="utf-8") as f:
            character_state = f.read()

    # 构建提示词
    prompt_text = prompt_definitions.continuation_architecture_prompt.format(
        existing_architecture=existing_architecture,
        global_summary=global_summary if global_summary else "（暂无前文摘要）",
        character_state=character_state if character_state else "（暂无角色状态）",
        new_chapters=new_chapters,
        user_guidance=user_guidance if user_guidance else "（用户未提供具体构想，请自由发挥）",
        num_characters=num_characters
    )
    if narrative_instruction:
        prompt_text = f"\n【叙事风格指导-架构层】\n{narrative_instruction}\n\n" + prompt_text

    # 调用 LLM
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget
    )

    logging.info("Generating continuation architecture...")
    continuation_result = invoke_with_cleaning(llm_adapter, prompt_text)
    if not continuation_result.strip():
        raise RuntimeError("续写架构生成失败，LLM 返回为空。")

    # 路由续写结果到各文件
    _route_continuation_result(filepath, continuation_result)

    return continuation_result


def continue_generate_seed(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    filepath: str,
    new_chapters: int,
    user_guidance: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    narrative_instruction: str = ""
) -> str:
    """
    续写步骤0: 生成续写方向大纲（续写种子）。
    读取 Novel_architecture.txt + global_summary.txt + character_state.txt，
    调用 continuation_seed_prompt，返回续写种子文本（不写文件）。
    """
    existing_architecture = build_full_architecture(filepath)
    if not existing_architecture:
        raise FileNotFoundError(f"架构文件不存在，请先执行 Step 1 生成小说架构。")

    global_summary = ""
    summary_file = os.path.join(filepath, "global_summary.txt")
    if os.path.exists(summary_file):
        with open(summary_file, "r", encoding="utf-8") as f:
            global_summary = f.read()

    character_state = ""
    char_state_file = os.path.join(filepath, "character_state.txt")
    if os.path.exists(char_state_file):
        with open(char_state_file, "r", encoding="utf-8") as f:
            character_state = f.read()

    prompt_text = prompt_definitions.continuation_seed_prompt.format(
        existing_architecture=existing_architecture,
        global_summary=global_summary if global_summary else "（暂无前文摘要）",
        character_state=character_state if character_state else "（暂无角色状态）",
        new_chapters=new_chapters,
        user_guidance=user_guidance if user_guidance else "（用户未提供具体构想，请自由发挥）"
    )
    if narrative_instruction:
        prompt_text = f"\n【叙事风格指导-架构层】\n{narrative_instruction}\n\n" + prompt_text

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget
    )

    logging.info("Generating continuation seed...")
    result = invoke_with_cleaning(llm_adapter, prompt_text)
    if not result.strip():
        raise RuntimeError("续写方向大纲生成失败，LLM 返回为空。")
    return result


def continue_generate_world(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    filepath: str,
    continuation_seed: str,
    new_chapters: int,
    user_guidance: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    narrative_instruction: str = ""
) -> str:
    """
    续写步骤0.5: 生成世界观扩展。
    读取 Novel_architecture.txt + global_summary.txt，加上 continuation_seed，
    调用 continuation_world_prompt，返回世界观扩展文本（不写文件）。
    """
    existing_architecture = build_full_architecture(filepath)
    if not existing_architecture:
        raise FileNotFoundError(f"架构文件不存在，请先执行 Step 1 生成小说架构。")

    global_summary = ""
    summary_file = os.path.join(filepath, "global_summary.txt")
    if os.path.exists(summary_file):
        with open(summary_file, "r", encoding="utf-8") as f:
            global_summary = f.read()

    prompt_text = prompt_definitions.continuation_world_prompt.format(
        existing_architecture=existing_architecture,
        global_summary=global_summary if global_summary else "（暂无前文摘要）",
        continuation_seed=continuation_seed if continuation_seed else "（暂无续写方向大纲）",
        new_chapters=new_chapters,
        user_guidance=user_guidance if user_guidance else "（用户未提供具体构想，请自由发挥）"
    )
    if narrative_instruction:
        prompt_text = f"\n【叙事风格指导-架构层】\n{narrative_instruction}\n\n" + prompt_text

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget
    )

    logging.info("Generating continuation world expansion...")
    result = invoke_with_cleaning(llm_adapter, prompt_text)
    if not result.strip():
        raise RuntimeError("续写世界观扩展生成失败，LLM 返回为空。")
    return result


def continue_generate_characters(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    filepath: str,
    new_chapters: int,
    user_guidance: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    narrative_instruction: str = "",
    continuation_seed: str = "",
    world_expansion: str = "",
    num_characters: str = "1-3"
) -> str:
    """
    续写步骤1: 生成新增角色设定。
    读取 Novel_architecture.txt + global_summary.txt + character_state.txt，
    调用 continuation_characters_prompt，返回新角色文本（不写文件）。
    """
    existing_architecture = build_full_architecture(filepath)
    if not existing_architecture:
        raise FileNotFoundError(f"架构文件不存在，请先执行 Step 1 生成小说架构。")

    global_summary = ""
    summary_file = os.path.join(filepath, "global_summary.txt")
    if os.path.exists(summary_file):
        with open(summary_file, "r", encoding="utf-8") as f:
            global_summary = f.read()

    character_state = ""
    char_state_file = os.path.join(filepath, "character_state.txt")
    if os.path.exists(char_state_file):
        with open(char_state_file, "r", encoding="utf-8") as f:
            character_state = f.read()

    prompt_text = prompt_definitions.continuation_characters_prompt.format(
        existing_architecture=existing_architecture,
        global_summary=global_summary if global_summary else "（暂无前文摘要）",
        character_state=character_state if character_state else "（暂无角色状态）",
        new_chapters=new_chapters,
        user_guidance=user_guidance if user_guidance else "（用户未提供具体构想，请自由发挥）",
        num_characters=num_characters
    )
    extra_context = ""
    if continuation_seed:
        extra_context += f"\n===== 续写方向大纲 =====\n{continuation_seed}\n"
    if world_expansion:
        extra_context += f"\n===== 世界观扩展 =====\n{world_expansion}\n"
    if extra_context:
        prompt_text = extra_context + prompt_text
    if narrative_instruction:
        prompt_text = f"\n【叙事风格指导-架构层】\n{narrative_instruction}\n\n" + prompt_text

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget
    )

    logging.info("Generating continuation characters...")
    result = invoke_with_cleaning(llm_adapter, prompt_text)
    if not result.strip():
        raise RuntimeError("续写新增角色生成失败，LLM 返回为空。")
    return result


def continue_generate_arcs(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    filepath: str,
    new_characters: str,
    new_chapters: int,
    user_guidance: str = "",
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    narrative_instruction: str = "",
    continuation_seed: str = "",
    world_expansion: str = ""
) -> str:
    """
    续写步骤2: 生成新增剧情弧。
    读取已有架构+摘要+角色状态 + new_characters（来自步骤1，可能被用户编辑），
    调用 continuation_arcs_prompt，返回新弧文本（不写文件）。
    """
    existing_architecture = build_full_architecture(filepath)
    if not existing_architecture:
        raise FileNotFoundError(f"架构文件不存在，请先执行 Step 1 生成小说架构。")

    global_summary = ""
    summary_file = os.path.join(filepath, "global_summary.txt")
    if os.path.exists(summary_file):
        with open(summary_file, "r", encoding="utf-8") as f:
            global_summary = f.read()

    character_state = ""
    char_state_file = os.path.join(filepath, "character_state.txt")
    if os.path.exists(char_state_file):
        with open(char_state_file, "r", encoding="utf-8") as f:
            character_state = f.read()

    prompt_text = prompt_definitions.continuation_arcs_prompt.format(
        existing_architecture=existing_architecture,
        global_summary=global_summary if global_summary else "（暂无前文摘要）",
        character_state=character_state if character_state else "（暂无角色状态）",
        new_characters=new_characters,
        new_chapters=new_chapters,
        user_guidance=user_guidance if user_guidance else "（用户未提供具体构想，请自由发挥）"
    )
    extra_context = ""
    if continuation_seed:
        extra_context += f"\n===== 续写方向大纲 =====\n{continuation_seed}\n"
    if world_expansion:
        extra_context += f"\n===== 世界观扩展 =====\n{world_expansion}\n"
    if extra_context:
        prompt_text = extra_context + prompt_text
    if narrative_instruction:
        prompt_text = f"\n【叙事风格指导-架构层】\n{narrative_instruction}\n\n" + prompt_text

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget
    )

    logging.info("Generating continuation arcs...")
    result = invoke_with_cleaning(llm_adapter, prompt_text)
    if not result.strip():
        raise RuntimeError("续写新增剧情弧生成失败，LLM 返回为空。")
    return result


def continue_generate_char_state(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    filepath: str,
    new_characters: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0
) -> str:
    """
    续写步骤3: 生成新角色初始状态。
    仅根据 new_characters 角色设定生成登场时的初始状态，
    不读取已有 character_state.txt，避免被已有剧情状态污染。
    """
    prompt_text = prompt_definitions.continuation_char_state_prompt.format(
        new_characters=new_characters
    )

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget
    )

    logging.info("Generating continuation character state...")
    result = invoke_with_cleaning(llm_adapter, prompt_text)
    if not result.strip():
        raise RuntimeError("续写新角色状态生成失败，LLM 返回为空。")
    return result


def compress_summary_and_state(
    interface_format: str,
    api_key: str,
    base_url: str,
    llm_model: str,
    filepath: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    timeout: int = 600,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    include_world_building: bool = False
) -> tuple:
    """
    对 global_summary.txt 和 character_state.txt 进行语义压缩。
    若 include_world_building=True，同时压缩 world_building.txt。
    压缩前备份原文件为 *_backup.txt。
    返回 (compressed_summary, compressed_state, compressed_world_building)。
    """
    summary_file = os.path.join(filepath, "global_summary.txt")
    char_state_file = os.path.join(filepath, "character_state.txt")

    global_summary = ""
    if os.path.exists(summary_file):
        with open(summary_file, "r", encoding="utf-8") as f:
            global_summary = f.read().strip()

    character_state = ""
    if os.path.exists(char_state_file):
        with open(char_state_file, "r", encoding="utf-8") as f:
            character_state = f.read().strip()

    if not global_summary and not character_state:
        raise RuntimeError("global_summary.txt 和 character_state.txt 均为空或不存在，无需压缩。")

    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=llm_model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget
    )

    compressed_summary = ""
    compressed_state = ""

    # 压缩前文摘要
    if global_summary:
        # 备份
        backup_file = os.path.join(filepath, "global_summary_backup.txt")
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(global_summary)
        logging.info("global_summary.txt backed up to global_summary_backup.txt.")

        prompt_text = prompt_definitions.compress_summary_prompt.format(
            global_summary=global_summary
        )
        logging.info("Compressing global_summary...")
        compressed_summary = invoke_with_cleaning(llm_adapter, prompt_text)
        if not compressed_summary.strip():
            raise RuntimeError("前文摘要压缩失败，LLM 返回为空。")
        save_string_to_txt(compressed_summary, summary_file)
        logging.info("Compressed summary written back to global_summary.txt.")

    # 压缩角色状态
    if character_state:
        # 备份
        backup_file = os.path.join(filepath, "character_state_backup.txt")
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(character_state)
        logging.info("character_state.txt backed up to character_state_backup.txt.")

        prompt_text = prompt_definitions.compress_character_state_prompt.format(
            character_state=character_state
        )
        logging.info("Compressing character_state...")
        compressed_state = invoke_with_cleaning(llm_adapter, prompt_text)
        if not compressed_state.strip():
            raise RuntimeError("角色状态压缩失败，LLM 返回为空。")
        save_string_to_txt(compressed_state, char_state_file)
        logging.info("Compressed character state written back to character_state.txt.")

    # 压缩世界观
    compressed_world_building = ""
    if include_world_building:
        wb_file = os.path.join(filepath, "world_building.txt")
        world_building = ""
        if os.path.exists(wb_file):
            with open(wb_file, "r", encoding="utf-8") as f:
                world_building = f.read().strip()

        if world_building:
            # 备份
            backup_file = os.path.join(filepath, "world_building_backup.txt")
            with open(backup_file, "w", encoding="utf-8") as f:
                f.write(world_building)
            logging.info("world_building.txt backed up to world_building_backup.txt.")

            prompt_text = prompt_definitions.compress_world_building_prompt.format(
                world_building=world_building
            )
            logging.info("Compressing world_building...")
            compressed_world_building = invoke_with_cleaning(llm_adapter, prompt_text)
            if not compressed_world_building.strip():
                raise RuntimeError("世界观压缩失败，LLM 返回为空。")
            save_world_building(filepath, compressed_world_building)
            logging.info("Compressed world building written back to world_building.txt.")

    return (compressed_summary, compressed_state, compressed_world_building)


def assemble_continuation(
    filepath: str, new_characters: str, new_arcs: str, new_char_state: str,
    continuation_seed: str = "", world_expansion: str = ""
) -> str:
    """
    组装续写内容：将新角色+新弧追加到各独立文件，
    新角色状态追加到 character_state.txt，重新组装只读副本。返回合并后的续写文本。
    """

    # 构建完整续写文本用于前端显示（返回值不变）
    parts = []
    if continuation_seed.strip():
        parts.append(f"续写方向大纲：\n{continuation_seed}")
    if world_expansion.strip():
        parts.append(f"世界观扩展：\n{world_expansion}")
    parts.append(f"一、新增角色设定\n{new_characters}")
    parts.append(f"二、新增剧情弧\n{new_arcs}")
    parts.append(f"三、新角色初始状态\n{new_char_state}")
    continuation_text = "\n\n".join(parts)

    # 新增角色设定 → 追加到 character_dynamics.txt
    if new_characters.strip():
        dynamics_file = os.path.join(filepath, "character_dynamics.txt")
        with open(dynamics_file, "a", encoding="utf-8") as f:
            f.write("\n\n#=== 续写新增角色设定 ===\n")
            f.write(new_characters)
        logging.info("New characters appended to character_dynamics.txt.")

    # 追加到各独立文件（不再直接写 Novel_architecture.txt）
    if continuation_seed.strip():
        cs_file = os.path.join(filepath, "core_seed.txt")
        with open(cs_file, "a", encoding="utf-8") as f:
            f.write("\n\n#=== 续写方向大纲 ===\n")
            f.write(continuation_seed)
        logging.info("Continuation seed appended to core_seed.txt.")
    if world_expansion.strip():
        wb_file = os.path.join(filepath, "world_building.txt")
        with open(wb_file, "a", encoding="utf-8") as f:
            f.write("\n\n#=== 续写世界观扩展 ===\n")
            f.write(world_expansion)
        logging.info("World expansion appended to world_building.txt.")
    if new_arcs.strip():
        pa_file = os.path.join(filepath, "plot_architecture.txt")
        with open(pa_file, "a", encoding="utf-8") as f:
            f.write("\n\n#=== 续写新增剧情弧 ===\n")
            f.write(new_arcs)
        logging.info("New arcs appended to plot_architecture.txt.")

    # 新角色状态 → 追加到 character_state.txt
    if new_char_state.strip():
        char_state_file = os.path.join(filepath, "character_state.txt")
        with open(char_state_file, "a", encoding="utf-8") as f:
            f.write("\n\n#=== 续写新增角色 ===\n")
            f.write(new_char_state)
        logging.info("New character states appended to character_state.txt.")

    # 重新组装只读副本
    regenerate_assembled_view(filepath)

    return continuation_text
