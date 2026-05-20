from openai import AsyncOpenAI
from app.core.settings import settings

client = AsyncOpenAI(
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
)
