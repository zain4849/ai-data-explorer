import React from "react";
import { Avatar, Box, Chip, Stack, Typography, alpha, useTheme } from "@mui/material";
import PersonRoundedIcon from "@mui/icons-material/PersonRounded";
import AutoAwesomeRoundedIcon from "@mui/icons-material/AutoAwesomeRounded";
import UploadFileRoundedIcon from "@mui/icons-material/UploadFileRounded";
import type { ChatMessage } from "../types/chat";
import AIResponseCard from "./AIResponseCard";

interface MessageBubbleProps {
  message: ChatMessage;
}

const TypingDots = () => ( // Manually implemented typing dots animation
  <Stack direction="row" spacing={0.5} sx={{ py: 1, px: 0.5 }}>
    {[0, 1, 2].map((i) => (
      <Box
        key={i}
        sx={{
          width: 7,
          height: 7,
          borderRadius: "50%",
          bgcolor: "text.disabled",
          animation: "typingBounce 1.2s infinite ease-in-out",
          animationDelay: `${i * 0.15}s`,
          "@keyframes typingBounce": {
            "0%, 60%, 100%": { transform: "translateY(0)" },
            "30%": { transform: "translateY(-6px)" },
          },
        }}
      />
    ))}
  </Stack>
);

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const isAssistant = message.role === "assistant";

  if (isUser) {
    return (
      <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 2.5, px: 1 }}>
        <Stack direction="row" spacing={1.5} alignItems="flex-start" sx={{ maxWidth: "70%" }}>
          <Box
            sx={{
              bgcolor: "primary.main",
              color: "primary.contrastText",
              borderRadius: "18px 18px 4px 18px",
              px: 2.5,
              py: 1.5,
            }}
          >
            <Typography variant="body1" sx={{ color: "inherit", whiteSpace: "pre-wrap" }}>
              {message.content}
            </Typography>
          </Box>
          <Avatar
            sx={{
              width: 32,
              height: 32,
              bgcolor: isDark ? alpha(theme.palette.primary.light, 0.9) : "primary.light",
              color: "primary.contrastText",
              flexShrink: 0,
            }}
          >
            <PersonRoundedIcon sx={{ fontSize: 18 }} />
          </Avatar>
        </Stack>
      </Box>
    );
  }

  if (isSystem) {
    return (
      <Box sx={{ display: "flex", justifyContent: "center", mb: 2.5, px: 1 }}>
        <Chip
          icon={<UploadFileRoundedIcon sx={{ fontSize: 16 }} />}
          label={message.content}
          sx={{
            bgcolor: alpha(theme.palette.primary.main, isDark ? 0.12 : 0.1),
            color: "text.primary",
            fontWeight: 500,
            fontSize: "0.82rem",
            py: 2,
            px: 1,
            borderRadius: 3,
            border: "1px solid",
            borderColor: alpha(theme.palette.primary.main, isDark ? 0.26 : 0.22),
            "& .MuiChip-icon": { color: "primary.dark" },
          }}
        />
      </Box>
    );
  }

  if (isAssistant) {
    return (
      <Box sx={{ display: "flex", justifyContent: "flex-start", mb: 2.5, px: 1 }}>
        <Stack direction="row" spacing={1.5} alignItems="flex-start" sx={{ maxWidth: "85%" }}>
          <Avatar
            sx={{
              width: 32,
              height: 32,
              background: isDark
                ? "linear-gradient(135deg, #6C9C5E 0%, #BFDDB4 100%)"
                : "linear-gradient(135deg, #6E9462 0%, #B0CDA4 100%)",
              flexShrink: 0,
              mt: 0.3,
            }}
          >
            <AutoAwesomeRoundedIcon sx={{ fontSize: 17, color: "#fff" }} />
          </Avatar>
          <Box sx={{ minWidth: 0, flex: 1 }}>
            {message.isLoading ? (
              <Box
                sx={{
                  bgcolor: isDark
                    ? alpha(theme.palette.background.paper, 0.98)
                    : theme.palette.background.paper,
                  borderRadius: "18px 18px 18px 4px",
                  px: 2.5,
                  py: 1.2,
                  display: "inline-block",
                  border: "1px solid",
                  borderColor: alpha(theme.palette.primary.main, isDark ? 0.18 : 0.08),
                }}
              >
                <TypingDots />
              </Box>
            ) : (
              <AIResponseCard message={message} />
            )}
          </Box>
        </Stack>
      </Box>
    );
  }

  return null;
};

export default MessageBubble;
