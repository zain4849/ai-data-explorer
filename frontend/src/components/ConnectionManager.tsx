import { useCallback, useEffect, useState } from "react";
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import StorageRoundedIcon from "@mui/icons-material/StorageRounded";
import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
import CheckCircleRoundedIcon from "@mui/icons-material/CheckCircleRounded";
import ErrorRoundedIcon from "@mui/icons-material/ErrorRounded";
import {
  createConnection,
  deleteConnection,
  listConnections,
  testConnection,
  type ConnectionInfo,
  type ConnectionPayload,
} from "../api/client";

interface ConnectionManagerProps {
  activeConnectionId: string | null;
  onSelectConnection: (id: string | null) => void;
}

const DB_TYPES = [
  { value: "postgresql", label: "PostgreSQL" },
  { value: "mysql", label: "MySQL" },
  { value: "sqlite", label: "SQLite" },
];

export default function ConnectionManager({
  activeConnectionId,
  onSelectConnection,
}: ConnectionManagerProps) {
  const [connections, setConnections] = useState<ConnectionInfo[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<
    Record<string, { ok: boolean; error?: string }>
  >({});

  // Form state
  const [form, setForm] = useState<ConnectionPayload>({
    name: "",
    db_type: "postgresql",
    host: "localhost",
    port: 5432,
    database: "",
    username: "",
    password: "",
    allow_ai_access: true,
  });

  const loadConnections = useCallback(async () => {
    try {
      const list = await listConnections();
      setConnections(list);
    } catch {
      /* user may not be authenticated yet */
    }
  }, []);

  useEffect(() => {
    loadConnections();
  }, [loadConnections]);

  const handleCreate = async () => {
    setError(null);
    try {
      const conn = await createConnection(form);
      setConnections((prev) => [conn, ...prev]);
      setDialogOpen(false);
      onSelectConnection(conn.id);
      setForm({
        name: "",
        db_type: "postgresql",
        host: "localhost",
        port: 5432,
        database: "",
        username: "",
        password: "",
        allow_ai_access: true,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create connection");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteConnection(id);
      setConnections((prev) => prev.filter((c) => c.id !== id));
      if (activeConnectionId === id) onSelectConnection(null);
    } catch {
      /* ignore */
    }
  };

  const handleTest = async (id: string) => {
    const result = await testConnection(id);
    setTestResults((prev) => ({ ...prev, [id]: result }));
  };

  return (
    <Box>
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
        <Typography variant="caption" fontWeight={600} color="text.secondary">
          Connections
        </Typography>
        <IconButton size="small" onClick={() => setDialogOpen(true)}>
          <AddRoundedIcon sx={{ fontSize: 16 }} />
        </IconButton>
      </Stack>

      <List dense disablePadding>
        {/* File Upload (built-in) */}
        <ListItemButton
          selected={activeConnectionId === null}
          onClick={() => onSelectConnection(null)}
          sx={{ borderRadius: 1, mb: 0.25, py: 0.5 }}
        >
          <ListItemIcon sx={{ minWidth: 28 }}>
            <StorageRoundedIcon sx={{ fontSize: 14 }} />
          </ListItemIcon>
          <ListItemText
            primary="File Upload"
            primaryTypographyProps={{ fontSize: "0.78rem" }}
          />
        </ListItemButton>

        {connections.map((conn) => (
          <ListItemButton
            key={conn.id}
            selected={conn.id === activeConnectionId}
            onClick={() => onSelectConnection(conn.id)}
            sx={{ borderRadius: 1, mb: 0.25, py: 0.5 }}
          >
            <ListItemIcon sx={{ minWidth: 28 }}>
              <StorageRoundedIcon sx={{ fontSize: 14 }} />
            </ListItemIcon>
            <ListItemText
              primary={conn.name}
              secondary={conn.db_type}
              primaryTypographyProps={{ fontSize: "0.78rem", noWrap: true }}
              secondaryTypographyProps={{ fontSize: "0.65rem" }}
            />
            <Stack direction="row" spacing={0.25}>
              {testResults[conn.id] && (
                testResults[conn.id].ok ? (
                  <CheckCircleRoundedIcon sx={{ fontSize: 14, color: "success.main" }} />
                ) : (
                  <ErrorRoundedIcon sx={{ fontSize: 14, color: "error.main" }} />
                )
              )}
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleTest(conn.id);
                }}
                sx={{ p: 0.25 }}
              >
                <Chip label="test" size="small" sx={{ fontSize: 9, height: 16, cursor: "pointer" }} />
              </IconButton>
              <IconButton
                size="small"
                onClick={(e) => {
                  e.stopPropagation();
                  handleDelete(conn.id);
                }}
                sx={{ p: 0.25, opacity: 0.5, "&:hover": { opacity: 1 } }}
              >
                <DeleteOutlineRoundedIcon sx={{ fontSize: 14 }} />
              </IconButton>
            </Stack>
          </ListItemButton>
        ))}
      </List>

      {/* Create Connection Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Add Database Connection</DialogTitle>
        <DialogContent>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField
              label="Connection Name"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              size="small"
              fullWidth
            />
            <TextField
              label="Database Type"
              value={form.db_type}
              onChange={(e) => {
                const db_type = e.target.value;
                setForm({
                  ...form,
                  db_type,
                  port: db_type === "mysql" ? 3306 : 5432,
                });
              }}
              size="small"
              select
              fullWidth
            >
              {DB_TYPES.map((opt) => (
                <MenuItem key={opt.value} value={opt.value}>
                  {opt.label}
                </MenuItem>
              ))}
            </TextField>
            {form.db_type !== "sqlite" ? (
              <>
                <TextField
                  label="Host"
                  value={form.host}
                  onChange={(e) => setForm({ ...form, host: e.target.value })}
                  size="small"
                  fullWidth
                />
                <TextField
                  label="Port"
                  type="number"
                  value={form.port}
                  onChange={(e) =>
                    setForm({ ...form, port: parseInt(e.target.value) || 0 })
                  }
                  size="small"
                  fullWidth
                />
                <TextField
                  label="Database"
                  value={form.database}
                  onChange={(e) => setForm({ ...form, database: e.target.value })}
                  size="small"
                  fullWidth
                />
                <TextField
                  label="Username"
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  size="small"
                  fullWidth
                />
                <TextField
                  label="Password"
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  size="small"
                  fullWidth
                />
              </>
            ) : (
              <TextField
                label="File Path"
                value={form.file_path || ""}
                onChange={(e) => setForm({ ...form, file_path: e.target.value })}
                size="small"
                fullWidth
                helperText="Path to the .db or .sqlite file on the server"
              />
            )}
            <FormControlLabel
              control={
                <Switch
                  checked={form.allow_ai_access ?? true}
                  onChange={(e) =>
                    setForm({ ...form, allow_ai_access: e.target.checked })
                  }
                />
              }
              label="Allow AI to access this data"
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleCreate} disabled={!form.name}>
            Add Connection
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
