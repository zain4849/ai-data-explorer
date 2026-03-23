import type { UploadResponse } from "../types/api";
import { BASE_URL, fetchWithRetry, getAuthHeaders } from "./core";

export interface ChatThreadApi {
  id: string;
  title: string;
  message_count: number;
  dataset_info: UploadResponse | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessageApi {
  id: string;
  role: string;
  content: string;
  sql?: string | null;
  result_json?: string | null;
  chart_html?: string | null;
  insights?: string | null;
  explanation?: string | null;
  file_name?: string | null;
  created_at: string;
}

export interface ChatThreadDetail {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: ChatMessageApi[];
  dataset_info: UploadResponse | null;
}

export async function listChatThreads(): Promise<ChatThreadApi[]> {
  const res = await fetchWithRetry(`${BASE_URL}/chat/threads`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new Error("Failed to list chat threads");
  return res.json();
}

export async function createChatThread(title?: string): Promise<ChatThreadDetail> {
  const res = await fetchWithRetry(`${BASE_URL}/chat/threads`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify({ title: title ?? "New Chat" }),
  });
  if (!res.ok) throw new Error("Failed to create chat thread");
  return res.json();
}

export async function getChatThread(threadId: string): Promise<ChatThreadDetail> {
  const res = await fetchWithRetry(`${BASE_URL}/chat/threads/${threadId}`, {
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new Error("Failed to get chat thread");
  return res.json();
}

export async function updateChatThread(
  threadId: string,
  update: { title?: string },
): Promise<ChatThreadDetail> {
  const res = await fetchWithRetry(`${BASE_URL}/chat/threads/${threadId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(update),
  });
  if (!res.ok) throw new Error("Failed to update chat thread");
  return res.json();
}

export async function deleteChatThread(threadId: string): Promise<void> {
  const res = await fetchWithRetry(`${BASE_URL}/chat/threads/${threadId}`, {
    method: "DELETE",
    headers: { ...getAuthHeaders() },
  });
  if (!res.ok) throw new Error("Failed to delete chat thread");
}

export async function addChatMessage(
  threadId: string,
  message: {
    role: string;
    content: string;
    sql?: string;
    result_json?: string;
    chart_html?: string;
    insights?: string;
    explanation?: string;
    file_name?: string;
  },
): Promise<ChatMessageApi> {
  const res = await fetchWithRetry(`${BASE_URL}/chat/threads/${threadId}/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...getAuthHeaders() },
    body: JSON.stringify(message),
  });
  if (!res.ok) throw new Error("Failed to add message");
  return res.json();
}
