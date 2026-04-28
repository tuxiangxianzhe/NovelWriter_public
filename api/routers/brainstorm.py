# api/routers/brainstorm.py
# -*- coding: utf-8 -*-
"""创意讨论路由（多轮对话 SSE 流式输出）"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.schemas import BrainstormChatRequest
from api.app_state import get_web_app
from api.sse_utils import run_with_sse

router = APIRouter(tags=["brainstorm"])


@router.post("/brainstorm/chat")
def brainstorm_chat(body: BrainstormChatRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.brainstorm_chat,
            body.llm_config_name,
            body.filepath,
            [m.dict() for m in body.messages],
            body.include_core_seed,
            body.include_characters,
            body.include_world_building,
            body.include_plot,
            body.include_blueprint,
            body.include_character_state,
            body.extra_context,
            body.discussion_mode,
        ):
            yield chunk

    return StreamingResponse(
        _gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
