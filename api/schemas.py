# api/schemas.py
# -*- coding: utf-8 -*-
"""Pydantic 请求/响应模型"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


# ── LLM / Embedding 配置 ──────────────────────────────────────────────────────

class LLMConfigCreate(BaseModel):
    config_name: str
    api_key: str = ""
    base_url: str = ""
    interface_format: str = "OpenAI"
    model_name: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 600
    enable_thinking: bool = False
    thinking_budget: int = 0
    enable_streaming: bool = True


class EmbeddingConfigCreate(BaseModel):
    config_name: str
    interface_format: str = "OpenAI"
    api_key: str = ""
    base_url: str = ""
    model_name: str = ""
    retrieval_k: int = 4


class TestLLMConfigRequest(BaseModel):
    interface_format: str = "OpenAI"
    api_key: str = ""
    base_url: str = ""
    model_name: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 600


class TestEmbeddingConfigRequest(BaseModel):
    interface_format: str = "OpenAI"
    api_key: str = ""
    base_url: str = ""
    model_name: str = ""


# ── 项目 ──────────────────────────────────────────────────────────────────────

class ProjectCreate(BaseModel):
    name: str
    filepath: str = ""


class ProjectUpdate(BaseModel):
    topic: str = ""
    genre: str = "玄幻"
    num_chapters: int = 10
    word_number: int = 3000
    filepath: Optional[str] = None
    user_guidance: str = ""
    xp_type: str = ""
    xp_selected_presets: Optional[List[str]] = None
    # 持久化到 project_config.json 的扩展字段
    llm_config_name: str = ""
    emb_config_name: str = ""
    arch_style: str = ""
    bp_style: str = ""
    ch_style: str = ""
    ch_narrative_style: str = ""
    expand_style: str = ""
    expand_narrative_style: str = ""
    cont_style: str = ""
    cont_xp_type: str = ""
    # 分步生成中间内容（断点续作）
    step_seed_text: str = ""
    step_char_text: str = ""
    step_char_state_text: str = ""
    step_world_text: str = ""
    step_plot_text: str = ""
    continue_guidance: str = ""
    cont_new_chapters: int = 5
    cont_step_chars_text: str = ""
    cont_step_arcs_text: str = ""
    cont_step_char_state_text: str = ""


# ── 生成请求 ──────────────────────────────────────────────────────────────────

class GenerateArchRequest(BaseModel):
    llm_config_name: str
    topic: str
    genre: str = "玄幻"
    num_chapters: int = 10
    word_number: int = 3000
    filepath: str = "./output"
    user_guidance: str = ""
    arch_style_name: Optional[str] = None
    xp_type: str = ""
    num_characters: str = "3-6"


class GenerateArchStepRequest(BaseModel):
    llm_config_name: str
    topic: str = ""
    genre: str = "玄幻"
    num_chapters: int = 10
    word_number: int = 3000
    filepath: str = "./output"
    step_guidance: str = ""
    global_guidance: str = ""
    arch_style_name: Optional[str] = None
    xp_type: str = ""
    num_characters: str = "3-6"
    # for characters/world/plot steps
    seed_text: str = ""
    char_text: str = ""
    world_text: str = ""


class SupplementCharactersRequest(BaseModel):
    llm_config_name: str
    existing_characters: str
    supplement_guidance: str
    num_characters: str = "1-2"
    core_seed: str = ""
    world_building: str = ""
    filepath: str = ""


class GenerateCharStateRequest(BaseModel):
    llm_config_name: str
    char_dynamics_text: str


class AssembleArchRequest(BaseModel):
    filepath: str
    topic: str
    genre: str
    num_chapters: int
    word_number: int
    seed_text: str
    char_text: str
    char_state_text: str
    world_text: str
    plot_text: str


class ContinueArchRequest(BaseModel):
    llm_config_name: str
    filepath: str
    new_chapters: int = 5
    user_guidance: str = ""
    arch_style_name: Optional[str] = None
    xp_type: str = ""
    num_characters: str = "1-3"


class ContinueArchStepRequest(BaseModel):
    llm_config_name: str
    filepath: str
    new_chapters: int = 5
    user_guidance: str = ""
    step_guidance: str = ""
    new_characters_text: str = ""
    arch_style_name: Optional[str] = None
    xp_type: str = ""
    num_characters: str = "1-3"
    continuation_seed: str = ""
    world_expansion: str = ""


class AssembleContinuationRequest(BaseModel):
    filepath: str
    new_chapters: int = 5
    new_characters_text: str
    new_arcs_text: str
    new_char_state_text: str
    continuation_seed: str = ""
    world_expansion: str = ""


class CompressContextRequest(BaseModel):
    llm_config_name: str
    filepath: str
    include_world_building: bool = True


class GenerateBlueprintRequest(BaseModel):
    llm_config_name: str
    filepath: str
    num_chapters: int = 10
    user_guidance: str = ""
    bp_style_name: Optional[str] = None
    xp_type: str = ""


class GenerateChapterRequest(BaseModel):
    llm_config_name: str
    emb_config_name: str
    filepath: str
    chapter_num: int
    word_number: int = 3000
    user_guidance: str = ""
    characters_involved: str = ""
    key_items: str = ""
    scene_location: str = ""
    time_constraint: str = ""
    style_name: Optional[str] = None
    narrative_style_name: Optional[str] = None
    xp_type: str = ""
    inject_world_building: bool = False
    scene_by_scene: bool = False  # 按场景分段生成（需有细纲）


class FinalizeChapterRequest(BaseModel):
    llm_config_name: str
    emb_config_name: str
    filepath: str
    chapter_num: int
    word_number: int = 3000


class ExpandScenesRequest(BaseModel):
    llm_config_name: str
    filepath: str
    chapter_num: int
    style_name: Optional[str] = None
    narrative_style_name: Optional[str] = None
    xp_type: str = ""
    polish_guidance: str = ""
    polish_mode: str = "enhance"  # enhance / sensual / modify / add
    include_outline: bool = False
    include_character_state: bool = False
    include_summary: bool = False
    include_world_building: bool = False


class BatchGenerateRequest(BaseModel):
    llm_config_name: str
    emb_config_name: str
    filepath: str
    word_number: int = 3000
    user_guidance: str = ""
    style_name: Optional[str] = None
    narrative_style_name: Optional[str] = None
    xp_type: str = ""
    inject_world_building: bool = False


class SaveChapterRequest(BaseModel):
    content: str


class SaveContentRequest(BaseModel):
    content: str
    filepath: str = "./output"


# ── 文风 ──────────────────────────────────────────────────────────────────────

class StyleAnalyzeRequest(BaseModel):
    llm_config_name: str
    sample_text: str
    style_name: str
    unlock: bool = False


class StyleAnalyzeDNARequest(BaseModel):
    llm_config_name: str
    sample_text: str
    style_name: str
    unlock: bool = False


class StyleMergeRequest(BaseModel):
    llm_config_name: str
    selected_styles: List[str]
    merge_name: str
    user_preference: str = ""
    unlock: bool = False


class StyleSaveRequest(BaseModel):
    analysis_result: str
    style_instruction: str
    source_sample: Optional[str] = None
    calibration_reference: Optional[str] = None
    narrative_for_architecture: Optional[str] = None
    narrative_for_blueprint: Optional[str] = None
    narrative_for_chapter: Optional[str] = None


class StyleCalibrateRequest(BaseModel):
    llm_config_name: str
    style_name: str
    max_iterations: int = 5
    unlock: bool = False


# ── 预设 ──────────────────────────────────────────────────────────────────────

class PresetCreate(BaseModel):
    name: str
    description: str = ""


class PromptUpdate(BaseModel):
    content: str


# ── 一致性检查 ────────────────────────────────────────────────────────────────

class ConsistencyCheckRequest(BaseModel):
    llm_config_name: str
    filepath: str
    chapter_num: int


# ── SSE 事件 ──────────────────────────────────────────────────────────────────

class HumanizerRequest(BaseModel):
    llm_config_name: str
    filepath: str
    chapter_num: int
    enable_r8: bool = False
    user_focus: str = ""
    depth: str = "standard"  # quick / standard / deep


class BatchHumanizerRequest(BaseModel):
    llm_config_name: str
    filepath: str
    start_chapter: int
    end_chapter: int
    enable_r8: bool = False
    user_focus: str = ""
    depth: str = "standard"


class GenerateDetailedOutlineRequest(BaseModel):
    llm_config_name: str
    filepath: str
    start_chapter: int
    end_chapter: int
    num_chapters: int = 10
    user_guidance: str = ""
    xp_type: str = ""
    outline_mode: str = "concise"  # concise / detailed


class ReviseStepRequest(BaseModel):
    llm_config_name: str
    original_content: str
    revision_guidance: str
    step_type: str = ""  # core_seed / characters / char_state / world / plot
    filepath: str = ""
    include_core_seed: bool = False
    include_characters: bool = False
    include_world_building: bool = False
    include_plot: bool = False


class BrainstormMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class BrainstormChatRequest(BaseModel):
    llm_config_name: str
    filepath: str
    messages: List[BrainstormMessage]
    include_core_seed: bool = True
    include_characters: bool = True
    include_world_building: bool = True
    include_plot: bool = True
    include_blueprint: bool = False
    include_character_state: bool = False
    extra_context: str = ""
    discussion_mode: str = "advisor"  # advisor / casual / brainstorm / devil / roleplay


class SSEEvent(BaseModel):
    type: str  # progress | result | error | done
    message: str = ""
    content: str = ""
