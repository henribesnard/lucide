import React, { useState, useEffect, useMemo } from 'react';
import { DateSelector } from '../DateSelector';
import type { Match } from '@/types/context';
import { format, addDays, subDays } from 'date-fns';
import { AuthManager } from '@/utils/auth';

interface MatchDropdownProps {
    leagueId: number;
    onSelect: (match: Match) => void;
}

export const MatchDropdown: React.FC<MatchDropdownProps> = ({
    leagueId,
    onSelect
}) => {
    const storageKey = useMemo(() => `match-dropdown-date:${leagueId}`, [leagueId]);
    const normalize = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const today = normalize(new Date());
    const clamp = (d: Date) => {
        const min = subDays(today, 7);
        const max = addDays(today, 7);
        const n = normalize(d);
        if (n < min) return min;
        if (n > max) return max;
        return n;
    };
    const [selectedDate, setSelectedDate] = useState(() => {
        if (typeof window !== 'undefined') {
            const stored = window.sessionStorage.getItem(storageKey);
            if (stored) {
                const parsed = new Date(`${stored}T00:00:00`);
                if (!isNaN(parsed.getTime())) return clamp(parsed);
            }
        }
        return today;
    });
    const [matches, setMatches] = useState<Match[]>([]);
    const [loading, setLoading] = useState(false);

    // Fonctions utilitaires
    const isLiveMatch = (statusShort: string) => {
        return ['1H', '2H', 'HT', 'ET', 'P', 'BT', 'SUSP', 'INT', 'LIVE'].includes(statusShort);
    };

    const isFinishedMatch = (statusShort: string) => {
        return ['FT', 'AET', 'PEN', 'AWD', 'WO'].includes(statusShort);
    };

    const isMatchPast = (match: Match) => {
        // Un match est considéré passé si son timestamp est > 2h dans le passé
        // (un match dure ~90-120 min, donc après 2h il est forcément terminé)
        const now = Date.now();
        const matchTime = match.timestamp * 1000; // timestamp en millisecondes
        const twoHoursInMs = 2 * 60 * 60 * 1000;
        return (now - matchTime) > twoHoursInMs;
    };

    const hasScore = (match: Match) => {
        // Un score est valide si les deux valeurs sont des nombres (même 0)
        return typeof match.goals.home === 'number' && typeof match.goals.away === 'number';
    };

    useEffect(() => {
        loadMatches();
        if (typeof window !== 'undefined') {
            // Stocker uniquement la date (sans fuseau) pour éviter les retours au jour courant
            window.sessionStorage.setItem(storageKey, format(selectedDate, 'yyyy-MM-dd'));
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [selectedDate, leagueId]);

    // Auto-refresh pour les matchs en direct
    useEffect(() => {
        const hasLiveMatches = matches.some(match => isLiveMatch(match.status.short));

        if (!hasLiveMatches) return;

        // Rafraîchir toutes les 30 secondes si des matchs sont en direct
        const interval = setInterval(() => {
            loadMatches();
        }, 30000);

        return () => clearInterval(interval);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [matches]);

    const loadMatches = async () => {
        setLoading(true);
        try {
            const dateStr = format(selectedDate, 'yyyy-MM-dd');
            const response = await AuthManager.authenticatedFetch(
                `/api/fixtures?league_id=${leagueId}&date=${dateStr}`
            );
            const data = await response.json();
            const mapped: Match[] = (data.fixtures || []).map((item: any) => ({
                id: item.fixture?.id ?? 0,
                date: item.fixture?.date ?? '',
                timestamp: item.fixture?.timestamp ?? 0,
                league: {
                    id: item.league?.id ?? 0,
                    name: item.league?.name ?? '',
                    logo: item.league?.logo ?? '',
                },
                teams: {
                    home: {
                        id: item.teams?.home?.id ?? 0,
                        name: item.teams?.home?.name ?? '',
                        logo: item.teams?.home?.logo ?? '',
                    },
                    away: {
                        id: item.teams?.away?.id ?? 0,
                        name: item.teams?.away?.name ?? '',
                        logo: item.teams?.away?.logo ?? '',
                    },
                },
                goals: {
                    home: item.goals?.home ?? null,
                    away: item.goals?.away ?? null,
                },
                status: {
                    short: item.fixture?.status?.short ?? 'NS',
                    long: item.fixture?.status?.long ?? '',
                    elapsed: item.fixture?.status?.elapsed ?? null,
                },
            }));
            setMatches(mapped);
        } catch (error) {
            console.error('Error loading matches:', error);
            setMatches([]);
        } finally {
            setLoading(false);
        }
    };

    const formatMatchTime = (dateStr: string) => {
        const date = new Date(dateStr);
        return format(date, 'HH:mm');
    };

    const formatElapsedTime = (elapsed: number | null, statusShort: string) => {
        if (!elapsed) return statusShort;
        if (statusShort === 'HT') return 'MT';
        return `${elapsed}'`;
    };

    return (
        <div className="w-80 max-h-[340px] bg-white rounded-2xl shadow-xl border border-slate-100 flex flex-col overflow-hidden">
            <DateSelector
                selectedDate={selectedDate}
                onDateChange={setSelectedDate}
            />

            <div className="overflow-y-auto flex-1 p-1">
                {loading ? (
                    <div className="p-4 text-center text-sm text-slate-400 animate-pulse">
                        Chargement...
                    </div>
                ) : matches.length > 0 ? (
                    matches.map(match => (
                        <button
                            key={match.id}
                            onClick={() => onSelect(match)}
                            className="w-full flex items-center justify-between px-3 py-2.5 text-left rounded-xl hover:bg-slate-50 transition-colors border-b border-slate-50 last:border-0 group"
                        >
                            <div className="flex items-center gap-2 flex-1 justify-end">
                                <span className="text-sm font-medium text-slate-700 truncate max-w-[80px]">
                                    {match.teams.home.name}
                                </span>
                                <img
                                    src={match.teams.home.logo}
                                    alt=""
                                    className="w-5 h-5 object-contain"
                                />
                            </div>

                            <div className="mx-2 flex flex-col items-center min-w-[80px]">
                                {isLiveMatch(match.status.short) ? (
                                    <>
                                        <div className="text-[8px] font-bold text-teal-600 mb-1 px-1.5 py-0.5 bg-teal-50 rounded flex items-center gap-1">
                                            <div className="w-1 h-1 rounded-full bg-teal-500 animate-pulse"></div>
                                            EN DIRECT
                                        </div>
                                        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-white border border-teal-200">
                                            <span className="text-sm font-bold text-slate-800">
                                                {match.goals.home ?? 0}
                                            </span>
                                            <span className="text-[10px] text-slate-400">-</span>
                                            <span className="text-sm font-bold text-slate-800">
                                                {match.goals.away ?? 0}
                                            </span>
                                        </div>
                                        <div className="text-[9px] text-teal-600 font-semibold mt-1">
                                            {formatElapsedTime(match.status.elapsed, match.status.short)}
                                        </div>
                                    </>
                                ) : isFinishedMatch(match.status.short) || (isMatchPast(match) && hasScore(match)) ? (
                                    <>
                                        <div className="text-[8px] font-bold text-slate-500 mb-1 px-1.5 py-0.5 bg-slate-100 rounded">
                                            TERMINÉ
                                        </div>
                                        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-white border border-slate-200">
                                            <span className="text-sm font-bold text-slate-800">
                                                {match.goals.home ?? 0}
                                            </span>
                                            <span className="text-[10px] text-slate-400">-</span>
                                            <span className="text-sm font-bold text-slate-800">
                                                {match.goals.away ?? 0}
                                            </span>
                                        </div>
                                    </>
                                ) : isMatchPast(match) && !hasScore(match) ? (
                                    <>
                                        <div className="text-[8px] font-bold text-slate-500 mb-1 px-1.5 py-0.5 bg-slate-100 rounded">
                                            TERMINÉ
                                        </div>
                                        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded bg-white border border-slate-200">
                                            <span className="text-sm font-bold text-slate-400">?</span>
                                            <span className="text-[10px] text-slate-400">-</span>
                                            <span className="text-sm font-bold text-slate-400">?</span>
                                        </div>
                                        <div className="text-[9px] text-slate-400 mt-1">
                                            Score indisponible
                                        </div>
                                    </>
                                ) : (
                                    <>
                                        <div className="text-[8px] font-bold text-slate-400 mb-1 px-1.5 py-0.5 bg-slate-50 rounded">
                                            À VENIR
                                        </div>
                                        <div className="px-2 py-0.5 rounded text-xs font-bold bg-slate-100 text-slate-500 group-hover:bg-teal-50 group-hover:text-teal-600 transition-colors">
                                            VS
                                        </div>
                                        <div className="text-[9px] text-slate-400 font-mono mt-1">
                                            {match.date ? formatMatchTime(match.date) : '--:--'}
                                        </div>
                                    </>
                                )}
                            </div>

                            <div className="flex items-center gap-2 flex-1 justify-start">
                                <img
                                    src={match.teams.away.logo}
                                    alt=""
                                    className="w-5 h-5 object-contain"
                                />
                                <span className="text-sm font-medium text-slate-700 truncate max-w-[80px]">
                                    {match.teams.away.name}
                                </span>
                            </div>
                        </button>
                    ))
                ) : (
                    <div className="p-8 text-center">
                        <div className="text-4xl mb-2">Zzz</div>
                        <div className="text-sm text-slate-500">
                            Aucun match prévu ce jour
                        </div>
                        <div className="text-xs text-slate-400 mt-1">
                            Essayez une autre date
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
