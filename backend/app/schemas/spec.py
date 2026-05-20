from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.requirements import ID_FR, ID_ENTITY

ID_ROUTE = r"^RT-\d{3}$"
ID_SCREEN = r"^SC-\d{3}$"
ID_COMPONENT = r"^CMP-\d{3}$"


class Stack(BaseModel):
    framework: Literal["react"] = "react"
    styling: Literal["tailwind"] = "tailwind"
    state: Literal["zustand", "react_state"] = "zustand"
    data: Literal["mock_in_memory"] = "mock_in_memory"


class Prop(BaseModel):
    name: str = Field(description="camelCase prop name.")
    type: str = Field(description="TypeScript type as a string.")


class Component(BaseModel):
    id: str = Field(pattern=ID_COMPONENT)
    name: str = Field(description="PascalCase React component name.")
    file_path: str = Field(description="Path under src/.")
    purpose: str = Field(description="One sentence describing what this component does.")
    props: list[Prop] = Field(default_factory=list)
    implements_requirements: list[str] = Field(default_factory=list)
    consumes_entities: list[str] = Field(default_factory=list)


class Screen(BaseModel):
    id: str = Field(pattern=ID_SCREEN)
    name: str = Field(description="PascalCase screen name.")
    file_path: str = Field(description="e.g. 'src/screens/SearchScreen.tsx'.")
    purpose: str
    component_ids: list[str] = Field(description="CMP-IDs composing this screen, in display order.")
    implements_requirements: list[str] = Field(default_factory=list)


class Route(BaseModel):
    id: str = Field(pattern=ID_ROUTE)
    path: str = Field(description="URL path, e.g. '/', '/results'.")
    screen_id: str = Field(pattern=ID_SCREEN)
    implements_requirements: list[str] = Field(default_factory=list)


class DataLayer(BaseModel):
    entity_ids: list[str] = Field(description="ENT-IDs used by this prototype.")
    mock_data_path: str = Field(default="src/data/mock.ts")
    seed_counts: dict[str, int] = Field(default_factory=dict)


class TechnicalSpec(BaseModel):
    stack: Stack = Field(default_factory=Stack)
    routes: list[Route]
    screens: list[Screen]
    components: list[Component]
    data_layer: DataLayer

    def all_implemented_fr_ids(self) -> set[str]:
        return {fr_id for comp in self.components for fr_id in comp.implements_requirements}

    def component_by_id(self, cmp_id: str) -> Component | None:
        return next((c for c in self.components if c.id == cmp_id), None)

    def screen_by_id(self, sc_id: str) -> Screen | None:
        return next((s for s in self.screens if s.id == sc_id), None)

    def components_implementing(self, fr_id: str) -> list[Component]:
        return [c for c in self.components if fr_id in c.implements_requirements]
