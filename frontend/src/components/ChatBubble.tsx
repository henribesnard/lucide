
"use client";

import { useState, useEffect, useMemo } from "react";
import Image from "next/image";
import { ChatInputBubble } from "./chat/ChatInputBubble";
import { useContextSelection } from "@/hooks/useContextSelection";
import { useLanguage } from "@/contexts/LanguageContext";
import { useTranslation } from "@/i18n/translations";
import { AuthManager } from "@/utils/auth";
import type { ChatContext, League } from "@/types/context";
import type { Conversation, ConversationUpsert } from "@/types/conversation";

/* Defines internal Message type */
interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
}

/* Chat Request/Response Interfaces */
interface ChatRequest {
  message: string;
  session_id?: string;
  model_type?: 'deepseek' | 'medium' | 'fast';
}

interface EnrichedChatRequest extends ChatRequest {
  context?: ChatContext;
  language?: string;
}

interface ChatResponse {
  response: string;
  session_id: string;
  intent: string;
  entities: Record<string, any>;
  tools: string[];
}

interface ChatBubbleProps {
  activeConversation: Conversation | null;
  onConversationUpsert: (update: ConversationUpsert) => void;
}

export default function ChatBubble({
  activeConversation,
  onConversationUpsert,
}: ChatBubbleProps) {
  // --- Global State ---
  const [messages, setMessages] = useState<Message[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [inputValue, setInputValue] = useState("");
  const [modelType, setModelType] = useState<'deepseek' | 'medium' | 'fast'>('deepseek');

  // --- Language Hook ---
  const { language } = useLanguage();
  const { t } = useTranslation(language);

  // --- Context Selection Hook ---
  const {
    league: selectedLeague,
    match: selectedMatch,
    team: selectedTeam,
    player: selectedPlayer,
    setLeague,
    setMatch,
    setTeam,
    setPlayer,
    getChatContext,
  } = useContextSelection();

  const contextLocked = Boolean(activeConversation);

  useEffect(() => {
    if (activeConversation) {
      const hydrated = activeConversation.messages.map((msg) => ({
        ...msg,
        timestamp: new Date(msg.timestamp),
      }));
      setMessages(hydrated);
      setSessionId(activeConversation.sessionId);
      setInputValue("");
      setLeague(activeConversation.contextSelection?.league || null);
      setMatch(activeConversation.contextSelection?.match || null);
      setTeam(activeConversation.contextSelection?.team || null);
      setPlayer(activeConversation.contextSelection?.player || null);
      return;
    }

    setMessages([]);
    setSessionId(null);
    setInputValue("");
    setLeague(null);
    setMatch(null);
    setTeam(null);
    setPlayer(null);
  }, [activeConversation?.id, setLeague, setMatch, setPlayer, setTeam]);

  // --- Data State ---
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loadingLeagues, setLoadingLeagues] = useState(false);

  // --- Data Fetching ---
  useEffect(() => {
    const fetchAllLeagues = async () => {
      setLoadingLeagues(true);
      try {
        const response = await AuthManager.authenticatedFetch('/api/leagues/all');
        const data = await response.json();
        setLeagues(data.leagues || []);
      } catch (error) {
        console.error("Error fetching leagues:", error);
        setLeagues([]);
      } finally {
        setLoadingLeagues(false);
      }
    };
    fetchAllLeagues();
  }, []);


  // --- Send Logic ---
  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue,
      timestamp: new Date(),
    };

    const priorMessages = messages;
    const nextMessages = [...priorMessages, userMessage];
    setMessages(nextMessages);
    const messageToSend = inputValue;
    setInputValue("");
    setIsLoading(true);

    try {
      const contextSelection = contextLocked && activeConversation?.contextSelection
        ? activeConversation.contextSelection
        : {
          league: selectedLeague,
          match: selectedMatch,
          team: selectedTeam,
          player: selectedPlayer,
        };
      const chatContext =
        contextLocked && activeConversation?.context
          ? activeConversation.context
          : getChatContext();
      let contextualMessage = messageToSend;

      if (chatContext?.context_type === "match" && contextSelection?.match) {
        const match = contextSelection.match;
        const matchInfo = `Match: ${match.teams.home.name} vs ${match.teams.away.name} (${match.league.name}, ${new Date(match.date).toLocaleDateString("fr-FR")})`;
        contextualMessage = `${matchInfo}\n\nQuestion: ${messageToSend}`;
      } else if (chatContext?.context_type === "league_team" && contextSelection?.league && contextSelection?.team) {
        const teamInfo = `Equipe: ${contextSelection.team.name} - ${contextSelection.league.name}`;
        contextualMessage = `${teamInfo}\n\nQuestion: ${messageToSend}`;
      } else if (chatContext?.context_type === "team" && contextSelection?.team) {
        const teamInfo = `Equipe: ${contextSelection.team.name}`;
        contextualMessage = `${teamInfo}\n\nQuestion: ${messageToSend}`;
      } else if (chatContext?.context_type === "player" && contextSelection?.player) {
        const playerInfo = `Joueur: ${contextSelection.player.name} (${contextSelection.player.position})`;
        contextualMessage = `${playerInfo}\n\nQuestion: ${messageToSend}`;
      } else if (chatContext?.context_type === "league" && contextSelection?.league) {
        const leagueInfo = `Ligue: ${contextSelection.league.name}`;
        contextualMessage = `${leagueInfo}\n\nQuestion: ${messageToSend}`;
      }

      const requestBody: EnrichedChatRequest = {
        message: contextualMessage,
        session_id: sessionId || undefined,
        context: chatContext,
        model_type: modelType,
        language: language,
      };

      const response = await AuthManager.authenticatedFetch('/chat/stream', {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      // Create placeholder assistant message
      const assistantMessageId = (Date.now() + 1).toString();
      const assistantMessage: Message = {
        id: assistantMessageId,
        type: "assistant",
        content: "",
        timestamp: new Date(),
      };

      let updatedMessages = [...nextMessages, assistantMessage];
      setMessages(updatedMessages);

      // Stream processing
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let fullResponse = "";
      let receivedSessionId = sessionId;
      let receivedIntent = "";
      let receivedTools: string[] = [];

      if (reader) {
        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));

                if (data.type === 'metadata') {
                  if (!sessionId && data.session_id) {
                    receivedSessionId = data.session_id;
                    setSessionId(data.session_id);
                  }
                  if (data.intent) receivedIntent = data.intent;
                  if (data.tools) receivedTools = data.tools;
                } else if (data.type === 'chunk') {
                  fullResponse += data.content;
                  // Update message content progressively
                  updatedMessages = nextMessages.concat([{
                    ...assistantMessage,
                    content: fullResponse,
                  }]);
                  setMessages(updatedMessages);
                } else if (data.type === 'error') {
                  throw new Error(data.message);
                }
              }
            }
          }
        } finally {
          reader.releaseLock();
        }
      }

      // Final update with complete message
      const finalAssistantMessage: Message = {
        id: assistantMessageId,
        type: "assistant",
        content: fullResponse,
        timestamp: new Date(),
      };

      updatedMessages = [...nextMessages, finalAssistantMessage];
      setMessages(updatedMessages);

      const storedMessages = updatedMessages.map((msg) => ({
        id: msg.id,
        type: msg.type,
        content: msg.content,
        timestamp: msg.timestamp.toISOString(),
      }));
      const titleSource = messageToSend.split("\n")[0].trim() || "Conversation";
      const title =
        titleSource.length > 48 ? `${titleSource.slice(0, 48)}...` : titleSource;
      const previewSource = finalAssistantMessage.content.replace(/\s+/g, " ").trim();
      const preview =
        previewSource.length > 80
          ? `${previewSource.slice(0, 80)}...`
          : previewSource;
      onConversationUpsert({
        sessionId: receivedSessionId || sessionId || "unknown",
        messages: storedMessages,
        context: chatContext,
        contextSelection,
        title,
        preview,
      });
    } catch (error) {
      console.error("Error calling chat API:", error);

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: error instanceof Error ? `Erreur: ${error.message}` : "Désolé, une erreur s'est produite.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };


  // --- Derived Props for ChatInputBubble ---
  const favoriteLeagueIds = useMemo(
    () => leagues.filter((l) => l.is_favorite).map((l) => l.id),
    [leagues]
  );

  const showWelcome = messages.length === 0;

  return (
    <div className="flex flex-col h-full bg-slate-50">
      {/* Changed min-h-screen to h-full because parent container usually handles layout */}
      {showWelcome ? (
        // Welcome Screen
        <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
          <div className="mb-12">
            <div className="flex items-center justify-center gap-4 mb-4">
              <div className="w-24 h-24 rounded-3xl bg-white flex items-center justify-center shadow-lg shadow-teal-500/10 ring-1 ring-slate-200/60">
                <Image src="/statos-s.svg" alt="STATOS" width={64} height={64} priority />
              </div>
            </div>

          </div>

          <div className="w-full max-w-2xl">
            <ChatInputBubble
              value={inputValue}
              onChange={setInputValue}
              onSubmit={handleSend}
              isLoading={isLoading}
              contextLocked={contextLocked}
              league={selectedLeague}
              match={selectedMatch}
              team={selectedTeam}
              player={selectedPlayer}
              onLeagueSelect={setLeague}
              onMatchSelect={setMatch}
              onTeamSelect={setTeam}
              onPlayerSelect={setPlayer}
              leagues={leagues}
              favoriteLeagueIds={favoriteLeagueIds}
              loadingLeagues={loadingLeagues}
              modelType={modelType}
              onModelTypeChange={setModelType}
            />
          </div>
        </div>
      ) : (
        // Messages Screen
        <div className="flex flex-col h-screen lg:h-auto lg:flex-1">
          {/* Header */}
          <div className="px-6 py-4 bg-white/80 backdrop-blur-md sticky top-0 z-10 border-b border-slate-200/50">
            <div className="max-w-4xl mx-auto flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-white flex items-center justify-center shadow-sm ring-1 ring-slate-200/60">
                <Image src="/statos-s.svg" alt="STATOS" width={24} height={24} />
              </div>
              <div>
                <span className="text-[10px] text-slate-500 font-medium">{t('assistantFootball')}</span>
              </div>
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto px-4 py-6 scroll-smooth">
            <div className="max-w-3xl mx-auto space-y-8">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2 duration-300`}
                >
                  <div
                    className={`
                        max-w-[85%] sm:max-w-[75%] px-5 py-3.5 rounded-2xl shadow-sm
                        ${message.type === 'user'
                        ? 'bg-teal-600 text-white rounded-tr-md'
                        : 'bg-white text-slate-700 border border-slate-100 rounded-tl-md'}
                      `}
                  >
                    <p className="text-[15px] leading-relaxed whitespace-pre-wrap">{message.content}</p>

                    {/* Timestamp */}
                    <span className={`text-[10px] mt-1.5 block opacity-60 font-medium ${message.type === 'user' ? 'text-teal-100' : 'text-slate-400'}`}>
                      {message.timestamp.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" })}
                    </span>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start animate-in fade-in duration-300">
                  <div className="bg-white border border-slate-100 px-5 py-4 rounded-2xl rounded-tl-md shadow-sm flex items-center gap-1.5">
                    <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce [animation-delay:-0.3s]"></div>
                    <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce [animation-delay:-0.15s]"></div>
                    <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce"></div>
                  </div>
                </div>
              )}

              {/* Spacer for bottom bubble */}
              <div className="h-32"></div>
            </div>
          </div>

          {/* Bottom Input Area */}
          <div className="px-4 pb-6 pt-2 bg-gradient-to-t from-slate-50 via-slate-50/90 to-transparent sticky bottom-0 z-20">
            <div className="max-w-3xl mx-auto">
              <ChatInputBubble
                value={inputValue}
                onChange={setInputValue}
                onSubmit={handleSend}
                isLoading={isLoading}
                contextLocked={contextLocked}
                league={selectedLeague}
                match={selectedMatch}
                team={selectedTeam}
                player={selectedPlayer}
                onLeagueSelect={setLeague}
                onMatchSelect={setMatch}
                onTeamSelect={setTeam}
                onPlayerSelect={setPlayer}
                leagues={leagues}
                favoriteLeagueIds={favoriteLeagueIds}
                loadingLeagues={loadingLeagues}
                modelType={modelType}
                onModelTypeChange={setModelType}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
