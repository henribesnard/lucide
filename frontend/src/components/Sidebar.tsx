"use client";

import { useState } from "react";

type Conversation = {
  id: string;
  title: string;
  date: string;
};

const mockConversations: Conversation[] = [
  { id: "1", title: "PSG vs OM - Analyse tactique", date: "Aujourd'hui" },
  { id: "2", title: "Top buteurs Ligue 1", date: "Hier" },
  { id: "3", title: "Cotes Champions League", date: "2 déc" },
  { id: "4", title: "Live Real Madrid - Barcelone", date: "28 nov" },
  { id: "5", title: "Pronostics week-end", date: "23 nov" },
];

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed left-4 top-4 z-50 flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-700 shadow-sm hover:bg-slate-50 lg:hidden"
      >
        ☰
      </button>

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white shadow-sm transition-transform lg:static lg:translate-x-0 ${
          isOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex items-center justify-between border-b border-slate-200 p-4">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-teal-600 to-teal-800 text-white">
              ⚽
            </div>
            <span className="font-semibold text-slate-900">Lucide</span>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="text-slate-400 hover:text-slate-600 lg:hidden"
          >
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="p-4">
          <button className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-teal-600 to-teal-700 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:from-teal-700 hover:to-teal-800">
            <span>+</span>
            <span>Nouvelle conversation</span>
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 scrollbar-hide">
          <div className="mb-3">
            <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Conversations récentes
            </h3>
            {mockConversations.map((conv) => (
              <button
                key={conv.id}
                className="flex w-full flex-col items-start gap-1 rounded-lg px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
              >
                <span className="truncate font-medium">{conv.title}</span>
                <span className="text-xs text-slate-400">{conv.date}</span>
              </button>
            ))}
          </div>

          <div className="border-t border-slate-200 pt-3">
            <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Raccourcis
            </h3>
            {[
              { label: "Live maintenant", icon: "🔴" },
              { label: "Pronostics", icon: "🎯" },
              { label: "Statistiques", icon: "📊" },
              { label: "Classements", icon: "🏆" },
            ].map((item) => (
              <button
                key={item.label}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
              >
                <span className="text-lg">{item.icon}</span>
                <span>{item.label}</span>
              </button>
            ))}
          </div>
        </nav>

        <div className="border-t border-slate-200 p-4">
          <div className="rounded-lg bg-gradient-to-br from-teal-50 to-blue-50 p-3">
            <p className="text-xs font-semibold text-teal-900">Assistant Football</p>
            <p className="mt-1 text-xs text-slate-600">
              Propulsé par API-Football + IA
            </p>
          </div>
        </div>
      </aside>

      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/20 lg:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}
    </>
  );
}
