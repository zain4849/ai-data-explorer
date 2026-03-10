import React, { useRef, useState } from "react";
import {
  alpha,
  Box,
  CircularProgress,
  IconButton,
  InputBase,
  Paper,
  Tooltip,
  useTheme,
} from "@mui/material";
import SendRoundedIcon from "@mui/icons-material/SendRounded";
import AttachFileRoundedIcon from "@mui/icons-material/AttachFileRounded";

interface ChatInputProps {
  onSend: (text: string) => void;
  onFileSelect: (file: File) => void;
  disabled?: boolean;
  isLoading?: boolean;
  placeholder?: string;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  onFileSelect,
  disabled = false,
  isLoading = false,
  placeholder = "Ask a question about your data...",
}) => {
  const [text, setText] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";

  const handleSend = () => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText("");
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box
      sx={{
        px: 3,
        py: 1.5,
        borderTop: "1px solid",
        borderColor: "divider",
        bgcolor: "background.default",
      }}
    >
      <Paper
        elevation={0}
        sx={{
          display: "flex",
          alignItems: "flex-end",
          bgcolor: isDark
            ? alpha(theme.palette.background.paper, 0.98)
            : theme.palette.background.paper,
          border: "1.5px solid",
          borderColor: "divider",
          borderRadius: 3,
          px: 1,
          py: 0.5,
          maxWidth: 820,
          mx: "auto",
          transition: "border-color 0.2s, box-shadow 0.2s, background-color 0.2s",
          boxShadow: isDark
            ? "0 18px 40px rgba(0,0,0,0.25)"
            : "0 12px 28px rgba(45,50,48,0.05)",
          "&:focus-within": {
            borderColor: "primary.main",
            boxShadow: `0 0 0 4px ${alpha(theme.palette.primary.main, 0.12)}`,
          },
        }}
      >
        <input
          ref={fileRef}
          hidden
          type="file"
          accept=".csv,.xlsx,.json"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onFileSelect(f);
            if (fileRef.current) fileRef.current.value = "";
          }}
        />
        <Tooltip title="Attach dataset (CSV, Excel, JSON)">
          <IconButton
            onClick={() => fileRef.current?.click()}
            sx={{ color: "text.secondary", mb: 0.3 }}
            size="small"
          >
            <AttachFileRoundedIcon fontSize="small" />
          </IconButton>
        </Tooltip>

        <InputBase
          multiline
          maxRows={5}
          fullWidth
          placeholder={placeholder}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          sx={{
            px: 1,
            py: 0.75,
            fontSize: "0.92rem",
            lineHeight: 1.5,
          }}
        />

        <IconButton
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          sx={{
            mb: 0.3,
            bgcolor: text.trim() ? "primary.main" : "transparent",
            color: text.trim() ? "primary.contrastText" : "text.disabled",
            width: 34,
            height: 34,
            borderRadius: 2,
            "&:hover": {
              bgcolor: text.trim() ? "primary.dark" : "transparent",
            },
            "&.Mui-disabled": {
              bgcolor: "transparent",
              color: "text.disabled",
            },
          }}
          size="small"
        >
          {isLoading ? (
            <CircularProgress size={18} sx={{ color: "text.secondary" }} />
          ) : (
            <SendRoundedIcon sx={{ fontSize: 18 }} />
          )}
        </IconButton>
      </Paper>
    </Box>
  );
};

export default ChatInput;
