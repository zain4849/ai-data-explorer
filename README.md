## AI-powered Data Explorer

A web app to explore CSV data using natural language, with auto-generated SQL, charts, and AI insights.

![Web App Screenshot](assets/app-ui.png)

## Features
- Upload CSV files through a web interface
- Execute queries using natural language
- Generate SQL queries automatically
- Visualize query results with charts
- Display insights from the data

## Project Structure
```zsh
project/
├── backend/ # FastAPI backend
├── frontend/ # React frontend
└── README.md
```
## Diagrams
Here are some diagrams explaining the project:

### High Level Architecture
Overview of how the frontend, backend, and database interact.
![Diagram 1](assets/high-level-architecture.png)

### Seqeunce Diagram
Step-by-step flow of a CSV query from user input to chart visualization.
![Diagram 2](assets/sequence-diagram.png)

## Getting Started (local dev)

### Prereqs

- **Python**: 3.12+
- **Node**: 20+
- **Ollama** (for local LLM): install and run it, then pull a model (e.g. `phi3`)

### Backend

1. Create a virtual environment:

```zsh
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

2. Install dependencies:
```zsh
pip install -r backend/requirements.txt
```

3. (Optional) install dev deps (tests):
```zsh
pip install -r backend/requirements-dev.txt
```

3. Run the backend:
```zsh
uvicorn backend.main:app --reload
```
The backend runs on http://localhost:8000.

### Frontend

1. Navigate to frontend:
```zsh
cd frontend
npm install
npm run dev
```
The frontend runs on http://localhost:5173.

### Environment variables

- Backend env vars are documented in `.env.example`.
- Frontend reads `VITE_API_BASE_URL` (defaults to `http://localhost:8000`).

## Run with Docker Compose (recommended)

This spins up **frontend + backend + Ollama**.

```zsh
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend: http://localhost:8000 (health: http://localhost:8000/health)
- Ollama: http://localhost:11434

First time only, pull the model inside the Ollama container:

```zsh
docker compose exec ollama ollama pull phi3
```

Then refresh the app and try a query.

## Tests

```zsh
pip install -r backend/requirements-dev.txt
pytest
```

<!--2. Usage

- Upload a CSV file
- Enter a question about your data in plain English
- See results, charts, and insights
-->
## Notes

This is an MVP demo for educational purposes. Data is loaded into in-memory DuckDB and is not persisted between restarts.

## Deploy (free tiers)

### Reality check about “free” + LLMs

- Hosting frontend and backend can be free (Vercel/Netlify + Render/Railway).
- **Running an LLM server (Ollama) publicly is not realistically free** on hosted platforms.
- For a public deployment, you typically use a **hosted LLM API** (which may have limited free credits) and set env vars on the backend.

### Option A (recommended for a public demo): Vercel + Render + hosted LLM API

- **Frontend (Vercel)**:
  - Import the repo.
  - Set the project root to `frontend/`.
  - Set env var `VITE_API_BASE_URL` to your backend URL (from Render).
  - Deploy.
- **Backend (Render)**:
  - Create a new Web Service from this repo.
  - Build command: `pip install -r backend/requirements.txt`
  - Start command: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
  - Set env vars:
    - `APP_ENV=production`
    - `BACKEND_CORS_ORIGINS=https://<your-vercel-domain>`
    - `LLM_PROVIDER=openai_compatible`
    - `OPENAI_API_KEY=...`
    - `OPENAI_API_BASE=...` (depends on provider, or omit for OpenAI)
    - `OPENAI_MODEL=...`
    - `DEFAULT_QUERY_LIMIT=100`

### Option B (local/private deployment): Docker Compose with Ollama

- Run `docker compose up --build`
- Pull model with `docker compose exec ollama ollama pull phi3`
- Share it only within a private network (or on your own VM), not as a public SaaS.

<!-- The project uses in-memory storage (DuckDB) and is intended for local use. -->
