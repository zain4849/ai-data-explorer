import { useCallback, useEffect, useState } from "react";
import { Alert, Box, Snackbar, type PaletteMode } from "@mui/material";
import { uploadFile, runQuery } from "./api/client";
import type { ChatMessage, ChatThread } from "./types/chat";
import type { UploadResponse } from "./types/api";
import Sidebar, { SIDEBAR_WIDTH } from "./components/Sidebar";
import ChatThreadView from "./components/ChatThread";
import ChatInput from "./components/ChatInput";
import WelcomeScreen from "./components/WelcomeScreen";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const genId = () => crypto.randomUUID?.() ?? `${Date.now()}-${Math.random()}`;

const STORAGE_KEY = "data-explorer-threads";

function loadThreads(): ChatThread[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw) as ChatThread[];
  } catch {
    /* ignore corrupt data */
  }
  return [];
}

function saveThreads(threads: ChatThread[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(threads));
  } catch {
    /* quota exceeded – non-critical */
  }
}

function createEmptyThread(): ChatThread {
  const id = genId();
  return {
    id,
    title: "New Chat",
    messages: [],
    datasetInfo: null,
    createdAt: Date.now(),
    updatedAt: Date.now(),
  };
}

interface AppProps {
  colorMode: PaletteMode;
  onToggleColorMode: () => void;
}

