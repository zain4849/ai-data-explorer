import { useCallback, useEffect, useRef, useState } from "react";
import { Alert, Box, Snackbar, type PaletteMode } from "@mui/material";
import {
  uploadFile,
  runQuery,
  listChatThreads,
  createChatThread,
  getChatThread,
  updateChatThread,
  deleteChatThread,
  addChatMessage,
  listDatasets,
  type ChatThreadApi,
  type DatasetInfo,
} from "./api/client";
import type { ChatMessage, ChatThread } from "./types/chat";
import type { UploadResponse } from "./types/api";
import { useAuth } from "./context/AuthContext";
import Sidebar, { SIDEBAR_WIDTH } from "./components/Sidebar";
import ChatThreadView from "./components/ChatThreadView";
import ChatInput from "./components/ChatInput";
import WelcomeScreen from "./components/WelcomeScreen";
import DashboardPage from "./pages/DashboardPage";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const genId = () => crypto.randomUUID?.() ?? `${Date.now()}-${Math.random()}`;

function titleFromQuery(query: string): string {
  const trimmed = query.slice(0, 50).trim();
  return trimmed.length < query.trim().length ? `${trimmed}...` : trimmed;
}

function apiMsgToLocal(m: {
  id: string;
  role: string;
  content: string;
  sql?: string | null;
  chart_html?: string | null;
  insights?: string | null;
  result_json?: string | null;
  file_name?: string | null;
  created_at: string;
}): ChatMessage {
  return {
    id: m.id,
    role: m.role as ChatMessage["role"], // Someone could be sending a message with a role that's not user, assistant, or system
    content: m.content,
    timestamp: new Date(m.created_at).getTime(),
    sql: m.sql ?? undefined, // sql for role assistant not needed for user messages
    chartHtml: m.chart_html ?? undefined, // chart_html for role assistant not needed for user messages
    insights: m.insights ?? undefined, // insights for role assistant, not needed for user messages
    tableData: m.result_json ? JSON.parse(m.result_json) : undefined, // result_json is a string, so we need to parse it into an object
    fileName: m.file_name ?? undefined, // file_name is a string, so we need to parse it into an object
  };
}

interface AppProps {
  colorMode: PaletteMode;
  onToggleColorMode: () => void;
}

// ---------------------------------------------------------------------------
// App
// ---------------------------------------------------------------------------

