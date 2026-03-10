import React, { useState } from "react";
import {
  alpha,
  Box,
  Collapse,
  Divider,
  IconButton,
  Paper,
  Stack,
  Typography,
  useTheme,
} from "@mui/material";
import CodeRoundedIcon from "@mui/icons-material/CodeRounded";
import BarChartRoundedIcon from "@mui/icons-material/BarChartRounded";
import TableChartRoundedIcon from "@mui/icons-material/TableChartRounded";
import ExpandMoreRoundedIcon from "@mui/icons-material/ExpandMoreRounded";
import ExpandLessRoundedIcon from "@mui/icons-material/ExpandLessRounded";
import type { ChatMessage } from "../types/chat";
import ChartView from "./ChartView";
import InsightsPanel from "./InsightsPanel";
import ResultsTable from "./ResultsTable";  

interface AIResponseCardProps {
  message: ChatMessage;
}

interface CollapsibleSectionProps {
  icon: React.ReactNode;
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}

const CollapsibleSection: React.FC<CollapsibleSectionProps> = ({
  icon,
  title,
  defaultOpen = false,
  children,
}) => {
  const [open, setOpen] = useState(defaultOpen);
  const theme = useTheme();

  return (
    <Box>
      <Stack
        direction="row"
        alignItems="center"
        spacing={1}
        onClick={() => setOpen(!open)}
        sx={{
          cursor: "pointer",
          py: 0.75,
          px: 0.5,
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
      <Collapse in={open}>
        <Box sx={{ pt: 0.5, pb: 1 }}>{children}</Box>
      </Collapse>
    </Box>
  );
};

const AIResponseCard: React.FC<AIResponseCardProps> = ({ message }) => {
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";

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
        {message.insights && (
          <Box sx={{ pb: 0.5 }}>
            <InsightsPanel insights={message.insights} />
          </Box>
        )}

        {/* Chart */}
        {message.chartHtml && (
          <>
            <Divider sx={{ opacity: 0.5 }} />
            <CollapsibleSection
              icon={<BarChartRoundedIcon sx={{ fontSize: 16, color: "primary.dark" }} />}
              title="Visualization"
              defaultOpen
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
                <ChartView chartHtml={message.chartHtml} />
              </Box>
            </CollapsibleSection>
          </>
        )}

        {/* SQL */}
        {message.sql && (
          <>
            <Divider sx={{ opacity: 0.5 }} />
            <CollapsibleSection
              icon={<CodeRoundedIcon sx={{ fontSize: 16, color: "primary.dark" }} />}
              title="Generated SQL"
            >
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
                  bgcolor: isDark ? "#0E1512" : "#23302A",
                  color: isDark ? "#C2DDB6" : "#B0CDA4",
                  border: `1px solid ${alpha(theme.palette.primary.light, isDark ? 0.16 : 0.12)}`,
                }}
              >
                {message.sql}
              </Box>
            </CollapsibleSection>
          </>
        )}

        {/* Data table */}
        {message.tableData && message.tableData.length > 0 && (
          <>
            <Divider sx={{ opacity: 0.5 }} />
            <CollapsibleSection
              icon={
                <TableChartRoundedIcon sx={{ fontSize: 16, color: "primary.dark" }} />
              }
              title={`Data (${message.tableData.length} rows)`}
            >
              <ResultsTable rows={message.tableData} />
            </CollapsibleSection>
          </>
        )}
      </Stack>
    </Paper>
  );
};

export default AIResponseCard;
