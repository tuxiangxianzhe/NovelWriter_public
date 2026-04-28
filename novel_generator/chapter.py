# novel_generator/chapter.py
# -*- coding: utf-8 -*-
"""
章节草稿生成及获取历史章节文本、当前章节摘要等
"""
import os
import json
import logging
import re  # 添加re模块导入
from llm_adapters import create_llm_adapter
import prompt_definitions
from chapter_directory_parser import get_chapter_info_from_blueprint
from novel_generator.common import invoke_with_cleaning
from utils import read_file, clear_file_content, save_string_to_txt
from novel_generator.finalization import filter_character_state, auto_detect_characters
from novel_generator.architecture import build_full_architecture, read_world_building
from novel_generator.vectorstore_utils import (
    get_relevant_context_from_vector_store,
    load_vector_store,
    get_author_reference_context
)
logging.basicConfig(
    filename='app.log',      # 日志文件名
    filemode='a',            # 追加模式（'w' 会覆盖）
    level=logging.INFO,      # 记录 INFO 及以上级别的日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_last_n_chapters_text(chapters_dir: str, current_chapter_num: int, n: int = 3) -> list:
    """
    从目录 chapters_dir 中获取最近 n 章的文本内容，返回文本列表。
    """
    texts = []
    start_chap = max(1, current_chapter_num - n)
    for c in range(start_chap, current_chapter_num):
        chap_file = os.path.join(chapters_dir, f"chapter_{c}.txt")
        if os.path.exists(chap_file):
            text = read_file(chap_file).strip()
            texts.append(text)
        else:
            texts.append("")
    return texts

def summarize_recent_chapters(
    interface_format: str,
    api_key: str,
    base_url: str,
    model_name: str,
    temperature: float,
    max_tokens: int,
    chapters_text_list: list,
    novel_number: int,            # 新增参数
    chapter_info: dict,           # 新增参数
    next_chapter_info: dict,      # 新增参数
    timeout: int = 600
) -> str:  # 修改返回值类型为 str，不再是 tuple
    """
    根据前三章内容生成当前章节的精准摘要。
    如果解析失败，则返回空字符串。
    """
    try:
        combined_text = "\n".join(chapters_text_list).strip()
        if not combined_text:
            return ""
            
        # 限制组合文本长度
        max_combined_length = 4000
        if len(combined_text) > max_combined_length:
            combined_text = combined_text[-max_combined_length:]
            
        llm_adapter = create_llm_adapter(
            interface_format=interface_format,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout
        )
        
        # 确保所有参数都有默认值
        chapter_info = chapter_info or {}
        next_chapter_info = next_chapter_info or {}
        
        prompt = prompt_definitions.summarize_recent_chapters_prompt.format(
            combined_text=combined_text,
            novel_number=novel_number,
            chapter_title=chapter_info.get("chapter_title", "未命名"),
            chapter_role=chapter_info.get("chapter_role", "常规章节"),
            chapter_purpose=chapter_info.get("chapter_purpose", "内容推进"),
            suspense_level=chapter_info.get("suspense_level", "中等"),
            foreshadowing=chapter_info.get("foreshadowing", "无"),
            plot_twist_level=chapter_info.get("plot_twist_level", "★☆☆☆☆"),
            chapter_summary=chapter_info.get("chapter_summary", ""),
            next_chapter_number=novel_number + 1,
            next_chapter_title=next_chapter_info.get("chapter_title", "（未命名）"),
            next_chapter_role=next_chapter_info.get("chapter_role", "过渡章节"),
            next_chapter_purpose=next_chapter_info.get("chapter_purpose", "承上启下"),
            next_chapter_summary=next_chapter_info.get("chapter_summary", "衔接过渡内容"),
            next_chapter_suspense_level=next_chapter_info.get("suspense_level", "中等"),
            next_chapter_foreshadowing=next_chapter_info.get("foreshadowing", "无特殊伏笔"),
            next_chapter_plot_twist_level=next_chapter_info.get("plot_twist_level", "★☆☆☆☆")
        )
        
        response_text = invoke_with_cleaning(llm_adapter, prompt)
        summary = extract_summary_from_response(response_text)
        
        if not summary:
            logging.warning("Failed to extract summary, using full response")
            return response_text[:2000]  # 限制长度
            
        return summary[:2000]  # 限制摘要长度
        
    except Exception as e:
        logging.error(f"Error in summarize_recent_chapters: {str(e)}")
        return ""

def extract_summary_from_response(response_text: str) -> str:
    """从响应文本中提取摘要部分"""
    if not response_text:
        return ""
        
    # 查找摘要标记
    summary_markers = [
        "当前章节摘要:", 
        "章节摘要:",
        "摘要:",
        "本章摘要:"
    ]
    
    for marker in summary_markers:
        if (marker in response_text):
            parts = response_text.split(marker, 1)
            if len(parts) > 1:
                return parts[1].strip()
    
    return response_text.strip()

def format_chapter_info(chapter_info: dict) -> str:
    """将章节信息字典格式化为文本"""
    template = """
章节编号：第{number}章
章节标题：《{title}》
章节定位：{role}
核心作用：{purpose}
主要人物：{characters}
关键道具：{items}
场景地点：{location}
伏笔设计：{foreshadow}
悬念密度：{suspense}
转折程度：{twist}
章节简述：{summary}
"""
    return template.format(
        number=chapter_info.get('chapter_number', '未知'),
        title=chapter_info.get('chapter_title', '未知'),
        role=chapter_info.get('chapter_role', '未知'),
        purpose=chapter_info.get('chapter_purpose', '未知'),
        characters=chapter_info.get('characters_involved', '未指定'),
        items=chapter_info.get('key_items', '未指定'),
        location=chapter_info.get('scene_location', '未指定'),
        foreshadow=chapter_info.get('foreshadowing', '无'),
        suspense=chapter_info.get('suspense_level', '一般'),
        twist=chapter_info.get('plot_twist_level', '★☆☆☆☆'),
        summary=chapter_info.get('chapter_summary', '未提供')
    )

def parse_search_keywords(response_text: str) -> list:
    """解析新版关键词格式（示例输入：'科技公司·数据泄露\n地下实验室·基因编辑'）"""
    return [
        line.strip().replace('·', ' ')
        for line in response_text.strip().split('\n')
        if '·' in line
    ][:5]  # 最多取5组

def apply_content_rules(texts: list, novel_number: int) -> list:
    """应用内容处理规则"""
    processed = []
    for text in texts:
        if re.search(r'第[\d]+章', text) or re.search(r'chapter_[\d]+', text):
            chap_nums = list(map(int, re.findall(r'\d+', text)))
            recent_chap = max(chap_nums) if chap_nums else 0
            time_distance = novel_number - recent_chap
            
            if time_distance <= 2:
                processed.append(f"[SKIP] 跳过近章内容：{text[:120]}...")
            elif 3 <= time_distance <= 5:
                processed.append(f"[MOD40%] {text}（需修改≥40%）")
            else:
                processed.append(f"[OK] {text}（可引用核心）")
        else:
            processed.append(f"[PRIOR] {text}（优先使用）")
    return processed

def apply_knowledge_rules(contexts: list, chapter_num: int) -> list:
    """应用知识库使用规则"""
    processed = []
    for text in contexts:
        # 检测历史章节内容
        if "第" in text and "章" in text:
            # 提取章节号判断时间远近
            chap_nums = [int(s) for s in text.split() if s.isdigit()]
            recent_chap = max(chap_nums) if chap_nums else 0
            time_distance = chapter_num - recent_chap
            
            # 相似度处理规则
            if time_distance <= 3:  # 近三章内容
                processed.append(f"[历史章节限制] 跳过近期内容: {text[:50]}...")
                continue
                
            # 允许引用但需要转换
            processed.append(f"[历史参考] {text} (需进行30%以上改写)")
        else:
            # 第三方知识优先处理
            processed.append(f"[外部知识] {text}")
    return processed

def get_filtered_knowledge_context(
    api_key: str,
    base_url: str,
    model_name: str,
    interface_format: str,
    embedding_adapter,
    filepath: str,
    chapter_info: dict,
    retrieved_texts: list,
    max_tokens: int = 2048,
    timeout: int = 600
) -> str:
    """优化后的知识过滤处理"""
    if not retrieved_texts:
        return "（无相关知识库内容）"

    try:
        processed_texts = apply_knowledge_rules(retrieved_texts, chapter_info.get('chapter_number', 0))
        llm_adapter = create_llm_adapter(
            interface_format=interface_format,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            temperature=0.3,
            max_tokens=max_tokens,
            timeout=timeout
        )
        
        # 限制检索文本长度并格式化
        formatted_texts = []
        max_text_length = 600
        for i, text in enumerate(processed_texts, 1):
            if len(text) > max_text_length:
                text = text[:max_text_length] + "..."
            formatted_texts.append(f"[预处理结果{i}]\n{text}")

        # 使用格式化函数处理章节信息
        formatted_chapter_info = (
            f"当前章节定位：{chapter_info.get('chapter_role', '')}\n"
            f"核心目标：{chapter_info.get('chapter_purpose', '')}\n"
            f"关键要素：{chapter_info.get('characters_involved', '')} | "
            f"{chapter_info.get('key_items', '')} | "
            f"{chapter_info.get('scene_location', '')}"
        )

        prompt = prompt_definitions.knowledge_filter_prompt.format(
            chapter_info=formatted_chapter_info,
            retrieved_texts="\n\n".join(formatted_texts) if formatted_texts else "（无检索结果）"
        )
        
        filtered_content = invoke_with_cleaning(llm_adapter, prompt)
        return filtered_content if filtered_content else "（知识内容过滤失败）"
        
    except Exception as e:
        logging.error(f"Error in knowledge filtering: {str(e)}")
        return "（内容过滤过程出错）"

def build_chapter_prompt(
    api_key: str,
    base_url: str,
    model_name: str,
    filepath: str,
    novel_number: int,
    word_number: int,
    temperature: float,
    user_guidance: str,
    characters_involved: str,
    key_items: str,
    scene_location: str,
    time_constraint: str,
    embedding_api_key: str,
    embedding_url: str,
    embedding_interface_format: str,
    embedding_model_name: str,
    embedding_retrieval_k: int = 2,
    interface_format: str = "openai",
    max_tokens: int = 2048,
    timeout: int = 600,
    writing_style: str = "",
    narrative_instruction: str = "",
    enable_author_reference: bool = True,
    inject_world_building: bool = False,
    author_style_name: str = "",
    styles_dir: str = "",
) -> str:
    """
    构造当前章节的请求提示词（完整实现版）
    修改重点：
    1. 优化知识库检索流程
    2. 新增内容重复检测机制
    3. 集成提示词应用规则
    """
    # 读取基础文件
    novel_architecture_text = build_full_architecture(filepath)
    directory_file = os.path.join(filepath, "Novel_directory.txt")
    blueprint_text = read_file(directory_file)
    global_summary_file = os.path.join(filepath, "global_summary.txt")
    global_summary_text = read_file(global_summary_file)
    character_state_file = os.path.join(filepath, "character_state.txt")
    character_state_text = read_file(character_state_file)

    # 获取章节信息
    chapter_info = get_chapter_info_from_blueprint(blueprint_text, novel_number)

    # 非首章：识别本章涉及角色 → 过滤角色状态
    if novel_number > 1:
        # 优先使用蓝图中标注的涉及角色
        blueprint_chars = chapter_info.get("characters_involved", "")
        if blueprint_chars:
            merged = characters_involved or ""
            for name in re.split(r'[,，、;；\s]+', blueprint_chars):
                name = name.strip()
                if name and name not in merged:
                    merged = (merged + "," + name) if merged else name
            characters_involved = merged
            logging.info(f"[角色检测] 蓝图标注: {blueprint_chars}")
        else:
            # 兜底：从蓝图文本自动匹配角色名
            auto_chars = auto_detect_characters(
                character_state_text,
                chapter_info.get("chapter_purpose", ""),
                chapter_info.get("chapter_summary", ""),
            )
            if auto_chars:
                merged = characters_involved or ""
                for name in auto_chars:
                    if name not in merged:
                        merged = (merged + "," + name) if merged else name
                characters_involved = merged
                logging.info(f"[角色检测] 自动识别: {auto_chars}")
        if characters_involved:
            original_len = len(character_state_text)
            character_state_text = filter_character_state(character_state_text, characters_involved)
            logging.info(f"[角色过滤] {original_len}字 → {len(character_state_text)}字")

    logging.info(f"[Prompt组成] 第{novel_number}章 基础文件: "
                 f"架构={len(novel_architecture_text)}字, "
                 f"蓝图={len(blueprint_text)}字, "
                 f"全局摘要={len(global_summary_text)}字, "
                 f"角色状态={len(character_state_text)}字")
    chapter_title = chapter_info["chapter_title"]
    chapter_role = chapter_info["chapter_role"]
    chapter_purpose = chapter_info["chapter_purpose"]
    suspense_level = chapter_info["suspense_level"]
    foreshadowing = chapter_info["foreshadowing"]
    plot_twist_level = chapter_info["plot_twist_level"]
    chapter_summary = chapter_info["chapter_summary"]

    # 获取下一章节信息
    next_chapter_number = novel_number + 1
    next_chapter_info = get_chapter_info_from_blueprint(blueprint_text, next_chapter_number)
    next_chapter_title = next_chapter_info.get("chapter_title", "（未命名）")
    next_chapter_role = next_chapter_info.get("chapter_role", "过渡章节")
    next_chapter_purpose = next_chapter_info.get("chapter_purpose", "承上启下")
    next_chapter_suspense = next_chapter_info.get("suspense_level", "中等")
    next_chapter_foreshadow = next_chapter_info.get("foreshadowing", "无特殊伏笔")
    next_chapter_twist = next_chapter_info.get("plot_twist_level", "★☆☆☆☆")
    next_chapter_summary = next_chapter_info.get("chapter_summary", "衔接过渡内容")

    # 创建章节目录
    chapters_dir = os.path.join(filepath, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)

    # 第一章特殊处理
    if novel_number == 1:
        # build_full_architecture 已包含角色动力学
        novel_setting_full = novel_architecture_text

        prompt = prompt_definitions.first_chapter_draft_prompt.format(
            novel_number=novel_number,
            word_number=word_number,
            chapter_title=chapter_title,
            chapter_role=chapter_role,
            chapter_purpose=chapter_purpose,
            suspense_level=suspense_level,
            foreshadowing=foreshadowing,
            plot_twist_level=plot_twist_level,
            chapter_summary=chapter_summary,
            characters_involved=characters_involved,
            key_items=key_items,
            scene_location=scene_location,
            time_constraint=time_constraint,
            user_guidance=user_guidance,
            novel_setting=novel_setting_full
        )
        # 作者参考库检索（第一章同样适用）
        if enable_author_reference and author_style_name and styles_dir:
            try:
                from embedding_adapters import create_embedding_adapter as _cea
                _emb = _cea(
                    embedding_interface_format,
                    embedding_api_key,
                    embedding_url,
                    embedding_model_name
                )
                author_query = f"{chapter_title} {chapter_role} {chapter_summary}"
                author_ref = get_author_reference_context(
                    embedding_adapter=_emb,
                    query=author_query,
                    style_name=author_style_name,
                    styles_dir=styles_dir,
                    k=4
                )
                if author_ref:
                    ref_block = (
                        f"\n【参考原文写法（来自作者参考库）】\n"
                        f"请参考以下原文片段的叙事节奏和写法，但不要直接复制：\n"
                        f"{author_ref}\n\n"
                    )
                    prompt = ref_block + prompt
                    logging.info(f"[Prompt组成] 第1章 注入作者参考库片段={len(author_ref)}字")
            except Exception as e:
                logging.warning(f"Author reference retrieval failed (ch1): {e}")

        if writing_style:
            style_prefix = f"\n【文风要求】\n请严格模仿以下文风进行创作：\n{writing_style}\n\n"
            prompt = style_prefix + prompt
        if narrative_instruction:
            prompt = f"\n【叙事风格指导-章节层】\n{narrative_instruction}\n\n" + prompt
        return prompt

    # 获取前文内容和摘要
    recent_texts = get_last_n_chapters_text(chapters_dir, novel_number, n=3)
    
    try:
        logging.info("Attempting to generate summary")
        short_summary = summarize_recent_chapters(
            interface_format=interface_format,
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            chapters_text_list=recent_texts,
            novel_number=novel_number,
            chapter_info=chapter_info,
            next_chapter_info=next_chapter_info,
            timeout=timeout
        )
        logging.info("Summary generated successfully")
    except Exception as e:
        logging.error(f"Error in summarize_recent_chapters: {str(e)}")
        short_summary = "（摘要生成失败）"

    # 获取前一章结尾
    previous_excerpt = ""
    for text in reversed(recent_texts):
        if text.strip():
            previous_excerpt = text[-800:] if len(text) > 800 else text
            break

    # 知识库检索和处理
    try:
        # 生成检索关键词
        llm_adapter = create_llm_adapter(
            interface_format=interface_format,
            base_url=base_url,
            model_name=model_name,
            api_key=api_key,
            temperature=0.3,
            max_tokens=max_tokens,
            timeout=timeout
        )
        
        search_prompt = prompt_definitions.knowledge_search_prompt.format(
            chapter_number=novel_number,
            chapter_title=chapter_title,
            characters_involved=characters_involved,
            key_items=key_items,
            scene_location=scene_location,
            chapter_role=chapter_role,
            chapter_purpose=chapter_purpose,
            foreshadowing=foreshadowing,
            short_summary=short_summary,
            user_guidance=user_guidance,
            time_constraint=time_constraint
        )
        
        search_response = invoke_with_cleaning(llm_adapter, search_prompt)
        keyword_groups = parse_search_keywords(search_response)

        # 执行向量检索
        all_contexts = []
        from embedding_adapters import create_embedding_adapter
        embedding_adapter = create_embedding_adapter(
            embedding_interface_format,
            embedding_api_key,
            embedding_url,
            embedding_model_name
        )
        
        store = load_vector_store(embedding_adapter, filepath)
        if store:
            collection_size = store._collection.count()
            actual_k = min(embedding_retrieval_k, max(1, collection_size))
            
            for group in keyword_groups:
                context = get_relevant_context_from_vector_store(
                    embedding_adapter=embedding_adapter,
                    query=group,
                    filepath=filepath,
                    k=actual_k
                )
                if context:
                    if any(kw in group.lower() for kw in ["技法", "手法", "模板"]):
                        all_contexts.append(f"[TECHNIQUE] {context}")
                    elif any(kw in group.lower() for kw in ["设定", "技术", "世界观"]):
                        all_contexts.append(f"[SETTING] {context}")
                    else:
                        all_contexts.append(f"[GENERAL] {context}")

        # 应用内容规则
        processed_contexts = apply_content_rules(all_contexts, novel_number)
        
        # 执行知识过滤
        chapter_info_for_filter = {
            "chapter_number": novel_number,
            "chapter_title": chapter_title,
            "chapter_role": chapter_role,
            "chapter_purpose": chapter_purpose,
            "characters_involved": characters_involved,
            "key_items": key_items,
            "scene_location": scene_location,
            "foreshadowing": foreshadowing,  # 修复拼写错误
            "suspense_level": suspense_level,
            "plot_twist_level": plot_twist_level,
            "chapter_summary": chapter_summary,
            "time_constraint": time_constraint
        }
        
        filtered_context = get_filtered_knowledge_context(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            interface_format=interface_format,
            embedding_adapter=embedding_adapter,
            filepath=filepath,
            chapter_info=chapter_info_for_filter,
            retrieved_texts=processed_contexts,
            max_tokens=max_tokens,
            timeout=timeout
        )
        
    except Exception as e:
        logging.error(f"知识处理流程异常：{str(e)}")
        filtered_context = "（知识库处理失败）"

    logging.info(f"[Prompt组成] 第{novel_number}章 摘要={len(short_summary)}字, "
                 f"前章结尾={len(previous_excerpt)}字, "
                 f"知识过滤={len(filtered_context)}字")

    # 构造世界观注入块
    if inject_world_building:
        world_building_text = read_world_building(filepath)
        if world_building_text.strip():
            world_building_block = f"\n└── 世界观设定：\n    {world_building_text}"
            logging.info(f"[Prompt组成] 第{novel_number}章 注入世界观={len(world_building_text)}字")
        else:
            world_building_block = ""
    else:
        world_building_block = ""

    # 判断是否需要注入开篇引导（续写弧首章或前章不存在）
    opening_guidance = ""
    is_arc_opener = False
    # 检测：前一章文件不存在（续写弧的第一章）
    prev_chapter_file = os.path.join(chapters_dir, f"chapter_{novel_number - 1}.txt")
    if novel_number > 1 and not os.path.exists(prev_chapter_file):
        is_arc_opener = True
    # 检测：章节定位中含有"开篇"、"起始"、"序章"等关键词
    if any(kw in chapter_role for kw in ("开篇", "起始", "新篇", "序章", "开局")):
        is_arc_opener = True

    if is_arc_opener:
        opening_guidance = """\
【新篇章开篇要求】
本章是新故事弧的起点，需要重新建立读者的阅读锚点：

1. 状态重锚——开篇用 1-2 段交代主角当前处境：
   - 距离上一弧过了多久、主角现在在哪、状态如何
   - 通过具体场景（而非旁白概述）呈现，如主角正在做某事
   - 自然带出上一弧遗留的影响（伤疤、新能力、关系变化等）

2. 新冲突植入——前 1/3 篇幅内建立新弧的核心悬念：
   - 出现一个新的异常/事件/人物，打破当前平衡
   - 让读者产生「这次又要面对什么」的期待

3. 新角色/新设定引入——如有新登场角色或新世界观元素：
   - 在行动和互动中展示，避免设定说明文
   - 与已有角色的首次互动要有张力"""
    elif novel_number <= 3:
        opening_guidance = """\
【前三章特别提醒】
当前仍处于故事的建立期，在推进剧情的同时注意：
- 尚未正式出场的主要角色，在出场时用行为和对话建立鲜明的第一印象
- 世界观规则尚未充分展示的部分，通过角色的行为和环境描写自然带出
- 避免所有角色都已经彼此熟悉的写法——如果是初次见面，要有初见的质感"""

    # 返回最终提示词
    prompt = prompt_definitions.next_chapter_draft_prompt.format(
        user_guidance=user_guidance if user_guidance else "无特殊指导",
        global_summary=global_summary_text,
        previous_chapter_excerpt=previous_excerpt,
        character_state=character_state_text,
        short_summary=short_summary,
        novel_number=novel_number,
        chapter_title=chapter_title,
        chapter_role=chapter_role,
        chapter_purpose=chapter_purpose,
        suspense_level=suspense_level,
        foreshadowing=foreshadowing,
        plot_twist_level=plot_twist_level,
        chapter_summary=chapter_summary,
        word_number=word_number,
        characters_involved=characters_involved,
        key_items=key_items,
        scene_location=scene_location,
        time_constraint=time_constraint,
        next_chapter_number=next_chapter_number,
        next_chapter_title=next_chapter_title,
        next_chapter_role=next_chapter_role,
        next_chapter_purpose=next_chapter_purpose,
        next_chapter_suspense_level=next_chapter_suspense,
        next_chapter_foreshadowing=next_chapter_foreshadow,
        next_chapter_plot_twist_level=next_chapter_twist,
        next_chapter_summary=next_chapter_summary,
        filtered_context=filtered_context,
        world_building_block=world_building_block,
        opening_guidance=opening_guidance,
    )
    # 作者参考库检索（绑定到文风，未选择文风时跳过）
    if enable_author_reference and author_style_name and styles_dir:
        try:
            from embedding_adapters import create_embedding_adapter as _cea
            _emb = _cea(
                embedding_interface_format,
                embedding_api_key,
                embedding_url,
                embedding_model_name
            )
            author_query = f"{chapter_title} {chapter_role} {chapter_summary}"
            author_ref = get_author_reference_context(
                embedding_adapter=_emb,
                query=author_query,
                style_name=author_style_name,
                styles_dir=styles_dir,
                k=4
            )
            if author_ref:
                ref_block = (
                    f"\n【参考原文写法（来自作者参考库）】\n"
                    f"请参考以下原文片段的叙事节奏和写法，但不要直接复制：\n"
                    f"{author_ref}\n\n"
                )
                prompt = ref_block + prompt
        except Exception as e:
            logging.warning(f"Author reference retrieval failed: {e}")

    if writing_style:
        style_prefix = f"\n【文风要求】\n请严格模仿以下文风进行创作：\n{writing_style}\n\n"
        prompt = style_prefix + prompt
    if narrative_instruction:
        prompt = f"\n【叙事风格指导-章节层】\n{narrative_instruction}\n\n" + prompt

    prompt_tokens_est = int(len(prompt) * 1.8)
    logging.info(f"[Prompt组成] 第{novel_number}章 最终prompt: "
                 f"总字符={len(prompt)}, 估算tokens≈{prompt_tokens_est}, "
                 f"文风={len(writing_style)}字, 叙事指令={len(narrative_instruction)}字")
    return prompt

def generate_chapter_draft(
    api_key: str,
    base_url: str,
    model_name: str,
    filepath: str,
    novel_number: int,
    word_number: int,
    temperature: float,
    user_guidance: str,
    characters_involved: str,
    key_items: str,
    scene_location: str,
    time_constraint: str,
    embedding_api_key: str,
    embedding_url: str,
    embedding_interface_format: str,
    embedding_model_name: str,
    embedding_retrieval_k: int = 2,
    interface_format: str = "openai",
    max_tokens: int = 2048,
    timeout: int = 600,
    custom_prompt_text: str = None,
    enable_thinking: bool = False,
    thinking_budget: int = 0,
    writing_style: str = "",
    narrative_instruction: str = "",
    enable_author_reference: bool = True,
    inject_world_building: bool = False,
    author_style_name: str = "",
    styles_dir: str = "",
    scene_by_scene: bool = False,
    progress=None,
    enable_streaming: bool = True,
) -> str:
    """
    生成章节草稿，支持自定义提示词。
    progress: 可选的进度回调，传入后启用流式输出，实时显示生成进度。
    """
    if custom_prompt_text is None:
        prompt_text = build_chapter_prompt(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name,
            filepath=filepath,
            novel_number=novel_number,
            word_number=word_number,
            temperature=temperature,
            user_guidance=user_guidance,
            characters_involved=characters_involved,
            key_items=key_items,
            scene_location=scene_location,
            time_constraint=time_constraint,
            embedding_api_key=embedding_api_key,
            embedding_url=embedding_url,
            embedding_interface_format=embedding_interface_format,
            embedding_model_name=embedding_model_name,
            embedding_retrieval_k=embedding_retrieval_k,
            interface_format=interface_format,
            max_tokens=max_tokens,
            timeout=timeout,
            writing_style=writing_style,
            narrative_instruction=narrative_instruction,
            enable_author_reference=enable_author_reference,
            inject_world_building=inject_world_building,
            author_style_name=author_style_name,
            styles_dir=styles_dir,
        )
    else:
        prompt_text = custom_prompt_text
        if writing_style:
            style_prefix = f"\n【文风要求】\n请严格模仿以下文风进行创作：\n{writing_style}\n\n"
            prompt_text = style_prefix + prompt_text
        if narrative_instruction:
            prompt_text = f"\n【叙事风格指导-章节层】\n{narrative_instruction}\n\n" + prompt_text

    chapters_dir = os.path.join(filepath, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)

    # ── 按场景分段生成模式 ──
    if scene_by_scene:
        outline_file = os.path.join(filepath, "Novel_detailed_outline.txt")
        outline_text = read_file(outline_file) if os.path.exists(outline_file) else ""
        chapter_outline = ""
        if outline_text.strip():
            from novel_generator.detailed_outline import get_chapter_outline
            chapter_outline = get_chapter_outline(outline_text, novel_number)
        if chapter_outline:
            scenes = parse_outline_scenes(chapter_outline)
            if len(scenes) > 1:
                logging.info(f"[Draft] Chapter {novel_number}: 进入按场景分段生成模式 ({len(scenes)} 个场景)")
                llm_adapter = create_llm_adapter(
                    interface_format=interface_format,
                    base_url=base_url,
                    model_name=model_name,
                    api_key=api_key,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    timeout=timeout,
                    enable_thinking=enable_thinking,
                    thinking_budget=thinking_budget
                )
                return generate_chapter_by_scenes(
                    filepath=filepath,
                    novel_number=novel_number,
                    word_number=word_number,
                    chapter_outline=chapter_outline,
                    scenes=scenes,
                    build_prompt_kwargs={},
                    llm_adapter=llm_adapter,
                    writing_style=writing_style,
                    narrative_instruction=narrative_instruction,
                    progress=progress,
                )
            else:
                logging.info(f"[Draft] Chapter {novel_number}: 细纲仅1个场景，回退到整章生成")
        else:
            logging.info(f"[Draft] Chapter {novel_number}: 无细纲，回退到整章生成")

    logging.info(f"[Draft] Chapter {novel_number}: prompt构建完成 (长度={len(prompt_text)}), 正在创建LLM adapter...")
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        enable_thinking=enable_thinking,
        thinking_budget=thinking_budget
    )

    logging.info(f"[Draft] Chapter {novel_number}: LLM adapter就绪, 正在调用LLM (model={model_name}, timeout={timeout}s)...")
    chapter_content = invoke_with_cleaning(llm_adapter, prompt_text, progress=progress,
                                              enable_streaming=enable_streaming)
    logging.info(f"[Draft] Chapter {novel_number}: LLM返回, 内容长度={len(chapter_content) if chapter_content else 0}")
    if not chapter_content.strip():
        logging.warning("Generated chapter draft is empty.")
    chapter_file = os.path.join(chapters_dir, f"chapter_{novel_number}.txt")
    clear_file_content(chapter_file)
    save_string_to_txt(chapter_content, chapter_file)
    logging.info(f"[Draft] Chapter {novel_number} generated as a draft.")
    return chapter_content


