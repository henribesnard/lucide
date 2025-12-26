"use client";

import { useRef } from "react";
import {
  MapPinIcon,
  ChevronDownIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

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
    flag: string;
  };
}

interface Match {
  fixture: {
    id: number;
    date: string;
    status: {
      short: string;
      long: string;
    };
  };
  teams: {
    home: {
      name: string;
      logo: string;
    };
    away: {
      name: string;
      logo: string;
    };
  };
  goals: {
    home: number | null;
    away: number | null;
  };
}

interface FiltersBarProps {
  // Country
  selectedCountry: Country | null;
  setSelectedCountry: (country: Country | null) => void;
  showCountryDropdown: boolean;
  setShowCountryDropdown: (show: boolean) => void;
  countrySearch: string;
  setCountrySearch: (search: string) => void;
  filteredCountries: Country[];

  // League
  selectedLeague: League | null;
  setSelectedLeague: (league: League | null) => void;
  showLeagueDropdown: boolean;
  setShowLeagueDropdown: (show: boolean) => void;
  leagueSearch: string;
  setLeagueSearch: (search: string) => void;
  filteredLeagues: League[];

  // Match
  selectedMatch: Match | null;
  setSelectedMatch: (match: Match | null) => void;
  showMatchDropdown: boolean;
  setShowMatchDropdown: (show: boolean) => void;
  matchSearch: string;
  setMatchSearch: (search: string) => void;
  selectedDate: string;
  setSelectedDate: (date: string) => void;
  selectedStatus: string;
  setSelectedStatus: (status: string) => void;
  filteredMatches: Match[];

  // Refs
  countryDropdownRef: React.RefObject<HTMLDivElement>;
  leagueDropdownRef: React.RefObject<HTMLDivElement>;
  matchDropdownRef: React.RefObject<HTMLDivElement>;

  // Helper functions
  isLiveMatch: (status: string) => boolean;
  getMatchTime: (fixtureId: number, status: any) => string;
}

