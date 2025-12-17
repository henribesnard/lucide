"use client";

import { GlobeAltIcon } from "@heroicons/react/24/outline";

interface Country {
  name: string;
  code: string;
  flag: string;
}

interface League {
  league: {
    id: number;
    name: string;
    logo: string;
  };
  country: {
    name: string;
    code: string;
    flag: string;
  };
}

interface Match {
  fixture: {
    id: number;
    date: string;
  };
  teams: {
    home: {
      id: number;
      name: string;
      logo: string;
    };
    away: {
      id: number;
      name: string;
      logo: string;
    };
  };
  goals: {
    home: number | null;
    away: number | null;
  };
}

interface ContextBarProps {
  country?: Country | null;
  league?: League | null;
  match?: Match | null;
  onCountryClick?: () => void;
  onLeagueClick?: () => void;
  onMatchClick?: () => void;
}

export default function ContextBar({
  country,
  league,
  match,
  onCountryClick,
  onLeagueClick,
  onMatchClick,
}: ContextBarProps) {
  return (
    <div className="flex items-center gap-0.5 px-3 py-1.5 border-t border-gray-100">
      {/* Country Button */}
      <button
        onClick={onCountryClick}
        className={`p-1.5 rounded-md transition-all ${
          country
            ? "bg-gray-100 text-gray-700"
            : "text-gray-400 hover:bg-gray-50 hover:text-gray-600"
        }`}
        title={country ? country.name : "Pays"}
        type="button"
      >
        {country && country.name.toLowerCase() !== "world" ? (
          <img
            src={country.flag}
            alt={country.name}
            className="w-4 h-3 object-contain"
          />
        ) : (
          <GlobeAltIcon className="w-4 h-4" />
        )}
      </button>

      {/* League Button */}
      <button
        onClick={onLeagueClick}
        disabled={!country}
        className={`p-1.5 rounded-md transition-all ${
          league
            ? "bg-gray-100 text-gray-700"
            : country
            ? "text-gray-400 hover:bg-gray-50 hover:text-gray-600"
            : "text-gray-300 cursor-not-allowed"
        }`}
        title={league ? league.league.name : "Ligue"}
        type="button"
      >
        {league && league.league.logo ? (
          <img
            src={league.league.logo}
            alt={league.league.name}
            className="w-4 h-4 object-contain"
            onError={(e) => {
              e.currentTarget.style.display = "none";
            }}
          />
        ) : (
          <span className="text-base leading-none">🏆</span>
        )}
      </button>

      {/* Match Button */}
      <button
        onClick={onMatchClick}
        disabled={!league}
        className={`p-1.5 rounded-md transition-all ${
          match
            ? "bg-gray-100 text-gray-700"
            : league
            ? "text-gray-400 hover:bg-gray-50 hover:text-gray-600"
            : "text-gray-300 cursor-not-allowed"
        }`}
        title={
          match
            ? `${match.teams.home.name} vs ${match.teams.away.name}`
            : "Match"
        }
        type="button"
      >
        {match ? (
          <div className="flex items-center gap-0.5">
            <img
              src={match.teams.home.logo}
              alt={match.teams.home.name}
              className="w-3.5 h-3.5 object-contain"
              onError={(e) => {
                e.currentTarget.style.display = "none";
              }}
            />
            <span className="text-[9px] text-gray-400">vs</span>
            <img
              src={match.teams.away.logo}
              alt={match.teams.away.name}
              className="w-3.5 h-3.5 object-contain"
              onError={(e) => {
                e.currentTarget.style.display = "none";
              }}
            />
          </div>
        ) : (
          <span className="text-base leading-none">⚽</span>
        )}
      </button>
    </div>
  );
}
