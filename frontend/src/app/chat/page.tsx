
"use client";

import { useEffect, useMemo, useState } from "react";
import { AuthGuard } from "@/components/AuthGuard";
import ChatBubble from "@/components/ChatBubble";
import MainSidebar from "@/components/MainSidebar";
import { AuthManager } from "@/utils/auth";
import type { Conversation, ConversationUpsert } from "@/types/conversation";

const LEGACY_STORAGE_KEY = "lucide_conversations_v1";
const STORAGE_PREFIX = "lucide_conversations_v2_";

const seedConversations: Conversation[] = [
  {
    id: "seed-1",
    sessionId: "seed-1",
    title: "PSG vs OM - Analyse",
    preview: "Pronostic 1X2 pour le classique",
    dateLabel: "Aujourd'hui",
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    messages: [
      {
        id: "seed-1-user",
        type: "user",
        content: "Analyse PSG vs OM.",
        timestamp: new Date().toISOString(),
      },
      {
        id: "seed-1-assistant",
        type: "assistant",
        content: "Voici une analyse rapide avec pronostic 1X2.",
        timestamp: new Date().toISOString(),
      },
    ],
    isArchived: false,
  },
  {
    id: "seed-2",
    sessionId: "seed-2",
    title: "Real Madrid - Buteurs",
    preview: "Qui va marquer ce soir?",
    dateLabel: "Hier",
    createdAt: new Date(Date.now() - 86400000).toISOString(),
    updatedAt: new Date(Date.now() - 86400000).toISOString(),
    messages: [
      {
        id: "seed-2-user",
        type: "user",
        content: "Quels buteurs pour Real Madrid ce soir?",
        timestamp: new Date(Date.now() - 86400000).toISOString(),
      },
      {
        id: "seed-2-assistant",
        type: "assistant",
        content: "Voici les buteurs probables selon la forme recente.",
        timestamp: new Date(Date.now() - 86400000).toISOString(),
      },
    ],
    isArchived: false,
  },
];

const getDateLabel = (isoDate: string) => {
  const target = new Date(isoDate);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const targetDay = new Date(target.getFullYear(), target.getMonth(), target.getDate());
  const diffDays = Math.round((today.getTime() - targetDay.getTime()) / 86400000);

  if (diffDays === 0) return "Aujourd'hui";
  if (diffDays === 1) return "Hier";
  return target.toLocaleDateString("fr-FR", { day: "2-digit", month: "short" });
};

const normalizeConversation = (conv: Conversation): Conversation => {
  const updatedAt = conv.updatedAt || conv.createdAt || new Date().toISOString();
  return {
    ...conv,
    id: conv.id || conv.sessionId,
    dateLabel: conv.dateLabel || getDateLabel(updatedAt),
    createdAt: conv.createdAt || updatedAt,
    updatedAt,
    title: conv.title || "Conversation",
    preview: conv.preview || "",
    messages: conv.messages || [],
  };
};

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [storageKey, setStorageKey] = useState<string | null>(null);
  const [isHydrated, setIsHydrated] = useState(false);

  const getStorageKey = (user: { user_id?: string; email?: string } | null) => {
    if (!user) return `${STORAGE_PREFIX}anonymous`;
    const identifier = user.user_id || user.email || "anonymous";
    return `${STORAGE_PREFIX}${identifier}`;
  };

  useEffect(() => {
    if (typeof window === "undefined") return;
    const user = AuthManager.getUser();
    const key = getStorageKey(user);
    setStorageKey(key);
    const raw = window.localStorage.getItem(key);
    if (raw) {
      try {
        const parsed = JSON.parse(raw) as Conversation[];
        setConversations(parsed.map(normalizeConversation));
        setIsHydrated(true);
        return;
      } catch (error) {
        console.error("Failed to parse conversations storage:", error);
      }
    }

    const legacyRaw = window.localStorage.getItem(LEGACY_STORAGE_KEY);
    if (legacyRaw) {
      try {
        const parsed = JSON.parse(legacyRaw) as Conversation[];
        const normalized = parsed.map(normalizeConversation);
        window.localStorage.setItem(key, JSON.stringify(normalized));
        setConversations(normalized);
        setIsHydrated(true);
        return;
      } catch (error) {
        console.error("Failed to migrate legacy conversations:", error);
      }
    }

    setConversations(seedConversations.map(normalizeConversation));
    setIsHydrated(true);
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (!storageKey || !isHydrated) return;
    window.localStorage.setItem(storageKey, JSON.stringify(conversations));
  }, [conversations, storageKey, isHydrated]);

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeConversationId) || null,
    [activeConversationId, conversations]
  );

  const handleConversationUpsert = (update: ConversationUpsert) => {
    setConversations((prev) => {
      const existingIndex = prev.findIndex(
        (conv) => conv.sessionId === update.sessionId || conv.id === update.sessionId
      );
      const now = update.updatedAt || new Date().toISOString();
      const existing = existingIndex >= 0 ? prev[existingIndex] : undefined;
      const conversation: Conversation = {
        id: existing?.id || update.sessionId,
        sessionId: update.sessionId,
        title: update.title || existing?.title || "Conversation",
        preview: update.preview || existing?.preview || "",
        dateLabel: getDateLabel(now),
        createdAt: existing?.createdAt || update.createdAt || now,
        updatedAt: now,
        context: update.context || existing?.context,
        contextSelection: update.contextSelection || existing?.contextSelection,
        messages: update.messages,
        isArchived: existing?.isArchived || false,
      };

      if (existingIndex >= 0) {
        const next = [...prev];
        next.splice(existingIndex, 1);
        return [conversation, ...next];
      }
      return [conversation, ...prev];
    });
    setActiveConversationId(update.sessionId);
  };

  const handleNewConversation = () => {
    setActiveConversationId(null);
  };

  const handleSelectConversation = (id: string) => {
    setActiveConversationId(id);
  };

  const handleToggleArchive = (id: string, archived: boolean) => {
    setConversations((prev) =>
      prev.map((conv) =>
        conv.id === id ? { ...conv, isArchived: archived } : conv
      )
    );
  };

  return (
    <AuthGuard>
      <div className="min-h-screen bg-slate-50">
        <MainSidebar
          conversations={conversations}
          activeConversationId={activeConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onToggleArchive={handleToggleArchive}
        />
        <div className="w-full lg:ml-16">
          <ChatBubble
            activeConversation={activeConversation}
            onConversationUpsert={handleConversationUpsert}
          />
        </div>
      </div>
    </AuthGuard>
  );
}
