import React from "react";
import {
  alpha,
  Box,
  Button,
  Chip,
  Divider,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Typography,
  useTheme,
  type PaletteMode,
} from "@mui/material";
import AddRoundedIcon from "@mui/icons-material/AddRounded";
import ChatBubbleOutlineRoundedIcon from "@mui/icons-material/ChatBubbleOutlineRounded";
import DeleteOutlineRoundedIcon from "@mui/icons-material/DeleteOutlineRounded";
import StorageRoundedIcon from "@mui/icons-material/StorageRounded";
import AutoGraphRoundedIcon from "@mui/icons-material/AutoGraphRounded";
import LightModeRoundedIcon from "@mui/icons-material/LightModeRounded";
import DarkModeRoundedIcon from "@mui/icons-material/DarkModeRounded";
import LogoutRoundedIcon from "@mui/icons-material/LogoutRounded";
import PersonRoundedIcon from "@mui/icons-material/PersonRounded";
import DashboardRoundedIcon from "@mui/icons-material/DashboardRounded";
import type { ChatThread } from "../types/chat";
import type { UploadResponse } from "../types/api";
import type { DatasetInfo } from "../api/client";
import { useAuth } from "../context/AuthContext";
import ConnectionManager from "./ConnectionManager";

export const SIDEBAR_WIDTH = 260;

