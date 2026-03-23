# LLM Setup: Use Gemini (Free) Instead of Local Ollama

Local LLMs (Ollama) are resource-heavy and can overload your PC. This project supports **Google Gemini** via the free [AI Studio API](https://aistudio.google.com/app/apikey).

## Verify your setup

After starting the backend, check the logs. You should see:

```
LLM: provider=gemini has_key=True
```

If you see `has_key=False` or `provider=ollama`, the config is wrong. Fix your `backend/.env` and restart.

## Quick switch to Gemini (free tier)

1. **Get a free API key**: https://aistudio.google.com/app/apikey

2. **Set environment variables** before starting the backend:

   ```bash
   export LLM_PROVIDER=gemini
   export GEMINI_API_KEY=your-api-key-here
   ```

3. Restart your backend.

### With Docker Compose

Create `backend/.env` with:

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-api-key-from-google-ai-studio
```

Then `docker compose up --build`.

### Running backend directly (no Docker)

```bash
export LLM_PROVIDER=gemini
export GEMINI_API_KEY=your-api-key
uvicorn backend.main:app --reload --port 8000
```

Or use a `.env` file and load it (e.g. with `python-dotenv` or your shell).

## Why this helps

| Local Ollama | Gemini (cloud) |
|--------------|----------------|
| Runs on your CPU/GPU | Runs on Google's servers |
| Can freeze or overload your PC | No local compute |
| One query = multiple LLM calls | Same, but fast responses |
| Free but heavy | Free tier, lightweight |

Each query triggers several LLM calls (SQL generation, insights, explanation). With Ollama that happens locally; with Gemini it happens in the cloud.

## Optional

- `GEMINI_MODEL` (default: `gemini-1.5-flash`) – `gemini-1.5-flash` is good for the free tier.
