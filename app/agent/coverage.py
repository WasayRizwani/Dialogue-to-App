"""Stage 5: coverage check — verify spec covers all requirements"""
from app.core.settings import settings
from app.llm import client


async def coverage(final_requirements: str, spec: str) -> str:
    response = client.chat.completions.create(
        model=settings.deepseek_model,
        max_tokens=settings.deepseek_max_tokens,
        messages=[
            {
                "role": "user",
                "content": (
                    "You are a QA analyst. Check whether every requirement below is addressed "
                    "in the technical spec. List any uncovered requirements.\n\n"
                    f"<requirements>\n{final_requirements}\n</requirements>\n\n"
                    f"<spec>\n{spec}\n</spec>"
                ),
            }
        ],
    )
    return response.choices[0].message.content
