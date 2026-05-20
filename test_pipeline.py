#!/usr/bin/env python3
"""
Smoke-test: run the full pipeline against a dialogue file and print each stage's output.

Usage (run from backend/):
    python test_pipeline.py                          # uses app/fixtures/dialogue1.txt
    python test_pipeline.py path/to/other.txt
"""
from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

DEFAULT_FIXTURE = Path(__file__).parent / "app/fixtures/dialogue1.txt"


def _banner(title: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print('─' * 60)


async def main(dialogue_path: Path) -> None:
    dialogue = dialogue_path.read_text(encoding="utf-8")
    print(f"Dialogue: {dialogue_path}  ({len(dialogue):,} chars)")

    # ── Stage 1: extract ────────────────────────────────────────
    _banner("Stage 1 · extract()")
    from app.agent.extract import extract
    t0 = time.perf_counter()
    draft = await extract(dialogue)
    print(f"  {time.perf_counter() - t0:.1f}s")
    print(f"  personas   : {len(draft.personas)}")
    print(f"  user stories: {len(draft.user_stories)}")
    print(f"  FRs        : {len(draft.functional_requirements)}")
    print(f"  entities   : {len(draft.data_entities)}")
    for fr in draft.functional_requirements:
        print(f"    {fr.id}  [{fr.priority}]  {fr.title}")

    # ── Stage 2: critic ─────────────────────────────────────────
    _banner("Stage 2 · critic()")
    from app.agent.critic import critic
    t0 = time.perf_counter()
    gaps = await critic(dialogue, draft)
    print(f"  {time.perf_counter() - t0:.1f}s")
    print(f"  gaps found : {len(gaps)}")
    for g in gaps:
        conf = g.confidence_in_resolution
        print(f"    [{g.category:<16}] [{conf}]  {g.description[:65]}")

    # ── Stage 3: merge ──────────────────────────────────────────
    _banner("Stage 3 · merge()")
    from app.agent.merge import merge
    requirements = merge(draft, gaps)
    print(f"  assumptions   : {len(requirements.assumptions)}")
    print(f"  open questions: {len(requirements.open_questions)}")
    if requirements.open_questions:
        print("  ⚠  open questions (need answers before build):")
        for oq in requirements.open_questions:
            print(f"    {oq.id}  {oq.text[:70]}")

    # ── Stage 4: plan ───────────────────────────────────────────
    _banner("Stage 4 · plan()")
    from app.agent.plan import plan
    t0 = time.perf_counter()
    spec = await plan(requirements)
    print(f"  {time.perf_counter() - t0:.1f}s")
    print(f"  screens    : {len(spec.screens)}")
    print(f"  components : {len(spec.components)}")
    print(f"  routes     : {len(spec.routes)}")
    for screen in spec.screens:
        route = next((r for r in spec.routes if r.screen_id == screen.id), None)
        path = route.path if route else "(unrouted)"
        print(f"    {screen.name:<30} {path}")

    # ── Stage 5: render_prompt ──────────────────────────────────
    _banner("Stage 5 · render_v0_prompt()")
    from app.agent.render_prompt import render_v0_prompt
    prompt = render_v0_prompt(requirements, spec)
    print(f"  prompt length: {len(prompt):,} chars")
    print()
    print(prompt)


if __name__ == "__main__":
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_FIXTURE
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        sys.exit(1)
    asyncio.run(main(path))
