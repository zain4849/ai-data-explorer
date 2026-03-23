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
import { AuthProvider, useAuth } from "./context/AuthContext.tsx";
import LoginPage from "./pages/LoginPage.tsx";

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
  const backgroundDefault = isDark ? "#000000" : "#FAFAFA";
  const backgroundPaper = isDark ? "#0A0A0A" : "#FFFFFF";
  const surfaceAccent = isDark ? "#141414" : "#F0F0F0";
  const primaryMain = isDark ? "#D4D4D4" : "#2A2A2A";
  const primaryLight = isDark ? "#E5E5E5" : "#404040";
  const primaryDark = isDark ? "#A3A3A3" : "#171717";
  const textPrimary = isDark ? "#EDEDED" : "#171717";
  const textSecondary = isDark ? "#737373" : "#525252";
  const divider = isDark
    ? "rgba(255,255,255,0.08)"
    : "rgba(0,0,0,0.08)";

  return createTheme({
    palette: {
      mode,
      primary: {
        main: primaryMain,
        light: primaryLight,
        dark: primaryDark,
        contrastText: isDark ? "#000000" : "#FFFFFF",
      },
      secondary: {
        main: isDark ? "#A3A3A3" : "#525252",
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
              ? "radial-gradient(ellipse at top, rgba(255,255,255,0.03), transparent 50%)"
              : "none",
          },
          "input:-webkit-autofill, input:-webkit-autofill:hover, input:-webkit-autofill:focus, input:-webkit-autofill:active":
            {
              WebkitBoxShadow: `0 0 0 100px ${backgroundPaper} inset !important`,
              WebkitTextFillColor: `${textPrimary} !important`,
              caretColor: `${textPrimary} !important`,
              transition: "background-color 5000s ease-in-out 0s",
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
              ? "0 12px 32px rgba(0,0,0,0.5)"
              : "0 12px 24px rgba(0,0,0,0.06)",
          },
        },
      },
    },
  });
}

function AuthGate({
  colorMode,
  onToggleColorMode,
}: {
  colorMode: PaletteMode;
  onToggleColorMode: () => void;
}) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <LoginPage />;
  return <App colorMode={colorMode} onToggleColorMode={onToggleColorMode} />;
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
        <AuthProvider>
          <AuthGate colorMode={mode} onToggleColorMode={toggleColorMode} />
        </AuthProvider>
      </ErrorBoundary>
    </ThemeProvider>
  );
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <RootApp />
  </StrictMode>,
);
