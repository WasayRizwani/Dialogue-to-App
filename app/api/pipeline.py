import json
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

from app.agent.pipeline import run
from app.api.runs import _store

router = APIRouter()


class PipelineRequest(BaseModel):
    dialogue: str


class PipelineResponse(BaseModel):
    run_id: str
    status: str = "queued"


def _escape_control_chars(raw: str) -> str:
    """Escape literal control characters inside JSON string values."""
    result = []
    in_string = False
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "\\" and in_string:
            result.append(ch)
            result.append(raw[i + 1])
            i += 2
            continue
        if ch == '"':
            in_string = not in_string
            result.append(ch)
        elif in_string and ch == "\n":
            result.append("\\n")
        elif in_string and ch == "\r":
            result.append("\\r")
        elif in_string and ch == "\t":
            result.append("\\t")
        else:
            result.append(ch)
        i += 1
    return "".join(result)


async def _run_in_background(run_id: str, dialogue: str) -> None:
    try:
        await run(dialogue, run_id=run_id)
    except Exception:
        pass  # pipeline.run() already writes status="failed" to _store


@router.post("/pipeline", response_model=PipelineResponse, status_code=202)
async def run_pipeline(request: Request, background_tasks: BackgroundTasks) -> PipelineResponse:
    raw = (await request.body()).decode("utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        try:
            data = json.loads(_escape_control_chars(raw))
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=422, detail=f"Invalid JSON body: {exc}") from exc

    body = PipelineRequest.model_validate(data)
    run_id = str(uuid.uuid4())
    _store[run_id] = {"status": "queued", "result": None}
    background_tasks.add_task(_run_in_background, run_id, body.dialogue)
    return PipelineResponse(run_id=run_id)
