import { useState } from "react";
import { runQuery } from "./api/client";
import "./App.css";
import QuerySection from "./components/QuerySection";
import UploadSection from "./components/UploadSection";
import type { QueryResponse } from "./types/api";
import ChartView from "./components/ChartView";
import InsightsPanel from "./components/InsightsPanel";

function App() {
  const [data, setData] = useState<QueryResponse | null>(null);

  const handleQuery = async (query: string) => {
    try {
      const response = await runQuery(query);
      setData(response);
    } catch {
      alert("Query failed");
    }
  };

  return (
    <>
      <UploadSection />
      <QuerySection onSubmit={handleQuery} />

      {data && (
        <>
          <h3>Generated SQL</h3>
          <pre>{data.sql}</pre>

          {/* <ResultsTable rows={data}/> */}
          <ChartView chartHtml={data.chart_html}/>
          <InsightsPanel insights={data.insights}/>
        </>
      )}
    </>
  );
}

export default App;
