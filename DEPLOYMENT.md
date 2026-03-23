## Deployment guide

This project supports two realistic deployment modes:

- **Public demo (recommended)**: Vercel (frontend) + Render/Railway (backend) + hosted LLM API (OpenAI-compatible).
- **Local/private**: Docker Compose (frontend + backend + Ollama).

**Never deployed before?** See [DEPLOY_FIRST_TIME.md](DEPLOY_FIRST_TIME.md) for a step-by-step walkthrough with security checklist.

## Public demo: Vercel + Render (free tiers)

### 1) Deploy the backend (Render)

1. Create a new **Web Service** from your GitHub repo.
2. Configure:
   - **Root directory**: repo root
   - **Build command**:
     - `pip install -r backend/requirements.txt`
   - **Start command**:
     - `uvicorn backend.main:app --host 0.0.0.0 --port 8000`
3. Set environment variables:
   - `APP_ENV=production`
   - `BACKEND_CORS_ORIGINS=https://<your-vercel-app-domain>`
   - `DEFAULT_QUERY_LIMIT=100`

4. Choose an LLM provider:
   - **Gemini (free, recommended)**:
     - `LLM_PROVIDER=gemini`
     - `GEMINI_API_KEY=...` (get free key at https://aistudio.google.com/app/apikey)
     - `GEMINI_MODEL=gemini-1.5-flash` (optional; default)
   - **OpenAI-compatible API**:
     - `LLM_PROVIDER=openai_compatible`
     - `OPENAI_API_KEY=...`
     - `OPENAI_API_BASE=...` (optional; defaults to OpenAI base URL)
     - `OPENAI_MODEL=...`
   - **Ollama (local-only, resource-heavy)**:
     - `LLM_PROVIDER=ollama`
     - `OLLAMA_URL=http://localhost:11434/api/generate`
     - `OLLAMA_MODEL_NAME=phi3`

After deploy, grab your backend URL, e.g. `https://your-backend.onrender.com`.

### 2) Deploy the frontend (Vercel)

1. Import the same repo into Vercel.
2. Set:
   - **Root directory**: `frontend/`
   - **Build command**: `npm run build`
   - **Output directory**: `dist`
3. Add environment variable:
   - `VITE_API_BASE_URL=https://your-backend.onrender.com`
4. Deploy.

## Local/private: Docker Compose (with Ollama)

1. Start everything:

```bash
docker compose up --build
```

2. Pull the model (first time only):

```bash
docker compose exec ollama ollama pull phi3
```

3. Open:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000/health`