export default function FiltersBar({
  selectedCountry,
  setSelectedCountry,
  showCountryDropdown,
  setShowCountryDropdown,
  countrySearch,
  setCountrySearch,
  filteredCountries,
  selectedLeague,
  setSelectedLeague,
  showLeagueDropdown,
  setShowLeagueDropdown,
  leagueSearch,
  setLeagueSearch,
  filteredLeagues,
  selectedMatch,
  setSelectedMatch,
  showMatchDropdown,
  setShowMatchDropdown,
  matchSearch,
  setMatchSearch,
  selectedDate,
  setSelectedDate,
  selectedStatus,
  setSelectedStatus,
  filteredMatches,
  countryDropdownRef,
  leagueDropdownRef,
  matchDropdownRef,
  isLiveMatch,
  getMatchTime,
}: FiltersBarProps) {
  return (
    <div className="mb-4">
      {/* Filters Buttons */}
      <div className="flex flex-wrap gap-2 justify-center mb-3">
        {/* Country Selector */}
        <div className="relative" ref={countryDropdownRef}>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setShowCountryDropdown(!showCountryDropdown);
            }}
            className="px-3 py-2.5 bg-white border-2 border-gray-300 hover:border-teal-500 rounded-xl transition-all flex items-center gap-2 shadow-sm hover:shadow-md"
            title={selectedCountry ? selectedCountry.name : "Sélectionner un pays"}
          >
            {selectedCountry ? (
              selectedCountry.name.toLowerCase() === 'world' ? (
                <svg className="w-5 h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM4.332 8.027a6.012 6.012 0 011.912-2.706C6.512 5.73 6.974 6 7.5 6A1.5 1.5 0 019 7.5V8a2 2 0 004 0 2 2 0 011.523-1.943A5.977 5.977 0 0116 10c0 .34-.028.675-.083 1H15a2 2 0 00-2 2v2.197A5.973 5.973 0 0110 16v-2a2 2 0 00-2-2 2 2 0 01-2-2 2 2 0 00-1.668-1.973z" clipRule="evenodd" />
                </svg>
              ) : (
                <img
                  src={selectedCountry.flag}
                  alt={selectedCountry.name}
                  className="w-5 h-3 object-contain flex-shrink-0"
                />
              )
            ) : (
              <MapPinIcon className="w-5 h-5 flex-shrink-0 text-gray-500" />
            )}
            <span className="text-sm font-medium text-gray-700">
              {selectedCountry ? selectedCountry.name : "Pays"}
            </span>
            <ChevronDownIcon className="w-4 h-4 flex-shrink-0 text-gray-500" />
          </button>

          {/* Country Dropdown */}
          {showCountryDropdown && (
            <div className="absolute top-full mt-2 left-0 w-72 bg-white border border-gray-200 rounded-lg shadow-xl z-[150] overflow-hidden">
              <div className="p-2 border-b">
                <input
                  type="text"
                  value={countrySearch}
                  onChange={(e) => setCountrySearch(e.target.value)}
                  placeholder="Rechercher un pays..."
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                  onMouseDown={(e) => e.stopPropagation()}
                />
              </div>
              <div className="overflow-y-auto scrollbar-thin" style={{ maxHeight: "200px" }}>
                {filteredCountries.map((country, index) => (
                  <button
                    key={`${country.code}-${index}`}
                    onClick={() => {
                      setSelectedCountry(country);
                      setSelectedLeague(null);
                      setSelectedMatch(null);
                      setShowCountryDropdown(false);
                      setCountrySearch("");
                    }}
                    className="w-full px-4 py-2 text-left hover:bg-teal-50 flex items-center gap-3 transition-colors"
                  >
                    {country.name.toLowerCase() === 'world' ? (
                      <svg className="w-6 h-6 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM4.332 8.027a6.012 6.012 0 011.912-2.706C6.512 5.73 6.974 6 7.5 6A1.5 1.5 0 019 7.5V8a2 2 0 004 0 2 2 0 011.523-1.943A5.977 5.977 0 0116 10c0 .34-.028.675-.083 1H15a2 2 0 00-2 2v2.197A5.973 5.973 0 0110 16v-2a2 2 0 00-2-2 2 2 0 01-2-2 2 2 0 00-1.668-1.973z" clipRule="evenodd" />
                      </svg>
                    ) : country.flag ? (
                      <img src={country.flag} alt={country.name} className="w-6 h-4 object-contain" />
                    ) : (
                      <div className="w-6 h-4 bg-gray-200 rounded" />
                    )}
                    <span className="text-sm">{country.name}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* League Selector */}
        {selectedCountry && (
          <div className="relative" ref={leagueDropdownRef}>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setShowLeagueDropdown(!showLeagueDropdown);
              }}
              className="px-3 py-2.5 bg-white border-2 border-gray-300 hover:border-teal-500 rounded-xl transition-all flex items-center gap-2 shadow-sm hover:shadow-md max-w-xs"
              title={selectedLeague ? selectedLeague.league.name : "Sélectionner une ligue"}
            >
              {selectedLeague ? (
                <>
                  <img
                    src={selectedLeague.league.logo || ''}
                    alt={selectedLeague.league.name}
                    className="w-5 h-5 object-contain flex-shrink-0"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                  <span className="text-sm font-medium text-gray-700 truncate">
                    {selectedLeague.league.name}
                  </span>
                </>
              ) : (
                <>
                  <span className="text-xl">🏆</span>
                  <span className="text-sm font-medium text-gray-700">Ligue</span>
                </>
              )}
              <ChevronDownIcon className="w-4 h-4 flex-shrink-0 text-gray-500" />
            </button>

            {/* League Dropdown */}
            {showLeagueDropdown && (
              <div className="absolute top-full mt-2 left-0 w-80 bg-white border border-gray-200 rounded-lg shadow-xl z-[200] overflow-hidden">
                <div className="p-2 border-b">
                  <input
                    type="text"
                    value={leagueSearch}
                    onChange={(e) => setLeagueSearch(e.target.value)}
                    placeholder="Rechercher une ligue..."
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    onMouseDown={(e) => e.stopPropagation()}
                  />
                </div>
                <div className="overflow-y-auto scrollbar-thin" style={{ maxHeight: "200px" }}>
                  {filteredLeagues.map((league) => (
                    <button
                      key={league.league.id}
                      onClick={() => {
                        setSelectedLeague(league);
                        setSelectedMatch(null);
                        setShowLeagueDropdown(false);
                        setLeagueSearch("");
                      }}
                      className="w-full px-4 py-2 text-left hover:bg-teal-50 transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <img
                          src={league.league.logo || ''}
                          alt={league.league.name}
                          className="w-6 h-6 object-contain"
                          onError={(e) => {
                            e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="24" height="24"%3E%3Crect width="24" height="24" fill="%23e5e7eb" rx="4"/%3E%3C/svg%3E';
                          }}
                        />
                        <div className="flex flex-col">
                          <div className="font-medium text-sm flex items-center gap-2">
                            {league.country.flag && (
                              <img
                                src={league.country.flag}
                                alt={league.country.name}
                                className="w-4 h-3 object-contain"
                                onError={(e) => {
                                  e.currentTarget.style.display = 'none';
                                }}
                              />
                            )}
                            <span>{league.league.name}</span>
                          </div>
                          <div className="text-xs text-gray-500">{league.country.name}</div>
                        </div>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* Match Selector */}
        {selectedLeague && (
          <div className="relative" ref={matchDropdownRef}>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setShowMatchDropdown(!showMatchDropdown);
              }}
              className="px-3 py-2.5 bg-white border-2 border-gray-300 hover:border-teal-500 rounded-xl transition-all flex items-center gap-2 shadow-sm hover:shadow-md max-w-xs"
              title={selectedMatch ? `${selectedMatch.teams.home.name} vs ${selectedMatch.teams.away.name}` : "Sélectionner un match"}
            >
              {selectedMatch ? (
                <div className="flex items-center gap-2">
                  <img
                    src={selectedMatch.teams.home.logo || ''}
                    alt={selectedMatch.teams.home.name}
                    className="w-5 h-5 object-contain"
                  />
                  <span className="text-xs font-semibold text-gray-500">vs</span>
                  <img
                    src={selectedMatch.teams.away.logo || ''}
                    alt={selectedMatch.teams.away.name}
                    className="w-5 h-5 object-contain"
                  />
                  <span className="text-sm font-medium text-gray-700 truncate max-w-[120px]">
                    {selectedMatch.teams.home.name}
                  </span>
                </div>
              ) : (
                <>
                  <span className="text-lg">⚽</span>
                  <span className="text-sm font-medium text-gray-700">Match</span>
                </>
              )}
              <ChevronDownIcon className="w-4 h-4 flex-shrink-0 text-gray-500" />
            </button>

            {/* Match Dropdown */}
            {showMatchDropdown && (
              <div className="absolute top-full mt-2 left-0 w-80 sm:w-96 bg-white border border-gray-200 rounded-lg shadow-xl z-[250] overflow-hidden" style={{ maxHeight: "310px" }}>
                <div className="p-2 border-b space-y-2">
                  <input
                    type="text"
                    value={matchSearch}
                    onChange={(e) => setMatchSearch(e.target.value)}
                    placeholder="Rechercher un match..."
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    onMouseDown={(e) => e.stopPropagation()}
                  />
                  <input
                    type="date"
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    onMouseDown={(e) => e.stopPropagation()}
                  />
                  {/* Status Filter */}
                  <div className="flex gap-1" onMouseDown={(e) => e.stopPropagation()}>
                    <button
                      onClick={() => setSelectedStatus("all")}
                      className={`flex-1 px-2 py-1 text-xs rounded ${
                        selectedStatus === "all"
                          ? "bg-teal-500 text-white"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      Tous
                    </button>
                    <button
                      onClick={() => setSelectedStatus("live")}
                      className={`flex-1 px-2 py-1 text-xs rounded ${
                        selectedStatus === "live"
                          ? "bg-red-500 text-white"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      Live
                    </button>
                    <button
                      onClick={() => setSelectedStatus("finished")}
                      className={`flex-1 px-2 py-1 text-xs rounded ${
                        selectedStatus === "finished"
                          ? "bg-gray-600 text-white"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      Terminé
                    </button>
                    <button
                      onClick={() => setSelectedStatus("upcoming")}
                      className={`flex-1 px-2 py-1 text-xs rounded ${
                        selectedStatus === "upcoming"
                          ? "bg-teal-500 text-white"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      À venir
                    </button>
                  </div>
                </div>
                <div className="overflow-y-auto scrollbar-thin" style={{ maxHeight: "190px" }} onMouseDown={(e) => e.stopPropagation()}>
                  {filteredMatches.length === 0 ? (
                    <div className="p-4 text-center text-sm text-gray-500">
                      Aucun match pour cette date
                    </div>
                  ) : (
                    filteredMatches.map((match) => {
                      const getStatusBadge = () => {
                        const status = match.fixture.status.short;
                        if (isLiveMatch(status)) {
                          return <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-semibold rounded animate-pulse">LIVE</span>;
                        } else if (status === "FT" || status === "AET" || status === "PEN") {
                          return <span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs font-semibold rounded">Terminé</span>;
                        } else {
                          return <span className="px-2 py-0.5 bg-teal-100 text-teal-700 text-xs font-semibold rounded">À venir</span>;
                        }
                      };

                      return (
                        <button
                          key={match.fixture.id}
                          onClick={() => {
                            setSelectedMatch(match);
                            setShowMatchDropdown(false);
                            setMatchSearch("");
                          }}
                          className="w-full px-4 py-3 text-left hover:bg-teal-50 transition-colors border-b border-gray-100 last:border-0"
                        >
                          <div className="flex items-center gap-2 sm:gap-3">
                            {/* Home Team */}
                            <div className="flex items-center gap-1.5 sm:gap-2 flex-1 min-w-0">
                              <img
                                src={match.teams.home.logo}
                                alt={match.teams.home.name}
                                className="w-5 h-5 sm:w-6 sm:h-6 object-contain flex-shrink-0"
                              />
                              <span className="font-medium text-xs sm:text-sm truncate">{match.teams.home.name}</span>
                            </div>

                            {/* Score or Time */}
                            <div className="flex flex-col items-center gap-1 px-2 flex-shrink-0">
                              {match.goals.home !== null ? (
                                <div className="flex flex-col items-center gap-0.5">
                                  <span className="text-base sm:text-lg font-bold text-teal-600">
                                    {match.goals.home} - {match.goals.away}
                                  </span>
                                  {isLiveMatch(match.fixture.status.short) && (
                                    <span className="text-xs font-semibold text-red-600">
                                      {getMatchTime(match.fixture.id, match.fixture.status)}
                                    </span>
                                  )}
                                </div>
                              ) : (
                                <span className="text-xs text-gray-500">
                                  {new Date(match.fixture.date).toLocaleTimeString("fr-FR", {
                                    hour: "2-digit",
                                    minute: "2-digit",
                                  })}
                                </span>
                              )}
                              {getStatusBadge()}
                            </div>

                            {/* Away Team */}
                            <div className="flex items-center gap-1.5 sm:gap-2 flex-1 justify-end min-w-0">
                              <span className="font-medium text-xs sm:text-sm truncate">{match.teams.away.name}</span>
                              <img
                                src={match.teams.away.logo}
                                alt={match.teams.away.name}
                                className="w-5 h-5 sm:w-6 sm:h-6 object-contain flex-shrink-0"
                              />
                            </div>
                          </div>
                        </button>
                      );
                    })
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Selected Filters Summary */}
      {(selectedCountry || selectedLeague || selectedMatch) && (
        <div className="flex flex-wrap gap-2 justify-center">
          {selectedCountry && (
            <div className="px-3 py-1.5 bg-teal-50 text-teal-700 rounded-full text-sm flex items-center gap-2 border border-teal-200">
              {selectedCountry.name.toLowerCase() === 'world' ? '🌍' : (
                <img src={selectedCountry.flag} alt="" className="w-4 h-2.5 object-contain" />
              )}
              <span className="font-medium">{selectedCountry.name}</span>
              <button
                onClick={() => {
                  setSelectedCountry(null);
                  setSelectedLeague(null);
                  setSelectedMatch(null);
                }}
                className="hover:bg-teal-100 rounded-full p-0.5 transition-colors"
                aria-label="Supprimer le filtre pays"
              >
                <XMarkIcon className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
          {selectedLeague && (
            <div className="px-3 py-1.5 bg-teal-50 text-teal-700 rounded-full text-sm flex items-center gap-2 border border-teal-200">
              <img src={selectedLeague.league.logo} alt="" className="w-4 h-4 object-contain" />
              <span className="font-medium">{selectedLeague.league.name}</span>
              <button
                onClick={() => {
                  setSelectedLeague(null);
                  setSelectedMatch(null);
                }}
                className="hover:bg-teal-100 rounded-full p-0.5 transition-colors"
                aria-label="Supprimer le filtre ligue"
              >
                <XMarkIcon className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
          {selectedMatch && (
            <div className="px-3 py-1.5 bg-teal-50 text-teal-700 rounded-full text-sm flex items-center gap-2 border border-teal-200 max-w-xs">
              <span className="font-medium truncate">{selectedMatch.teams.home.name} vs {selectedMatch.teams.away.name}</span>
              <button
                onClick={() => setSelectedMatch(null)}
                className="hover:bg-teal-100 rounded-full p-0.5 transition-colors flex-shrink-0"
                aria-label="Supprimer le filtre match"
              >
                <XMarkIcon className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
