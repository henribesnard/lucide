import React, { useState, useEffect } from 'react';
import { AuthManager } from '@/utils/auth';
import { SearchIcon } from '../icons/ContextIcons';
import type { Team } from '@/types/context';

interface TeamDropdownProps {
  leagueId?: number;
  season?: number;
  onSelect: (team: Team) => void;
}

export const TeamDropdown: React.FC<TeamDropdownProps> = ({
  leagueId,
  season,
  onSelect,
}) => {
  const [teams, setTeams] = useState<Team[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const requiresQuery = !leagueId && search.length < 2;

  useEffect(() => {
    const fetchTeams = async () => {
      if (requiresQuery) {
        setLoading(false);
        setTeams([]);
        return;
      }
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (leagueId) params.append('league', leagueId.toString());
        if (season) params.append('season', season.toString());
        if (search) params.append('search', search);

        const query = params.toString();
        const url = query ? `/api/teams?${query}` : '/api/teams';
        const response = await AuthManager.authenticatedFetch(url);
        const data = await response.json();
        setTeams(data.teams || []);
      } catch (error) {
        console.error('Error fetching teams:', error);
        setTeams([]);
      } finally {
        setLoading(false);
      }
    };

    fetchTeams();
  }, [leagueId, season, search, requiresQuery]);

  return (
    <div className="w-80 max-h-[340px] bg-white rounded-2xl shadow-xl border border-slate-100 flex flex-col overflow-hidden">
      <div className="p-3 border-b border-slate-50">
        <div className="relative flex items-center bg-slate-50 rounded-xl px-3 py-2">
          <SearchIcon className="w-4 h-4 text-slate-400 mr-2" />
          <input
            type="text"
            placeholder="Rechercher une equipe..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-transparent border-none outline-none text-sm text-slate-700 placeholder-slate-400 w-full"
            autoFocus
          />
        </div>
      </div>

      <div className="overflow-y-auto flex-1 p-1 space-y-1">
        {loading ? (
          <div className="p-4 text-center text-sm text-slate-400">Chargement...</div>
        ) : requiresQuery ? (
          <div className="p-4 text-center text-sm text-slate-400">
            Choisissez une ligue ou tapez au moins 2 caracteres
          </div>
        ) : teams.length === 0 ? (
          <div className="p-4 text-center text-sm text-slate-400">Aucune equipe trouvee</div>
        ) : (
          teams.map((team) => (
            <button
              key={team.id}
              onClick={() => onSelect(team)}
              className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-blue-50 transition-colors text-left"
            >
              <img
                src={team.logo}
                alt={team.name}
                className="w-7 h-7 object-contain"
              />
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-slate-700 truncate">
                  {team.name}
                </div>
                <div className="text-xs text-slate-400 truncate">
                  {team.country}{team.code ? ` - ${team.code}` : ''}
                </div>
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  );
};
