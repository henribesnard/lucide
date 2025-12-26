"use client";

import { useState } from "react";
import Image from "next/image";
import {
  Bars3Icon,
  XMarkIcon,
  PlusIcon,
  BoltIcon,
  ChartBarIcon,
  ChartPieIcon,
  TrophyIcon,
} from "@heroicons/react/24/outline";

type Conversation = {
  id: string;
  title: string;
  date: string;
};

const mockConversations: Conversation[] = [
  { id: "1", title: "PSG vs OM - Analyse tactique", date: "Aujourd'hui" },
  { id: "2", title: "Top buteurs Ligue 1", date: "Hier" },
  { id: "3", title: "Cotes Champions League", date: "2 dec" },
  { id: "4", title: "Live Real Madrid - Barcelone", date: "28 nov" },
  { id: "5", title: "Pronostics week-end", date: "23 nov" },
];

const shortcuts = [
  { label: "Live maintenant", icon: BoltIcon },
  { label: "Pronostics", icon: ChartBarIcon },
  { label: "Statistiques", icon: ChartPieIcon },
  { label: "Classements", icon: TrophyIcon },
];

export function Sidebar() {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="fixed left-4 top-4 z-50 flex h-10 w-10 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-700 shadow-sm hover:bg-slate-50 lg:hidden"
        aria-label="Menu"
      >
        <Bars3Icon className="h-5 w-5" />
      </button>

      <aside
        className={`fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white shadow-sm transition-transform lg:static lg:translate-x-0 ${isOpen ? "translate-x-0" : "-translate-x-full"
          }`}
      >
        <div className="flex items-center justify-between border-b border-slate-200 p-4">
          <div className="flex items-center gap-2">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-white ring-1 ring-slate-200/60">
              <Image src="/statos-s.svg" alt="STATOS" width={24} height={24} />
            </div>
          </div>
          <button
            onClick={() => setIsOpen(false)}
            className="text-slate-400 hover:text-slate-600 lg:hidden"
            aria-label="Fermer"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        <div className="p-4">
          <button className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-teal-600 to-teal-700 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:from-teal-700 hover:to-teal-800">
            <PlusIcon className="h-4 w-4" />
            <span>Nouvelle conversation</span>
          </button>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 scrollbar-hide">
          <div className="mb-3">
            <h3 className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
              Conversations recentes
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
            {shortcuts.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.label}
                  className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
                >
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 text-slate-600">
                    <Icon className="h-4 w-4" />
                  </span>
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        </nav>

        <div className="border-t border-slate-200 p-4">
          <div className="rounded-lg bg-gradient-to-br from-teal-50 to-teal-100 p-3">
            <p className="text-xs font-semibold text-teal-900">Assistant STATOS</p>
            <p className="mt-1 text-xs text-slate-600">
              Propulse par API-Football + IA
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