function titleFromQuery(query: string): string {
  const trimmed = query.slice(0, 50).trim();
  return trimmed.length < query.trim().length ? `${trimmed}...` : trimmed;
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

function App({ colorMode, onToggleColorMode }: AppProps) {
  const [threads, setThreads] = useState<ChatThread[]>(() => {
    const stored = loadThreads();
    return stored.length > 0 ? stored : [createEmptyThread()];
  });
  const [activeThreadId, setActiveThreadId] = useState<string>(
    () => threads[0]?.id ?? ""
  );
  const [dataset, setDataset] = useState<UploadResponse | null>(null);
  const [isQuerying, setIsQuerying] = useState(false);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: "error" | "success" | "info";
  }>({ open: false, message: "", severity: "info" });

  const activeThread = threads.find((t) => t.id === activeThreadId) ?? threads[0];
  const messages = activeThread?.messages ?? [];

  // Persist on every change
  useEffect(() => {
    saveThreads(threads);
  }, [threads]);

  // ------- Thread helpers -------

  const updateThread = useCallback(
    (id: string, patch: Partial<ChatThread>) => {
      setThreads((prev) =>
        prev.map((t) =>
          t.id === id ? { ...t, ...patch, updatedAt: Date.now() } : t
        )
      );
    },
    []
  );

  const pushMessage = useCallback(
    (threadId: string, msg: ChatMessage) => {
      setThreads((prev) =>
        prev.map((t) =>
          t.id === threadId
            ? { ...t, messages: [...t.messages, msg], updatedAt: Date.now() }
            : t
        )
      );
    },
    []
  );

  const replaceLastMessage = useCallback(
    (threadId: string, msg: ChatMessage) => {
      setThreads((prev) =>
        prev.map((t) => {
          if (t.id !== threadId) return t;
          const msgs = [...t.messages];
          msgs[msgs.length - 1] = msg;
          return { ...t, messages: msgs, updatedAt: Date.now() };
        })
      );
    },
    []
  );

  const handleNewChat = () => {
    const thread = createEmptyThread();
    setThreads((prev) => [thread, ...prev]);
    setActiveThreadId(thread.id);
  };

  const handleSelectThread = (id: string) => {
    setActiveThreadId(id);
    const t = threads.find((t) => t.id === id);
    if (t?.datasetInfo) setDataset(t.datasetInfo);
  };

  const handleDeleteThread = (id: string) => {
    setThreads((prev) => {
      const next = prev.filter((t) => t.id !== id);
      if (next.length === 0) next.push(createEmptyThread());
      if (activeThreadId === id) setActiveThreadId(next[0].id);
      return next;
    });
  };

  // ------- File upload -------

  const handleFileUpload = async (file: File) => {
    const systemMsg: ChatMessage = {
      id: genId(),
      role: "system",
      content: `Uploading ${file.name}...`,
      timestamp: Date.now(),
      isLoading: true,
    };
    pushMessage(activeThreadId, systemMsg);

    try {
      const response = await uploadFile(file);
      setDataset(response);
      updateThread(activeThreadId, { datasetInfo: response });

      const doneMsg: ChatMessage = {
        ...systemMsg,
        content: `Uploaded ${file.name} — ${response.row_count.toLocaleString()} rows, ${response.columns.length} columns`,
        isLoading: false,
        uploadInfo: response,
        fileName: file.name,
      };
      replaceLastMessage(activeThreadId, doneMsg);

      if (activeThread.title === "New Chat") {
        updateThread(activeThreadId, { title: file.name });
      }

      setSnackbar({
        open: true,
        message: `${file.name} uploaded successfully`,
        severity: "success",
      });
    } catch (err) {
      const errText =
        err instanceof Error ? err.message : "Upload failed";

      const errorMsg: ChatMessage = {
        ...systemMsg,
        content: `Failed to upload ${file.name}: ${errText}`,
        isLoading: false,
      };
      replaceLastMessage(activeThreadId, errorMsg);
      setSnackbar({ open: true, message: errText, severity: "error" });
    }
  };

  // ------- Query -------

  const handleSendQuery = async (query: string) => {
    if (isQuerying) return;

    const userMsg: ChatMessage = {
      id: genId(),
      role: "user",
      content: query,
      timestamp: Date.now(),
    };
    pushMessage(activeThreadId, userMsg);

    if (
      activeThread.title === "New Chat" ||
      activeThread.title === activeThread.datasetInfo?.columns?.[0]
    ) {
      updateThread(activeThreadId, { title: titleFromQuery(query) });
    }

    const loadingMsg: ChatMessage = {
      id: genId(),
      role: "assistant",
      content: "",
      timestamp: Date.now(),
      isLoading: true,
    };
    pushMessage(activeThreadId, loadingMsg);
    setIsQuerying(true);

    try {
      const response = await runQuery(query);
      const assistantMsg: ChatMessage = {
        ...loadingMsg,
        isLoading: false,
        content: response.insights || "Here are the results:",
        sql: response.sql,
        chartHtml: response.chart_html,
        insights: response.insights,
        tableData: response.result,
      };
      replaceLastMessage(activeThreadId, assistantMsg);
    } catch (err) {
      const errText =
        err instanceof Error ? err.message : "Query failed. Please try again.";
      const errorMsg: ChatMessage = {
        ...loadingMsg,
        isLoading: false,
        content: `Something went wrong: ${errText}`,
      };
      replaceLastMessage(activeThreadId, errorMsg);
      setSnackbar({ open: true, message: errText, severity: "error" });
    } finally {
      setIsQuerying(false);
    }
  };

  // ------- Render -------

  const hasMessages = messages.length > 0;

  return (
    <Box sx={{ display: "flex", height: "100vh", bgcolor: "background.default" }}>
      <Sidebar
        threads={threads}
        activeThreadId={activeThreadId}
        dataset={dataset}
        colorMode={colorMode}
        onNewChat={handleNewChat}
        onSelectThread={handleSelectThread}
        onDeleteThread={handleDeleteThread}
        onToggleColorMode={onToggleColorMode}
      />

      <Box
        sx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          height: "100vh",
          minWidth: 0,
          ml: 0,
          width: `calc(100% - ${SIDEBAR_WIDTH}px)`,
        }}
      >
        {hasMessages ? (
          <ChatThreadView messages={messages} />
        ) : (
          <WelcomeScreen
            hasDataset={!!dataset}
            onSuggestedPrompt={handleSendQuery}
            onFileSelect={handleFileUpload}
          />
        )}

        <ChatInput
          onSend={handleSendQuery}
          onFileSelect={handleFileUpload}
          disabled={isQuerying}
          isLoading={isQuerying}
          placeholder={
            dataset
              ? "Ask a question about your data..."
              : "Upload a file first, or ask a general question..."
          }
        />
      </Box>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert
          onClose={() => setSnackbar((s) => ({ ...s, open: false }))}
          severity={snackbar.severity}
          variant="filled"
          sx={{ borderRadius: 2 }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default App;
