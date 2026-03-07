export interface QueryResponse {
    sql: string,
    result: Record<string, unknown>[],
    insights: string,
    chart_html: string, // HTML string
}

export interface UploadResponse {
    preview: Record<string, unknown>[],
    row_count: number,
    columns: string[],
}