import { BASE_URL, fetchWithRetry, getAuthHeaders } from "./core";

export interface ConnectionPayload {
  name: string;
  db_type: string;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
  file_path?: string;
  allow_ai_access?: boolean;
  max_rows_to_ai?: number;
  mask_columns?: string;
}

export interface ConnectionInfo {
  id: string;
  name: string;
  db_type: string;
  created_at: string;
  allow_ai_access: boolean;
}

export interface TableInfoApi {
  name: string;
  schema?: string;
  row_count?: number;
}

export interface ColumnInfoApi {
  name: string;
  type: string;
  is_pk?: boolean;
  fk_reference?: string;
  known_values?: string[];
}

export async function listConnections(): Promise<ConnectionInfo[]> {
  const res = await fetchWithRetry(`${BASE_URL}/connections`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new Error("Failed to list connections");
  return res.json();
}

export async function createConnection(payload: ConnectionPayload): Promise<ConnectionInfo> {
  const res = await fetchWithRetry(`${BASE_URL}/connections`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Failed to create connection");
  }
  return res.json();
}

export async function deleteConnection(id: string): Promise<void> {
  const res = await fetchWithRetry(`${BASE_URL}/connections/${id}`, {
    method: "DELETE",
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new Error("Failed to delete connection");
}

export async function testConnection(id: string): Promise<{ ok: boolean; error?: string }> {
  const res = await fetchWithRetry(`${BASE_URL}/connections/${id}/test`, {
    method: "POST",
    headers: { ...getAuthHeaders() },
  });
  return res.json();
}

export async function listTables(connectionId: string): Promise<TableInfoApi[]> {
  const res = await fetchWithRetry(`${BASE_URL}/connections/${connectionId}/tables`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new Error("Failed to list tables");
  return res.json();
}

export async function getTableSchema(connectionId: string, table: string): Promise<ColumnInfoApi[]> {
  const res = await fetchWithRetry(
    `${BASE_URL}/connections/${connectionId}/tables/${encodeURIComponent(table)}/schema`,
    { headers: { ...getAuthHeaders() } },
  );
  if (!res.ok) throw new Error("Failed to get table schema");
  return res.json();
}

export async function sampleTable(connectionId: string, table: string): Promise<Record<string, unknown>[]> {
  const res = await fetchWithRetry(
    `${BASE_URL}/connections/${connectionId}/tables/${encodeURIComponent(table)}/sample`,
    { headers: { ...getAuthHeaders() } },
  );
  if (!res.ok) throw new Error("Failed to get table sample");
  return res.json();
}
