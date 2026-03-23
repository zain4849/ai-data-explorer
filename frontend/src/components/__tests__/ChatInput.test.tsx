import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { ThemeProvider, createTheme } from "@mui/material";
import ChatInput from "../ChatInput";

const theme = createTheme();

function renderWithTheme(ui: React.ReactElement) {
  return render(<ThemeProvider theme={theme}>{ui}</ThemeProvider>);
}

describe("ChatInput", () => {
  it("renders placeholder text", () => {
    renderWithTheme(
      <ChatInput onSend={vi.fn()} onFileSelect={vi.fn()} placeholder="Ask a question..." />,
    );
    expect(screen.getByPlaceholderText("Ask a question...")).toBeInTheDocument();
  });

  it("calls onSend when enter is pressed with text", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    renderWithTheme(<ChatInput onSend={onSend} onFileSelect={vi.fn()} />);

    const input = screen.getByRole("textbox");
    await user.type(input, "show me data{Enter}");
    expect(onSend).toHaveBeenCalledWith("show me data");
  });

  it("does not call onSend when input is empty", async () => {
    const user = userEvent.setup();
    const onSend = vi.fn();
    renderWithTheme(<ChatInput onSend={onSend} onFileSelect={vi.fn()} />);

    const input = screen.getByRole("textbox");
    await user.type(input, "{Enter}");
    expect(onSend).not.toHaveBeenCalled();
  });

  it("disables input when disabled prop is true", () => {
    renderWithTheme(
      <ChatInput onSend={vi.fn()} onFileSelect={vi.fn()} disabled />,
    );
    expect(screen.getByRole("textbox")).toBeDisabled();
  });
});
