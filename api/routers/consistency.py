# api/routers/consistency.py
# -*- coding: utf-8 -*-
"""一致性检查路由"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from api.schemas import ConsistencyCheckRequest
from api.app_state import get_web_app
from api.sse_utils import run_with_sse

router = APIRouter(tags=["consistency"])


@router.post("/consistency/check")
def check_consistency(body: ConsistencyCheckRequest):
    app = get_web_app()

    async def _gen():
        async for chunk in run_with_sse(
            app.check_consistency_web,
            body.llm_config_name, body.filepath, body.chapter_num,
        ):
            yield chunk

    return StreamingResponse(
        _gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
