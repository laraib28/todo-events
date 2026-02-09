"use client";

import type { JSX } from "react";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
}

/**
 * Simple markdown-like formatting for chat messages
 * Supports:
 * - Bold: **text** or __text__
 * - Lists: - item or * item
 * - Code: `code`
 */
function formatContent(content: string): JSX.Element[] {
  const lines = content.split("\n");
  const elements: JSX.Element[] = [];

  lines.forEach((line, index) => {
    let formattedLine: JSX.Element;

    // Check if line is a list item
    if (line.trim().match(/^[-*]\s/)) {
      const text = line.replace(/^[-*]\s/, "");
      formattedLine = (
        <li key={index} className="ml-4">
          {formatInlineContent(text)}
        </li>
      );
    } else if (line.trim()) {
      formattedLine = <div key={index}>{formatInlineContent(line)}</div>;
    } else {
      formattedLine = <br key={index} />;
    }

    elements.push(formattedLine);
  });

  return elements;
}

/**
 * Format inline markdown (bold, code)
 */
function formatInlineContent(text: string): (string | JSX.Element)[] {
  const parts: (string | JSX.Element)[] = [];
  let remaining = text;
  let key = 0;

  // Bold: **text** or __text__
  const boldRegex = /(\*\*|__)(.*?)\1/g;
  // Code: `text`
  const codeRegex = /`([^`]+)`/g;

  // Combine patterns
  const combinedRegex = /(\*\*|__)(.*?)\1|`([^`]+)`/g;
  let lastIndex = 0;
  let match;

  while ((match = combinedRegex.exec(text)) !== null) {
    // Add text before match
    if (match.index > lastIndex) {
      parts.push(text.substring(lastIndex, match.index));
    }

    // Add formatted match
    if (match[1]) {
      // Bold
      parts.push(
        <strong key={`bold-${key++}`} className="font-semibold">
          {match[2]}
        </strong>
      );
    } else if (match[3]) {
      // Code
      parts.push(
        <code
          key={`code-${key++}`}
          className="bg-gray-200 px-1 rounded text-xs font-mono"
        >
          {match[3]}
        </code>
      );
    }

    lastIndex = match.index + match[0].length;
  }

  // Add remaining text
  if (lastIndex < text.length) {
    parts.push(text.substring(lastIndex));
  }

  return parts.length > 0 ? parts : [text];
}

export default function ChatMessage({ role, content }: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div
        className={`max-w-[70%] rounded-lg px-4 py-2 ${
          isUser
            ? "bg-blue-500 text-white"
            : "bg-gray-100 text-gray-900 border border-gray-200"
        }`}
      >
        <div className="text-sm font-semibold mb-1">
          {isUser ? "You" : "AI Assistant"}
        </div>
        <div className="text-sm space-y-1">
          {isUser ? (
            <div className="whitespace-pre-wrap">{content}</div>
          ) : (
            <div className="formatted-content">{formatContent(content)}</div>
          )}
        </div>
      </div>
    </div>
  );
}
