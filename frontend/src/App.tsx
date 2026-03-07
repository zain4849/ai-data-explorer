import { useState } from "react";
import {
  Alert,
  AppBar,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Divider,
  Grid,
  Paper,
  Stack,
  Toolbar,
  Typography,
} from "@mui/material";
import AutoGraphRoundedIcon from "@mui/icons-material/AutoGraphRounded";
import CloudUploadRoundedIcon from "@mui/icons-material/CloudUploadRounded";
import InsightsRoundedIcon from "@mui/icons-material/InsightsRounded";
import QueryStatsRoundedIcon from "@mui/icons-material/QueryStatsRounded";
import StorageRoundedIcon from "@mui/icons-material/StorageRounded";
import TableChartRoundedIcon from "@mui/icons-material/TableChartRounded";
import { runQuery } from "./api/client";
import QuerySection from "./components/QuerySection";
import UploadSection from "./components/UploadSection";
import type { QueryResponse, UploadResponse } from "./types/api";
import ChartView from "./components/ChartView";
import InsightsPanel from "./components/InsightsPanel";
import ResultsTable from "./components/ResultsTable";

function App() {
  const [data, setData] = useState<QueryResponse | null>(null);
  const [dataset, setDataset] = useState<UploadResponse | null>(null);
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

  const stats = [
    {
      label: "Rows",
      value: dataset ? dataset.row_count.toLocaleString() : "--",
      icon: <StorageRoundedIcon fontSize="small" color="primary" />,
    },
    {
      label: "Columns",
      value: dataset ? String(dataset.columns.length) : "--",
      icon: <TableChartRoundedIcon fontSize="small" color="primary" />,
    },
    {
      label: "Results",
      value: data ? String(data.result.length) : "--",
      icon: <QueryStatsRoundedIcon fontSize="small" color="primary" />,
    },
  ];

  return (
    <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
      {/* Top bar */}
      <AppBar
        position="static"
        elevation={0}
        sx={{
          bgcolor: "primary.main",
          borderBottom: "1px solid",
          borderColor: "primary.dark",
        }}
      >
        <Toolbar sx={{ gap: 2 }}>
          <AutoGraphRoundedIcon />
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            AI Data Explorer
          </Typography>
          <Stack direction="row" spacing={2}>
            {stats.map((s) => (
              <Stack
                key={s.label}
                direction="row"
                spacing={0.75}
                alignItems="center"
                sx={{ color: "rgba(255,255,255,0.85)" }}
              >
                {s.icon}
                <Typography variant="body2" sx={{ color: "inherit" }}>
                  {s.label}:
                </Typography>
                <Typography variant="body2" fontWeight={700} sx={{ color: "#fff" }}>
                  {s.value}
                </Typography>
              </Stack>
            ))}
          </Stack>
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ py: 3 }}>
        <Grid container spacing={2.5}>
          {/* ---- Left column: Upload + Query ---- */}
          <Grid size={{ xs: 12, md: 4 }}>
            <Stack spacing={2.5}>
              {/* Upload card */}
              <Card variant="outlined" sx={{ borderRadius: 3 }}>
                <CardContent sx={{ p: 2.5, "&:last-child": { pb: 2.5 } }}>
                  <Stack spacing={2}>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <CloudUploadRoundedIcon color="primary" fontSize="small" />
                      <Typography variant="subtitle1" fontWeight={700}>
                        Dataset
                      </Typography>
                    </Stack>
                    <UploadSection onUploadSuccess={setDataset} />
                    {dataset && (
                      <Stack spacing={0.75}>
                        <Typography variant="caption" color="text.secondary">
                          Columns
                        </Typography>
                        <Stack direction="row" spacing={0.5} useFlexGap flexWrap="wrap">
                          {dataset.columns.slice(0, 14).map((col) => (
                            <Chip
                              key={col}
                              label={col}
                              size="small"
                              variant="outlined"
                              sx={{ fontSize: 11 }}
                            />
                          ))}
                          {dataset.columns.length > 14 && (
                            <Chip
                              label={`+${dataset.columns.length - 14}`}
                              size="small"
                              sx={{ fontSize: 11 }}
                            />
                          )}
                        </Stack>
                      </Stack>
                    )}
                  </Stack>
                </CardContent>
              </Card>

              {/* Query card */}
              <Card variant="outlined" sx={{ borderRadius: 3 }}>
                <CardContent sx={{ p: 2.5, "&:last-child": { pb: 2.5 } }}>
                  <Stack spacing={2}>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <AutoGraphRoundedIcon color="primary" fontSize="small" />
                      <Typography variant="subtitle1" fontWeight={700}>
                        Query
                      </Typography>
                    </Stack>
                    <QuerySection
                      onSubmit={handleQuery}
                      disabled={isQuerying || !dataset}
                    />
                    {!dataset && (
                      <Alert severity="info" variant="outlined">
                        Upload a CSV first.
                      </Alert>
                    )}
                    {isQuerying && (
                      <Stack direction="row" spacing={1} alignItems="center">
                        <CircularProgress size={16} />
                        <Typography variant="caption" color="text.secondary">
                          Generating SQL and insights...
                        </Typography>
                      </Stack>
                    )}
                    {queryError && <Alert severity="error">{queryError}</Alert>}
                  </Stack>
                </CardContent>
              </Card>
            </Stack>
          </Grid>

          {/* ---- Right column: Results ---- */}
          <Grid size={{ xs: 12, md: 8 }}>
            <Card
              variant="outlined"
              sx={{ borderRadius: 3, minHeight: 400 }}
            >
              <CardContent sx={{ p: 2.5, "&:last-child": { pb: 2.5 } }}>
                {data ? (
                  <Stack spacing={2.5}>
                    <Stack direction="row" spacing={1} alignItems="center">
                      <InsightsRoundedIcon color="primary" fontSize="small" />
                      <Typography variant="subtitle1" fontWeight={700}>
                        Results
                      </Typography>
                    </Stack>

                    <Divider />

                    {/* SQL */}
                    <Box>
                      <Typography variant="caption" color="text.secondary" gutterBottom>
                        Generated SQL
                      </Typography>
                      <Box
                        component="pre"
                        sx={{
                          m: 0,
                          mt: 0.5,
                          p: 1.5,
                          borderRadius: 2,
                          fontSize: 13,
                          fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                          lineHeight: 1.6,
                          overflow: "auto",
                          bgcolor: "#1e1e2e",
                          color: "#cdd6f4",
                          border: "1px solid",
                          borderColor: "divider",
                        }}
                      >
                        {data.sql}
                      </Box>
                    </Box>

                    {/* Chart */}
                    <Box>
                      <Typography variant="caption" color="text.secondary" gutterBottom>
                        Visualization
                      </Typography>
                      <Paper
                        variant="outlined"
                        sx={{ mt: 0.5, p: 1.5, borderRadius: 2, overflow: "hidden" }}
                      >
                        <ChartView chartHtml={data.chart_html} />
                      </Paper>
                    </Box>

                    {/* Insights */}
                    <Box>
                      <Typography variant="caption" color="text.secondary" gutterBottom>
                        AI insights
                      </Typography>
                      <Paper variant="outlined" sx={{ mt: 0.5, p: 2, borderRadius: 2 }}>
                        <InsightsPanel insights={data.insights} />
                      </Paper>
                    </Box>

                    {/* Table */}
                    <Box>
                      <Typography variant="caption" color="text.secondary" gutterBottom>
                        Data ({data.result.length} rows)
                      </Typography>
                      <Box sx={{ mt: 0.5 }}>
                        <ResultsTable rows={data.result} />
                      </Box>
                    </Box>
                  </Stack>
                ) : (
                  <Stack
                    spacing={1.5}
                    alignItems="center"
                    justifyContent="center"
                    sx={{
                      height: "100%",
                      minHeight: 360,
                      textAlign: "center",
                      py: 6,
                    }}
                  >
                    <InsightsRoundedIcon
                      sx={{ fontSize: 48, color: "action.disabled" }}
                    />
                    <Typography variant="h6" color="text.secondary">
                      No results yet
                    </Typography>
                    <Typography
                      variant="body2"
                      color="text.disabled"
                      sx={{ maxWidth: 380 }}
                    >
                      Upload a CSV and run a query to see the generated SQL, chart,
                      insights, and data table here.
                    </Typography>
                  </Stack>
                )}
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
}

export default App;
