import type { QueryResponse, UploadResponse } from "../types/api";
import { BASE_URL, fetchWithRetry, getAuthHeaders } from "./core";

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
  //
  // FormData {
  //   file: File("data.csv")
  // }
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetchWithRetry(`${BASE_URL}/datasets`, {
    method: "POST",
    body: formData,
    headers: { ...getAuthHeaders() },
  });

  if (!response.ok) throw new Error("Failed to upload csv file");

  return response.json();
}

export async function runQuery(
  query: string,
  connectionId?: string,
): Promise<QueryResponse> {
  const params = new URLSearchParams({ nl_query: query });
  if (connectionId) params.set("connection_id", connectionId); // Only if we have a connector like postgres, mysql, sqlite, etc.

  const response = await fetchWithRetry(
    `${BASE_URL}/queries?${params.toString()}`,
    { headers: { ...getAuthHeaders() } },
  );

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    const detail =
      typeof err?.detail === "string" ? err.detail : "Query failed";
    throw new Error(detail);
  }

  return response.json();
}  // {
  //    "sql": sql,
  //    "result": dataframe_to_json_records(df, 50),
  //    "insights": insights,
  //    "chart_html": chart_html
  // }

export async function executeSQL(
  sql: string,
  connectionId?: string,
): Promise<QueryResponse> {
  const response = await fetchWithRetry(`${BASE_URL}/query/execute`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ sql, connection_id: connectionId }),
  });
  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    const detail =
      typeof err?.detail === "string" ? err.detail : "SQL execution failed";
    throw new Error(detail);
  }
  return response.json();
}
