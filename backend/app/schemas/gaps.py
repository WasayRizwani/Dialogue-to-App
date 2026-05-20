from typing import Literal

from pydantic import BaseModel, Field


class Gap(BaseModel):
    category: Literal[
        "ambiguity",
        "edge_case",
        "missing_entity",
        "missing_flow",
        "nfr",
    ]
    description: str = Field(description="One sentence stating the gap clearly.")
    evidence: str = Field(description="Short quote or paraphrase from the dialogue. Max 15 words.")
    suggested_resolution: str = Field(description="What you would assume if forced to decide.")
    confidence_in_resolution: Literal["high", "medium", "low"]
    affects_requirement_ids: list[str] = Field(default_factory=list)
