# api/routers/knowledge.py
# -*- coding: utf-8 -*-
"""知识库路由"""

import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from api.app_state import get_web_app

router = APIRouter(tags=["knowledge"])


@router.post("/knowledge/import")
async def import_knowledge(
    emb_config_name: str = Form(...),
    filepath: str = Form(...),
    file: UploadFile = File(...),
):
    app = get_web_app()

    if not emb_config_name or emb_config_name not in app.config.get("embedding_configs", {}):
        raise HTTPException(status_code=400, detail="❌ 请先选择有效的 Embedding 配置")

    emb_conf = app.config["embedding_configs"][emb_config_name]

    content_bytes = await file.read()
    try:
        knowledge_text = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        knowledge_text = content_bytes.decode("gbk", errors="replace")

    from embedding_adapters import create_embedding_adapter
    from novel_generator.vectorstore_utils import import_knowledge_to_vectorstore

    embedding_adapter = create_embedding_adapter(
        emb_conf.get("interface_format", emb_config_name),
        emb_conf["api_key"],
        emb_conf["base_url"],
        emb_conf["model_name"]
    )

    try:
        import_knowledge_to_vectorstore(
            embedding_adapter=embedding_adapter,
            knowledge_text=knowledge_text,
            filepath=filepath
        )
        return {"message": "✅ 知识库导入成功!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"❌ 导入失败: {str(e)}")


@router.delete("/knowledge")
def clear_knowledge(filepath: str):
    app = get_web_app()
    msg = app.clear_knowledge_web(filepath)
    if msg.startswith("❌"):
        raise HTTPException(status_code=400, detail=msg)
    return {"message": msg}



# 作者参考库已迁移到 styles 路由（绑定到文风而非项目）
