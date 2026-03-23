/**
 * API client barrel file.
 * Re-exports all API functions and types from domain modules.
 */

// Query (upload, runQuery, executeSQL)
export { executeSQL, runQuery, uploadFile } from "./query";

// Connections
export {
  createConnection,
  deleteConnection,
  getTableSchema,
  listConnections,
  listTables,
  sampleTable,
  testConnection,
} from "./connections";
export type {
  ColumnInfoApi,
  ConnectionInfo,
  ConnectionPayload,
  TableInfoApi,
} from "./connections";

// Dashboards
export {
  addTileToDashboard,
  createDashboard,
  listDashboards,
} from "./dashboards";
export type {
  AddTileRequest,
  DashboardInfo,
  DashboardTileInfo,
} from "./dashboards";

// Datasets
export { deleteDataset, listDatasets } from "./datasets";
export type { DatasetInfo } from "./datasets";

// Chat
export {
  addChatMessage,
  createChatThread,
  deleteChatThread,
  getChatThread,
  listChatThreads,
  updateChatThread,
} from "./chat";
export type {
  ChatMessageApi,
  ChatThreadApi,
  ChatThreadDetail,
} from "./chat";

// Export
export { exportData } from "./export";
