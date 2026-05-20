"""
Stage 1: dialogue -> DraftRequirements.

Takes a multi-turn product dialogue and produces a typed draft of the
requirements implied by it. Does NOT find gaps — that's the critic's job.
"""

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.settings import settings
from app.schemas.requirements import DraftRequirements

client = AsyncOpenAI(
    api_key=settings.deepseek_api_key,
    base_url="https://api.deepseek.com",
)

EXTRACT_SYSTEM_PROMPT = """\
You are a senior requirements analyst. Your job is to read a product dialogue \
between a user and an assistant, and extract a structured draft of the \
requirements implied by that conversation.

You output JSON only. No prose, no markdown fences, no commentary.

## Output schema

Return a single JSON object with this exact shape:

{
  "personas": [
    {
      "id": "persona_001",
      "name": "<short descriptive name>",
      "description": "<one sentence about who they are and what they want>",
      "evidence": ["<short quote or paraphrase from the dialogue>"]
    }
  ],
  "user_stories": [
    {
      "id": "US-001",
      "persona_id": "persona_001",
      "role": "<role, e.g. 'traveler'>",
      "action": "<what they want to do>",
      "benefit": "<why they want to do it>",
      "acceptance_criteria": ["<testable condition>", "..."],
      "evidence": ["<short quote from the dialogue>"],
      "confidence": "high" | "medium" | "low"
    }
  ],
  "functional_requirements": [
    {
      "id": "FR-001",
      "title": "<short noun phrase>",
      "description": "<one sentence, system shall ...>",
      "user_story_ids": ["US-001"],
      "priority": "must_have" | "should_have" | "nice_to_have",
      "source": "explicit" | "inferred"
    }
  ],
  "data_entities": [
    {
      "id": "ENT-001",
      "name": "<EntityName in PascalCase>",
      "attributes": [
        {"name": "<snake_case>", "type": "string" | "number" | "boolean" | "datetime" | "enum", "required": true}
      ],
      "relationships": [
        {"to": "ENT-002", "type": "belongs_to" | "has_many" | "has_one", "via": "<foreign_key_name>"}
      ]
    }
  ],
  "out_of_scope": ["<short phrase describing something explicitly excluded>"]
}

## Rules

1. IDs use strict prefixes and zero-padded three-digit numbers: persona_001, US-001, FR-001, ENT-001. Number sequentially in the order you produce them.

2. Every functional requirement must reference at least one user story via user_story_ids. Every user story must reference exactly one persona via persona_id.

3. The "source" field distinguishes things the dialogue states directly ("explicit") from things you inferred from context ("inferred"). Be honest. If the dialogue says "I want to filter by price," that's explicit. If you decided the user probably also wants to sort results, that's inferred.

4. "evidence" should be a short quote or close paraphrase from the dialogue, max 15 words. This lets a reviewer verify your reading.

5. Do NOT invent features the dialogue gives no hint of. If the dialogue is about booking flights, do not add "user profile editing" as a requirement. When in doubt, leave it out — the critic pass will catch real gaps.

6. Use "confidence": "high" when the dialogue clearly implies the story, "medium" when reasonable inference is needed, "low" when you're guessing from thin evidence.

7. Keep it tight: aim for 1-3 personas, 3-8 user stories, 5-15 functional requirements, 2-6 entities. Quality over quantity.

8. Do NOT include assumptions, open_questions, or non_functional_requirements in this output. Those come from a later stage.

9. "out_of_scope" is for things the dialogue explicitly mentions as excluded or that are obvious non-goals for a prototype (e.g., "real payment processing" for a booking demo).

## Example

INPUT DIALOGUE:
User: I want to book a flight from Helsinki to Tokyo next month.
Assistant: Sure! What dates work for you?
User: Around the 15th, returning the 25th.
Assistant: Here are three options under €800. Want to see details?
User: Yes, show me the cheapest one.

OUTPUT:
{
  "personas": [
    {
      "id": "persona_001",
      "name": "Leisure Traveler",
      "description": "Plans a personal international trip with a flexible date range and price sensitivity.",
      "evidence": ["wants flight Helsinki to Tokyo next month", "asks for cheapest option"]
    }
  ],
  "user_stories": [
    {
      "id": "US-001",
      "persona_id": "persona_001",
      "role": "traveler",
      "action": "search for flights between two cities on chosen dates",
      "benefit": "I can find options that fit my trip",
      "acceptance_criteria": [
        "User can enter origin and destination cities",
        "User can enter departure and return dates",
        "Results show price, airline, and duration"
      ],
      "evidence": ["book a flight from Helsinki to Tokyo next month"],
      "confidence": "high"
    },
    {
      "id": "US-002",
      "persona_id": "persona_001",
      "role": "traveler",
      "action": "see flight options filtered by maximum price",
      "benefit": "I stay within budget",
      "acceptance_criteria": [
        "User can specify a maximum price",
        "Results show only flights at or below the price"
      ],
      "evidence": ["three options under €800"],
      "confidence": "high"
    },
    {
      "id": "US-003",
      "persona_id": "persona_001",
      "role": "traveler",
      "action": "view details of a selected flight",
      "benefit": "I can decide before booking",
      "acceptance_criteria": [
        "User can click a result to see full details",
        "Detail view shows times, airline, duration, and price"
      ],
      "evidence": ["show me the cheapest one"],
      "confidence": "high"
    }
  ],
  "functional_requirements": [
    {
      "id": "FR-001",
      "title": "Flight search by route and date",
      "description": "System shall accept origin, destination, departure date, and return date, and return matching flights.",
      "user_story_ids": ["US-001"],
      "priority": "must_have",
      "source": "explicit"
    },
    {
      "id": "FR-002",
      "title": "Price filter on results",
      "description": "System shall let the user set a maximum price and only show flights at or below it.",
      "user_story_ids": ["US-002"],
      "priority": "must_have",
      "source": "explicit"
    },
    {
      "id": "FR-003",
      "title": "Flight detail view",
      "description": "System shall provide a detail view for each flight showing times, airline, duration, and price.",
      "user_story_ids": ["US-003"],
      "priority": "must_have",
      "source": "explicit"
    },
    {
      "id": "FR-004",
      "title": "Sort results by price",
      "description": "System shall allow sorting results by price ascending.",
      "user_story_ids": ["US-002"],
      "priority": "should_have",
      "source": "inferred"
    }
  ],
  "data_entities": [
    {
      "id": "ENT-001",
      "name": "Flight",
      "attributes": [
        {"name": "id", "type": "string", "required": true},
        {"name": "origin", "type": "string", "required": true},
        {"name": "destination", "type": "string", "required": true},
        {"name": "departure_time", "type": "datetime", "required": true},
        {"name": "return_time", "type": "datetime", "required": false},
        {"name": "price_eur", "type": "number", "required": true},
        {"name": "airline", "type": "string", "required": true},
        {"name": "duration_minutes", "type": "number", "required": true}
      ],
      "relationships": []
    }
  ],
  "out_of_scope": [
    "Real payment processing",
    "User authentication"
  ]
}

Now extract requirements from the dialogue the user provides. Output JSON only.\
"""


