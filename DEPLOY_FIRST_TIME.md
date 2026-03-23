# First-Time Deployment Guide

A beginner-friendly walkthrough to deploy your AI Data Explorer safely. No prior deployment experience needed.

---

## Part 1: Security checklist (before you deploy)

**Never commit secrets to GitHub.** Your `.gitignore` already excludes `.env` files. Here’s what to verify:

### ✅ Verify nothing sensitive is in the repo

1. **Double-check your .gitignore includes:**
   - `.env`
   - `.env.local`
   - `.env.*.local`

2. **Confirm no secrets in recent commits:**

   ```bash
   # Search for common secret patterns in tracked files
   git log -p --all -S "GEMINI_API_KEY" -- "*.py" "*.ts" "*.tsx" "*.json" "*.yml" "*.yaml" 2>/dev/null | head -20
   ```

   If you see actual key values, treat them as compromised and rotate the keys.

3. **Secrets you must NEVER commit:**
   - `GEMINI_API_KEY` (or any LLM API key)
   - `SECRET_KEY` (JWT signing)
   - `DATABASE_URL` (PostgreSQL connection string with password)
   - `OAUTH_*_SECRET` values
   - `ENCRYPTION_KEY`

4. **Where secrets live in production:**
   - **Render:** Environment Variables in the dashboard
   - **Vercel:** Environment Variables in Project Settings

---

## Part 2: What you’ll need (free accounts)

