import type { ChatContext, League, Match, Team, Player } from "@/types/context";

export type ConversationMessage = {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: string;
};

export type ConversationContextSelection = {
  league?: League | null;
  match?: Match | null;
  team?: Team | null;
  player?: Player | null;
};

export type Conversation = {
  id: string;
  title: string;
  preview: string;
  dateLabel: string;
  createdAt: string;
  updatedAt: string;
  sessionId: string;
  context?: ChatContext;
  contextSelection?: ConversationContextSelection;
  messages: ConversationMessage[];
  isArchived?: boolean;
};

export type ConversationUpsert = {
  sessionId: string;
  messages: ConversationMessage[];
  context?: ChatContext;
  contextSelection?: ConversationContextSelection;
  title?: string;
  preview?: string;
  createdAt?: string;
  updatedAt?: string;
};
