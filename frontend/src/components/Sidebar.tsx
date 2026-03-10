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
import type { ChatThread } from "../types/chat";
import type { UploadResponse } from "../types/api";

export const SIDEBAR_WIDTH = 260;

interface SidebarProps {
  threads: ChatThread[];
  activeThreadId: string;
  dataset: UploadResponse | null;
  colorMode: PaletteMode;
  onNewChat: () => void;
  onSelectThread: (id: string) => void;
  onDeleteThread: (id: string) => void;
  onToggleColorMode: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  threads,
  activeThreadId,
  dataset,
  colorMode,
  onNewChat,
  onSelectThread,
  onDeleteThread,
  onToggleColorMode,
}) => {
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";
  const sidebarBg = isDark ? "#101815" : "#243129";
  const sidebarBorder = alpha(theme.palette.primary.light, isDark ? 0.14 : 0.1);
  const highlightBg = alpha(theme.palette.primary.main, isDark ? 0.24 : 0.18);
  const hoverBg = alpha(theme.palette.primary.light, isDark ? 0.09 : 0.08);
  const surfaceBg = alpha(theme.palette.primary.light, isDark ? 0.1 : 0.08);
  const sidebarText = isDark ? "#EDF4E8" : "#F2F5ED";
  const sidebarMuted = isDark ? "#C2DDB6" : "#B0CDA4";
  const sidebarSubtle = alpha(theme.palette.primary.light, 0.5);

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
            bgcolor: alpha(theme.palette.common.white, isDark ? 0.06 : 0.05),
            border: `1px solid ${alpha(theme.palette.primary.light, isDark ? 0.18 : 0.12)}`,
            "&:hover": {
              bgcolor: alpha(theme.palette.primary.light, isDark ? 0.14 : 0.1),
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
            borderColor: alpha(theme.palette.primary.light, isDark ? 0.24 : 0.2),
            borderRadius: 2,
            py: 0.9,
            fontSize: "0.84rem",
            justifyContent: "flex-start",
            "&:hover": {
              borderColor: alpha(theme.palette.primary.light, isDark ? 0.4 : 0.35),
              bgcolor: hoverBg,
            },
          }}
        >
          New Chat
        </Button>
      </Box>

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
                  "&:hover": { bgcolor: alpha(theme.palette.primary.main, isDark ? 0.3 : 0.24) },
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

      {/* Dataset info */}
      {dataset && (
        <>
          <Divider sx={{ borderColor: sidebarBorder, mx: 1.5 }} />
          <Box sx={{ px: 2, py: 1.5 }}>
            <Stack direction="row" spacing={0.75} alignItems="center" sx={{ mb: 1 }}>
              <StorageRoundedIcon
                sx={{ fontSize: 15, color: alpha(sidebarMuted, 0.8) }}
              />
              <Typography
                variant="caption"
                sx={{ color: alpha(sidebarMuted, 0.8), fontWeight: 600 }}
              >
                Dataset
              </Typography>
            </Stack>
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
                    bgcolor: alpha(theme.palette.primary.main, isDark ? 0.24 : 0.2),
                    color: sidebarMuted,
                  }}
                />
              )}
            </Stack>
          </Box>
        </>
      )}
    </Box>
  );
};

export default Sidebar;
