import React, { useRef } from "react";
import { Box, Button, Chip, Stack, Typography, alpha, useTheme } from "@mui/material";
import AutoGraphRoundedIcon from "@mui/icons-material/AutoGraphRounded";
import AttachFileRoundedIcon from "@mui/icons-material/AttachFileRounded";

interface WelcomeScreenProps {
  hasDataset: boolean;
  onSuggestedPrompt: (prompt: string) => void;
  onFileSelect: (file: File) => void;
}

const SUGGESTED_PROMPTS = [
  "Show me the first 10 rows",
  "What are the summary statistics?",
  "Which column has the most unique values?",
  "Plot a chart of the main trends",
];

const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  hasDataset,
  onSuggestedPrompt,
  onFileSelect,
}) => {
  const fileRef = useRef<HTMLInputElement>(null);
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        flex: 1,
        textAlign: "center",
        px: 3,
        pb: 8,
      }}
    >
      <Box
        sx={{
          width: 64,
          height: 64,
          borderRadius: "18px",
          background: isDark
            ? "linear-gradient(135deg, #6C9C5E 0%, #BFDDB4 100%)"
            : "linear-gradient(135deg, #6E9462 0%, #B0CDA4 100%)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          mb: 3,
          boxShadow: isDark
            ? "0 18px 40px rgba(0,0,0,0.28)"
            : "0 18px 36px rgba(110,148,98,0.18)",
        }}
      >
        <AutoGraphRoundedIcon sx={{ fontSize: 34, color: "#fff" }} />
      </Box>

      <Typography
        variant="h4"
        sx={{
          fontWeight: 800,
          fontSize: "1.75rem",
          letterSpacing: "-0.03em",
          color: "text.primary",
          mb: 1,
        }}
      >
        AI Data Explorer
      </Typography>

      <Typography
        variant="body1"
        sx={{
          color: "text.secondary",
          maxWidth: 440,
          mb: 4,
          lineHeight: 1.6,
        }}
      >
        {hasDataset
          ? "Your dataset is loaded. Ask any question about your data using natural language."
          : "Upload a CSV, Excel, or JSON file to get started. Then ask questions in plain English."}
      </Typography>

      {!hasDataset && (
        <>
          <input
            ref={fileRef}
            hidden
            type="file"
            accept=".csv,.xlsx,.json"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) onFileSelect(f);
            }}
          />
          <Button
            variant="contained"
            size="large"
            startIcon={<AttachFileRoundedIcon />}
            onClick={() => fileRef.current?.click()}
            sx={{
              px: 4,
              py: 1.3,
              borderRadius: 3,
              fontSize: "0.95rem",
              background: isDark
                ? "linear-gradient(135deg, #6C9C5E 0%, #BFDDB4 100%)"
                : "linear-gradient(135deg, #6E9462 0%, #B0CDA4 100%)",
              color: "#fff",
              mb: 4,
              boxShadow: isDark
                ? "0 14px 30px rgba(0,0,0,0.24)"
                : "0 12px 26px rgba(110,148,98,0.2)",
            }}
          >
            Upload a dataset
          </Button>
        </>
      )}

      {hasDataset && (
        <Stack spacing={1} sx={{ width: "100%", maxWidth: 460 }}>
          <Typography
            variant="overline"
            sx={{ color: "text.secondary", fontSize: "0.7rem", letterSpacing: "0.06em" }}
          >
            Try asking
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" justifyContent="center" useFlexGap>
            {SUGGESTED_PROMPTS.map((prompt) => (
              <Chip
                key={prompt}
                label={prompt}
                onClick={() => onSuggestedPrompt(prompt)}
                sx={{
                  cursor: "pointer",
                  bgcolor: alpha(theme.palette.primary.main, isDark ? 0.16 : 0.1),
                  color: isDark ? theme.palette.primary.light : "primary.dark",
                  fontWeight: 500,
                  fontSize: "0.8rem",
                  py: 2.2,
                  borderRadius: 3,
                  border: "1px solid",
                  borderColor: alpha(theme.palette.primary.main, isDark ? 0.3 : 0.22),
                  "&:hover": {
                    bgcolor: alpha(theme.palette.primary.main, isDark ? 0.24 : 0.2),
                  },
                }}
              />
            ))}
          </Stack>
        </Stack>
      )}
    </Box>
  );
};

export default WelcomeScreen;
