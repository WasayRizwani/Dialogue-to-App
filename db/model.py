from sqlmodel import SQLModel, Field, Column
from sqlalchemy import JSON
from datetime import datetime

class Run(SQLModel, table=True):
    id: str = Field(primary_key=True)
    dialogue: str
    requirements: dict | None = Field(default=None, sa_column=Column(JSON))
    spec: dict | None = Field(default=None, sa_column=Column(JSON))
    v0_prompt: str | None = None
    preview_url: str | None = None
    builder: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None
    total_tokens: int | None = None
    total_cost_usd: float | None = None