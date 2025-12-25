"use client";

import { useState } from "react";
import Image from "next/image";
import {
  BoltIcon,
  CalendarDaysIcon,
  TrophyIcon,
  StarIcon,
} from "@heroicons/react/24/outline";

type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  intent?: string;
  tools?: string[];
  entities?: Record<string, unknown>;
};

type ChatInterfaceProps = {
  messages: Message[];
  input: string;
  loading: boolean;
  onInputChange: (value: string) => void;
  onSendMessage: (text?: string) => void;
};

const categories = ["Stats", "Pronostic", "Live"] as const;
const leagues = [
  "Toutes ligues",
  "Ligue 1",
  "Premier League",
  "La Liga",
  "Serie A",
  "Bundesliga",
  "Champions League",
];

const suggestions = [
  {
    icon: BoltIcon,
    title: "Live maintenant",
    desc: "Matchs en cours et scores temps reel",
  },
  {
    icon: CalendarDaysIcon,
    title: "Programme du jour",
    desc: "Tous les matchs d'aujourd'hui",
  },
  {
    icon: TrophyIcon,
    title: "Champions League",
    desc: "Resultats et classement",
  },
  {
    icon: StarIcon,
    title: "Top buteurs",
    desc: "Meilleurs marqueurs de la saison",
  },
];

export function ChatInterface({
  messages,
  input,
  loading,
  onInputChange,
  onSendMessage,
}: ChatInterfaceProps) {
  const [category, setCategory] = useState<string>("Stats");
  const [league, setLeague] = useState<string>("Toutes ligues");

  return (
    <div className="flex h-full flex-col bg-gradient-to-b from-slate-50 to-white">
      {messages.length === 0 ? (
        <div className="flex flex-1 flex-col items-center justify-center px-4 pb-24">
          <div className="mb-12 text-center">
            <div className="mb-4 flex justify-center">
              <div className="flex h-24 w-24 items-center justify-center rounded-3xl bg-white shadow-lg shadow-teal-500/10 ring-1 ring-slate-200/60">
                <Image src="/statos-s.svg" alt="STATOS" width={64} height={64} priority />
              </div>
            </div>

            <p className="mx-auto max-w-2xl text-lg text-slate-600">
              Posez vos questions, analysez les matchs, comparez les cotes et suivez le live.
            </p>
          </div>

          <div className="grid w-full max-w-3xl gap-3 md:grid-cols-2">
            {suggestions.map((suggestion) => {
              const Icon = suggestion.icon;
              return (
                <button
                  key={suggestion.title}
                  onClick={() => onSendMessage(suggestion.title)}
                  className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 text-left shadow-sm transition-all hover:border-teal-400 hover:shadow-md"
                >
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50 text-teal-700">
                    <Icon className="h-5 w-5" />
                  </span>
                  <div>
                    <p className="font-semibold text-slate-900">{suggestion.title}</p>
                    <p className="text-sm text-slate-600">{suggestion.desc}</p>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto px-4 py-6 scrollbar-hide">
          <div className="mx-auto max-w-3xl space-y-6">
            {messages.map((msg) => {
              const isUser = msg.role === "user";
              return (
                <div
                  key={msg.id}
                  className={`flex gap-4 ${isUser ? "flex-row-reverse" : ""}`}
                >
                  <div
                    className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${isUser
                      ? "bg-gradient-to-br from-teal-600 to-teal-700 text-white"
                      : "bg-white text-slate-700 ring-1 ring-slate-200"
                      }`}
                  >
                    {isUser ? (
                      "U"
                    ) : (
                      <Image src="/statos-s.svg" alt="STATOS" width={16} height={16} />
                    )}
                  </div>
                  <div className="flex-1">
                    <div
                      className={`rounded-2xl px-4 py-3 ${isUser
                        ? "bg-gradient-to-br from-teal-600 to-teal-700 text-white"
                        : "bg-slate-100 text-slate-900"
                        }`}
                    >
                      <p className="whitespace-pre-line text-sm leading-relaxed">{msg.content}</p>
                    </div>
                    {(msg.intent || msg.tools || msg.entities) && (
                      <div className="mt-2 flex flex-wrap gap-2">
                        {msg.intent && (
                          <span className="rounded-md bg-teal-50 px-2 py-1 text-xs font-semibold text-teal-700">
                            {msg.intent}
                          </span>
                        )}
                        {msg.tools?.map((tool) => (
                          <span
                            key={tool}
                            className="rounded-md bg-slate-200 px-2 py-1 text-xs font-semibold text-slate-700"
                          >
                            {tool}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            {loading && (
              <div className="flex gap-4">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white ring-1 ring-slate-200">
                  <Image src="/statos-s.svg" alt="STATOS" width={16} height={16} />
                </div>
                <div className="flex-1 rounded-2xl bg-slate-100 px-4 py-3">
                  <div className="space-y-2">
                    <div className="h-2 w-16 animate-pulse rounded bg-slate-300" />
                    <div className="h-2 w-3/4 animate-pulse rounded bg-slate-300" />
                    <div className="h-2 w-1/2 animate-pulse rounded bg-slate-300" />
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      <div className="border-t border-slate-200 bg-white/95 p-6 backdrop-blur-sm">
        <div className="mx-auto max-w-4xl">
          <div className="rounded-2xl border border-slate-300 bg-white p-2 shadow-xl focus-within:border-teal-500 focus-within:ring-2 focus-within:ring-teal-200">
            <div className="flex items-center gap-2">
              <button
                title="Rechercher"
                className="flex h-10 w-10 items-center justify-center rounded-xl text-slate-500 hover:bg-slate-100"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </button>

              <div className="flex flex-wrap items-center gap-2">
                {categories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setCategory(cat)}
                    className={`rounded-lg px-3 py-1.5 text-sm font-semibold transition-colors ${category === cat
                      ? "bg-teal-100 text-teal-700"
                      : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                      }`}
                  >
                    {cat}
                  </button>
                ))}

                <select
                  value={league}
                  onChange={(e) => setLeague(e.target.value)}
                  className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-sm font-semibold text-slate-700 hover:border-teal-600"
                >
                  {leagues.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </select>
              </div>

              <input
                value={input}
                onChange={(e) => onInputChange(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    onSendMessage();
                  }
                }}
                placeholder="Demandez n'importe quoi. Tapez @ pour les mentions."
                className="flex-1 border-none bg-transparent px-3 py-2 text-sm outline-none placeholder:text-slate-400"
              />

              <div className="flex items-center gap-1">
                <button
                  title="Ajouter une image"
                  className="flex h-10 w-10 items-center justify-center rounded-xl text-slate-500 hover:bg-slate-100"
                >
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </button>

                <button
                  onClick={() => onSendMessage()}
                  disabled={loading || !input.trim()}
                  className="ml-1 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-r from-teal-600 to-teal-700 text-white shadow-md transition-all hover:from-teal-700 hover:to-teal-800 disabled:opacity-50"
                >
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </button>
              </div>
            </div>
          </div>

          <p className="mt-3 text-center text-xs text-slate-500">
            STATOS peut faire des erreurs. Verifiez les informations importantes.
          </p>
        </div>
      </div>
    </div>
  );
}
