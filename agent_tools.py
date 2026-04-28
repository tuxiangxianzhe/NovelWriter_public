# agent_tools.py
# -*- coding: utf-8 -*-
"""
NovelWriter Agent Tool Schema 定义
将 NovelWriter 的核心 API 封装为 LLM function calling / tool use 的工具定义。
支持 OpenAI、Claude、Gemini 等主流 LLM 的 tool use 格式。
"""

AGENT_TOOLS = [
    # ═══════════════════════════════════════════════════
    # 项目管理
    # ═══════════════════════════════════════════════════
    {
        "name": "list_projects",
        "description": "列出所有小说项目及当前激活的项目名",
        "api": {"method": "GET", "path": "/projects"},
        "parameters": {},
        "streaming": False,
    },
    {
        "name": "create_project",
        "description": "创建一个新的小说项目",
        "api": {"method": "POST", "path": "/projects"},
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "项目名称"},
                "filepath": {"type": "string", "description": "项目文件路径，如 ./output/我的小说"},
            },
            "required": ["name"],
        },
        "streaming": False,
    },
    {
        "name": "activate_project",
        "description": "切换到指定的小说项目",
        "api": {"method": "POST", "path": "/projects/{name}/activate"},
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "要激活的项目名称"},
            },
            "required": ["name"],
        },
        "streaming": False,
    },
    {
        "name": "update_project",
        "description": "更新项目的元数据（主题、类型、章节数、字数、XP类型等）",
        "api": {"method": "PUT", "path": "/projects/{name}"},
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "项目名称"},
                "topic": {"type": "string", "description": "小说主题/简介"},
                "genre": {"type": "string", "description": "小说类型（如：玄幻、都市、科幻）"},
                "num_chapters": {"type": "integer", "description": "总章节数"},
                "word_number": {"type": "integer", "description": "每章字数"},
                "user_guidance": {"type": "string", "description": "创作指导/要求"},
                "xp_type": {"type": "string", "description": "XP类型/核心玩法描述"},
            },
            "required": ["name"],
        },
        "streaming": False,
    },

    # ═══════════════════════════════════════════════════
    # 架构生成（分步）
    # ═══════════════════════════════════════════════════
    {
        "name": "generate_core_seed",
        "description": "根据主题、类型等信息，生成小说的核心种子（故事核心概念/前提）",
        "api": {"method": "POST", "path": "/generate/architecture/step/core_seed"},
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "小说主题/简介"},
                "genre": {"type": "string", "description": "小说类型"},
                "num_chapters": {"type": "integer", "description": "总章节数"},
                "word_number": {"type": "integer", "description": "每章字数"},
                "step_guidance": {"type": "string", "description": "本步骤的额外指导"},
                "xp_type": {"type": "string", "description": "XP类型/核心玩法"},
            },
            "required": ["topic", "genre"],
        },
        "streaming": True,
    },
    {
        "name": "generate_characters",
        "description": "基于核心种子，生成角色动力学（角色设定、关系网）",
        "api": {"method": "POST", "path": "/generate/architecture/step/characters"},
        "parameters": {
            "type": "object",
            "properties": {
                "seed_text": {"type": "string", "description": "核心种子文本"},
                "step_guidance": {"type": "string", "description": "角色设计的额外指导"},
                "num_characters": {"type": "string", "description": "角色数量，如 '3-5'"},
                "xp_type": {"type": "string", "description": "XP类型"},
            },
            "required": ["seed_text"],
        },
        "streaming": True,
    },
    {
        "name": "generate_world_building",
        "description": "基于核心种子和角色，生成世界观设定",
        "api": {"method": "POST", "path": "/generate/architecture/step/world"},
        "parameters": {
            "type": "object",
            "properties": {
                "seed_text": {"type": "string", "description": "核心种子文本"},
                "char_text": {"type": "string", "description": "角色动力学文本（可选，用于参考）"},
                "step_guidance": {"type": "string", "description": "世界观设计的额外指导"},
                "xp_type": {"type": "string", "description": "XP类型"},
            },
            "required": ["seed_text"],
        },
        "streaming": True,
    },
    {
        "name": "generate_plot",
        "description": "基于核心种子、角色、世界观，生成情节架构",
        "api": {"method": "POST", "path": "/generate/architecture/step/plot"},
        "parameters": {
            "type": "object",
            "properties": {
                "seed_text": {"type": "string", "description": "核心种子文本"},
                "char_text": {"type": "string", "description": "角色动力学文本"},
                "world_text": {"type": "string", "description": "世界观文本"},
                "step_guidance": {"type": "string", "description": "情节设计的额外指导"},
                "num_chapters": {"type": "integer", "description": "总章节数"},
                "xp_type": {"type": "string", "description": "XP类型"},
            },
            "required": ["seed_text", "char_text", "world_text"],
        },
        "streaming": True,
    },
    {
        "name": "generate_char_state",
        "description": "基于角色动力学，生成角色初始状态（树状结构的角色属性）",
        "api": {"method": "POST", "path": "/generate/architecture/step/char_state"},
        "parameters": {
            "type": "object",
            "properties": {
                "char_dynamics_text": {"type": "string", "description": "角色动力学文本"},
            },
            "required": ["char_dynamics_text"],
        },
        "streaming": True,
    },
    {
        "name": "assemble_architecture",
        "description": "将分步生成的各组件（种子、角色、世界观、情节、角色状态）组装为完整架构并保存",
        "api": {"method": "POST", "path": "/generate/architecture/assemble"},
        "parameters": {
            "type": "object",
            "properties": {
                "seed_text": {"type": "string", "description": "核心种子文本"},
                "char_text": {"type": "string", "description": "角色动力学文本"},
                "char_state_text": {"type": "string", "description": "角色状态文本"},
                "world_text": {"type": "string", "description": "世界观文本"},
                "plot_text": {"type": "string", "description": "情节架构文本"},
                "topic": {"type": "string", "description": "主题"},
                "genre": {"type": "string", "description": "类型"},
                "num_chapters": {"type": "integer", "description": "章节数"},
                "word_number": {"type": "integer", "description": "每章字数"},
            },
            "required": ["seed_text", "char_text", "world_text", "plot_text"],
        },
        "streaming": False,
    },

    # ═══════════════════════════════════════════════════
    # 修订
    # ═══════════════════════════════════════════════════
    {
        "name": "revise_content",
        "description": "根据用户的修改建议，修订架构中的某个组件（核心种子/角色/世界观/情节/角色状态）",
        "api": {"method": "POST", "path": "/generate/architecture/step/revise"},
        "parameters": {
            "type": "object",
            "properties": {
                "original_content": {"type": "string", "description": "待修订的原始内容"},
                "revision_guidance": {"type": "string", "description": "用户的修改建议"},
                "step_type": {
                    "type": "string",
                    "description": "修订的组件类型",
                    "enum": ["core_seed", "characters", "char_state", "world", "plot"],
                },
                "include_core_seed": {"type": "boolean", "description": "是否注入核心种子作为参考"},
                "include_characters": {"type": "boolean", "description": "是否注入角色信息作为参考"},
                "include_world_building": {"type": "boolean", "description": "是否注入世界观作为参考"},
                "include_plot": {"type": "boolean", "description": "是否注入情节架构作为参考"},
            },
            "required": ["original_content", "revision_guidance", "step_type"],
        },
        "streaming": True,
    },

    # ═══════════════════════════════════════════════════
    # 蓝图与细纲
    # ═══════════════════════════════════════════════════
    {
        "name": "generate_blueprint",
        "description": "基于完整架构，生成章节蓝图（每章的定位、悬念、伏笔、强度等）",
        "api": {"method": "POST", "path": "/generate/blueprint"},
        "parameters": {
            "type": "object",
            "properties": {
                "num_chapters": {"type": "integer", "description": "总章节数"},
                "user_guidance": {"type": "string", "description": "蓝图生成的额外指导"},
                "xp_type": {"type": "string", "description": "XP类型"},
            },
            "required": [],
        },
        "streaming": True,
    },
    {
        "name": "generate_detailed_outline",
        "description": "基于架构和蓝图，生成指定章节范围的详细细纲（场景分解、节奏、对话要点）",
        "api": {"method": "POST", "path": "/generate/detailed_outline"},
        "parameters": {
            "type": "object",
            "properties": {
                "start_chapter": {"type": "integer", "description": "起始章节号"},
                "end_chapter": {"type": "integer", "description": "结束章节号"},
                "num_chapters": {"type": "integer", "description": "总章节数"},
                "user_guidance": {"type": "string", "description": "细纲生成的额外指导"},
                "xp_type": {"type": "string", "description": "XP类型"},
                "outline_mode": {
                    "type": "string",
                    "description": "细纲模式：concise(精简1000-2000字/章) 或 detailed(详细3000-5000字/章)",
                    "enum": ["concise", "detailed"],
                },
            },
            "required": ["start_chapter", "end_chapter"],
        },
        "streaming": True,
    },

    # ═══════════════════════════════════════════════════
    # 章节生成与编辑
    # ═══════════════════════════════════════════════════
    {
        "name": "generate_chapter",
        "description": "生成指定章节的正文草稿",
        "api": {"method": "POST", "path": "/generate/chapter"},
        "parameters": {
            "type": "object",
            "properties": {
                "chapter_num": {"type": "integer", "description": "要生成的章节号"},
                "word_number": {"type": "integer", "description": "目标字数"},
                "user_guidance": {"type": "string", "description": "本章的创作指导"},
                "characters_involved": {"type": "string", "description": "本章涉及的角色（逗号分隔）"},
                "key_items": {"type": "string", "description": "关键道具"},
                "scene_location": {"type": "string", "description": "场景地点"},
                "time_constraint": {"type": "string", "description": "时间压力"},
                "style_name": {"type": "string", "description": "文风样式名称"},
                "narrative_style_name": {"type": "string", "description": "叙事DNA样式名称"},
                "xp_type": {"type": "string", "description": "XP类型"},
                "inject_world_building": {"type": "boolean", "description": "是否注入世界观"},
                "scene_by_scene": {"type": "boolean", "description": "是否按场景分段生成（需有细纲）"},
            },
            "required": ["chapter_num"],
        },
        "streaming": True,
    },
    {
        "name": "get_chapter",
        "description": "读取已保存的章节内容",
        "api": {"method": "GET", "path": "/generate/chapter/{num}"},
        "parameters": {
            "type": "object",
            "properties": {
                "num": {"type": "integer", "description": "章节号"},
            },
            "required": ["num"],
        },
        "streaming": False,
    },
    {
        "name": "save_chapter",
        "description": "保存或覆盖章节内容",
        "api": {"method": "PUT", "path": "/generate/chapter/{num}"},
        "parameters": {
            "type": "object",
            "properties": {
                "num": {"type": "integer", "description": "章节号"},
                "content": {"type": "string", "description": "章节正文内容"},
            },
            "required": ["num", "content"],
        },
        "streaming": False,
    },
    {
        "name": "list_chapters",
        "description": "列出所有已生成的章节及其状态",
        "api": {"method": "GET", "path": "/generate/chapters"},
        "parameters": {},
        "streaming": False,
    },

    # ═══════════════════════════════════════════════════
    # 润色与精炼
    # ═══════════════════════════════════════════════════
    {
        "name": "polish_chapter",
        "description": "对章节进行润色（通用润色/修改剧情/增加内容）",
        "api": {"method": "POST", "path": "/generate/expand"},
        "parameters": {
            "type": "object",
            "properties": {
                "chapter_num": {"type": "integer", "description": "章节号"},
                "polish_guidance": {"type": "string", "description": "润色建议（描述要改什么）"},
                "polish_mode": {
                    "type": "string",
                    "description": "润色模式",
                    "enum": ["enhance", "modify", "add"],
                },
                "style_name": {"type": "string", "description": "文风样式名称"},
                "include_outline": {"type": "boolean", "description": "是否注入细纲"},
                "include_character_state": {"type": "boolean", "description": "是否注入角色状态"},
                "include_summary": {"type": "boolean", "description": "是否注入前文摘要"},
                "include_world_building": {"type": "boolean", "description": "是否注入世界观"},
            },
            "required": ["chapter_num"],
        },
        "streaming": True,
    },
    {
        "name": "finalize_chapter",
        "description": "精炼定稿章节（更新前文摘要、角色状态、向量库）",
        "api": {"method": "POST", "path": "/generate/finalize"},
        "parameters": {
            "type": "object",
            "properties": {
                "chapter_num": {"type": "integer", "description": "章节号"},
                "word_number": {"type": "integer", "description": "目标字数"},
            },
            "required": ["chapter_num"],
        },
        "streaming": True,
    },

    # ═══════════════════════════════════════════════════
    # 文件读写（通用）
    # ═══════════════════════════════════════════════════
    {
        "name": "read_file",
        "description": "读取项目中的任意文件内容（如架构、蓝图、角色状态、细纲等）",
        "api": {"method": "GET", "path": "/files/content"},
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "文件路径（相对于项目目录），如：core_seed.txt, Novel_directory.txt, character_state.txt, chapters/chapter_1.txt",
                },
            },
            "required": ["path"],
        },
        "streaming": False,
    },
    {
        "name": "save_file",
        "description": "保存内容到项目中的任意文件",
        "api": {"method": "PUT", "path": "/files/content"},
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径（相对于项目目录）"},
                "content": {"type": "string", "description": "要保存的内容"},
            },
            "required": ["path", "content"],
        },
        "streaming": False,
    },
    {
        "name": "list_files",
        "description": "列出项目目录下的所有文件",
        "api": {"method": "GET", "path": "/files"},
        "parameters": {},
        "streaming": False,
    },

    # ═══════════════════════════════════════════════════
    # 架构组件保存
    # ═══════════════════════════════════════════════════
    {
        "name": "save_architecture_component",
        "description": "保存架构的某个组件（核心种子/角色动力学/世界观/情节架构/角色状态）",
        "api": {"method": "PUT", "path": "/generate/architecture/component/{component_name}"},
        "parameters": {
            "type": "object",
            "properties": {
                "component_name": {
                    "type": "string",
                    "description": "组件名称",
                    "enum": ["core_seed", "character_dynamics", "world_building", "plot_architecture", "character_state"],
                },
                "content": {"type": "string", "description": "组件内容"},
            },
            "required": ["component_name", "content"],
        },
        "streaming": False,
    },
    {
        "name": "save_blueprint",
        "description": "保存章节蓝图",
        "api": {"method": "PUT", "path": "/generate/blueprint"},
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "蓝图内容"},
            },
            "required": ["content"],
        },
        "streaming": False,
    },
    {
        "name": "save_detailed_outline",
        "description": "保存章节细纲",
        "api": {"method": "PUT", "path": "/generate/detailed_outline"},
        "parameters": {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "细纲内容"},
            },
            "required": ["content"],
        },
        "streaming": False,
    },

    # ═══════════════════════════════════════════════════
    # 导出
    # ═══════════════════════════════════════════════════
    {
        "name": "export_novel",
        "description": "将所有章节合并导出为完整小说文本",
        "api": {"method": "GET", "path": "/generate/export"},
        "parameters": {},
        "streaming": False,
    },
]


