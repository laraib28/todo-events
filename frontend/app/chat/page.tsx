"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import ChatContainer from "@/components/ChatContainer";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatResponse {
  message: string;
  metadata?: {
    action: string;
    task_id?: number;
    count?: number;
  };
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSendMessage = async (userMessage: string) => {
    if (!userMessage.trim()) return;

    // Add user message to UI immediately
    const newUserMessage: Message = {
      role: "user",
      content: userMessage,
    };
    setMessages((prev) => [...prev, newUserMessage]);

    // Set loading state
    setIsLoading(true);
    setError(null);

    try {
      // Send message to API
      const response = await api.sendChatMessage(userMessage) as ChatResponse;

      // Add assistant response
      const assistantMessage: Message = {
        role: "assistant",
        content: response.message,
      };
      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      setError(err.message || "Failed to send message");

      // Add error message from assistant
      const errorMessage: Message = {
        role: "assistant",
        content: `Sorry, I encountered an error: ${err.message || "Failed to send message"}. Please try again.`,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-4xl mx-auto">
        <div className="mb-4">
          <h1 className="text-3xl font-bold text-gray-900">AI Chat</h1>
          <p className="text-gray-600 mt-1">
            Manage your tasks with natural language
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        <ChatContainer
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
