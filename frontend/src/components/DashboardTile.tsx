import { Paper, Typography, useTheme } from "@mui/material";
import type { DashboardTileInfo } from "../api/client";
import ChartView from "./ChartView";

interface DashboardTileProps {
  tile: DashboardTileInfo;
}

export default function DashboardTile({ tile }: DashboardTileProps) {
  const theme = useTheme();

  let config: Record<string, unknown> = {};
  try {
    config = JSON.parse(tile.config_json);
  } catch {
    /* invalid JSON */
  }

  return (
    <Paper
      elevation={0}
      sx={{
        height: "100%",
        border: `1px solid ${theme.palette.divider}`,
        borderRadius: 2,
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
      }}
    >
      {tile.title && (
        <Typography
          variant="caption"
          fontWeight={600}
          sx={{ px: 1.5, pt: 1, pb: 0.5, color: "text.secondary" }}
        >
          {tile.title}
        </Typography>
      )}
      {tile.tile_type === "chart" && config.chart_html ? (
        <ChartView chartHtml={config.chart_html as string} />
      ) : tile.tile_type === "text" ? (
        <Typography variant="body2" sx={{ p: 1.5 }}>
          {(config.text as string) || ""}
        </Typography>
      ) : (
        <Typography variant="body2" color="text.disabled" sx={{ p: 1.5, textAlign: "center" }}>
          {tile.tile_type} tile
        </Typography>
      )}
    </Paper>
  );
}
