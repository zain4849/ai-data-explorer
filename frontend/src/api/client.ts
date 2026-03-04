const BASE_URL = "http://localhost:8000";

export async function uploadCsv(file: File) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${BASE_URL}/upload_csv`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error("Failed to upload csv file");

  return response.json(); // Will get first 5 records for confirmation
}

export async function runQuery(query: string) {
  const response = await fetch(
    `${BASE_URL}/query?nl_query=${encodeURIComponent(query)}`,
  );

  if (!response.ok) throw new Error("Query failed");

  return response.json();
  // {
  //    "sql": sql,
  //    "result": dataframe_to_json_records(df, 50),
  //    "insights": insights,
  //    "chart_html": chart_html
  // }
}
