import React, { useCallback, useEffect, useState } from "react";
import {
  alpha,
  Box,
  Button,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Paper,
  Stack,
  TextField,
  Tooltip,
  Typography,
  useTheme,
} from "@mui/material";
import CodeRoundedIcon from "@mui/icons-material/CodeRounded";
import BarChartRoundedIcon from "@mui/icons-material/BarChartRounded";
import TableChartRoundedIcon from "@mui/icons-material/TableChartRounded";
import ExpandMoreRoundedIcon from "@mui/icons-material/ExpandMoreRounded";
import ExpandLessRoundedIcon from "@mui/icons-material/ExpandLessRounded";
import PlayArrowRoundedIcon from "@mui/icons-material/PlayArrowRounded";
import EditRoundedIcon from "@mui/icons-material/EditRounded";
import DownloadRoundedIcon from "@mui/icons-material/DownloadRounded";
import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import type { ChatMessage } from "../types/chat";
import {
  executeSQL,
  exportData,
  addTileToDashboard,
  listDashboards,
  createDashboard,
  type DashboardInfo,
} from "../api/client";
import { useAuth } from "../context/AuthContext";
import ChartView from "./ChartView";
import InsightsPanel from "./InsightsPanel";
import ResultsTable from "./ResultsTable";

interface AIResponseCardProps {
  message: ChatMessage;
  connectionId?: string | null;
  onSnackbar?: (message: string, severity?: "error" | "success" | "info") => void;
}

interface CollapsibleSectionProps {
  icon: React.ReactNode;
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
  actions?: React.ReactNode;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  icon,
  title,
  defaultOpen = false,
  children,
  actions,
}) => {
  const [open, setOpen] = useState(defaultOpen);
  const theme = useTheme();

  return (
    <Box>
      <Stack
        direction="row"
        alignItems="center"
        spacing={1}
        sx={{ py: 0.75, px: 0.5 }}
      >
        <Stack
          direction="row"
          alignItems="center"
          spacing={1}
          onClick={() => setOpen(!open)}
          sx={{
            cursor: "pointer",
            flex: 1,
            borderRadius: 1.5,
            "&:hover": { bgcolor: alpha(theme.palette.text.primary, 0.04) },
          }}
        >
          {icon}
          <Typography
            variant="caption"
            sx={{ fontWeight: 600, color: "text.secondary", flex: 1 }}
          >
            {title}
          </Typography>
          <IconButton size="small" sx={{ p: 0.2 }}>
            {open ? (
              <ExpandLessRoundedIcon sx={{ fontSize: 18, color: "text.secondary" }} />
            ) : (
              <ExpandMoreRoundedIcon sx={{ fontSize: 18, color: "text.secondary" }} />
            )}
          </IconButton>
        </Stack>
        {actions}
      </Stack>
      <Collapse in={open}>
        <Box sx={{ pt: 0.5, pb: 1 }}>{children}</Box>
      </Collapse>
    </Box>
  );
};

