"use client";

type Insight = {
  title: string;
  value: string;
};

type RightSidebarProps = {
  insights: Insight[];
  health?: { status: string; llm_provider: string } | null;
};

export function RightSidebar({ insights, health }: RightSidebarProps) {
  return (
    <aside className="hidden w-80 flex-col gap-4 border-l border-slate-200 bg-white p-4 lg:flex">
      <div>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Statut système
        </h3>
        <div className="rounded-lg border border-slate-200 bg-slate-50 p-3">
          <div className="flex items-center gap-2 text-xs">
            <span className={`h-2 w-2 rounded-full ${health?.status === "ok" ? "bg-teal-500" : "bg-amber-500"}`} />
            <span className="font-medium text-slate-700">
              {health ? `${health.status.toUpperCase()} · ${health.llm_provider}` : "Chargement..."}
            </span>
          </div>
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Informations en temps réel
        </h3>
        <div className="space-y-2">
          <div className="flex items-center gap-2 rounded-lg border border-teal-200 bg-teal-50 px-3 py-2">
            <span className="text-sm font-semibold text-teal-700">Live ready</span>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2">
            <span className="text-sm font-semibold text-amber-700">Cotes temps réel</span>
          </div>
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Stats rapides
        </h3>
        <div className="space-y-3">
          {insights.map((insight, idx) => (
            <div key={idx} className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-wide text-teal-700">
                {insight.title}
              </p>
              <p className="mt-1 text-sm font-semibold text-slate-900">{insight.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-slate-500">
          Raccourcis
        </h3>
        <div className="space-y-1">
          {[
            "Live maintenant",
            "Programme Ligue 1",
            "Champions League",
            "Top buteurs",
          ].map((action) => (
            <button
              key={action}
              className="w-full rounded-lg px-3 py-2 text-left text-sm text-slate-700 hover:bg-slate-50"
            >
              {action}
            </button>
          ))}
        </div>
      </div>
    </aside>
  );
}
