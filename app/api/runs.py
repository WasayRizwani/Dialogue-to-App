from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

_store: dict[str, dict] = {}


class RunResult(BaseModel):
    run_id: str
    status: str
    result: dict | None = None


@router.get("/runs/{run_id}", response_model=RunResult)
async def get_run(run_id: str) -> RunResult:
    if run_id not in _store:
        raise HTTPException(status_code=404, detail="Run not found")
    entry = _store[run_id]
    return RunResult(run_id=run_id, **entry)
