import React, { useState, useEffect } from 'react';
import { AuthManager } from '@/utils/auth';
import { SearchIcon } from '../icons/ContextIcons';
import type { Player } from '@/types/context';

interface PlayerDropdownProps {
  matchId?: number;
  teamId?: number;
  leagueId?: number;
  onSelect: (player: Player) => void;
}

interface PlayersByTeam {
  team: {
    id: number;
    name: string;
    logo: string;
  };
  players: Player[];
}

export const PlayerDropdown: React.FC<PlayerDropdownProps> = ({
  matchId,
  teamId,
  leagueId,
  onSelect,
}) => {
  const [players, setPlayers] = useState<Player[]>([]);
  const [playersByTeam, setPlayersByTeam] = useState<{home: PlayersByTeam | null; away: PlayersByTeam | null}>({
    home: null,
    away: null
  });
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const isMatchMode = Boolean(matchId);

  // Fonction pour décoder les entités HTML (comme &apos; → ')
  const decodeHtmlEntities = (text: string): string => {
    const parser = new DOMParser();
    const doc = parser.parseFromString(text, 'text/html');
    return doc.documentElement.textContent || text;
  };

  useEffect(() => {
    const fetchPlayers = async () => {
      // Mode Match: charger joueurs des 2 équipes
      if (isMatchMode && matchId) {
        setLoading(true);
        try {
          const response = await AuthManager.authenticatedFetch(
            `/api/fixtures/${matchId}/players`
          );
          const data = await response.json();
          setPlayersByTeam({
            home: data.teams?.home || null,
            away: data.teams?.away || null
          });
        } catch (error) {
          console.error('Error fetching match players:', error);
          setPlayersByTeam({ home: null, away: null });
        } finally {
          setLoading(false);
        }
        return;
      }

      // Mode Équipe: charger joueurs d'une équipe
      if (search.length < 3 && !teamId && !leagueId) {
        setPlayers([]);
        return;
      }

      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (teamId) params.append('team', teamId.toString());
        if (leagueId) params.append('league', leagueId.toString());
        if (search) params.append('search', search);

        const response = await AuthManager.authenticatedFetch(
          `/api/players?${params.toString()}`
        );
        const data = await response.json();
        setPlayers(data.players || []);
      } catch (error) {
        console.error('Error fetching players:', error);
        setPlayers([]);
      } finally {
        setLoading(false);
      }
    };

    const debounce = setTimeout(fetchPlayers, 300);
    return () => clearTimeout(debounce);
  }, [matchId, teamId, leagueId, search, isMatchMode]);

  // Filtrage local pour le mode match
  const filteredHomePlayers = isMatchMode && playersByTeam.home
    ? playersByTeam.home.players.filter(p =>
        search.length === 0 || p.name.toLowerCase().includes(search.toLowerCase())
      )
    : [];

  const filteredAwayPlayers = isMatchMode && playersByTeam.away
    ? playersByTeam.away.players.filter(p =>
        search.length === 0 || p.name.toLowerCase().includes(search.toLowerCase())
      )
    : [];

  const renderPlayerButton = (player: Player) => (
    <button
      key={player.id}
      onClick={() => onSelect(player)}
      className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-purple-50 transition-colors text-left"
    >
      <img
        src={player.photo}
        alt={player.name}
        className="w-9 h-9 object-cover rounded-full"
      />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-slate-700 truncate">
          {decodeHtmlEntities(player.name)}
        </div>
        <div className="text-xs text-slate-400 truncate">
          {player.position} - {player.nationality} - {player.age} ans
        </div>
      </div>
      {player.injured && (
        <span className="text-[10px] bg-red-100 text-red-700 px-2 py-0.5 rounded">
          Blesse
        </span>
      )}
    </button>
  );

  return (
    <div className="w-80 max-h-[340px] bg-white rounded-2xl shadow-xl border border-slate-100 flex flex-col overflow-hidden">
      <div className="p-3 border-b border-slate-50">
        <div className="relative flex items-center bg-slate-50 rounded-xl px-3 py-2">
          <SearchIcon className="w-4 h-4 text-slate-400 mr-2" />
          <input
            type="text"
            placeholder={isMatchMode ? "Rechercher un joueur..." : "Rechercher un joueur... (min 3 caracteres)"}
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
        ) : isMatchMode ? (
          // Mode Match: Afficher joueurs groupés par équipe
          <>
            {playersByTeam.home && (
              <div className="mb-3">
                <div className="px-3 py-2 flex items-center gap-2 bg-slate-50 sticky top-0">
                  <img src={playersByTeam.home.team.logo} alt="" className="w-5 h-5" />
                  <span className="text-xs font-semibold text-slate-600">
                    {playersByTeam.home.team.name}
                  </span>
                </div>
                {filteredHomePlayers.length === 0 ? (
                  <div className="p-2 text-center text-xs text-slate-400">Aucun joueur</div>
                ) : (
                  filteredHomePlayers.map(renderPlayerButton)
                )}
              </div>
            )}
            {playersByTeam.away && (
              <div>
                <div className="px-3 py-2 flex items-center gap-2 bg-slate-50 sticky top-0">
                  <img src={playersByTeam.away.team.logo} alt="" className="w-5 h-5" />
                  <span className="text-xs font-semibold text-slate-600">
                    {playersByTeam.away.team.name}
                  </span>
                </div>
                {filteredAwayPlayers.length === 0 ? (
                  <div className="p-2 text-center text-xs text-slate-400">Aucun joueur</div>
                ) : (
                  filteredAwayPlayers.map(renderPlayerButton)
                )}
              </div>
            )}
          </>
        ) : (
          // Mode Équipe: Afficher liste simple avec recherche
          <>
            {search.length < 3 && !teamId && !leagueId ? (
              <div className="p-4 text-center text-sm text-slate-400">
                Tapez au moins 3 caracteres pour rechercher
              </div>
            ) : players.length === 0 ? (
              <div className="p-4 text-center text-sm text-slate-400">Aucun joueur trouve</div>
            ) : (
              players.map(renderPlayerButton)
            )}
          </>
        )}
      </div>
    </div>
  );
};
