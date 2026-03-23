import { useCallback, useEffect, useState } from "react";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Stack,
  TextField,
  Typography,
  useTheme,
} from "@mui/material";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import ArrowBackRoundedIcon from "@mui/icons-material/ArrowBackRounded";
import {
  createDashboard,
  listDashboards,
  type DashboardInfo,
} from "../api/client";
import DashboardTile from "../components/DashboardTile";

interface DashboardPageProps {
  onBack: () => void;
}

export default function DashboardPage({ onBack }: DashboardPageProps) {
  const theme = useTheme();
  const [dashboards, setDashboards] = useState<DashboardInfo[]>([]);
  const [activeDashboard, setActiveDashboard] = useState<DashboardInfo | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newTitle, setNewTitle] = useState("");

  const load = useCallback(async () => {
    try {
      const list = await listDashboards();
      setDashboards(list);
    } catch {
      /* not authenticated or server error */
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    try {
      const dash = await createDashboard(newTitle.trim());
      setDashboards((prev) => [dash, ...prev]);
      setActiveDashboard(dash);
      setDialogOpen(false);
      setNewTitle("");
    } catch {
      /* ignore */
    }
  };

  if (activeDashboard) {
    return (
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column", height: "100vh", overflow: "auto" }}>
        <Stack direction="row" alignItems="center" spacing={1} sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
          <IconButton onClick={() => setActiveDashboard(null)}>
            <ArrowBackRoundedIcon />
          </IconButton>
          <Typography variant="h6" sx={{ flex: 1 }}>
            {activeDashboard.title}
          </Typography>
        </Stack>
        <Box sx={{ flex: 1, p: 3 }}>
          {activeDashboard.tiles.length === 0 ? (
            <Box sx={{ textAlign: "center", py: 10 }}>
              <DashboardRoundedIcon sx={{ fontSize: 48, color: "text.disabled", mb: 2 }} />
              <Typography color="text.secondary">
                This dashboard is empty. Add tiles from your query results to build it.
              </Typography>
            </Box>
          ) : (
            <Box
              sx={{
                display: "grid",
                gridTemplateColumns: "repeat(12, 1fr)",
                gap: 2,
              }}
            >
              {activeDashboard.tiles.map((tile) => (
                <Box
                  key={tile.id}
                  sx={{
                    gridColumn: `span ${tile.grid_w}`,
                    minHeight: tile.grid_h * 100,
                  }}
                >
                  <DashboardTile tile={tile} />
                </Box>
              ))}
            </Box>
          )}
        </Box>
      </Box>
    );
  }

  return (
    <Box sx={{ flex: 1, display: "flex", flexDirection: "column", height: "100vh", overflow: "auto" }}>
      <Stack direction="row" alignItems="center" spacing={1} sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
        <IconButton onClick={onBack}>
          <ArrowBackRoundedIcon />
        </IconButton>
        <Typography variant="h6" sx={{ flex: 1 }}>
          Dashboards
        </Typography>
        <Button
          variant="contained"
          size="small"
          startIcon={<AddRoundedIcon />}
          onClick={() => setDialogOpen(true)}
        >
          New Dashboard
        </Button>
      </Stack>

      <Box sx={{ flex: 1, p: 3 }}>
        {dashboards.length === 0 ? (
          <Box sx={{ textAlign: "center", py: 10 }}>
            <DashboardRoundedIcon sx={{ fontSize: 48, color: "text.disabled", mb: 2 }} />
            <Typography color="text.secondary">No dashboards yet</Typography>
            <Button
              variant="outlined"
              startIcon={<AddRoundedIcon />}
              onClick={() => setDialogOpen(true)}
              sx={{ mt: 2 }}
            >
              Create your first dashboard
            </Button>
          </Box>
        ) : (
          <Box
            sx={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))",
              gap: 2,
            }}
          >
            {dashboards.map((dash) => (
              <Paper
                key={dash.id}
                elevation={0}
                onClick={() => setActiveDashboard(dash)}
                sx={{
                  p: 2.5,
                  border: `1px solid ${theme.palette.divider}`,
                  borderRadius: 2,
                  cursor: "pointer",
                  "&:hover": { borderColor: "primary.main" },
                }}
              >
                <Typography variant="subtitle1" fontWeight={600}>
                  {dash.title}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {dash.tiles.length} tiles &middot; {new Date(dash.created_at).toLocaleDateString()}
                </Typography>
              </Paper>
            ))}
          </Box>
        )}
      </Box>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>New Dashboard</DialogTitle>
        <DialogContent>
          <TextField
            label="Title"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            fullWidth
            size="small"
            autoFocus
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={!newTitle.trim()}>
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
