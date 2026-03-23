import { BASE_URL, fetchWithRetry, getAuthHeaders } from "./core";

export interface DashboardInfo {
  id: string;
  title: string;
  description?: string;
  tiles: DashboardTileInfo[];
  created_at: string;
}

export interface DashboardTileInfo {
  id: string;
  tile_type: string;
  title?: string;
  config_json: string;
  grid_x: number;
  grid_y: number;
  grid_w: number;
  grid_h: number;
}

export interface AddTileRequest {
  tile_type: string;
  title?: string;
  config_json: string;
  grid_x?: number;
  grid_y?: number;
  grid_w?: number;
  grid_h?: number;
}

export async function listDashboards(): Promise<DashboardInfo[]> {
  const res = await fetchWithRetry(`${BASE_URL}/dashboards`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new Error("Failed to list dashboards");
  return res.json();
}

export async function createDashboard(title: string, description?: string): Promise<DashboardInfo> {
  const res = await fetchWithRetry(`${BASE_URL}/dashboards`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ title, description }),
  });
  if (!res.ok) throw new Error("Failed to create dashboard");
  return res.json();
}

export async function addTileToDashboard(
  dashboardId: string,
  tile: AddTileRequest
): Promise<DashboardTileInfo> {
  const res = await fetchWithRetry(`${BASE_URL}/dashboards/${dashboardId}/tiles`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(tile),
  });
  if (!res.ok) throw new Error("Failed to add tile to dashboard");
  return res.json();
}
