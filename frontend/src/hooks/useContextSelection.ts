import { useState, useCallback, useMemo } from 'react';
import type {
  League,
  Match,
  Team,
  Player,
  ContextSelection,
  ContextType,
  ChatContext,
} from '@/types/context';

export const useContextSelection = () => {
  const [league, setLeague] = useState<League | null>(null);
  const [match, setMatch] = useState<Match | null>(null);
  const [team, setTeam] = useState<Team | null>(null);
  const [player, setPlayer] = useState<Player | null>(null);

  const contextType = useMemo((): ContextType | null => {
    if (player) return 'player';
    if (match) return 'match';
    if (league && team) return 'league_team';
    if (team) return 'team';
    if (league) return 'league';
    return null;
  }, [league, match, team, player]);

  const contextSelection = useMemo((): ContextSelection | null => {
    if (!contextType) return null;

    return {
      type: contextType,
      league: league || undefined,
      match: match || undefined,
      team: team || undefined,
      player: player || undefined,
    };
  }, [contextType, league, match, team, player]);

  const getChatContext = useCallback((): ChatContext | undefined => {
    if (!contextType) return undefined;

    const ctx: ChatContext = {
      context_type: contextType,
    };

    if (match) {
      ctx.match_id = match.id;
      ctx.league_id = match.league.id;
      ctx.home_team_id = match.teams.home.id;
      ctx.away_team_id = match.teams.away.id;
      ctx.match_date = match.date;
    } else if (contextType === 'league_team' && league && team) {
      ctx.league_id = league.id;
      ctx.league_name = league.name;
      ctx.league_country = league.country;
      ctx.team_id = team.id;
      ctx.team_name = team.name;
      ctx.team_code = team.code;
    } else if (team) {
      ctx.team_id = team.id;
      ctx.team_name = team.name;
      ctx.team_code = team.code;
    } else if (player) {
      ctx.player_id = player.id;
      ctx.player_name = player.name;
      ctx.position = player.position;
    } else if (league) {
      ctx.league_id = league.id;
      ctx.league_name = league.name;
      ctx.league_country = league.country;
    }

    return ctx;
  }, [contextType, league, match, team, player]);

  const handleSetLeague = useCallback((newLeague: League | null) => {
    setLeague(newLeague);
    if (!newLeague) {
      setMatch(null);
    }
  }, []);

  const handleSetMatch = useCallback((newMatch: Match | null) => {
    setMatch(newMatch);
    if (newMatch) {
      setTeam(null);
      setPlayer(null);
    }
  }, []);

  const handleSetTeam = useCallback((newTeam: Team | null) => {
    setTeam(newTeam);
    if (newTeam) {
      setMatch(null);
      setPlayer(null);
    }
  }, []);

  const handleSetPlayer = useCallback((newPlayer: Player | null) => {
    setPlayer(newPlayer);
    if (newPlayer) {
      setMatch(null);
      setTeam(null);
      setLeague(null);
    }
  }, []);

  const clearAll = useCallback(() => {
    setLeague(null);
    setMatch(null);
    setTeam(null);
    setPlayer(null);
  }, []);

  return {
    league,
    match,
    team,
    player,
    contextType,
    contextSelection,
    setLeague: handleSetLeague,
    setMatch: handleSetMatch,
    setTeam: handleSetTeam,
    setPlayer: handleSetPlayer,
    clearAll,
    getChatContext,
    hasContext: Boolean(contextType),
  };
};
