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
        body.enable_thinking, body.thinking_budget
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