# ============================================================
# 按场景分段生成
# ============================================================

def parse_outline_scenes(chapter_outline: str) -> list:
    """
    解析章节细纲为场景列表。
    返回 [{"index": 1, "text": "场景完整文本", "is_intense": bool}, ...]
    is_intense 表示该场景是否为高强度场景（情感高潮、关键转折等需要充分展开的）。
    """
    if not chapter_outline or not chapter_outline.strip():
        return []

    scenes = []
    pattern = r'(?=(?:^|\n)\s*场景\s*(\d+)\s*[（(：:])'
    parts = re.split(pattern, chapter_outline, flags=re.MULTILINE)

    header = parts[0] if parts else ""

    i = 1
    while i < len(parts) - 1:
        scene_num = int(parts[i])
        scene_text = parts[i + 1].strip()
        is_intense = _detect_intense_scene(scene_text, header)
        scenes.append({
            "index": scene_num,
            "text": f"场景{scene_num}{scene_text}",
            "is_intense": is_intense,
        })
        i += 2

    if not scenes:
        is_intense = _detect_intense_scene(chapter_outline, "")
        scenes.append({
            "index": 1,
            "text": chapter_outline,
            "is_intense": is_intense,
        })

    logging.info(f"[SceneParse] 解析出 {len(scenes)} 个场景: "
                 f"{[(s['index'], '高强度' if s['is_intense'] else '普通') for s in scenes]}")
    return scenes


