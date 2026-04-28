# api/routers/config.py
# -*- coding: utf-8 -*-
"""LLM / Embedding 配置路由"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from api.schemas import LLMConfigCreate, EmbeddingConfigCreate, TestLLMConfigRequest, TestEmbeddingConfigRequest
from api.app_state import get_web_app
from api.sse_utils import run_with_sse
from embedding_adapters import create_embedding_adapter, clear_embedding_cache
from llm_adapters import create_llm_adapter

router = APIRouter(tags=["config"])


# ── LLM ───────────────────────────────────────────────────────────────────────

@router.get("/config/llm")
def list_llm_configs():
    app = get_web_app()
    configs = app.config.get("llm_configs", {})
    return {
        "configs": configs,
        "choices": list(configs.keys()),
        "choose": app.config.get("choose_configs", {})
    }


@router.post("/config/llm")
def save_llm_config(body: LLMConfigCreate):
    app = get_web_app()
    _, msg = app.save_llm_config(
        body.config_name, body.api_key, body.base_url,
        body.interface_format, body.model_name,
        body.temperature, body.max_tokens, body.timeout,
        body.enable_thinking, body.thinking_budget,
        body.enable_streaming,
    )
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


@router.delete("/config/llm/{name}")
def delete_llm_config(name: str):
    app = get_web_app()
    _, msg = app.delete_llm_config(name)
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}


# ── Embedding ─────────────────────────────────────────────────────────────────

@router.get("/config/embedding")
def list_embedding_configs():
    app = get_web_app()
    configs = app.config.get("embedding_configs", {})
    return {
        "configs": configs,
        "choices": list(configs.keys())
    }


@router.post("/config/embedding")
def save_embedding_config(body: EmbeddingConfigCreate):
    app = get_web_app()
    _, msg = app.save_embedding_config(
        body.config_name, body.interface_format, body.api_key,
        body.base_url, body.model_name, body.retrieval_k
    )
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    clear_embedding_cache()
    return {"message": msg}


@router.delete("/config/embedding/{name}")
def delete_embedding_config(name: str):
    app = get_web_app()
    _, msg = app.delete_embedding_config(name)
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    clear_embedding_cache()
    return {"message": msg}


# ── 连通性测试 ────────────────────────────────────────────────────────────────

def _test_llm_sync(interface_format, api_key, base_url, model_name,
                    temperature, max_tokens, timeout, progress):
    progress(0.1, desc="正在创建 LLM 适配器...")
    llm_adapter = create_llm_adapter(
        interface_format=interface_format,
        base_url=base_url,
        model_name=model_name,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
    )
    progress(0.3, desc="正在发送测试请求...")
    response = llm_adapter.invoke("Please reply 'OK'")
    if response:
        progress(0.9, desc="测试成功")
        return f"✅ LLM 连通性测试成功！回复: {response[:200]}"
    return "❌ LLM 测试失败：未获取到响应"


def _test_emb_sync(interface_format, api_key, base_url, model_name, progress):
    progress(0.1, desc="正在创建 Embedding 适配器...")
    adapter = create_embedding_adapter(
        interface_format=interface_format,
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
    )
    progress(0.3, desc="正在发送测试请求...")
    embeddings = adapter.embed_query("测试文本")
    if embeddings and len(embeddings) > 0:
        progress(0.9, desc="测试成功")
        return f"✅ Embedding 连通性测试成功！向量维度: {len(embeddings)}"
    return "❌ Embedding 测试失败：未获取到向量"


@router.post("/config/llm/test")
async def test_llm_config(body: TestLLMConfigRequest):
    return StreamingResponse(
        run_with_sse(
            _test_llm_sync,
            body.interface_format, body.api_key, body.base_url,
            body.model_name, body.temperature, body.max_tokens, body.timeout,
        ),
        media_type="text/event-stream",
    )


@router.post("/config/embedding/test")
async def test_embedding_config(body: TestEmbeddingConfigRequest):
    return StreamingResponse(
        run_with_sse(
            _test_emb_sync,
            body.interface_format, body.api_key, body.base_url, body.model_name,
        ),
        media_type="text/event-stream",
    )


# ── 代理设置 ─────────────────────────────────────────────────────────────────

@router.get("/config/proxy")
def get_proxy():
    app = get_web_app()
    proxy = app.config.get("proxy_setting", {"proxy_url": "", "proxy_port": "", "enabled": False})
    return proxy


@router.put("/config/proxy")
def save_proxy(body: dict):
    app = get_web_app()
    app.config["proxy_setting"] = {
        "proxy_url": body.get("proxy_url", "").strip(),
        "proxy_port": str(body.get("proxy_port", "")).strip(),
        "enabled": bool(body.get("enabled", False)),
    }
    from config_manager import save_config
    save_config(app.config, app.config_file)
    # 立即生效
    from llm_adapters import _apply_proxy_settings
    _apply_proxy_settings()
    return {"message": "✅ 代理设置已保存"}


# ── 用户画像 ─────────────────────────────────────────────────────────────────

import json
import os
from datetime import datetime

_PROFILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "user_profile.json")


def _read_profile():
    if os.path.exists(_PROFILE_PATH):
        with open(_PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"profile": "", "updated_at": ""}


def _write_profile(data):
    with open(_PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("/config/user_profile")
def get_user_profile():
    return _read_profile()


@router.post("/config/user_profile/extract")
def extract_user_preferences(body: dict):
    """从用户文本中提取偏好信号，返回提取结果（不自动写入）"""
    text = body.get("text", "").strip()
    llm_config_name = body.get("llm_config_name", "")
    if not text or not llm_config_name:
        return {"preferences": ""}

    app = get_web_app()
    if llm_config_name not in app.config.get("llm_configs", {}):
        return {"preferences": ""}

    llm_conf = app.config["llm_configs"][llm_config_name]
    existing_profile = _read_profile().get("profile", "")

    from llm_adapters import create_llm_adapter
    from novel_generator.common import invoke_with_cleaning

    llm_adapter = create_llm_adapter(
        interface_format=llm_conf["interface_format"],
        base_url=llm_conf["base_url"],
        model_name=llm_conf["model_name"],
        api_key=llm_conf["api_key"],
        temperature=0.3,
        max_tokens=512,
        timeout=30,
    )

    prompt = f"""分析以下用户在小说创作过程中写的文本，判断其中是否隐含了用户的内容偏好/审美倾向。

