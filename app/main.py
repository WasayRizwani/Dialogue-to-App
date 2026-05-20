from fastapi import FastAPI
from app.core.settings import settings
from app.api import pipeline, runs

app = FastAPI(title="DialogueToApp", debug=settings.app_env == "development")

app.include_router(pipeline.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
