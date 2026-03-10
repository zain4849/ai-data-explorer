import type { ReactNode } from "react";
import { Box, Button, Typography } from "@mui/material";
import ErrorOutlineRoundedIcon from "@mui/icons-material/ErrorOutlineRounded";
import {
  ErrorBoundary as ReactErrorBoundary,
  type FallbackProps,
} from "react-error-boundary";

/*
In React, errors in components can crash the whole app if not handled.
- Normally, if a component throws an error during rendering, the whole React tree can unmount.
- An Error Boundary is a special component that catches JavaScript errors anywhere in its child component tree, logs them, and renders a fallback UI instead of crashing the whole app.

In other words: it’s your app’s safety net for unexpected runtime errors.
*/

interface Props {
  children: ReactNode;
}

function ErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
  const errorMessage =
    error instanceof Error ? error.message : "An unexpected error occurred.";

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        height: "100vh",
        textAlign: "center",
        px: 3,
        bgcolor: "background.default",
      }}
    >
      <ErrorOutlineRoundedIcon
        sx={{ fontSize: 56, color: "error.main", mb: 2 }}
      />
      <Typography variant="h5" sx={{ mb: 1, fontWeight: 700 }}>
        Something went wrong
      </Typography>
      <Typography
        variant="body2"
        sx={{ color: "text.secondary", mb: 3, maxWidth: 480 }}
      >
        {errorMessage}
      </Typography>
      <Button
        variant="contained"
        onClick={resetErrorBoundary}
        sx={{ borderRadius: 2 }}
      >
        Try again
      </Button>
    </Box>
  );
}

function ErrorBoundary({ children }: Props) {
  return (
    <ReactErrorBoundary
      FallbackComponent={ErrorFallback}
      onError={(error, info) => {
        console.error("Uncaught error:", error, info.componentStack);
      }}
    >
      {children}
    </ReactErrorBoundary>
  );
}

export default ErrorBoundary;
