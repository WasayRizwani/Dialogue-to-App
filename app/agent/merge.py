"""Stage 3: DraftRequirements + list[Gap] -> RequirementsDoc."""

from app.schemas.gaps import Gap
from app.schemas.merge import Assumption, OpenQuestion, RequirementsDoc
from app.schemas.requirements import DraftRequirements


def merge(draft: DraftRequirements, gaps: list[Gap]) -> RequirementsDoc:
    assumptions = []
    open_questions = []

    for i, gap in enumerate(gaps, start=1):
        if gap.confidence_in_resolution == "high":
            assumptions.append(Assumption(
                id=f"ASM-{i:03d}",
                text=gap.suggested_resolution,
                rationale=gap.description,
                confidence="high",
                affects=gap.affects_requirement_ids,
                evidence=gap.evidence,
            ))
        elif gap.confidence_in_resolution == "medium":
            assumptions.append(Assumption(
                id=f"ASM-{i:03d}",
                text=gap.suggested_resolution,
                rationale=gap.description,
                confidence="medium",
                affects=gap.affects_requirement_ids,
                evidence=gap.evidence,
                needs_review=True,
            ))
        else:  # low
            open_questions.append(OpenQuestion(
                id=f"OQ-{len(open_questions)+1:03d}",
                text=gap.description,
                suggested_resolution=gap.suggested_resolution,
                blocks=gap.affects_requirement_ids,
                evidence=gap.evidence,
            ))

    return RequirementsDoc(
        **draft.model_dump(),
        assumptions=assumptions,
        open_questions=open_questions,
    )
