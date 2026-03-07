import type { QueryResponse, UploadResponse } from "../types/api";

const BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function uploadCSV(file: File): Promise<UploadResponse> {
  // If customer uploads a file called customers.csv, the file object will look like this:
  // File {
  //   name: "customers.csv",
  //   size: 24,
  //   type: "text/csv",
  //   lastModified: 1709650000000,
  //   lastModifiedDate: Wed Mar 05 2026 12:30:00 GMT+0000,
  //   webkitRelativePath: ""
  // }
  
  // FormData {
  //   file: File("data.csv")
  // }
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/upload_csv`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error("Failed to upload csv file");

  console.log("good so far")

  return response.json();
}

export async function runQuery(query: string): Promise<QueryResponse> {
  const response = await fetch(
    `${BASE_URL}/query?nl_query=${encodeURIComponent(query)}`,
  );

  if (!response.ok) throw new Error("Query failed");

  return response.json();
}
  // {
  //    "sql": sql,
  //    "result": dataframe_to_json_records(df, 50),
  //    "insights": insights,
  //    "chart_html": chart_html
  // }