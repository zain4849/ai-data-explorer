import { useEffect, useMemo, useRef, useState } from "react";
import { Box, alpha, useTheme } from "@mui/material";

interface Props {
  chartHtml: string;
}

const ChartView = ({ chartHtml }: Props) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [height, setHeight] = useState(420);
  const theme = useTheme();

  const srcDoc = useMemo(() => {
    const chartTheme = {
      bodyBg: "transparent",
      paperBg:
        theme.palette.mode === "dark"
          ? alpha(theme.palette.background.default, 0.18)
          : theme.palette.background.paper,
      plotBg:
        theme.palette.mode === "dark"
          ? alpha(theme.palette.background.default, 0.34)
          : alpha(theme.palette.primary.light, 0.08),
      fontColor: theme.palette.text.primary,
      gridColor: alpha(theme.palette.text.primary, theme.palette.mode === "dark" ? 0.14 : 0.1),
      axisColor: alpha(theme.palette.text.primary, theme.palette.mode === "dark" ? 0.2 : 0.14),
    };

    return `<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  body{margin:0;overflow:hidden;background:transparent}
  .plotly-graph-div{width:100%!important}
</style></head>
<body>${chartHtml}
<script>
  const chartTheme = ${JSON.stringify(chartTheme)};
  const axisMatcher = /^[xy]axis\\d*$/;

  function postHeight() {
    window.parent.postMessage({chartHeight:document.body.scrollHeight},"*");
  }

  function themedAxis(axis = {}) {
    return {
      ...axis,
      gridcolor: chartTheme.gridColor,
      linecolor: chartTheme.axisColor,
      zerolinecolor: chartTheme.gridColor,
      tickfont: { ...(axis.tickfont || {}), color: chartTheme.fontColor },
      title: {
        ...(axis.title || {}),
        font: { ...((axis.title && axis.title.font) || {}), color: chartTheme.fontColor }
      }
    };
  }

  function applyTheme() {
    const graph = document.querySelector(".plotly-graph-div");
    if (!graph || !window.Plotly) return false;

    const currentLayout = graph.layout || {};
    const nextLayout = {
      paper_bgcolor: chartTheme.paperBg,
      plot_bgcolor: chartTheme.plotBg,
      font: { ...(currentLayout.font || {}), color: chartTheme.fontColor },
      legend: {
        ...(currentLayout.legend || {}),
        bgcolor: "rgba(0,0,0,0)",
        font: { ...((currentLayout.legend && currentLayout.legend.font) || {}), color: chartTheme.fontColor }
      }
    };

    Object.keys(currentLayout).forEach((key) => {
      if (axisMatcher.test(key)) {
        nextLayout[key] = themedAxis(currentLayout[key]);
      }
    });

    window.Plotly.relayout(graph, nextLayout).then(postHeight).catch(postHeight);
    return true;
  }

  new ResizeObserver(()=>{
    postHeight();
  }).observe(document.body);

  let attempts = 0;
  const timer = window.setInterval(() => {
    attempts += 1;
    const applied = applyTheme();
    postHeight();
    if (applied || attempts > 24) {
      window.clearInterval(timer);
    }
  }, 150);

  window.addEventListener("load", () => {
    applyTheme();
    postHeight();
  });
</script></body></html>`;
  }, [chartHtml, theme]);

  useEffect(() => {
    const onMsg = (e: MessageEvent) => {
      if (e.data?.chartHeight) setHeight(e.data.chartHeight);
    };
    window.addEventListener("message", onMsg);
    return () => window.removeEventListener("message", onMsg);
  }, []);

  if (!chartHtml) return null;

  return (
    <Box sx={{ width: "100%" }}>
      <iframe
        ref={iframeRef}
        srcDoc={srcDoc}
        sandbox="allow-scripts"
        title="Chart visualization"
        style={{
          width: "100%",
          height,
          border: "none",
          display: "block",
        }}
      />
    </Box>
  );
};

export default ChartView;
