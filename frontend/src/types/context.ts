
// Nouveau modèle de contexte : ligue au premier niveau, match optionnel.
export interface League {
  id: number;
  name: string;
  country: string;
  country_code: string;
  logo: string;
  flag: string;
  type: 'league' | 'cup';
  season: number;
  is_favorite?: boolean;
}

export interface Match {
  id: number;
  date: string;
  timestamp: number;
  league: {
    id: number;
    name: string;
    logo: string;
  };
  teams: {
    home: { id: number; name: string; logo: string };
    away: { id: number; name: string; logo: string };
  };
  goals: {
    home: number | null;
    away: number | null;
  };
  status: {
    short: string;
    long: string;
    elapsed: number | null;
  };
}

export interface Team {
  id: number;
  name: string;
  code: string;
  country: string;
  founded: number;
  logo: string;
  national: boolean;
}

export interface Player {
  id: number;
  name: string;
  firstname: string;
  lastname: string;
  age: number;
  birth: {
    date: string;
    place: string;
    country: string;
  };
  nationality: string;
  height: string;
  weight: string;
  position: string;
  photo: string;
  injured?: boolean;
}

export type ContextType =
  | 'league'
  | 'match'
  | 'team'
  | 'league_team'
  | 'player';

export interface ContextSelection {
  type: ContextType;
  league?: League;
  match?: Match;
  team?: Team;
  player?: Player;
}

export interface ChatContext {
  context_type: ContextType;
  match_id?: number;
  league_id?: number;
  team_id?: number;
  player_id?: number;
  league_name?: string;
  league_country?: string;
  home_team_id?: number;
  away_team_id?: number;
  match_date?: string;
  team_name?: string;
  team_code?: string;
  player_name?: string;
  position?: string;
}

// Legacy zone types kept for compatibility with older components (deprecated)
export type ZoneType = 'national' | 'continental' | 'international';

export interface Zone {
  name: string;
  code: string;
  flag: string;
  zone_type?: ZoneType;
  full_name?: string;
}

export type Country = Zone;
