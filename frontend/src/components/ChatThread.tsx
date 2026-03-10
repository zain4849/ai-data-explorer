import React, { useEffect, useRef } from "react";
import { Box } from "@mui/material";
import type { ChatMessage } from "../types/chat";
import MessageBubble from "./MessageBubble";

interface ChatThreadProps {
  messages: ChatMessage[];
}

const ChatThread: React.FC<ChatThreadProps> = ({ messages }: ChatThreadProps) => {
  const bottomRef = useRef<HTMLDivElement>(null); // Watch cosden solutions for useRef

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <Box
      sx={{
        flex: 1,
        overflow: "auto",
        display: "flex",
        flexDirection: "column",
        py: 3,
        px: 2,
        maxWidth: 880,
        mx: "auto",
        width: "100%",
      }}
    >
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      <div ref={bottomRef} />
    </Box>
  );
};

export default ChatThread;
