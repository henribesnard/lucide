"use client";

import { useState, useEffect } from "react";
import {
  MagnifyingGlassIcon,
  MapPinIcon,
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
    code: string;
    flag: string;
  };
}

interface Match {
  fixture: {
    id: number;
    date: string;
    timestamp: number;
    status: {
      long: string;
      short: string;
    };
  };
  league: {
    id: number;
    name: string;
    country: string;
    logo: string;
    flag: string;
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

interface MatchSelectorProps {
  onMatchSelect?: (match: Match) => void;
}

export default function MatchSelector({ onMatchSelect }: MatchSelectorProps) {
  const [step, setStep] = useState<"country" | "league" | "match">("country");
  const [selectedCountry, setSelectedCountry] = useState<Country | null>(null);
  const [selectedLeague, setSelectedLeague] = useState<League | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );

  const [countries, setCountries] = useState<Country[]>([]);
  const [leagues, setLeagues] = useState<League[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Fetch countries on mount
  useEffect(() => {
    fetchCountries();
  }, []);

  // Fetch leagues when country selected
  useEffect(() => {
    if (selectedCountry) {
      fetchLeagues(selectedCountry.name);
    }
  }, [selectedCountry]);

  // Fetch matches when league selected
  useEffect(() => {
    if (selectedLeague) {
      fetchMatches(selectedLeague.league.id, selectedDate);
    }
  }, [selectedLeague, selectedDate]);

  const fetchCountries = async () => {
    try {
      setLoading(true);
      const response = await fetch("http://localhost:8000/api/countries");
      const data = await response.json();
      setCountries(data.countries || []);
    } catch (error) {
      console.error("Error fetching countries:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLeagues = async (countryName: string) => {
    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:8000/api/leagues?country=${encodeURIComponent(countryName)}`
      );
      const data = await response.json();
      setLeagues(data.leagues || []);
    } catch (error) {
      console.error("Error fetching leagues:", error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMatches = async (leagueId: number, date: string) => {
    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:8000/api/fixtures?league_id=${leagueId}&date=${date}`
      );
      const data = await response.json();
      setMatches(data.fixtures || []);
    } catch (error) {
      console.error("Error fetching matches:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCountrySelect = (country: Country) => {
    setSelectedCountry(country);
    setSearchQuery("");
    setStep("league");
  };

  const handleLeagueSelect = (league: League) => {
    setSelectedLeague(league);
    setSearchQuery("");
    setStep("match");
  };

  const handleMatchSelect = (match: Match) => {
    if (onMatchSelect) {
      onMatchSelect(match);
    }
  };

  const filteredCountries = countries.filter((c) =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredLeagues = leagues.filter((l) =>
    l.league.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredMatches = matches.filter(
    (m) =>
      m.teams.home.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.teams.away.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Selection Header - Horizontal Pills */}
      <div className="mb-6 flex items-center gap-2 flex-wrap">
        <button
          onClick={() => {
            setStep("country");
            setSelectedCountry(null);
            setSelectedLeague(null);
          }}
          className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
            step === "country"
              ? "bg-teal-600 text-white"
              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          <MapPinIcon className="w-4 h-4 inline mr-1" />
          {selectedCountry ? selectedCountry.name : "Pays"}
        </button>

        {selectedCountry && (
          <>
            <span className="text-gray-400">/</span>
            <button
              onClick={() => {
                setStep("league");
                setSelectedLeague(null);
              }}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                step === "league"
                  ? "bg-teal-600 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              {selectedLeague ? selectedLeague.league.name : "Ligue"}
            </button>
          </>
        )}

        {selectedLeague && (
          <>
            <span className="text-gray-400">/</span>
            <button
              className="px-4 py-2 rounded-full text-sm font-medium bg-teal-600 text-white"
            >
              Matchs
            </button>
          </>
        )}

        {/* Date Picker */}
        {step === "match" && (
          <input
            type="date"
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
            className="ml-auto px-3 py-2 border border-gray-300 rounded-full text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
        )}
      </div>

      {/* Search Bar */}
      <div className="mb-4 relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder={
            step === "country"
              ? "Rechercher un pays..."
              : step === "league"
              ? "Rechercher une ligue..."
              : "Rechercher un match..."
          }
          className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
      </div>

      {/* Content */}
      <div className="bg-white rounded-xl border border-gray-200 p-4 max-h-[400px] overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="flex gap-2">
              <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce" style={{ animationDelay: "0.1s" }}></div>
              <div className="w-2 h-2 bg-teal-500 rounded-full animate-bounce" style={{ animationDelay: "0.2s" }}></div>
            </div>
          </div>
        ) : (
          <>
            {/* Country Selection - Simple Grid */}
            {step === "country" && (
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
                {filteredCountries.map((country, index) => (
                  <button
                    key={`${country.code}-${country.name}-${index}`}
                    onClick={() => handleCountrySelect(country)}
                    className="p-3 border border-gray-200 rounded-lg hover:border-teal-500 hover:bg-teal-50 transition-all text-center"
                  >
                    <div className="w-12 h-8 mx-auto mb-2 flex items-center justify-center">
                      {country.flag ? (
                        <img
                          src={country.flag}
                          alt={country.name}
                          className="w-full h-full object-contain"
                        />
                      ) : (
                        <span className="text-2xl">🏴</span>
                      )}
                    </div>
                    <div className="text-sm font-medium text-gray-900">
                      {country.name}
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* League Selection - Simple List */}
            {step === "league" && (
              <div className="space-y-2">
                {filteredLeagues.map((league) => (
                  <button
                    key={league.league.id}
                    onClick={() => handleLeagueSelect(league)}
                    className="w-full p-3 border border-gray-200 rounded-lg hover:border-teal-500 hover:bg-teal-50 transition-all flex items-center gap-3"
                  >
                    <div className="w-8 h-6 flex items-center justify-center flex-shrink-0">
                      {league.country.flag ? (
                        <img
                          src={league.country.flag}
                          alt={league.country.name}
                          className="w-full h-full object-contain"
                        />
                      ) : (
                        <span className="text-lg">🏴</span>
                      )}
                    </div>
                    <div className="flex-1 text-left">
                      <div className="font-medium text-gray-900">
                        {league.league.name}
                      </div>
                      <div className="text-xs text-gray-500">
                        {league.country.name}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            )}

            {/* Match Selection */}
            {step === "match" && (
              <div className="space-y-2">
                {filteredMatches.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <p>Aucun match prévu pour cette date</p>
                  </div>
                ) : (
                  filteredMatches.map((match) => (
                    <button
                      key={match.fixture.id}
                      onClick={() => handleMatchSelect(match)}
                      className="w-full p-4 border border-gray-200 rounded-lg hover:border-teal-500 hover:bg-teal-50 transition-all"
                    >
                      <div className="flex items-center justify-between">
                        {/* Home Team */}
                        <div className="flex items-center gap-2 flex-1">
                          <span className="font-semibold text-gray-900">
                            {match.teams.home.name}
                          </span>
                        </div>

                        {/* Time or Score */}
                        <div className="px-4 text-center">
                          {match.goals.home !== null ? (
                            <div className="text-lg font-bold text-teal-600">
                              {match.goals.home} - {match.goals.away}
                            </div>
                          ) : (
                            <div className="text-sm text-gray-500">
                              {new Date(match.fixture.date).toLocaleTimeString(
                                "fr-FR",
                                {
                                  hour: "2-digit",
                                  minute: "2-digit",
                                }
                              )}
                            </div>
                          )}
                        </div>

                        {/* Away Team */}
                        <div className="flex items-center gap-2 flex-1 justify-end">
                          <span className="font-semibold text-gray-900">
                            {match.teams.away.name}
                          </span>
                        </div>
                      </div>
                    </button>
                  ))
                )}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
