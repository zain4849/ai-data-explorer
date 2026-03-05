import { useState } from "react";
import { runQuery } from "./api/client";
import "./App.css";
import QuerySection from "./components/QuerySection";
import UploadSection from "./components/UploadSection";
import type { QueryResponse } from "./types/api";
import ChartView from "./components/ChartView";
import InsightsPanel from "./components/InsightsPanel";
import ResultsTable from "./components/ResultsTable";

function App() {
  const [data, setData] = useState<QueryResponse | null>(null);
  const [isQuerying, setIsQuerying] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);

  const handleQuery = async (query: string) => {
    setIsQuerying(true);
    setQueryError(null);
    try {
      const response = await runQuery(query);
      setData(response);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Query failed. Please try again.";
      setQueryError(message);
    } finally {
      setIsQuerying(false);
    }
  };

  return (
    <div className="app-root">
      <header className="app-header">
        <h1>AI Data Explorer</h1>
        <p>Upload any CSV and ask questions in plain English.</p>
      </header>

      <main className="app-main">
        <section className="app-left">
          <h2>Data & Query</h2>
          <UploadSection />
          <QuerySection onSubmit={handleQuery} />
          {isQuerying && <p>Running query...</p>}
          {queryError && <p style={{ color: "red" }}>{queryError}</p>}
          {!data && !isQuerying && !queryError && (
            <p style={{ marginTop: "1rem" }}>
              Upload a CSV, then enter a question about your data to see
              results here.
            </p>
          )}
        </section>

        <section className="app-right">
          <h2>Results</h2>
          {data ? (
            <>
              <h3>Generated SQL</h3>
              <pre>{data.sql}</pre>

              <ResultsTable rows={data.result} />
              <ChartView chartHtml={data.chart_html} />
              <InsightsPanel insights={data.insights} />
            </>
          ) : (
            <p>No results yet.</p>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