function App({ colorMode, onToggleColorMode }: AppProps) {
  const { user } = useAuth();

  const [threads, setThreads] = useState<ChatThread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string>("");
  const [dataset, setDataset] = useState<UploadResponse | null>(null);
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [activeConnectionId, setActiveConnectionId] = useState<string | null>(null);
  const [isQuerying, setIsQuerying] = useState(false);
  const [view, setView] = useState<"chat" | "dashboards">("chat");
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: "error" | "success" | "info";
  }>({ open: false, message: "", severity: "info" });

  const initialLoadDone = useRef(false);

  const activeThread = threads.find((t) => t.id === activeThreadId) ?? threads[0];
  const messages = activeThread?.messages ?? [];

  // ------- Initial load from server -------
  useEffect(() => {
    if (!user || initialLoadDone.current) return;
    initialLoadDone.current = true;

    (async () => {
      try {
        const [serverThreads, serverDatasets] = await Promise.all([
          listChatThreads(),
          listDatasets(),
        ]);
        setDatasets(serverDatasets);

        if (serverThreads.length === 0) {
          const created = await createChatThread("New Chat"); // POST request to the backend
          const local: ChatThread = {
            id: created.id,
            title: created.title,
            messages: [],
            datasetInfo: null,
            createdAt: new Date(created.created_at).getTime(),
            updatedAt: new Date(created.updated_at).getTime(),
          };
          setThreads([local]);
          setActiveThreadId(local.id);
        } else {
          const firstDetail = await getChatThread(serverThreads[0].id); // GET request to the backend, gets the first thread
          const localThreads: ChatThread[] = serverThreads.map((st: ChatThreadApi) => ({ // Convert ChatThreadApi -> ChatThread
            id: st.id,
            title: st.title,
            messages:
              st.id === firstDetail.id
                ? firstDetail.messages.map(apiMsgToLocal)
                : [],
            datasetInfo: null,
            createdAt: new Date(st.created_at).getTime(),
            updatedAt: new Date(st.updated_at).getTime(), 
          }));
          setThreads(localThreads);
          setActiveThreadId(localThreads[0].id);
        }
      } catch (err) {
        console.error("Failed to load threads from server:", err);
        const fallback: ChatThread = {
          id: genId(),
          title: "New Chat",
          messages: [],
          datasetInfo: null,
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };
        setThreads([fallback]);
        setActiveThreadId(fallback.id);
      }
    })();
  }, [user]);

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

  const handleNewChat = async () => {
    try {
      const created = await createChatThread("New Chat");
      const thread: ChatThread = {
        id: created.id,
        title: created.title,
        messages: [],
        datasetInfo: null,
        createdAt: new Date(created.created_at).getTime(),
        updatedAt: new Date(created.updated_at).getTime(),
      };
      setThreads((prev) => [thread, ...prev]);
      setActiveThreadId(thread.id);
    } catch {
      const thread: ChatThread = {
        id: genId(),
        title: "New Chat",
        messages: [],
        datasetInfo: null,
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      setThreads((prev) => [thread, ...prev]);
      setActiveThreadId(thread.id);
    }
  };

  const handleSelectThread = async (id: string) => {
    setActiveThreadId(id);
    const existing = threads.find((t) => t.id === id);
    if (existing?.datasetInfo) setDataset(existing.datasetInfo);

    // Lazy-load messages if not yet fetched
    if (existing && existing.messages.length === 0) {
      try {
        const detail = await getChatThread(id);
        const msgs = detail.messages.map(apiMsgToLocal);
        updateThread(id, { messages: msgs, datasetInfo: null });
      } catch {
        /* messages will stay empty until user interacts */
      }
    }
  };

  const handleDeleteThread = async (id: string) => {
    try {
      await deleteChatThread(id);
    } catch {
      /* continue with local delete even if server fails */
    }
    setThreads((prev) => {
      const next = prev.filter((t) => t.id !== id);
      if (next.length === 0) {
        handleNewChat();
        return next;
      }
      if (activeThreadId === id) setActiveThreadId(next[0].id);
      return next;
    });
  };

  // ------- Persist message to server (fire-and-forget) -------

  const persistMessage = useCallback(
    (threadId: string, msg: ChatMessage) => {
      addChatMessage(threadId, {
        role: msg.role,
        content: msg.content,
        sql: msg.sql,
        result_json: msg.tableData ? JSON.stringify(msg.tableData) : undefined,
        chart_html: msg.chartHtml,
        insights: msg.insights,
        file_name: msg.fileName,
      }).catch((err) => console.warn("Failed to persist message:", err));
    },
    []
  );

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
      setActiveConnectionId(null); // Switch to File Upload so NL queries run against uploaded data (DuckDB)
      updateThread(activeThreadId, { datasetInfo: response });

      const doneMsg: ChatMessage = {
        ...systemMsg,
        content: `Uploaded ${file.name} — ${response.row_count.toLocaleString()} rows, ${response.columns.length} columns`,
        isLoading: false,
        uploadInfo: response,
        fileName: file.name,
      };
      replaceLastMessage(activeThreadId, doneMsg);
      persistMessage(activeThreadId, doneMsg);

      if (activeThread.title === "New Chat") {
        const newTitle = file.name;
        updateThread(activeThreadId, { title: newTitle });
        updateChatThread(activeThreadId, { title: newTitle }).catch(() => {});
      }
      
      // Refresh datasets list
      listDatasets().then(setDatasets).catch(() => {});

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
    persistMessage(activeThreadId, userMsg);

    if (
      activeThread.title === "New Chat" ||
      activeThread.title === activeThread.datasetInfo?.columns?.[0]
    ) {
      const newTitle = titleFromQuery(query);
      updateThread(activeThreadId, { title: newTitle });
      updateChatThread(activeThreadId, { title: newTitle }).catch(() => {});
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
      const connectionId =
        activeThread.datasetInfo != null || dataset != null
          ? undefined
          : (activeConnectionId ?? undefined);
      const response = await runQuery(query, connectionId);
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
      persistMessage(activeThreadId, assistantMsg);
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
      {/* Sidebar */}
      <Sidebar
        threads={threads}
        activeThreadId={activeThreadId}
        dataset={dataset}
        datasets={datasets}
        colorMode={colorMode}
        activeConnectionId={activeConnectionId}
        onNewChat={handleNewChat}
        onSelectThread={handleSelectThread}
        onDeleteThread={handleDeleteThread}
        onToggleColorMode={onToggleColorMode}
        onSelectConnection={setActiveConnectionId}
        onShowDashboards={() => setView("dashboards")}
      />

      {/* Main content area */}
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
        {view === "dashboards" ? (
          <DashboardPage onBack={() => setView("chat")} />
        ) : (
          <>
            {hasMessages ? (
              <ChatThreadView
                messages={messages}
                onSnackbar={(msg, severity) =>
                  setSnackbar({ open: true, message: msg, severity: severity ?? "info" })
                }
              />
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
          </>
        )}
      </Box>

      {/* Snackbar */}
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
