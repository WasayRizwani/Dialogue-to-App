"""Stage 4: RequirementsDoc -> TechnicalSpec."""
from __future__ import annotations

from app.core.settings import settings
from app.llm import client
from app.schemas.merge import RequirementsDoc
from app.schemas.spec import TechnicalSpec


PLAN_SYSTEM_PROMPT = """\
You are a senior frontend architect. You take a finalized requirements \
document and produce a technical spec for a React + Tailwind prototype.

You output JSON only. No prose, no markdown fences, no commentary.

## Your job

Convert the requirements document into a buildable spec containing:

- routes: URL paths and which screen each one renders.
- screens: page-level components.
- components: building blocks composing the screens.
- data_layer: which entities the prototype uses and how much mock data to seed.

## Output schema

Return a single JSON object:

{
  "stack": {
    "framework": "react",
    "styling": "tailwind",
    "state": "zustand",
    "data": "mock_in_memory"
  },
  "routes": [
    {
      "id": "RT-001",
      "path": "/",
      "screen_id": "SC-001",
      "implements_requirements": ["FR-001"]
    }
  ],
  "screens": [
    {
      "id": "SC-001",
      "name": "SearchScreen",
      "file_path": "src/screens/SearchScreen.tsx",
      "purpose": "<one sentence>",
      "component_ids": ["CMP-001"],
      "implements_requirements": ["FR-001"]
    }
  ],
  "components": [
    {
      "id": "CMP-001",
      "name": "FlightSearchForm",
      "file_path": "src/components/FlightSearchForm.tsx",
      "purpose": "<one sentence>",
      "props": [
        {"name": "onSubmit", "type": "(query: SearchQuery) => void"}
      ],
      "implements_requirements": ["FR-001"],
      "consumes_entities": []
    }
  ],
  "data_layer": {
    "entity_ids": ["ENT-001"],
    "mock_data_path": "src/data/mock.ts",
    "seed_counts": {"ENT-001": 25}
  }
}

## Critical rules

1. COVERAGE IS MANDATORY. Every functional requirement (FR-ID) in the
   input must appear in the implements_requirements array of at least
   one component. If you skip an FR, the build fails. Before you finish,
   mentally list every FR-ID and confirm each appears in at least one
   component.

2. IDs are sequential and zero-padded: RT-001, SC-001, CMP-001. Number
   each list independently starting from 001.

3. References must be valid:
   - route.screen_id must match an existing SC-ID.
   - screen.component_ids must match existing CMP-IDs.
   - implements_requirements entries must match FR-IDs from the input.
   - consumes_entities entries must match ENT-IDs from the input.

4. Honor assumptions and out_of_scope. If an assumption says "payment
   is mocked," do NOT add a real payment component. If out_of_scope
   includes "user authentication," do NOT add a login screen.

5. Respect open questions. If an open question blocks an FR (its
   "blocks" array contains that FR-ID), still produce a component for
   that FR using the question's suggested_resolution as the default
   behavior — flag in the component's purpose that the resolution is
   provisional.

6. Keep the prototype small: aim for 2-5 screens, 5-12 components,
   1-5 entities. Prefer composing existing components over creating
   new ones for every FR.

7. File paths follow a fixed structure:
   - screens: src/screens/<Name>.tsx
   - components: src/components/<Name>.tsx
   - mock data: src/data/mock.ts

8. seed_counts: choose realistic numbers. For a list-heavy app like
   search results, 20-40 rows. For detail-heavy apps with relationships,
   5-15 of the parent entity.

9. Component granularity: a screen is one component-shaped thing; a
   "component" in the spec is a reusable building block within screens
   (form, card, filter panel, modal). Don't create a separate Component
   that's identical to a Screen.

10. Do NOT generate code. Only the spec. Code generation happens later
    via the v0 API.

Now produce a spec for the requirements doc provided.\
"""


class PlanError(Exception):
    pass


async def plan(
    requirements: RequirementsDoc,
    fixup_message: str | None = None,
) -> TechnicalSpec:
    user_message = (
        f"<requirements_doc>\n{requirements.model_dump_json(indent=2)}\n</requirements_doc>"
    )
    if fixup_message:
        user_message += f"\n\n<fixup>\n{fixup_message}\n</fixup>"

    messages = [
        {"role": "system", "content": PLAN_SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    raw = await _call_model(messages)
    try:
        spec = TechnicalSpec.model_validate_json(raw)
    except Exception as first_error:
        repair_messages = messages + [
            {"role": "assistant", "content": raw},
            {
                "role": "user",
                "content": (
                    f"Your output failed validation:\n{first_error}\n\n"
                    "Re-emit the JSON fixing only the validation error. JSON only."
                ),
            },
        ]
        raw_retry = await _call_model(repair_messages)
        try:
            spec = TechnicalSpec.model_validate_json(raw_retry)
        except Exception as second_error:
            raise PlanError(
                f"Plan failed after retry. Last error: {second_error}\n"
                f"Last raw output: {raw_retry[:500]}"
            ) from second_error

    _validate_references(spec, requirements)
    return spec


def _validate_references(spec: TechnicalSpec, requirements: RequirementsDoc) -> None:
    valid_fr_ids = {fr.id for fr in requirements.functional_requirements}
    valid_entity_ids = {e.id for e in requirements.data_entities}
    valid_screen_ids = {s.id for s in spec.screens}
    valid_component_ids = {c.id for c in spec.components}

    errors = []

    for route in spec.routes:
        if route.screen_id not in valid_screen_ids:
            errors.append(f"Route {route.id} references missing screen {route.screen_id}")
        for fr_id in route.implements_requirements:
            if fr_id not in valid_fr_ids:
                errors.append(f"Route {route.id} references unknown FR {fr_id}")

    for screen in spec.screens:
        for cmp_id in screen.component_ids:
            if cmp_id not in valid_component_ids:
                errors.append(f"Screen {screen.id} references missing component {cmp_id}")
        for fr_id in screen.implements_requirements:
            if fr_id not in valid_fr_ids:
                errors.append(f"Screen {screen.id} references unknown FR {fr_id}")

    for comp in spec.components:
        for fr_id in comp.implements_requirements:
            if fr_id not in valid_fr_ids:
                errors.append(f"Component {comp.id} references unknown FR {fr_id}")
        for ent_id in comp.consumes_entities:
            if ent_id not in valid_entity_ids:
                errors.append(f"Component {comp.id} references unknown entity {ent_id}")

    for ent_id in spec.data_layer.entity_ids:
        if ent_id not in valid_entity_ids:
            errors.append(f"Data layer references unknown entity {ent_id}")

    if errors:
        raise PlanError("Spec has invalid references:\n" + "\n".join(errors))


async def _call_model(messages: list[dict]) -> str:
    response = await client.chat.completions.create(
        model=settings.deepseek_model,
        max_tokens=settings.deepseek_max_tokens,
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=messages,
    )
    return response.choices[0].message.content
