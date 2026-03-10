import type { QueryResponse, UploadResponse } from "../types/api";

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const REQUEST_TIMEOUT_MS = 30_000;

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

async function fetchWithRetry(
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

export async function uploadFile(file: File): Promise<UploadResponse> {
  // If customer uploads a file called customers.csv, the file object will look like this:
  // File {
  //   name: "customers.csv",
  //   size: 24,
  //   type: "text/csv",
  //   lastModified: 1709650000000,
  //   lastModifiedDate: Wed Mar 05 2026 12:30:00 GMT+0000,
  //   webkitRelativePath: ""
  // }
  
  // FormData {
  //   file: File("data.csv")
  // }
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetchWithRetry(`${BASE_URL}/upload_csv`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error("Failed to upload csv file");

  return response.json();
}

export async function runQuery(query: string): Promise<QueryResponse> {
  const response = await fetchWithRetry(
    `${BASE_URL}/query?nl_query=${encodeURIComponent(query)}`,
  );

  if (!response.ok) throw new Error("Query failed");

  return response.json();
}  // {
  //    "sql": sql,
  //    "result": dataframe_to_json_records(df, 50),
  //    "insights": insights,
  //    "chart_html": chart_html
  // }
