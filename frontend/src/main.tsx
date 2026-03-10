import { StrictMode, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  CssBaseline,
  ThemeProvider,
  alpha,
  createTheme,
  type PaletteMode,
} from "@mui/material";
import App from "./App.tsx";
import ErrorBoundary from "./components/ErrorBoundary.tsx";

const COLOR_MODE_KEY = "data-explorer-color-mode";

function getInitialMode(): PaletteMode {
  const stored = localStorage.getItem(COLOR_MODE_KEY);
  if (stored === "light" || stored === "dark") return stored;

  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function createAppTheme(mode: PaletteMode) {
  const isDark = mode === "dark";
  const backgroundDefault = isDark ? "#111715" : "#F2F5ED";
  const backgroundPaper = isDark ? "#18211E" : "#FFFFFF";
  const surfaceAccent = isDark ? "#22302B" : "#E7EFE0";
  const primaryMain = isDark ? "#9CC58C" : "#8BB17D";
  const primaryLight = isDark ? "#C2DDB6" : "#B0CDA4";
  const primaryDark = isDark ? "#7DAE6B" : "#6E9462";
  const textPrimary = isDark ? "#EDF4E8" : "#2D3230";
  const textSecondary = isDark ? "#A5B5A7" : "#7A8B74";
  const divider = isDark
    ? "rgba(194,221,182,0.12)"
    : "rgba(45,50,48,0.09)";

  return createTheme({
    palette: {
      mode,
      primary: {
        main: primaryMain,
        light: primaryLight,
        dark: primaryDark,
        contrastText: isDark ? "#102015" : "#2D3230",
      },
      secondary: {
        main: isDark ? "#8DA892" : "#7A8B74",
      },
      background: {
        default: backgroundDefault,
        paper: backgroundPaper,
      },
      text: {
        primary: textPrimary,
        secondary: textSecondary,
      },
      divider,
    },
    shape: {
      borderRadius: 14,
    },
    typography: {
      fontFamily: '"Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif',
      h4: { letterSpacing: "-0.02em", fontWeight: 800 },
      h5: { letterSpacing: "-0.015em", fontWeight: 700 },
      h6: { fontWeight: 700, fontSize: "1.05rem" },
      body1: { fontSize: "0.938rem", lineHeight: 1.6 },
      body2: { fontSize: "0.84rem", lineHeight: 1.55 },
    },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            backgroundColor: backgroundDefault,
            backgroundImage: isDark
              ? "radial-gradient(circle at top, rgba(156,197,140,0.12), transparent 30%)"
              : "radial-gradient(circle at top, rgba(139,177,125,0.1), transparent 28%)",
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: "none",
            borderRadius: 10,
            fontWeight: 600,
            boxShadow: "none",
            "&:hover": { boxShadow: "none" },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: "none",
          },
        },
      },
      MuiAlert: {
        styleOverrides: {
          root: {
            borderRadius: 10,
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            fontWeight: 500,
          },
        },
      },
      MuiTableCell: {
        styleOverrides: {
          head: {
            backgroundColor: surfaceAccent,
          },
        },
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            backgroundColor: alpha(backgroundPaper, 0.96),
            color: textPrimary,
            border: `1px solid ${divider}`,
            boxShadow: isDark
              ? "0 12px 32px rgba(0,0,0,0.26)"
              : "0 12px 24px rgba(45,50,48,0.08)",
          },
        },
      },
    },
  });
}

function RootApp() {
  const [mode, setMode] = useState<PaletteMode>(() => getInitialMode());
  const theme = useMemo(() => createAppTheme(mode), [mode]);

  const toggleColorMode = () => {
    setMode((currentMode) => {
      const nextMode = currentMode === "light" ? "dark" : "light";
      localStorage.setItem(COLOR_MODE_KEY, nextMode);
      return nextMode;
    });
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <ErrorBoundary>
        <App colorMode={mode} onToggleColorMode={toggleColorMode} />
      </ErrorBoundary>
    </ThemeProvider>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RootApp />
  </StrictMode>,
);