| Service   | Purpose                     | Sign up                                                    |
|----------|-----------------------------|------------------------------------------------------------|
| GitHub   | Host your code              | [github.com](https://github.com)                          |
| Render   | Host backend + PostgreSQL   | [render.com](https://render.com)                          |
| Vercel   | Host frontend               | [vercel.com](https://vercel.com)                          |
| Google AI Studio | Free LLM API key     | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) |

---

## Part 3: Step-by-step deployment

### Step 0: Push your code to GitHub

1. Create a repo on GitHub (if you haven’t).
2. Push your local project:

   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/ai-powered-data-explorer.git
   git push -u origin main
   ```

3. **Before pushing:** Make sure `backend/.env` exists only locally and is not tracked:

   ```bash
   git status   # .env should NOT appear
   git check-ignore -v backend/.env   # Should say it's ignored
   ```

---

### Step 1: Deploy the backend on Render

1. Go to [render.com](https://render.com) → **Get started** → sign in with GitHub.

2. **New → Web Service**

3. **Connect** your `ai-powered-data-explorer` repo.

4. Configure:
   - **Name:** `ai-powered-data-explorer-api` (or similar)
   - **Region:** Closest to you
   - **Branch:** `main`
   - **Root Directory:** (leave empty)
   - **Runtime:** Python 3
   - **Build Command:**
     ```
     pip install -r backend/requirements.txt
     ```
   - **Start Command:**
     ```
     uvicorn backend.main:app --host 0.0.0.0 --port $PORT
     ```
     (Render sets `$PORT` automatically.)

5. **Add PostgreSQL database**

   - On the Render dashboard: **New → PostgreSQL**
   - Name it (e.g. `ai-explorer-db`)
   - Create the database
   - Open **Internal Database URL** and copy it (e.g. `postgresql://user:pass@host:port/dbname`)

6. **Environment variables**

   Open your Web Service → **Environment** and add:

   | Key                    | Value                                      | Notes                                      |
   |------------------------|--------------------------------------------|--------------------------------------------|
   | `APP_ENV`              | `production`                               | Required                                   |
   | `DATABASE_URL`         | *(Internal Database URL from step 5)*      | Paste the full URL                         |
   | `SECRET_KEY`           | *(generate below)*                         | **Required in production**                 |
   | `GEMINI_API_KEY`       | *(from Google AI Studio)*                  | Required for AI queries                    |
   | `LLM_PROVIDER`         | `gemini`                                   |                                           |
   | `GEMINI_MODEL`         | `gemini-1.5-flash`                         | Optional                                   |
   | `DEFAULT_QUERY_LIMIT`   | `100`                                      | Optional                                   |
   | `BACKEND_CORS_ORIGINS` | `https://your-app.vercel.app`              | Update after Step 2 with your Vercel URL   |

   **Generate `SECRET_KEY`** (e.g. 32+ random characters):

   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

   **Get `GEMINI_API_KEY`:**

   - Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
   - Create API key → copy it

7. Click **Create Web Service**.

8. Wait for the first deploy. When it’s ready, you’ll see a URL like:

   `https://ai-powered-data-explorer-api.onrender.com`

9. Test the health endpoint:

   ```
   https://YOUR-BACKEND-URL.onrender.com/health
   ```

   You should see: `{"status":"ok","environment":"production"}`.

---

### Step 2: Set CORS on the backend

1. In Render, go to your Web Service → **Environment**.
2. Update `BACKEND_CORS_ORIGINS` with your eventual Vercel URL.  
   Example: `https://ai-powered-data-explorer-xyz.vercel.app`  
   You can update this again after deploying the frontend.

---

### Step 3: Deploy the frontend on Vercel

1. Go to [vercel.com](https://vercel.com) → sign in with GitHub.

2. **Add New… → Project**.

3. Import your `ai-powered-data-explorer` repo.

4. Configure:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend` (click and choose)
   - **Build Command:** `npm run build` (default)
   - **Output Directory:** `dist` (default)
   - **Install Command:** `npm install` (default)

5. **Environment Variables**

   Add:

   | Key                 | Value                              |
   |---------------------|------------------------------------|
   | `VITE_API_BASE_URL` | `https://YOUR-BACKEND-URL.onrender.com` |

   Use the backend URL from Render (no trailing slash).

6. Click **Deploy**.

7. When deploy finishes, Vercel gives you a URL like:

   `https://ai-powered-data-explorer-xxxxx.vercel.app`

---

### Step 4: Connect backend and frontend

1. **Update CORS on Render**
   - Web Service → **Environment**
   - Set `BACKEND_CORS_ORIGINS` to your Vercel URL:  
     `https://ai-powered-data-explorer-xxxxx.vercel.app`
   - Save → Render will redeploy.

2. **Test the full flow**
   - Open your Vercel URL.
   - Try: sign up / log in, upload a CSV, ask a question.
   - Check for CORS or network errors in DevTools (F12 → Console/Network).

---

## Part 4: What can go wrong

| Problem                       | Fix                                                                 |
|------------------------------|---------------------------------------------------------------------|
| "Database is not ready"       | Add `DATABASE_URL` in Render and ensure PostgreSQL is running       |
| "The AI query engine..."     | Add `GEMINI_API_KEY` and `LLM_PROVIDER=gemini`                      |
| CORS errors in browser       | Set `BACKEND_CORS_ORIGINS` to the exact Vercel URL (protocol + host)|
| Blank page / 404             | Check Vercel Root Directory is `frontend`                           |
| "Authentication failed"      | Ensure `SECRET_KEY` is set and different from the default          |
| Render app sleeps            | Free tier sleeps after inactivity; first request can take ~30–60s   |

---

## Part 5: Optional improvements

- **Custom domain:** Vercel and Render both support adding your domain.
- **OAuth (Google/GitHub):** Create OAuth apps and add `OAUTH_GOOGLE_CLIENT_ID`, `OAUTH_GOOGLE_CLIENT_SECRET`, etc. in Render.
- **Add live demo link to README:**

  ```markdown
  ## Live demo
  [Try it live](https://your-app.vercel.app)
  ```

---

## Quick reference: secrets that must stay secret

| Secret              | Where to set        | Used for              |
|---------------------|---------------------|------------------------|
| `GEMINI_API_KEY`    | Render env          | LLM queries           |
| `SECRET_KEY`        | Render env          | JWT signing           |
| `DATABASE_URL`      | Render env (auto)   | PostgreSQL            |
| `OAUTH_*_SECRET`    | Render env          | OAuth providers       |
| `VITE_API_BASE_URL` | Vercel env          | Public, not a secret  |

---

## Summary

1. Push code to GitHub (no `.env` or secrets committed).
2. Create Render Web Service + PostgreSQL, add `DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`, `APP_ENV`, `LLM_PROVIDER`, `BACKEND_CORS_ORIGINS`.
3. Deploy Vercel frontend with Root Directory `frontend` and `VITE_API_BASE_URL` pointing to Render.
4. Set `BACKEND_CORS_ORIGINS` to your Vercel URL.
5. Test signup, login, upload, and a query.

You’re done.
