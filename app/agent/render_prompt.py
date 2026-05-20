"""
Stage 6: RequirementsDoc + TechnicalSpec -> v0-optimized prompt string.

Pure Python. No LLM call. Deterministic.

Output is a single prompt string that gets passed to the builder adapter
(v0 SDK, Lovable URL, etc).
"""

from app.schemas.merge import RequirementsDoc
from app.schemas.spec import TechnicalSpec, Component


def render_v0_prompt(
    requirements: RequirementsDoc,
    spec: TechnicalSpec,
) -> str:
    """Build the v0 prompt from the requirements doc and technical spec."""
    sections = [
        _render_header(requirements, spec),
        _render_screens_section(spec),
        _render_data_section(requirements, spec),
        _render_components_section(spec),
        _render_interactions_section(requirements, spec),
        _render_assumptions_section(requirements),
        _render_constraints_section(requirements, spec),
    ]
    # Filter out any empty sections (assumptions may be empty)
    return "\n\n".join(s for s in sections if s.strip())


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def _render_header(requirements: RequirementsDoc, spec: TechnicalSpec) -> str:
    persona_summary = ", ".join(p.name for p in requirements.personas) or "general users"
    return (
        f"Build a {spec.stack.framework} + {spec.stack.styling} prototype "
        f"for {persona_summary}.\n\n"
        f"Use TypeScript, mock data only (no real backend), and shadcn/ui "
        f"components where appropriate."
    )


def _render_screens_section(spec: TechnicalSpec) -> str:
    lines = ["## Screens"]
    for screen in spec.screens:
        route = next((r for r in spec.routes if r.screen_id == screen.id), None)
        path = route.path if route else "(unrouted)"
        components_in_screen = [
            spec.component_by_id(cid) for cid in screen.component_ids
        ]
        component_names = ", ".join(
            c.name for c in components_in_screen if c is not None
        ) or "no child components"
        lines.append(
            f"- **{screen.name}** (`{path}`, `{screen.file_path}`): "
            f"{screen.purpose} Contains: {component_names}."
        )
    return "\n".join(lines)


def _render_data_section(
    requirements: RequirementsDoc,
    spec: TechnicalSpec,
) -> str:
    if not spec.data_layer.entity_ids:
        return ""

    lines = ["## Data model"]
    lines.append(
        f"Generate mock data in `{spec.data_layer.mock_data_path}`. "
        "Export typed arrays of seed data and TypeScript interfaces."
    )
    lines.append("")
    for ent_id in spec.data_layer.entity_ids:
        entity = next(
            (e for e in requirements.data_entities if e.id == ent_id),
            None,
        )
        if not entity:
            continue
        seed_count = spec.data_layer.seed_counts.get(ent_id, 10)
        lines.append(f"**{entity.name}** ({seed_count} rows)")
        for attr in entity.attributes:
            required_mark = "" if attr.required else " (optional)"
            lines.append(f"  - `{attr.name}: {_ts_type(attr.type)}`{required_mark}")
        if entity.relationships:
            for rel in entity.relationships:
                target = next(
                    (e for e in requirements.data_entities if e.id == rel.to),
                    None,
                )
                target_name = target.name if target else rel.to
                lines.append(
                    f"  - {rel.type.replace('_', ' ')} `{target_name}` via `{rel.via}`"
                )
        lines.append("")
    return "\n".join(lines).rstrip()


def _render_components_section(spec: TechnicalSpec) -> str:
    lines = ["## Components"]
    for comp in spec.components:
        props_str = _format_props(comp)
        lines.append(
            f"- **{comp.name}** (`{comp.file_path}`){props_str}: {comp.purpose}"
        )
    return "\n".join(lines)


def _render_interactions_section(
    requirements: RequirementsDoc,
    spec: TechnicalSpec,
) -> str:
    """
    Reframe FRs as user-facing behaviors. v0 responds well to
    "when user X, then Y" phrasing.
    """
    lines = ["## Interactions"]
    for fr in requirements.functional_requirements:
        # Find the components that implement this FR
        implementing = spec.components_implementing(fr.id)
        if not implementing:
            # Will be flagged by coverage check; emit anyway so v0 still tries
            lines.append(f"- {fr.description}")
            continue
        component_hint = ", ".join(c.name for c in implementing)
        lines.append(f"- {fr.description} _(implemented by {component_hint})_")
    return "\n".join(lines)


def _render_assumptions_section(requirements: RequirementsDoc) -> str:
    if not requirements.assumptions:
        return ""
    lines = ["## Assumptions to honor"]
    for asm in requirements.assumptions:
        lines.append(f"- {asm.text}")
    return "\n".join(lines)


def _render_constraints_section(
    requirements: RequirementsDoc,
    spec: TechnicalSpec,
) -> str:
    lines = ["## Constraints"]

    # Hard scope boundaries
    if requirements.out_of_scope:
        lines.append("**Out of scope** (do NOT build these):")
        for item in requirements.out_of_scope:
            lines.append(f"- {item}")
        lines.append("")

    # Universal prototype constraints
    lines.append("**Engineering**:")
    lines.append("- Mobile-first responsive design.")
    lines.append("- Light theme by default; ensure good contrast.")
    lines.append("- All data is mock — no API calls, no auth, no backend.")
    lines.append("- Use React Router (or Next.js App Router) for routing.")
    lines.append(f"- State management: {spec.stack.state}.")
    lines.append("- Keep file structure as specified above.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts_type(schema_type: str) -> str:
    """Map our schema's attribute types to TypeScript types."""
    return {
        "string": "string",
        "number": "number",
        "boolean": "boolean",
        "datetime": "string",  # ISO strings in mock data
        "enum": "string",      # widen for prototype; real enums later
    }.get(schema_type, "string")


def _format_props(comp: Component) -> str:
    if not comp.props:
        return ""
    rendered = ", ".join(f"`{p.name}: {p.type}`" for p in comp.props)
    return f" — props: {rendered}"