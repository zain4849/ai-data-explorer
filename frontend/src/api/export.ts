import { BASE_URL, fetchWithRetry, getAuthHeaders } from "./core";

export async function exportData(
  format: "csv" | "xlsx" | "pdf" | "png" | "pptx",
  payload: { sql?: string; connection_id?: string; chart_html?: string },
): Promise<Blob> {
  const res = await fetchWithRetry(`${BASE_URL}/export/${format}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Export to ${format} failed`);
  return res.blob();
}
