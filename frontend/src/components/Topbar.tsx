"use client";

import type { HealthResponse } from "../lib/types";

type TopbarProps = {
  sessionId?: string;
  health?: HealthResponse | null;
};

export function Topbar({ sessionId, health }: TopbarProps) {
  return (
    <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-full items-center justify-between px-6">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-teal-600 to-teal-800 text-white text-sm">
            ⚽
          </div>
          <span className="font-display text-lg font-bold text-slate-900">lucide</span>
          <span className="ml-2 rounded-md bg-teal-50 px-2 py-0.5 text-xs font-semibold text-teal-700">
            pro
          </span>
        </div>

        <div className="flex items-center gap-3">
          {health && (
            <div className="hidden items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-xs text-slate-600 md:flex">
              <span className={`h-1.5 w-1.5 rounded-full ${health.status === "ok" ? "bg-green-500" : "bg-amber-500"}`} />
              <span>{health.llm_provider}</span>
            </div>
          )}

          {sessionId && (
            <div className="hidden items-center gap-2 rounded-full bg-slate-100 px-3 py-1.5 text-xs text-slate-600 lg:flex">
              <span className="h-1.5 w-1.5 rounded-full bg-green-500" />
              <span>Session active</span>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
