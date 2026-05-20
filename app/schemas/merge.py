from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.requirements import DraftRequirements

ID_ASSUMPTION = r"^ASM-\d{3}$"
ID_OPEN_QUESTION = r"^OQ-\d{3}$"


class Assumption(BaseModel):
    id: str = Field(pattern=ID_ASSUMPTION)
    text: str = Field(description="The decision itself, written as a statement.")
    rationale: str = Field(description="Why this decision was made.")
    confidence: Literal["high", "medium"]
    evidence: str = Field(description="Short quote or paraphrase from dialogue or draft. Max 15 words.")
    affects: list[str] = Field(default_factory=list)
    needs_review: bool = Field(
        default=False,
        description="True for medium-confidence assumptions — flagged for human review.",
    )


class OpenQuestion(BaseModel):
    id: str = Field(pattern=ID_OPEN_QUESTION)
    text: str = Field(description="The question itself.")
    suggested_resolution: str = Field(description="What the agent would assume if forced to decide.")
    blocks: list[str] = Field(default_factory=list)
    evidence: str = Field(description="Short quote or paraphrase showing where the gap surfaces.")


class RequirementsDoc(DraftRequirements):
    assumptions: list[Assumption] = Field(default_factory=list)
    open_questions: list[OpenQuestion] = Field(default_factory=list)

    def has_blocking_questions(self) -> bool:
        return any(q.blocks for q in self.open_questions)

    def medium_confidence_assumptions(self) -> list[Assumption]:
        return [a for a in self.assumptions if a.needs_review]
