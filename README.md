# DialogueToApp

Turn a product dialogue into a live web app.

Paste in a conversation describing what you want to build — DialogueToApp runs it through a multi-stage AI pipeline, generates a structured requirements doc and React component spec, then submits the result to [v0.dev](https://v0.dev) and returns a link to your deployed prototype.

---

## How it works

```
dialogue
   │
   ▼
[1] Extract       dialogue → personas, user stories, functional requirements, data entities
   │
   ▼
[2] Critic        finds gaps: ambiguities, edge cases, missing flows, implicit NFRs
   │
   ▼
[3] Merge         resolves high/medium gaps into assumptions; surfaces low-confidence gaps as open questions
   │
   ▼
[4] Plan          requirements → TechnicalSpec (routes, screens, React components, mock data layer)
   │
   ▼
[5] Coverage      verifies every FR maps to at least one component — retries if not
   │
   ▼
[6] Render        spec + requirements → v0-optimised prompt string
   │
   ▼
[7] v0 Deploy     POSTs the prompt to v0.dev → returns your app URL
```

All LLM calls use **DeepSeek** via an OpenAI-compatible client. The v0 deploy step uses the **v0.dev API**.

---

## API

### `POST /api/pipeline`

Submit a dialogue. Returns a `run_id` immediately (HTTP 202); processing runs in the background.

**Request**
```json
{ "dialogue": "User: I want to track my daily habits...\nAssistant: What kind of habits?" }
```

**Response**
```json
{ "run_id": "3f2a...", "status": "queued" }
```

---

### `GET /api/runs/{run_id}`

Poll for results. `status` is one of `queued` / `running` / `complete` / `failed`.

**Response (complete)**
```json
{
  "run_id": "3f2a...",
  "status": "complete",
  "result": {
    "requirements": { ... },
    "spec": { ... },
    "v0_prompt": "Build a react + tailwind prototype...",
    "v0_url": "https://v0.dev/chat/xxxxx"
  }
}
```

---

## Setup

### Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/)
- A **DeepSeek API key** — [platform.deepseek.com](https://platform.deepseek.com)
- A **v0.dev API token** — [v0.dev/settings/api-keys](https://v0.dev/settings/api-keys)

### Local

```bash
cd backend
cp .env.example .env
# fill in DEEPSEEK_API_KEY and V0_API_TOKEN in .env

poetry install
poetry run uvicorn app.main:app --reload
```

Server starts at `http://localhost:8000`.

### Docker

```bash
# 1. copy and fill in your API keys
cp backend/.env.example backend/.env

# 2. build and start
docker compose up --build

# run in the background
docker compose up --build -d

# view logs
docker compose logs -f backend

# stop
docker compose down

# stop and remove the persistent SQLite volume
docker compose down -v
```

The backend is exposed on `http://localhost:8000`. SQLite data is stored in the `sqlite_data` Docker volume so it survives restarts.

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DEEPSEEK_API_KEY` | Yes | — | DeepSeek API key |
| `DEEPSEEK_BASE_URL` | No | `https://api.deepseek.com` | DeepSeek base URL |
| `DEEPSEEK_MODEL` | No | `deepseek-chat` | Model name |
| `DEEPSEEK_MAX_TOKENS` | No | `4096` | Max tokens per LLM call |
| `V0_API_TOKEN` | Yes | — | v0.dev API token |
| `APP_ENV` | No | `development` | `development` or `production` |
| `LOG_LEVEL` | No | `INFO` | Log level |

---

## Project structure

```
backend/
├── app/
│   ├── agent/
│   │   ├── extract.py        # Stage 1 — dialogue → DraftRequirements
│   │   ├── critic.py         # Stage 2 — find gaps
│   │   ├── merge.py          # Stage 3 — resolve gaps → RequirementsDoc
│   │   ├── plan.py           # Stage 4 — requirements → TechnicalSpec
│   │   ├── coverage.py       # Stage 5 — FR coverage check
│   │   ├── render_prompt.py  # Stage 6 — spec → v0 prompt string
│   │   ├── v0_deploy.py      # Stage 7 — POST to v0.dev API
│   │   └── pipeline.py       # Orchestrator
│   ├── api/
│   │   ├── pipeline.py       # POST /api/pipeline
│   │   └── runs.py           # GET /api/runs/{run_id}
│   ├── core/
│   │   └── settings.py       # Pydantic settings
│   ├── llm.py                # Shared DeepSeek client
│   └── main.py               # FastAPI app
├── db/                       # SQLModel / SQLite setup
├── pyproject.toml
└── Dockerfile
docker-compose.yml
```

---

## Tech stack

| Layer | Choice |
|---|---|
| Runtime | Python 3.11, FastAPI, Uvicorn |
| LLM | DeepSeek (`deepseek-chat`) via OpenAI-compatible API |
| UI generation | v0.dev API |
| Generated prototype | React + Tailwind + shadcn/ui + Zustand |
| Database | SQLite via SQLModel |
| Packaging | Poetry |
| Deployment | Docker / docker-compose |