def get_tools_for_openai() -> list:
    """转换为 OpenAI function calling 格式"""
    tools = []
    for t in AGENT_TOOLS:
        tool = {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
            },
        }
        if t.get("parameters") and t["parameters"].get("properties"):
            tool["function"]["parameters"] = t["parameters"]
        else:
            tool["function"]["parameters"] = {"type": "object", "properties": {}}
        tools.append(tool)
    return tools


def get_tools_for_claude() -> list:
    """转换为 Claude tool use 格式"""
    tools = []
    for t in AGENT_TOOLS:
        tool = {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t.get("parameters", {"type": "object", "properties": {}}),
        }
        if not tool["input_schema"].get("properties"):
            tool["input_schema"] = {"type": "object", "properties": {}}
        tools.append(tool)
    return tools


def get_tool_by_name(name: str) -> dict | None:
    """根据工具名获取工具定义"""
    for t in AGENT_TOOLS:
        if t["name"] == name:
            return t
    return None


# 工具分类索引（方便 Agent system prompt 中按类别介绍）
TOOL_CATEGORIES = {
    "项目管理": ["list_projects", "create_project", "activate_project", "update_project"],
    "架构生成": ["generate_core_seed", "generate_characters", "generate_world_building", "generate_plot", "generate_char_state", "assemble_architecture"],
    "内容修订": ["revise_content"],
    "蓝图与细纲": ["generate_blueprint", "generate_detailed_outline"],
    "章节生成": ["generate_chapter", "get_chapter", "save_chapter", "list_chapters"],
    "润色与精炼": ["polish_chapter", "finalize_chapter"],
    "文件读写": ["read_file", "save_file", "list_files"],
    "架构保存": ["save_architecture_component", "save_blueprint", "save_detailed_outline"],
    "导出": ["export_novel"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# 工具执行器：通过 HTTP 调用 NovelWriter API
# ═══════════════════════════════════════════════════════════════════════════════

import requests
import json
import urllib.parse
import logging

_logger = logging.getLogger(__name__)


class ToolExecutor:
    """
    工具执行器：根据工具名和参数，调用 NovelWriter API 并返回结果。
    支持普通 JSON 接口和 SSE 流式接口。
    """

    def __init__(self, api_base: str = "http://localhost:7860/api", default_params: dict = None):
        """
        Args:
            api_base: NovelWriter API 基础地址
            default_params: 默认参数（如 llm_config_name, filepath 等），工具调用时自动补全
        """
        self.api_base = api_base.rstrip("/")
        self.default_params = default_params or {}

    def update_defaults(self, **kwargs):
        """更新默认参数"""
        self.default_params.update(kwargs)

    def execute(self, tool_name: str, params: dict = None) -> dict:
        """
        执行工具调用。

        Args:
            tool_name: 工具名（如 "generate_core_seed"）
            params: 工具参数

        Returns:
            {"success": True/False, "data": ..., "error": ...}
        """
        tool = get_tool_by_name(tool_name)
        if not tool:
            return {"success": False, "error": f"未知工具: {tool_name}"}

        params = params or {}
        # 用默认参数补全缺失的字段
        merged = {**self.default_params, **params}

        api_info = tool["api"]
        method = api_info["method"].upper()
        path = api_info["path"]

        # 处理路径参数（如 /generate/chapter/{num}）
        for key in list(merged.keys()):
            placeholder = "{" + key + "}"
            if placeholder in path:
                path = path.replace(placeholder, urllib.parse.quote(str(merged.pop(key))))

        # 处理组件名等路径参数
        for key in ["component_name", "name"]:
            placeholder = "{" + key + "}"
            if placeholder in path:
                if key in merged:
                    path = path.replace(placeholder, urllib.parse.quote(str(merged.pop(key))))

        url = f"{self.api_base}{path}"

        # filepath 需要 URL 编码（中文路径）
        if "filepath" in merged and method == "GET":
            merged["filepath"] = merged["filepath"]  # requests 会自动编码 query params

        try:
            if tool.get("streaming"):
                return self._execute_sse(method, url, merged)
            else:
                return self._execute_json(method, url, merged)
        except Exception as e:
            _logger.error(f"工具调用失败 [{tool_name}]: {e}")
            return {"success": False, "error": str(e)}

    def _execute_json(self, method: str, url: str, params: dict) -> dict:
        """执行普通 JSON 请求"""
        if method == "GET":
            resp = requests.get(url, params=params, timeout=30)
        elif method == "POST":
            resp = requests.post(url, json=params, timeout=30)
        elif method == "PUT":
            resp = requests.put(url, json=params, timeout=30)
        elif method == "DELETE":
            resp = requests.delete(url, params=params, timeout=30)
        else:
            return {"success": False, "error": f"不支持的方法: {method}"}

        if resp.status_code >= 400:
            return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:500]}"}

        try:
            data = resp.json()
        except Exception:
            data = resp.text

        return {"success": True, "data": data}

    def _execute_sse(self, method: str, url: str, params: dict) -> dict:
        """执行 SSE 流式请求，等待完成后返回最终结果"""
        resp = requests.post(url, json=params, stream=True, timeout=600)
        if resp.status_code >= 400:
            return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text[:500]}"}

        result = ""
        last_progress = ""
        for line in resp.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            try:
                event = json.loads(line[6:])
                etype = event.get("type", "")
                if etype == "progress":
                    last_progress = event.get("message", "")
                elif etype == "result":
                    result = event.get("content", "")
                elif etype == "error":
                    return {"success": False, "error": event.get("message", "未知错误")}
            except json.JSONDecodeError:
                continue

        if result:
            return {"success": True, "data": result}
        elif last_progress:
            return {"success": True, "data": last_progress}
        else:
            return {"success": False, "error": "SSE流结束但未收到结果"}

    def load_project_defaults(self):
        """从当前活跃项目中加载默认参数"""
        result = self.execute("list_projects")
        if not result["success"]:
            return

        data = result["data"]
        active = data.get("active_project", "")
        if not active:
            return

        # 获取项目详情
        resp = requests.get(f"{self.api_base}/projects/active", timeout=10)
        if resp.status_code != 200:
            return

        project = resp.json().get("project", {})
        self.default_params.update({
            "llm_config_name": project.get("llm_config_name", ""),
            "emb_config_name": project.get("emb_config_name", ""),
            "filepath": project.get("filepath", f"./output/{active}"),
            "style_name": project.get("ch_style", ""),
            "narrative_style_name": project.get("ch_narrative_style", ""),
            "xp_type": project.get("xp_type", ""),
            "word_number": project.get("word_number", 3000),
            "num_chapters": project.get("num_chapters", 10),
            "topic": project.get("topic", ""),
            "genre": project.get("genre", ""),
        })
        _logger.info(f"已加载项目默认参数: {active}")
        return project
