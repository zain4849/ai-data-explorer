import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { ThemeProvider, createTheme } from "@mui/material";
import WelcomeScreen from "../WelcomeScreen";

const theme = createTheme();

function renderWithTheme(ui: React.ReactElement) {
  return render(<ThemeProvider theme={theme}>{ui}</ThemeProvider>);
}

describe("WelcomeScreen", () => {
  it("renders the title", () => {
    renderWithTheme(
      <WelcomeScreen hasDataset={false} onSuggestedPrompt={vi.fn()} onFileSelect={vi.fn()} />,
    );
    expect(screen.getByText("AI Data Explorer")).toBeInTheDocument();
  });

  it("shows upload button when no dataset is loaded", () => {
    renderWithTheme(
      <WelcomeScreen hasDataset={false} onSuggestedPrompt={vi.fn()} onFileSelect={vi.fn()} />,
    );
    expect(screen.getByText("Upload a dataset")).toBeInTheDocument();
  });

  it("shows suggested prompts when dataset is loaded", () => {
    renderWithTheme(
      <WelcomeScreen hasDataset={true} onSuggestedPrompt={vi.fn()} onFileSelect={vi.fn()} />,
    );
    expect(screen.getByText("Show me the first 10 rows")).toBeInTheDocument();
    expect(screen.getByText("What are the summary statistics?")).toBeInTheDocument();
  });

  it("calls onSuggestedPrompt when a chip is clicked", async () => {
    const user = userEvent.setup();
    const onSuggestedPrompt = vi.fn();
    renderWithTheme(
      <WelcomeScreen hasDataset={true} onSuggestedPrompt={onSuggestedPrompt} onFileSelect={vi.fn()} />,
    );
    await user.click(screen.getByText("Show me the first 10 rows"));
    expect(onSuggestedPrompt).toHaveBeenCalledWith("Show me the first 10 rows");
  });
});