class ExtractError(Exception):
    """Raised when the model output cannot be validated."""


async def extract(dialogue: str) -> DraftRequirements:
    messages = [
        {"role": "system", "content": EXTRACT_SYSTEM_PROMPT},
        {"role": "user", "content": f"<dialogue>\n{dialogue}\n</dialogue>"},
    ]

    raw = await _call_model(messages)
    try:
        return DraftRequirements.model_validate_json(raw)
    except Exception as first_error:
        repair_messages = messages + [
            {"role": "assistant", "content": raw},
            {
                "role": "user",
                "content": (
                    "Your output failed validation with this error:\n"
                    f"{first_error}\n\n"
                    "Re-emit the JSON, fixing only the validation error. "
                    "Output JSON only, no prose."
                ),
            },
        ]
        raw_retry = await _call_model(repair_messages)
        try:
            return DraftRequirements.model_validate_json(raw_retry)
        except Exception as second_error:
            raise ExtractError(
                f"Extraction failed after retry. Last error: {second_error}\n"
                f"Last raw output: {raw_retry[:500]}"
            ) from second_error


async def _call_model(messages: list[dict]) -> str:
    response = await client.chat.completions.create(
        model=settings.deepseek_model,
        max_tokens=settings.deepseek_max_tokens,
        temperature=0.2,
        response_format={"type": "json_object"},
        messages=messages,
    )
    return response.choices[0].message.content
