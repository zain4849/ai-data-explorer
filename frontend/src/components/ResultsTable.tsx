import React from "react";

interface ResultsTableProps {
  rows: Record<string, unknown>[];
}

const ResultsTable: React.FC<ResultsTableProps> = ({ rows }) => {
  if (!rows || rows.length === 0) {
    return <p>No rows returned for this query.</p>;
  }

  const columns = Object.keys(rows[0] ?? {});

  return (
    <div style={{ maxHeight: "400px", overflow: "auto", marginTop: "1rem" }}>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                style={{
                  position: "sticky",
                  top: 0,
                  background: "#f5f5f5",
                  textAlign: "left",
                  padding: "0.5rem",
                  borderBottom: "1px solid #ddd",
                }}
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx}>
              {columns.map((col) => (
                <td
                  key={col}
                  style={{
                    padding: "0.5rem",
                    borderBottom: "1px solid #eee",
                    fontSize: "0.9rem",
                  }}
                >
                  {String((row as Record<string, unknown>)[col] ?? "")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ResultsTable;