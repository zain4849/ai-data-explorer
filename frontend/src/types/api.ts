export interface QueryResponse {
    sql: string,
    result: Record<string, any>[],
    insights: string,
    chart_html: string, // HTML string
}