interface SidebarProps {
  threads: ChatThread[];
  activeThreadId: string;
  dataset: UploadResponse | null;
  datasets?: DatasetInfo[];
  colorMode: PaletteMode;
  activeConnectionId: string | null;
  onNewChat: () => void;
  onSelectThread: (id: string) => void;
  onDeleteThread: (id: string) => void;
  onToggleColorMode: () => void;
  onSelectConnection: (id: string | null) => void;
  onShowDashboards?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  threads,
  activeThreadId,
  dataset,
  datasets = [],
  colorMode,
  activeConnectionId,
  onNewChat,
  onSelectThread,
  onDeleteThread,
  onToggleColorMode,
  onSelectConnection,
  onShowDashboards,
}) => {
  const { user, logout } = useAuth();
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";
  const sidebarBg = isDark ? "#050505" : "#111111";
  const sidebarBorder = isDark ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.08)";
  const highlightBg = "rgba(255,255,255,0.1)";
  const hoverBg = isDark ? "rgba(255,255,255,0.04)" : "rgba(255,255,255,0.06)";
  const surfaceBg = isDark ? "rgba(255,255,255,0.06)" : "rgba(255,255,255,0.08)";
  const sidebarText = "#E5E5E5";
  const sidebarMuted = "#A0A0A0";
  const sidebarSubtle = isDark ? "rgba(255,255,255,0.3)" : "rgba(255,255,255,0.35)";

  return (
    <Box
      sx={{
        width: SIDEBAR_WIDTH,
        minWidth: SIDEBAR_WIDTH,
        height: "100vh",
        bgcolor: sidebarBg,
        color: sidebarText,
        display: "flex",
        flexDirection: "column",
        borderRight: `1px solid ${sidebarBorder}`,
      }}
    >
      {/* Logo */}
      <Stack
        direction="row"
        spacing={1}
        alignItems="center"
        sx={{ px: 2.5, py: 2 }}
      >
        <AutoGraphRoundedIcon sx={{ color: sidebarMuted, fontSize: 26 }} />
        <Typography
          variant="h6"
          sx={{
            color: sidebarText,
            fontWeight: 800,
            fontSize: "1rem",
            letterSpacing: "-0.02em",
            flex: 1,
          }}
        >
          Data Explorer
        </Typography>
        <IconButton
          size="small"
          onClick={onToggleColorMode}
          aria-label={`Switch to ${colorMode === "light" ? "dark" : "light"} mode`}
          sx={{
            color: sidebarText,
            bgcolor: "rgba(255,255,255,0.06)",
            border: `1px solid rgba(255,255,255,0.1)`,
            "&:hover": {
              bgcolor: "rgba(255,255,255,0.1)",
            },
          }}
        >
          {colorMode === "light" ? (
            <DarkModeRoundedIcon sx={{ fontSize: 18 }} />
          ) : (
            <LightModeRoundedIcon sx={{ fontSize: 18 }} />
          )}
        </IconButton>
      </Stack>

      {/* + New Chat */}
      <Box sx={{ px: 1.5, pb: 1 }}>
        <Button
          fullWidth
          variant="outlined"
          startIcon={<AddRoundedIcon />}
          onClick={onNewChat}
          sx={{
            color: sidebarText,
            borderColor: "rgba(255,255,255,0.12)",
            borderRadius: 2,
            py: 0.9,
            fontSize: "0.84rem",
            justifyContent: "flex-start",
            "&:hover": {
              borderColor: "rgba(255,255,255,0.2)",
              bgcolor: hoverBg,
            },
          }}
        >
          New Chat
        </Button>
      </Box>

      {onShowDashboards && (
        <Box sx={{ px: 1.5, pb: 1 }}>
          <Button
            fullWidth
            variant="text"
            startIcon={<DashboardRoundedIcon />}
            onClick={onShowDashboards}
            sx={{
              color: sidebarMuted,
              borderRadius: 2,
              py: 0.7,
              fontSize: "0.82rem",
              justifyContent: "flex-start",
              "&:hover": { bgcolor: hoverBg },
            }}
          >
            Dashboards
          </Button>
        </Box>
      )}

      <Divider sx={{ borderColor: sidebarBorder, mx: 1.5 }} />

      {/* Thread list */}
      <Box sx={{ flex: 1, overflow: "auto", py: 0.5 }}>
        <Typography
          variant="overline"
          sx={{
            px: 2.5,
            pt: 1.5,
            pb: 0.5,
            display: "block",
            color: sidebarSubtle,
            fontSize: "0.68rem",
            letterSpacing: "0.08em",
          }}
        >
          Conversations
        </Typography>
        <List dense disablePadding>
          {threads.map((thread) => (
            <ListItemButton
              key={thread.id}
              selected={thread.id === activeThreadId}
              onClick={() => onSelectThread(thread.id)}
              sx={{
                mx: 1,
                borderRadius: 1.5,
                mb: 0.25,
                py: 0.65,
                "&.Mui-selected": {
                  bgcolor: highlightBg,
                  "&:hover": { bgcolor: "rgba(255,255,255,0.14)" },
                },
                "&:hover": { bgcolor: hoverBg },
              }}
            >
              <ListItemIcon sx={{ minWidth: 30 }}>
                <ChatBubbleOutlineRoundedIcon
                  sx={{ fontSize: 16, color: sidebarSubtle }}
                />
              </ListItemIcon>
              <ListItemText
                primary={thread.title}
                primaryTypographyProps={{
                  noWrap: true,
                  fontSize: "0.82rem",
                  color: thread.id === activeThreadId ? sidebarText : sidebarMuted,
                }}
              />
              {threads.length > 1 && (
                <IconButton
                  size="small"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteThread(thread.id);
                  }}
                  sx={{
                    opacity: 0,
                    ".MuiListItemButton-root:hover &": { opacity: 0.6 },
                    color: sidebarSubtle,
                    p: 0.4,
                  }}
                >
                  <DeleteOutlineRoundedIcon sx={{ fontSize: 15 }} />
                </IconButton>
              )}
            </ListItemButton>
          ))}
        </List>
      </Box>

      {/* Connection manager */}
      <Divider sx={{ borderColor: sidebarBorder, mx: 1.5 }} />
      <Box sx={{ px: 1.5, py: 1 }}>
        <ConnectionManager
          activeConnectionId={activeConnectionId}
          onSelectConnection={onSelectConnection}
        />
      </Box>

      {/* Datasets */}
      {(datasets.length > 0 || dataset) && (
        <>
          <Divider sx={{ borderColor: sidebarBorder, mx: 1.5 }} />
          <Box sx={{ px: 2, py: 1.5, maxHeight: 180, overflow: "auto" }}>
            <Stack direction="row" spacing={0.75} alignItems="center" sx={{ mb: 1 }}>
              <StorageRoundedIcon
                sx={{ fontSize: 15, color: alpha(sidebarMuted, 0.8) }}
              />
              <Typography
                variant="caption"
                sx={{ color: alpha(sidebarMuted, 0.8), fontWeight: 600 }}
              >
                Datasets
              </Typography>
            </Stack>
            {datasets.length > 0
              ? datasets.map((ds) => (
                  <Box key={ds.id} sx={{ mb: 1 }}>
                    <Typography
                      variant="caption"
                      sx={{ color: sidebarText, display: "block", fontWeight: 600, fontSize: "0.75rem" }}
                      noWrap
                    >
                      {ds.name}
                    </Typography>
                    <Typography
                      variant="caption"
                      sx={{ color: sidebarMuted, display: "block", mb: 0.5 }}
                    >
                      {ds.row_count.toLocaleString()} rows &middot;{" "}
                      {ds.columns.length} cols &middot; {ds.table_name}
                    </Typography>
                    <Stack
                      direction="row"
                      spacing={0.4}
                      useFlexGap
                      flexWrap="wrap"
                      sx={{ maxHeight: 40, overflow: "hidden" }}
                    >
                      {ds.columns.slice(0, 5).map((col) => (
                        <Chip
                          key={col}
                          label={col}
                          size="small"
                          sx={{
                            fontSize: 10,
                            height: 18,
                            bgcolor: surfaceBg,
                            color: sidebarMuted,
                          }}
                        />
                      ))}
                      {ds.columns.length > 5 && (
                        <Chip
                          label={`+${ds.columns.length - 5}`}
                          size="small"
                          sx={{
                            fontSize: 10,
                            height: 18,
                            bgcolor: "rgba(255,255,255,0.1)",
                            color: sidebarMuted,
                          }}
                        />
                      )}
                    </Stack>
                  </Box>
                ))
              : dataset && (
                  <Box>
                    <Typography
                      variant="caption"
                      sx={{ color: sidebarMuted, display: "block", mb: 0.5 }}
                    >
                      {dataset.row_count.toLocaleString()} rows &middot;{" "}
                      {dataset.columns.length} columns
                    </Typography>
                    <Stack
                      direction="row"
                      spacing={0.4}
                      useFlexGap
                      flexWrap="wrap"
                      sx={{ maxHeight: 80, overflow: "hidden" }}
                    >
                      {dataset.columns.slice(0, 8).map((col) => (
                        <Chip
                          key={col}
                          label={col}
                          size="small"
                          sx={{
                            fontSize: 10,
                            height: 20,
                            bgcolor: surfaceBg,
                            color: sidebarMuted,
                          }}
                        />
                      ))}
                      {dataset.columns.length > 8 && (
                        <Chip
                          label={`+${dataset.columns.length - 8}`}
                          size="small"
                          sx={{
                            fontSize: 10,
                            height: 20,
                            bgcolor: "rgba(255,255,255,0.1)",
                            color: sidebarMuted,
                          }}
                        />
                      )}
                    </Stack>
                  </Box>
                )}
          </Box>
        </>
      )}

      {/* User profile */}
      {user && (
        <>
          <Divider sx={{ borderColor: sidebarBorder, mx: 1.5 }} />
          <Stack
            direction="row"
            alignItems="center"
            spacing={1}
            sx={{ px: 2, py: 1.5 }}
          >
            <PersonRoundedIcon sx={{ fontSize: 18, color: sidebarMuted }} />
            <Typography
              variant="caption"
              sx={{ color: sidebarMuted, flex: 1, fontWeight: 500 }}
              noWrap
            >
              {user.name || user.email}
            </Typography>
            <IconButton
              size="small"
              onClick={logout}
              aria-label="Sign out"
              sx={{
                color: sidebarSubtle,
                "&:hover": { color: sidebarText },
              }}
            >
              <LogoutRoundedIcon sx={{ fontSize: 16 }} />
            </IconButton>
          </Stack>
        </>
      )}
    </Box>
  );
};

export default Sidebar;
