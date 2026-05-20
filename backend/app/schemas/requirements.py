from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ID_PERSONA = r"^persona_\d{3}$"
ID_USER_STORY = r"^US-\d{3}$"
ID_FR = r"^FR-\d{3}$"
ID_ENTITY = r"^ENT-\d{3}$"


class Attribute(BaseModel):
    name: str
    type: Literal["string", "number", "boolean", "datetime", "enum"]
    required: bool


class Relationship(BaseModel):
    to: str = Field(pattern=ID_ENTITY)
    type: Literal["belongs_to", "has_many", "has_one"]
    via: str


class DataEntity(BaseModel):
    id: str = Field(pattern=ID_ENTITY)
    name: str
    attributes: list[Attribute]
    relationships: list[Relationship] = Field(default_factory=list)


class Persona(BaseModel):
    id: str = Field(pattern=ID_PERSONA)
    name: str
    description: str
    evidence: list[str]


class UserStory(BaseModel):
    id: str = Field(pattern=ID_USER_STORY)
    persona_id: str = Field(pattern=ID_PERSONA)
    role: str
    action: str
    benefit: str
    acceptance_criteria: list[str]
    evidence: list[str]
    confidence: Literal["high", "medium", "low"]


class FunctionalRequirement(BaseModel):
    id: str = Field(pattern=ID_FR)
    title: str
    description: str
    user_story_ids: list[str]
    priority: Literal["must_have", "should_have", "nice_to_have"]
    source: Literal["explicit", "inferred"]


class DraftRequirements(BaseModel):
    personas: list[Persona]
    user_stories: list[UserStory]
    functional_requirements: list[FunctionalRequirement]
    data_entities: list[DataEntity]
    out_of_scope: list[str]
