import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi } from "vitest";
import { ThemeProvider, createTheme } from "@mui/material";
import Sidebar from "../Sidebar";
import type { ChatThread } from "../../types/chat";

const theme = createTheme();

function renderWithTheme(ui: React.ReactElement) {
  return render(<ThemeProvider theme={theme}>{ui}</ThemeProvider>);
}

const makeThread = (overrides: Partial<ChatThread> = {}): ChatThread => ({
  id: "t1",
  title: "Test Chat",
  messages: [],
  datasetInfo: null,
  createdAt: Date.now(),
  updatedAt: Date.now(),
  ...overrides,
});

describe("Sidebar", () => {
  it("renders the app name", () => {
    renderWithTheme(
      <Sidebar
        threads={[makeThread()]}
        activeThreadId="t1"
        dataset={null}
        colorMode="light"
        activeConnectionId={null}
        onNewChat={vi.fn()}
        onSelectThread={vi.fn()}
        onDeleteThread={vi.fn()}
        onToggleColorMode={vi.fn()}
        onSelectConnection={vi.fn()}
      />,
    );
    expect(screen.getByText("Data Explorer")).toBeInTheDocument();
  });

  it("renders thread titles", () => {
    renderWithTheme(
      <Sidebar
        threads={[makeThread({ title: "My Analysis" }), makeThread({ id: "t2", title: "Sales Data" })]}
        activeThreadId="t1"
        dataset={null}
        colorMode="light"
        activeConnectionId={null}
        onNewChat={vi.fn()}
        onSelectThread={vi.fn()}
        onDeleteThread={vi.fn()}
        onToggleColorMode={vi.fn()}
        onSelectConnection={vi.fn()}
      />,
    );
    expect(screen.getByText("My Analysis")).toBeInTheDocument();
    expect(screen.getByText("Sales Data")).toBeInTheDocument();
  });

  it("calls onNewChat when the button is clicked", async () => {
    const user = userEvent.setup();
    const onNewChat = vi.fn();
    renderWithTheme(
      <Sidebar
        threads={[makeThread()]}
        activeThreadId="t1"
        dataset={null}
        colorMode="light"
        activeConnectionId={null}
        onNewChat={onNewChat}
        onSelectThread={vi.fn()}
        onDeleteThread={vi.fn()}
        onToggleColorMode={vi.fn()}
        onSelectConnection={vi.fn()}
      />,
    );
    await user.click(screen.getByText("New Chat"));
    expect(onNewChat).toHaveBeenCalled();
  });

  it("shows dataset info when dataset is provided", () => {
    renderWithTheme(
      <Sidebar
        threads={[makeThread()]}
        activeThreadId="t1"
        dataset={{ preview: [], row_count: 500, columns: ["name", "age", "city"] }}
        colorMode="light"
        activeConnectionId={null}
        onNewChat={vi.fn()}
        onSelectThread={vi.fn()}
        onDeleteThread={vi.fn()}
        onToggleColorMode={vi.fn()}
        onSelectConnection={vi.fn()}
      />,
    );
    expect(screen.getByText("Dataset")).toBeInTheDocument();
    expect(screen.getByText(/500 rows/)).toBeInTheDocument();
  });
});
