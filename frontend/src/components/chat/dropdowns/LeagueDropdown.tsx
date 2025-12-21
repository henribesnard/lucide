import React, { useMemo, useState } from 'react';
import type { League } from '@/types/context';
import { SearchIcon } from '../icons/ContextIcons';

interface LeagueDropdownProps {
    leagues: League[];
    favoriteIds: number[];
    onSelect: (league: League) => void;
    loading?: boolean;
}

const displayNames = typeof Intl !== 'undefined'
    ? new Intl.DisplayNames(['fr'], { type: 'region' })
    : null;

function toFrenchCountryName(country: string, countryCode?: string) {
    if (countryCode) {
        const code = countryCode.toUpperCase();
        if (code === 'WORLD') return 'International';
        try {
            const localized = displayNames?.of(code);
            if (localized) return localized;
        } catch {
            // fallback below
        }
    }
    // Fallback manual tweaks for some names
    const manual: Record<string, string> = {
        'England': 'Angleterre',
        'Scotland': 'Écosse',
        'Wales': 'Pays de Galles',
        'Northern Ireland': 'Irlande du Nord',
        'United States': 'États-Unis',
        'USA': 'États-Unis',
        'Germany': 'Allemagne',
        'Italy': 'Italie',
        'Spain': 'Espagne',
        'France': 'France',
        'Portugal': 'Portugal',
        'Netherlands': 'Pays-Bas',
        'World': 'International'
    };
    return manual[country] || country;
}

export const LeagueDropdown: React.FC<LeagueDropdownProps> = ({
    leagues,
    favoriteIds,
    onSelect,
    loading
}) => {
    const [searchTerm, setSearchTerm] = useState('');

    const filtered = useMemo(() => {
        const query = searchTerm.toLowerCase();
        return leagues.filter(
            (l) =>
                l.name.toLowerCase().includes(query) ||
                l.country.toLowerCase().includes(query)
        );
    }, [leagues, searchTerm]);

    const grouped = useMemo(() => {
        const favorites: League[] = [];
        const others: League[] = [];
        filtered.forEach((l) => {
            if (favoriteIds.includes(l.id) || l.is_favorite) {
                favorites.push({ ...l, is_favorite: true });
            } else {
                others.push(l);
            }
        });
        favorites.sort((a, b) => a.name.localeCompare(b.name));
        others.sort((a, b) => {
            const countryCompare = (a.country || '').localeCompare(b.country || '');
            if (countryCompare !== 0) return countryCompare;
            return a.name.localeCompare(b.name);
        });
        return { favorites, others };
    }, [filtered, favoriteIds]);

    const renderRow = (league: League) => {
        const countryLabel = toFrenchCountryName(league.country, league.country_code);
        const typeLabel = league.type === 'cup' ? 'Coupe' : 'Ligue';

        return (
            <button
                key={league.id}
                onClick={() => onSelect(league)}
                className="w-full flex items-center gap-3 px-3 py-2 hover:bg-slate-50 transition-colors rounded-xl text-left"
            >
                <img src={league.logo} alt={league.name} className="w-6 h-6 object-contain" />
                <div className="flex-1">
                    <div className="text-sm font-medium text-slate-700">
                        {league.name}
                    </div>
                    <div className="flex items-center gap-1.5 text-[10px] text-slate-400">
                        <span>{countryLabel}</span>
                    </div>
                </div>
                <div className={`px-2 py-0.5 rounded text-[9px] font-medium uppercase ${league.type === 'cup' ? 'bg-amber-100 text-amber-600' : 'bg-blue-100 text-blue-600'}`}>
                    {typeLabel}
                </div>
            </button>
        );
    };

    return (
        <div className="w-80 max-h-[340px] bg-white rounded-2xl shadow-xl border border-slate-100 flex flex-col overflow-hidden">
            <div className="p-3 border-b border-slate-50">
                <div className="relative flex items-center bg-slate-50 rounded-xl px-3 py-2">
                    <SearchIcon className="w-4 h-4 text-slate-400 mr-2" />
                    <input
                        type="text"
                        placeholder="Rechercher une ligue..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="bg-transparent border-none outline-none text-sm text-slate-700 placeholder-slate-400 w-full"
                        autoFocus
                    />
                </div>
            </div>

            <div className="overflow-y-auto flex-1 p-1 space-y-2">
                {loading ? (
                    <div className="p-4 text-center text-sm text-slate-400">Chargement...</div>
                ) : (
                    <>
                        {grouped.favorites.length > 0 && (
                            <div>
                                <div className="px-3 py-1 flex items-center gap-2 text-[10px] font-bold text-amber-500 uppercase tracking-wider">
                                    * Favoris
                                </div>
                                {grouped.favorites.map(renderRow)}
                            </div>
                        )}

                        {grouped.others.length > 0 && (
                            <div>
                                <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-t border-slate-50 pt-2 mt-1">
                                    {grouped.favorites.length > 0 ? 'Toutes les ligues' : 'Ligues'}
                                </div>
                                {grouped.others.map(renderRow)}
                            </div>
                        )}

                        {filtered.length === 0 && (
                            <div className="p-4 text-center text-sm text-slate-400">Aucune ligue trouvée</div>
                        )}
                    </>
                )}
            </div>
        </div>
    );
};
