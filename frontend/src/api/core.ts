/** Shared fetch utilities and config for API calls. */

export const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/v1";

const REQUEST_TIMEOUT_MS = 30_000;
const TOKEN_KEY = "data-explorer-tokens";

export function getAuthHeaders(): Record<string, string> {
  try {
    const raw = localStorage.getItem(TOKEN_KEY);
    if (raw) {
      const { access_token } = JSON.parse(raw);
      if (access_token) return { Authorization: `Bearer ${access_token}` };
    }
  } catch { /* ignore */ }
  return {};
}

async function fetchWithTimeout(
  input: RequestInfo | URL,
  init?: RequestInit,
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    return await fetch(input, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timer);
  }
}

export async function fetchWithRetry(
  input: RequestInfo | URL,
  init?: RequestInit,
  retries = 2,
): Promise<Response> {
  let lastError: unknown;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetchWithTimeout(input, init);
      if (res.ok || res.status < 500) return res;
      lastError = new Error(`HTTP ${res.status}`);
    } catch (err) {
      lastError = err;
    }
    if (attempt < retries) {
      await new Promise((r) => setTimeout(r, 1000 * 2 ** attempt));
    }
  }
  throw lastError;
}
