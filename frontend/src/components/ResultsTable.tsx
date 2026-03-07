import React from "react";
import {
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

interface ResultsTableProps {
  rows: Record<string, unknown>[];
}

const ResultsTable: React.FC<ResultsTableProps> = ({ rows }) => {
  if (!rows || rows.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No rows returned for this query.
      </Typography>
    );
  }

  const columns = Object.keys(rows[0] ?? {});

  return (
    <TableContainer
      component={Paper}
      elevation={0}
      sx={{
        maxHeight: 420,
        borderRadius: 3,
        border: "1px solid",
        borderColor: "divider",
      }}
    >
      <Table stickyHeader size="small">
        <TableHead>
          <TableRow>
            {columns.map((col) => (
              <TableCell
                key={col}
                sx={{
                  fontWeight: 700,
                  bgcolor: "background.paper",
                }}
              >
                {col}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {rows.map((row, idx) => (
            <TableRow key={idx} hover>
              {columns.map((col) => (
                <TableCell
                  key={col}
                  sx={{
                    maxWidth: 240,
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {String((row as Record<string, unknown>)[col] ?? "")}
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default ResultsTable;