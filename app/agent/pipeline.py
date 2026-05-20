"""
Pipeline orchestrator: dialogue → extract → critic → merge → plan → render_v0_prompt → v0_deploy.

`run` is the entry point called by the API router. It drives every stage
sequentially, persists results into the shared run store, and returns a run_id.
"""

import uuid

from app.agent.extract import extract
from app.agent.critic import critic
from app.agent.merge import merge
from app.agent.plan import plan
from app.agent.render_prompt import render_v0_prompt
from app.agent.v0_deploy import v0_deploy
from app.schemas.requirements import DraftRequirements
from app.schemas.gaps import Gap
from app.schemas.merge import RequirementsDoc
from app.schemas.spec import TechnicalSpec
from app.api.runs import _store


async def run(dialogue: str, run_id: str | None = None) -> str:
    if run_id is None:
        run_id = str(uuid.uuid4())
    _store[run_id] = {"status": "running", "result": None}

    try:
        draft: DraftRequirements = await extract(dialogue)

        gaps: list[Gap] = await critic(dialogue, draft)

        requirements: RequirementsDoc = merge(draft, gaps)

        # plan() produces the TechnicalSpec that render_v0_prompt requires
        spec: TechnicalSpec = await plan(requirements)

        prompt: str = render_v0_prompt(requirements, spec)

        v0_url: str = await v0_deploy(prompt)

        _store[run_id] = {
            "status": "complete",
            "result": {
                "requirements": requirements.model_dump(),
                "spec": spec.model_dump(),
                "v0_prompt": prompt,
                "v0_url": v0_url,
            },
        }

    except Exception as exc:
        _store[run_id] = {"status": "failed", "result": {"error": str(exc)}}
        raise

    return run_id