用户文本：
{text}

已有画像（避免重复提取）：
{existing_profile if existing_profile else '（空）'}

提取规则：
- 只提取关于内容偏好的信息（角色类型偏好、关系模式偏好、剧情节奏偏好等）
- 不提取写作风格偏好（那是文风管的）
- 不提取针对具体项目的设定（那是项目自己管的）
- 不提取已经在"已有画像"中存在的偏好
- 如果文本中没有可提取的偏好信息，返回空

如果提取到了偏好，用简短的条目格式输出（每条一行，以"- "开头）。
如果没有可提取的，只输出一个字：无"""

    result = invoke_with_cleaning(llm_adapter, prompt, enable_streaming=False)
    result = result.strip()
    if result == "无" or not result or len(result) < 3:
        return {"preferences": ""}
    return {"preferences": result}


@router.post("/config/user_profile/append")
def append_user_profile(body: dict):
    """将新偏好追加到现有画像"""
    new_preferences = body.get("preferences", "").strip()
    if not new_preferences:
        return {"message": "无新偏好"}
    data = _read_profile()
    existing = data.get("profile", "").strip()
    if existing:
        data["profile"] = existing + "\n" + new_preferences
    else:
        data["profile"] = new_preferences
    data["updated_at"] = datetime.now().isoformat()
    _write_profile(data)
    return {"message": "✅ 画像已更新"}


@router.put("/config/user_profile")
def save_user_profile(body: dict):
    profile_text = body.get("profile", "")
    enabled = body.get("enabled", True)
    data = {
        "profile": profile_text,
        "enabled": enabled,
        "updated_at": datetime.now().isoformat(),
    }
    _write_profile(data)
    return {"message": "✅ 用户画像已保存"}