def _detect_intense_scene(text: str, header: str) -> bool:
    """判断场景文本是否为高强度场景（需要充分展开）"""
    combined = text + "\n" + header
    # 检查强度星级标记 ★★★及以上
    star_match = re.search(r'[强度|张力].*?([★]{3,})', combined)
    if star_match:
        return True
    # 关键词检测
    intense_keywords = [
        '高潮', '冲突爆发', '关键转折', '决战', '对决',
        '亲密', '情感爆发', '揭示', '反转', '决断',
    ]
    keyword_count = sum(1 for kw in intense_keywords if kw in text)
    return keyword_count >= 2


def generate_chapter_by_scenes(
    filepath: str,
    novel_number: int,
    word_number: int,
    chapter_outline: str,
    scenes: list,
    build_prompt_kwargs: dict,
    llm_adapter,
    writing_style: str = "",
    narrative_instruction: str = "",
    progress=None,
) -> str:
    """
    按场景逐段生成章节内容。
    - 普通场景：简练清晰，推进高效
    - 高强度场景：浓墨重彩，感官与心理充分
    每个场景生成时会带上前面已生成的场景作为上下文。
    """
    chapters_dir = os.path.join(filepath, "chapters")
    previous_excerpt = ""
    for c in range(max(1, novel_number - 1), novel_number):
        chap_file = os.path.join(chapters_dir, f"chapter_{c}.txt")
        if os.path.exists(chap_file):
            text = read_file(chap_file).strip()
            if text:
                previous_excerpt = text[-600:] if len(text) > 600 else text

    global_summary_file = os.path.join(filepath, "global_summary.txt")
    global_summary = read_file(global_summary_file).strip() if os.path.exists(global_summary_file) else ""
    character_state_file = os.path.join(filepath, "character_state.txt")
    character_state = read_file(character_state_file).strip() if os.path.exists(character_state_file) else ""

    total_scenes = len(scenes)
    generated_parts = []
    avg_words = word_number // total_scenes

    for idx, scene in enumerate(scenes):
        scene_num = scene["index"]
        is_intense = scene["is_intense"]
        scene_outline = scene["text"]

        if progress:
            progress(0.1 + 0.8 * idx / total_scenes,
                     desc=f"生成场景 {scene_num}/{total_scenes}（{'高强度' if is_intense else '普通'}）...")

        previously_generated = "\n\n".join(generated_parts) if generated_parts else ""

        if is_intense:
            scene_words = int(avg_words * 1.5)
            style_directive = (
                "【本场景写作要求：高强度场景】\n"
                "- 浓墨重彩，充分展开感官细节（视觉、触觉、听觉、嗅觉）\n"
                "- 动作描写具体连贯，不要用省略号或概括性语句跳过\n"
                "- 角色的反应、心理变化要具体呈现\n"
                "- 节奏放慢，给予每个阶段充分的篇幅\n"
                "- 保持角色性格一致，心理与行为统一\n"
            )
        else:
            scene_words = max(avg_words, 500)
            style_directive = (
                "【本场景写作要求：普通场景】\n"
                "- 文字简练清晰，推进高效，不堆砌环境和心理描写\n"
                "- 对话精炼有力，推动剧情\n"
                "- 动作和事件描述直接到位，不过度渲染\n"
                "- 保持节奏紧凑\n"
            )

        prompt = f"""你是一位专业小说作家，正在为第{novel_number}章的第{scene_num}个场景撰写正文。

===== 本章细纲概览 =====
{chapter_outline}

===== 当前场景细纲 =====
{scene_outline}

{style_directive}

===== 上下文信息 =====
前文摘要：{global_summary[:1000] if global_summary else '（无）'}
角色状态：{character_state[:1000] if character_state else '（无）'}
"""
        if previously_generated:
            tail = previously_generated[-1500:] if len(previously_generated) > 1500 else previously_generated
            prompt += f"\n本章已生成的前序场景（紧接着写，保持连贯）：\n...{tail}\n"
        elif previous_excerpt:
            prompt += f"\n上一章结尾：\n...{previous_excerpt}\n"

        prompt += f"""
===== 输出要求 =====
- 本场景目标字数约 {scene_words} 字
- 直接输出场景正文，不要输出标题、场景编号或任何说明
- 紧接前文继续写，保持文风和叙事视角一致
- 仅输出本场景内容，不要写到下一个场景

请开始撰写："""

        if writing_style:
            prompt = f"【文风要求】\n{writing_style}\n\n{prompt}"
        if narrative_instruction:
            prompt = f"【叙事风格指导】\n{narrative_instruction}\n\n{prompt}"

        scene_content = invoke_with_cleaning(llm_adapter, prompt, progress=None, enable_streaming=True)

        if scene_content and scene_content.strip():
            generated_parts.append(scene_content.strip())
            logging.info(f"[SceneGen] 第{novel_number}章 场景{scene_num} "
                         f"({'高强度' if is_intense else '普通'}): {len(scene_content)}字")
        else:
            logging.warning(f"[SceneGen] 第{novel_number}章 场景{scene_num} 生成为空")

    full_chapter = "\n\n".join(generated_parts)

    if progress:
        progress(0.95, desc="场景拼合完成，保存中...")

    chapters_dir = os.path.join(filepath, "chapters")
    os.makedirs(chapters_dir, exist_ok=True)
    chapter_file = os.path.join(chapters_dir, f"chapter_{novel_number}.txt")
    clear_file_content(chapter_file)
    save_string_to_txt(full_chapter, chapter_file)

    logging.info(f"[SceneGen] 第{novel_number}章 共{total_scenes}个场景, 总计{len(full_chapter)}字")
    return full_chapter
