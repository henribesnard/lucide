"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import { AuthGuard } from "@/components/AuthGuard";
import { RouteErrorBoundary } from "@/components/RouteErrorBoundary";
import ChatBubble from "@/components/ChatBubble";
import MainSidebar from "@/components/MainSidebar";
import { ConversationsAPI, type ConversationListItem } from "@/utils/conversations";
import type { Conversation, ConversationUpsert } from "@/types/conversation";

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

/**
 * Convertir une conversation de l'API vers le format frontend
 */
const apiToFrontendConversation = (apiConv: ConversationListItem): Conversation => {
  return {
    id: apiConv.conversation_id,
    sessionId: apiConv.conversation_id,
    title: apiConv.title,
    preview: "", // Sera rempli quand on charge les messages
    dateLabel: getDateLabel(apiConv.updated_at),
    createdAt: apiConv.created_at,
    updatedAt: apiConv.updated_at,
    messages: [],
    isArchived: apiConv.is_archived,
  };
};

export default function ChatPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Charger les conversations depuis l'API
   */
  const loadConversations = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Charger les conversations actives et archivées
      const [activeConvs, archivedConvs] = await Promise.all([
        ConversationsAPI.list(false),
        ConversationsAPI.list(true),
      ]);

      const allConversations = [...activeConvs, ...archivedConvs].map(apiToFrontendConversation);
      setConversations(allConversations);
    } catch (err) {
      console.error("Failed to load conversations:", err);
      setError(err instanceof Error ? err.message : "Failed to load conversations");
      setConversations([]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  /**
   * Charger les conversations au montage du composant
   */
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeConversationId) || null,
    [activeConversationId, conversations]
  );

  const handleConversationUpsert = async (update: ConversationUpsert) => {
    // Mise à jour optimiste de l'UI
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

    // Persister dans la base de données
    try {
      const existing = conversations.find(
        (conv) => conv.sessionId === update.sessionId || conv.id === update.sessionId
      );

      if (existing && existing.id !== update.sessionId) {
        // Mettre à jour une conversation existante
        await ConversationsAPI.update(existing.id, {
          title: update.title || existing.title,
        });
      }
      // Note: Si c'est une nouvelle conversation (existing.id === update.sessionId),
      // elle sera créée automatiquement par le backend lors du premier message
    } catch (err) {
      console.error("Failed to persist conversation:", err);
      // On ne rollback pas l'UI car la conversation fonctionne quand même
      // (stockée en mémoire côté backend)
    }
  };

  const handleNewConversation = () => {
    setActiveConversationId(null);
  };

  const handleSelectConversation = (id: string) => {
    setActiveConversationId(id);
  };

  const handleToggleArchive = async (id: string, archived: boolean) => {
    try {
      // Mise à jour optimiste
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === id ? { ...conv, isArchived: archived } : conv
        )
      );

      // Appel API
      await ConversationsAPI.update(id, { is_archived: archived });
    } catch (err) {
      console.error("Failed to toggle archive:", err);
      // Rollback en cas d'erreur
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === id ? { ...conv, isArchived: !archived } : conv
        )
      );
      setError(err instanceof Error ? err.message : "Failed to update conversation");
    }
  };

  return (
    <AuthGuard>
      <RouteErrorBoundary routeName="chat">
        <div className="min-h-screen bg-slate-50">
          {error && (
            <div className="fixed top-4 right-4 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg shadow-md z-50">
              <p className="text-sm font-medium">{error}</p>
              <button
                onClick={() => setError(null)}
                className="absolute top-1 right-1 text-red-600 hover:text-red-800"
              >
                ×
              </button>
            </div>
          )}

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
      </RouteErrorBoundary>
    </AuthGuard>
  );
}
