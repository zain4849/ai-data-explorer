import { BASE_URL, fetchWithRetry, getAuthHeaders } from "./core";

export interface DatasetInfo {
  id: string;
  name: string;
  table_name: string;
  file_type: string;
  row_count: number;
  columns: string[];
  created_at: string;
}

export async function listDatasets(): Promise<DatasetInfo[]> {
  const res = await fetchWithRetry(`${BASE_URL}/datasets`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new Error("Failed to list datasets");
  return res.json();
}

export async function deleteDataset(id: string): Promise<void> {
  const res = await fetchWithRetry(`${BASE_URL}/datasets/${id}`, {
    method: "DELETE",
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new Error("Failed to delete dataset");
}