const AIResponseCard: React.FC<AIResponseCardProps> = ({
  message,
  connectionId,
  onSnackbar,
}) => {
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";
  const { user } = useAuth();
  const [isEditing, setIsEditing] = useState(false);
  const [editedSql, setEditedSql] = useState(message.sql || "");
  const [isRunning, setIsRunning] = useState(false);
  const [runResult, setRunResult] = useState<{
    tableData?: Record<string, unknown>[];
    chartHtml?: string;
    insights?: string;
  } | null>(null);

  // Add to dashboard
  const [addToDashboardOpen, setAddToDashboardOpen] = useState(false);
  const [dashboards, setDashboards] = useState<DashboardInfo[]>([]);
  const [isAddingTile, setIsAddingTile] = useState(false);
  const [newDashboardTitle, setNewDashboardTitle] = useState("");

  const loadDashboards = useCallback(async () => {
    try {
      const list = await listDashboards();
      setDashboards(list);
    } catch {
      setDashboards([]);
    }
  }, []);

  useEffect(() => {
    if (addToDashboardOpen) loadDashboards();
  }, [addToDashboardOpen, loadDashboards]);

  const handleAddToDashboard = async (dashboardId: string, chartHtml: string) => {
    setIsAddingTile(true);
    try {
      await addTileToDashboard(dashboardId, {
        tile_type: "chart",
        title: message.content?.slice(0, 80) || "Chart",
        config_json: JSON.stringify({ chart_html: chartHtml }),
      });
      setAddToDashboardOpen(false);
      onSnackbar?.("Added to dashboard!", "success");
    } catch (err) {
      onSnackbar?.(err instanceof Error ? err.message : "Failed to add tile", "error");
    } finally {
      setIsAddingTile(false);
    }
  };

  const handleCreateAndAdd = async (chartHtml: string) => {
    if (!newDashboardTitle.trim()) return;
    setIsAddingTile(true);
    try {
      const dash = await createDashboard(newDashboardTitle.trim());
      await addTileToDashboard(dash.id, {
        tile_type: "chart",
        title: message.content?.slice(0, 80) || "Chart",
        config_json: JSON.stringify({ chart_html: chartHtml }),
      });
      setAddToDashboardOpen(false);
      setNewDashboardTitle("");
      onSnackbar?.("Added to dashboard!", "success");
    } catch (err) {
      onSnackbar?.(err instanceof Error ? err.message : "Failed to add tile", "error");
    } finally {
      setIsAddingTile(false);
    }
  };

  const handleRunSQL = async () => {
    if (!editedSql.trim()) return;
    setIsRunning(true);
    try {
      const resp = await executeSQL(editedSql, connectionId ?? undefined);
      setRunResult({
        tableData: resp.result,
        chartHtml: resp.chart_html,
        insights: resp.insights,
      });
      setIsEditing(false);
    } catch {
      // Errors handled via snackbar at parent level
    } finally {
      setIsRunning(false);
    }
  };

  const handleExport = async (format: "csv" | "xlsx") => {
    try {
      const sql = editedSql || message.sql;
      const blob = await exportData(format, {
        sql: sql || undefined,
        connection_id: connectionId ?? undefined,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `export.${format}`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      /* ignore */
    }
  };

  const displayData = runResult?.tableData ?? message.tableData;
  const displayChart = runResult?.chartHtml ?? message.chartHtml;
  const displayInsights = runResult?.insights ?? message.insights;

  return (
    <Paper
      elevation={0}
      sx={{
        bgcolor: isDark
          ? alpha(theme.palette.background.paper, 0.96)
          : theme.palette.background.paper,
        borderRadius: "18px 18px 18px 4px",
        px: 2.5,
        py: 2,
        border: "1px solid",
        borderColor: alpha(theme.palette.primary.main, isDark ? 0.18 : 0.12),
        boxShadow: isDark
          ? "0 20px 40px rgba(0,0,0,0.18)"
          : "0 12px 28px rgba(45,50,48,0.05)",
      }}
    >
      <Stack spacing={1}>
        {/* Insights text */}
        {displayInsights && (
          <Box sx={{ pb: 0.5 }}>
            <InsightsPanel insights={displayInsights} />
          </Box>
        )}

        {/* Chart */}
        {displayChart && (
          <>
            <Divider sx={{ opacity: 0.5 }} />
            <CollapsibleSection
              icon={<BarChartRoundedIcon sx={{ fontSize: 16, color: "primary.dark" }} />}
              title="Visualization"
              defaultOpen
              actions={
                user ? (
                  <Tooltip title="Add to dashboard">
                    <IconButton
                      size="small"
                      onClick={() => setAddToDashboardOpen(true)}
                      sx={{ p: 0.4 }}
                    >
                      <DashboardRoundedIcon sx={{ fontSize: 14 }} />
                    </IconButton>
                  </Tooltip>
                ) : undefined
              }
            >
              <Box
                sx={{
                  borderRadius: 2,
                  overflow: "hidden",
                  bgcolor: isDark
                    ? alpha(theme.palette.background.default, 0.8)
                    : theme.palette.background.paper,
                  border: "1px solid",
                  borderColor: "divider",
                }}
              >
                <ChartView chartHtml={displayChart} />
              </Box>
            </CollapsibleSection>
          </>
        )}

        {/* Add to dashboard dialog */}
        <Dialog
          open={addToDashboardOpen}
          onClose={() => !isAddingTile && setAddToDashboardOpen(false)}
          maxWidth="xs"
          fullWidth
        >
          <DialogTitle>Add to dashboard</DialogTitle>
          <DialogContent>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Choose a dashboard or create a new one
            </Typography>
            <List dense disablePadding>
              {dashboards.map((d) => (
                <ListItemButton
                  key={d.id}
                  onClick={() => displayChart && handleAddToDashboard(d.id, displayChart)}
                  disabled={isAddingTile}
                >
                  <ListItemText primary={d.title} secondary={`${d.tiles.length} tiles`} />
                </ListItemButton>
              ))}
            </List>
            <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
              <TextField
                size="small"
                label="New dashboard title"
                value={newDashboardTitle}
                onChange={(e) => setNewDashboardTitle(e.target.value)}
                fullWidth
                placeholder="e.g. Indian disease analysis"
              />
              <Button
                variant="contained"
                startIcon={<AddRoundedIcon />}
                onClick={() => displayChart && handleCreateAndAdd(displayChart)}
                disabled={!newDashboardTitle.trim() || isAddingTile}
                sx={{ flexShrink: 0 }}
              >
                {isAddingTile ? "Adding..." : "Create & Add"}
              </Button>
            </Stack>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setAddToDashboardOpen(false)} disabled={isAddingTile}>
              Cancel
            </Button>
          </DialogActions>
        </Dialog>

        {/* SQL (editable) */}
        {message.sql && (
          <>
            <Divider sx={{ opacity: 0.5 }} />
            <CollapsibleSection
              icon={<CodeRoundedIcon sx={{ fontSize: 16, color: "primary.dark" }} />}
              title="Generated SQL"
              actions={
                <Stack direction="row" spacing={0.5}>
                  <Tooltip title={isEditing ? "Cancel edit" : "Edit SQL"}>
                    <IconButton
                      size="small"
                      onClick={() => {
                        setIsEditing(!isEditing);
                        if (!isEditing) setEditedSql(message.sql || "");
                      }}
                      sx={{ p: 0.4 }}
                    >
                      <EditRoundedIcon sx={{ fontSize: 14 }} />
                    </IconButton>
                  </Tooltip>
                  {isEditing && (
                    <Button
                      size="small"
                      variant="contained"
                      startIcon={<PlayArrowRoundedIcon sx={{ fontSize: 14 }} />}
                      onClick={handleRunSQL}
                      disabled={isRunning}
                      sx={{ fontSize: "0.7rem", py: 0.25, px: 1 }}
                    >
                      {isRunning ? "Running..." : "Run"}
                    </Button>
                  )}
                </Stack>
              }
            >
              {isEditing ? (
                <TextField
                  multiline
                  fullWidth
                  value={editedSql}
                  onChange={(e) => setEditedSql(e.target.value)}
                  sx={{
                    "& .MuiInputBase-root": {
                      fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                      fontSize: 12.5,
                      lineHeight: 1.6,
                      bgcolor: isDark ? "#0A0A0A" : "#1A1A1A",
                      color: isDark ? "#B0B0B0" : "#C8C8C8",
                    },
                  }}
                />
              ) : (
                <Box
                  component="pre"
                  sx={{
                    m: 0,
                    p: 1.5,
                    borderRadius: 2,
                    fontSize: 12.5,
                    fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                    lineHeight: 1.6,
                    overflow: "auto",
                    bgcolor: isDark ? "#0A0A0A" : "#1A1A1A",
                    color: isDark ? "#B0B0B0" : "#C8C8C8",
                    border: `1px solid ${isDark ? "rgba(255,255,255,0.08)" : "rgba(255,255,255,0.06)"}`,
                  }}
                >
                  {editedSql || message.sql}
                </Box>
              )}
            </CollapsibleSection>
          </>
        )}

        {/* Data table */}
        {displayData && displayData.length > 0 && (
          <>
            <Divider sx={{ opacity: 0.5 }} />
            <CollapsibleSection
              icon={
                <TableChartRoundedIcon sx={{ fontSize: 16, color: "primary.dark" }} />
              }
              title={`Data (${displayData.length} rows)`}
              actions={
                <Stack direction="row" spacing={0.5}>
                  <Tooltip title="Download CSV">
                    <IconButton size="small" onClick={() => handleExport("csv")} sx={{ p: 0.4 }}>
                      <DownloadRoundedIcon sx={{ fontSize: 14 }} />
                    </IconButton>
                  </Tooltip>
                </Stack>
              }
            >
              <ResultsTable rows={displayData} />
            </CollapsibleSection>
          </>
        )}
      </Stack>
    </Paper>
  );
};

export default AIResponseCard;
