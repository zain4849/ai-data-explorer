// ==== Not returned by the API, but used in the frontend ================================================
import type { UploadResponse } from "./api";

export interface ChatMessage {
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
    timestamp: number;
    sql?: string;
    chartHtml?: string;
    insights?: string;
    tableData?: Record<string, unknown>[];
    uploadInfo?: UploadResponse;
    fileName?: string;
    isLoading?: boolean;
}

export interface ChatThread {
    id: string;
    title: string;
    messages: ChatMessage[];
    datasetInfo: UploadResponse | null;
    createdAt: number;
    updatedAt: number;
}