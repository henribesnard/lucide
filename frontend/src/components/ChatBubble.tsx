"use client";

import { useState, useEffect, useRef } from "react";
import {
  PaperAirplaneIcon,
  MicrophoneIcon,
  MagnifyingGlassIcon,
  MapPinIcon,
  ChevronDownIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";
import ContextHeader from "./ContextHeader";

interface Message {
  id: string;
  type: "user" | "assistant";
  content: string;
  timestamp: Date;
}

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
  league: {
    id: number;
    name: string;
    country: string;
    logo: string;
    flag: string;
    season: number;
    round: string;
  };
}

interface ChatRequest {
  message: string;
  session_id?: string;
}

interface ChatResponse {
  response: string;
  session_id: string;
  intent: string;
  entities: Record<string, any>;
  tools: string[];
}

interface EnrichedChatRequest extends ChatRequest {
  context?: {
    match_id?: number;
    league_id?: number;
    home_team_id?: number;
    away_team_id?: number;
    match_date?: string;
  };
}

// Helper function to calculate current season
function getCurrentSeason(): number {
  const now = new Date();
  const month = now.getMonth(); // 0-11
  const year = now.getFullYear();
  // Season starts in August (month 7)
  return month >= 7 ? year : year - 1;
}

export default function ChatBubble() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [lastFetchAt, setLastFetchAt] = useState<number | null>(null);
  const [liveTick, setLiveTick] = useState<number>(0);
  const [liveElapsedMap, setLiveElapsedMap] = useState<Record<number, { base: number; ts: number }>>({});

  // Dropdown states
  const [showCountryDropdown, setShowCountryDropdown] = useState(false);
  const [showLeagueDropdown, setShowLeagueDropdown] = useState(false);
  const [showMatchDropdown, setShowMatchDropdown] = useState(false);
  const [showStatusDropdown, setShowStatusDropdown] = useState(false);

  // Data states
  const [countries, setCountries] = useState<Country[]>([]);
  const [leagues, setLeagues] = useState<League[]>([]);
  const [matches, setMatches] = useState<Match[]>([]);

  // Selected states
  const [selectedCountry, setSelectedCountry] = useState<Country | null>(null);
  const [selectedLeague, setSelectedLeague] = useState<League | null>(null);
  const [selectedMatch, setSelectedMatch] = useState<Match | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(
    new Date().toISOString().split("T")[0]
  );
  const [selectedStatus, setSelectedStatus] = useState<string>("all"); // all, live, finished, upcoming

  // Search states
  const [countrySearch, setCountrySearch] = useState("");
  const [leagueSearch, setLeagueSearch] = useState("");
  const [matchSearch, setMatchSearch] = useState("");

  const countryDropdownRef = useRef<HTMLDivElement>(null);
  const leagueDropdownRef = useRef<HTMLDivElement>(null);
  const matchDropdownRef = useRef<HTMLDivElement>(null);

  // Fetch countries on mount
  useEffect(() => {
    fetchCountries();
  }, []);

  // Fetch leagues when country changes
  useEffect(() => {
    if (selectedCountry) {
      fetchLeagues(selectedCountry.name);
    }
  }, [selectedCountry]);

  // Fetch matches when league or date changes
  useEffect(() => {
    if (selectedLeague) {
      fetchMatches(selectedLeague.league.id, selectedDate);
    }
  }, [selectedLeague, selectedDate]);

  // Close dropdowns when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;

      if (
        countryDropdownRef.current &&
        !countryDropdownRef.current.contains(target)
      ) {
        setShowCountryDropdown(false);
      }
      if (
        leagueDropdownRef.current &&
        !leagueDropdownRef.current.contains(target)
      ) {
        setShowLeagueDropdown(false);
      }
      if (
        matchDropdownRef.current &&
        !matchDropdownRef.current.contains(target)
      ) {
        setShowMatchDropdown(false);
      }
    };

    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, []);

  const fetchCountries = async () => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const response = await fetch(`${API_URL}/api/countries`);
      const data = await response.json();
      const list = data.countries || [];
      const hasWorld = list.some((c: Country) => c.name.toLowerCase() === "world");
      if (!hasWorld) {
        list.push({ name: "World", code: "WO", flag: "" });
      }
      setCountries(list);
    } catch (error) {
      console.error("Error fetching countries:", error);
    }
  };

  const fetchLeagues = async (countryName: string) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const response = await fetch(
        `${API_URL}/api/leagues?country=${encodeURIComponent(countryName)}`
      );
      const data = await response.json();
      setLeagues(data.leagues || []);
    } catch (error) {
      console.error("Error fetching leagues:", error);
    }
  };

  const fetchMatches = async (leagueId: number, date: string) => {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const response = await fetch(
        `${API_URL}/api/fixtures?league_id=${leagueId}&date=${date}`
      );
      const data = await response.json();
      const fixtures = data.fixtures || [];
      const now = Date.now();
      setMatches(fixtures);
      setLastFetchAt(now);

      setLiveElapsedMap((prev) => {
        const next: Record<number, { base: number; ts: number }> = {};
        for (const fx of fixtures) {
          if (!isLiveStatus(fx.fixture.status.short)) continue;
          const apiElapsed = fx.fixture.status.elapsed ?? 0;
          const prevEntry = prev[fx.fixture.id];
          const progressedPrev =
            prevEntry && prevEntry.ts
              ? prevEntry.base + Math.floor((now - prevEntry.ts) / 60000)
              : apiElapsed;
          const base = Math.max(apiElapsed, progressedPrev);
          next[fx.fixture.id] = { base, ts: now };
        }
        return next;
      });
    } catch (error) {
      console.error("Error fetching matches:", error);
    }
  };

  const isLiveStatus = (status: string): boolean => {
    return ["1H", "2H", "HT", "ET", "P", "LIVE"].includes(status);
  };

  const isLiveMatch = (status: string): boolean => {
    return isLiveStatus(status);
  };

  const isFinishedStatus = (status: string): boolean => {
    return ["FT", "AET", "PEN"].includes(status);
  };

  const isUpcomingStatus = (status: string): boolean => {
    return ["TBD", "NS"].includes(status);
  };

  const getMatchStatusCategory = (status: string): string => {
    if (isLiveStatus(status)) return "live";
    if (isFinishedStatus(status)) return "finished";
    if (isUpcomingStatus(status)) return "upcoming";
    return "upcoming"; // default
  };

  const getMatchTime = (fixtureId: number, status: { short: string; elapsed: number | null }): string => {
    if (status.short === "HT") return "Mi-temps";
    if (status.short === "P") return "Penaltys";
    if (isLiveStatus(status.short)) {
      const entry = liveElapsedMap[fixtureId];
      const base = entry ? entry.base : status.elapsed ?? 0;
      const ts = entry ? entry.ts : lastFetchAt;
      const delta = ts ? Math.floor((Date.now() - ts) / 60000) : 0;
      const total = Math.max(0, base + delta);
      return `${total}'`;
    }
    if (status.elapsed !== null) return `${status.elapsed}'`;
    return "LIVE";
  };

  // Refresh live matches periodically to keep elapsed time and scores up to date
  useEffect(() => {
    if (!selectedLeague) return;
    const hasLive = matches.some((m) => isLiveStatus(m.fixture.status.short));
    if (!hasLive) return;

    const intervalId = setInterval(() => {
      fetchMatches(selectedLeague.league.id, selectedDate);
    }, 30000); // 30s refresh

    return () => clearInterval(intervalId);
  }, [matches, selectedLeague, selectedDate]);

  // Local tick to refresh displayed elapsed time even before API refresh
  useEffect(() => {
    const hasLive = matches.some((m) => isLiveStatus(m.fixture.status.short));
    if (!hasLive) return;
    const tickId = setInterval(() => setLiveTick((t) => t + 1), 15000); // 15s
    return () => clearInterval(tickId);
  }, [matches]);

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const messageToSend = inputValue;
    setInputValue("");
    setIsLoading(true);

    try {
      let contextualMessage = messageToSend;

      if (selectedMatch) {
        const matchInfo = `Match: ${selectedMatch.teams.home.name} vs ${selectedMatch.teams.away.name} (${selectedMatch.league.name}, ${new Date(selectedMatch.fixture.date).toLocaleDateString("fr-FR")})`;
        contextualMessage = `${matchInfo}\n\nQuestion: ${messageToSend}`;
      }

      const requestBody: EnrichedChatRequest = {
        message: contextualMessage,
        session_id: sessionId || undefined,
      };

      if (selectedMatch) {
        requestBody.context = {
          match_id: selectedMatch.fixture.id,
          league_id: selectedMatch.league.id,
          home_team_id: selectedMatch.teams.home.id,
          away_team_id: selectedMatch.teams.away.id,
          match_date: selectedMatch.fixture.date,
        };
      }

      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ChatResponse = await response.json();

      if (!sessionId) {
        setSessionId(data.session_id);
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: data.response,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error("Error calling chat API:", error);

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: "assistant",
        content: "Desole, une erreur s'est produite. Veuillez reessayer.",
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const filteredCountries = countries.filter((c) =>
    c.name.toLowerCase().includes(countrySearch.toLowerCase())
  );

  const filteredLeagues = leagues.filter((l) =>
    l.league.name.toLowerCase().includes(leagueSearch.toLowerCase())
  );

  const filteredMatches = matches.filter((m) => {
    // Filter by search text
    const matchesSearch =
      m.teams.home.name.toLowerCase().includes(matchSearch.toLowerCase()) ||
      m.teams.away.name.toLowerCase().includes(matchSearch.toLowerCase());

    // Filter by status
    const matchStatus = getMatchStatusCategory(m.fixture.status.short);
    const matchesStatus = selectedStatus === "all" || matchStatus === selectedStatus;

    return matchesSearch && matchesStatus;
  });

  const showWelcome = messages.length === 0;

  return (
    <div className="flex flex-col min-h-screen bg-white">
      {showWelcome ? (
        /* Welcome Screen - Top aligned */
        <div className="flex-1 flex flex-col items-center px-6 py-12 pt-20">
          <div className="w-full max-w-4xl text-center">
            {/* Logo and Title */}
            <div className="mb-12">
              <div className="flex items-center justify-center gap-4 mb-3">
                <div className="w-14 h-14 bg-gradient-to-br from-teal-500 to-teal-600 rounded-xl flex items-center justify-center">
                  <span className="text-white font-bold text-2xl">L</span>
                </div>
                <h1 className="text-5xl font-bold text-gray-900">Lucide</h1>
              </div>
              <p className="text-gray-600 text-lg">
                Analyse de matchs et paris sportifs
              </p>
            </div>

            {/* Input Area with integrated dropdowns */}
            <div className="relative">
              <div className="relative bg-white border-2 border-gray-300 rounded-2xl shadow-sm focus-within:border-teal-500 focus-within:shadow-lg transition-all">
                {/* Left Icons - Tools with Dropdowns */}
                <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  {/* Country Selector */}
                  <div className="relative" ref={countryDropdownRef}>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowCountryDropdown(!showCountryDropdown);
                      }}
                      className="p-2 text-gray-700 hover:bg-teal-50 rounded-lg transition-colors flex items-center gap-1.5"
                      title={selectedCountry ? selectedCountry.name : "Pays"}
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
                        <MapPinIcon className="w-5 h-5 flex-shrink-0" />
                      )}
                      <ChevronDownIcon className="w-3.5 h-3.5 flex-shrink-0" />
                    </button>

                    {/* Country Dropdown */}
                    {showCountryDropdown && (
                      <div className="absolute left-0 top-full mt-2 w-72 bg-white border border-gray-200 rounded-lg shadow-xl z-[150] overflow-hidden" style={{ maxHeight: "260px" }}>
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
                        <div
                          className="overflow-y-auto scrollbar-thin"
                          style={{ maxHeight: "200px" }}
                          onMouseDown={(e) => e.stopPropagation()}
                        >
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
                                <img
                                  src={country.flag}
                                  alt={country.name}
                                  className="w-6 h-4 object-contain"
                                />
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
                        className="p-2 text-gray-700 hover:bg-teal-50 rounded-lg transition-colors flex items-center gap-1.5"
                        title={selectedLeague ? selectedLeague.league.name : "Ligue"}
                      >
                        {selectedLeague ? (
                          <img
                            src={selectedLeague.league.logo || ''}
                            alt={selectedLeague.league.name}
                            className="w-5 h-5 object-contain flex-shrink-0"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none';
                            }}
                          />
                        ) : (
                          <span>🏆</span>
                        )}
                        <ChevronDownIcon className="w-3.5 h-3.5 flex-shrink-0" />
                      </button>

                      {/* League Dropdown */}
                      {showLeagueDropdown && (
                        <div className="absolute left-0 top-full mt-2 w-80 bg-white border border-gray-200 rounded-lg shadow-xl z-[200] overflow-hidden" style={{ maxHeight: "260px" }}>
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
                          <div
                            className="overflow-y-auto scrollbar-thin"
                            style={{ maxHeight: "200px" }}
                            onMouseDown={(e) => e.stopPropagation()}
                          >
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
                        className="px-3 py-2 text-gray-700 hover:bg-teal-50 rounded-lg transition-colors flex items-center gap-2 text-sm font-medium"
                        title={selectedMatch ? `${selectedMatch.teams.home.name} vs ${selectedMatch.teams.away.name}` : "Match"}
                      >
                        {selectedMatch ? (
                          <div className="flex items-center gap-1.5 flex-shrink-0">
                            <img
                              src={selectedMatch.teams.home.logo || ''}
                              alt={selectedMatch.teams.home.name}
                              className="w-6 h-6 object-contain"
                              onError={(e) => {
                                e.currentTarget.style.display = 'none';
                              }}
                            />
                            <span className="text-xs font-semibold text-gray-500">vs</span>
                            <img
                              src={selectedMatch.teams.away.logo || ''}
                              alt={selectedMatch.teams.away.name}
                              className="w-6 h-6 object-contain"
                              onError={(e) => {
                                e.currentTarget.style.display = 'none';
                              }}
                            />
                          </div>
                        ) : (
                          <span>Match</span>
                        )}
                        <ChevronDownIcon className="w-4 h-4 flex-shrink-0" />
                      </button>

                      {/* Match Dropdown */}
                      {showMatchDropdown && (
                        <div className="absolute left-0 top-full mt-2 w-96 bg-white border border-gray-200 rounded-lg shadow-xl z-[250] overflow-hidden" style={{ maxHeight: "310px" }}>
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
                                🔴 Live
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
                                    ? "bg-blue-500 text-white"
                                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                                }`}
                              >
                                À venir
                              </button>
                            </div>
                          </div>
                          <div
                            className="overflow-y-auto scrollbar-thin"
                            style={{ maxHeight: "190px" }}
                            onMouseDown={(e) => e.stopPropagation()}
                          >
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
                                    return <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-semibold rounded">À venir</span>;
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
                                    <div className="flex items-center gap-3">
                                      {/* Home Team */}
                                      <div className="flex items-center gap-2 flex-1">
                                        <img
                                          src={match.teams.home.logo}
                                          alt={match.teams.home.name}
                                          className="w-6 h-6 object-contain"
                                        />
                                        <span className="font-medium text-sm truncate">{match.teams.home.name}</span>
                                      </div>

                                      {/* Score or Time */}
                                      <div className="flex flex-col items-center gap-1 px-3">
                                        {match.goals.home !== null ? (
                                          <div className="flex flex-col items-center gap-0.5">
                                            <span className="text-lg font-bold text-teal-600">
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
                                      <div className="flex items-center gap-2 flex-1 justify-end">
                                        <span className="font-medium text-sm truncate">{match.teams.away.name}</span>
                                        <img
                                          src={match.teams.away.logo}
                                          alt={match.teams.away.name}
                                          className="w-6 h-6 object-contain"
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

                {/* Text Input */}
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Posez votre question..."
                  rows={1}
                  className="w-full py-4 bg-transparent focus:outline-none resize-none text-gray-900 placeholder-gray-400 text-sm sm:text-base"
                  style={{
                    minHeight: "56px",
                    maxHeight: "200px",
                    paddingLeft: selectedMatch ? "220px" : selectedLeague ? "150px" : selectedCountry ? "105px" : "16px",
                    paddingRight: "100px"
                  }}
                />

                {/* Right Icons - Actions */}
                <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
                  <button
                    type="button"
                    className="p-2 text-gray-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
                    title="Commande vocale"
                  >
                    <MicrophoneIcon className="w-5 h-5" />
                  </button>

                  <button
                    onClick={handleSend}
                    disabled={!inputValue.trim() || isLoading}
                    className="p-2.5 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
                    title="Envoyer"
                  >
                    <PaperAirplaneIcon className="w-5 h-5" />
                  </button>
                </div>
              </div>

            </div>
          </div>
        </div>
      ) : (
        /* Messages View */
        <div className="flex flex-col h-screen">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
            <div className="max-w-4xl mx-auto flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-gradient-to-br from-teal-500 to-teal-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold">L</span>
                </div>
                <div>
                  <h1 className="text-lg font-semibold text-gray-900">Lucide</h1>
                  <p className="text-xs text-gray-500">
                    Analyse de matchs et paris sportifs
                  </p>
                </div>
              </div>

            </div>
          </div>

          {/* Context Header - Shows match or league context */}
          <ContextHeader
            fixtureId={selectedMatch?.fixture.id}
            leagueId={selectedLeague?.league.id}
            season={selectedLeague ? getCurrentSeason() : undefined}
          />

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto px-6 py-8 bg-gradient-to-b from-gray-50 to-white">
            <div className="max-w-4xl mx-auto space-y-6">
              {messages.map((message) => {
                if (message.type === "user") {
                  return (
                    <div key={message.id} className="flex justify-end animate-fade-in">
                      <div className="max-w-[80%] bg-teal-600 text-white rounded-2xl rounded-tr-sm px-4 py-3 shadow-md">
                        <p className="text-sm leading-relaxed">{message.content}</p>
                        <span className="text-xs opacity-70 mt-1 block">
                          {message.timestamp.toLocaleTimeString("fr-FR", {
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                    </div>
                  );
                }

                if (message.type === "assistant") {
                  return (
                    <div key={message.id} className="flex justify-start animate-fade-in">
                      <div className="max-w-[80%]">
                        <div className="flex items-start gap-3">
                          <div className="w-8 h-8 bg-gradient-to-br from-teal-500 to-teal-600 rounded-lg flex items-center justify-center flex-shrink-0">
                            <span className="text-white font-bold text-sm">L</span>
                          </div>
                          <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                            <p className="text-sm leading-relaxed text-gray-800">
                              {message.content}
                            </p>
                            <span className="text-xs text-gray-500 mt-1 block">
                              {message.timestamp.toLocaleTimeString("fr-FR", {
                                hour: "2-digit",
                                minute: "2-digit",
                              })}
                            </span>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                }

                return null;
              })}

              {isLoading && (
                <div className="flex justify-start animate-fade-in">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-teal-500 to-teal-600 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-sm animate-pulse">L</span>
                    </div>
                    <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3">
                      <div className="flex gap-2">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "0.1s" }}
                        ></div>
                        <div
                          className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                          style={{ animationDelay: "0.2s" }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Input Area - Same as welcome screen */}
          <div className="px-3 sm:px-6 py-4 sm:py-6 border-t border-gray-200 bg-white/80 backdrop-blur-sm sticky bottom-0">
            <div className="max-w-4xl mx-auto">
              <div className="relative bg-white border-2 border-gray-300 rounded-2xl shadow-sm focus-within:border-teal-500 focus-within:shadow-md transition-all">
                {/* Left Icons - Tools with Dropdowns */}
                <div className="absolute left-2 sm:left-3 top-1/2 -translate-y-1/2 flex items-center gap-0.5 sm:gap-1">
                  {/* Country Selector */}
                  <div className="relative" ref={countryDropdownRef}>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setShowCountryDropdown(!showCountryDropdown);
                      }}
                      className="p-1.5 sm:p-2 text-gray-700 hover:bg-teal-50 rounded-lg transition-colors flex items-center gap-1 sm:gap-1.5"
                      title={selectedCountry ? selectedCountry.name : "Pays"}
                    >
                      {selectedCountry ? (
                        selectedCountry.name.toLowerCase() === 'world' ? (
                          <svg className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM4.332 8.027a6.012 6.012 0 011.912-2.706C6.512 5.73 6.974 6 7.5 6A1.5 1.5 0 019 7.5V8a2 2 0 004 0 2 2 0 011.523-1.943A5.977 5.977 0 0116 10c0 .34-.028.675-.083 1H15a2 2 0 00-2 2v2.197A5.973 5.973 0 0110 16v-2a2 2 0 00-2-2 2 2 0 01-2-2 2 2 0 00-1.668-1.973z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          <img
                            src={selectedCountry.flag}
                            alt={selectedCountry.name}
                            className="w-4 h-2.5 sm:w-5 sm:h-3 object-contain flex-shrink-0"
                          />
                        )
                      ) : (
                        <MapPinIcon className="w-4 h-4 sm:w-5 sm:h-5 flex-shrink-0" />
                      )}
                      <ChevronDownIcon className="w-3 h-3 sm:w-3.5 sm:h-3.5 flex-shrink-0" />
                    </button>

                    {/* Country Dropdown - Same as welcome screen */}
                    {showCountryDropdown && (
                      <div className="absolute left-0 bottom-full mb-2 w-72 bg-white border border-gray-200 rounded-lg shadow-xl z-[150] overflow-hidden" style={{ maxHeight: "260px" }}>
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
                        <div
                          className="overflow-y-auto scrollbar-thin"
                          style={{ maxHeight: "200px" }}
                          onMouseDown={(e) => e.stopPropagation()}
                        >
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
                                <img
                                  src={country.flag}
                                  alt={country.name}
                                  className="w-6 h-4 object-contain"
                                />
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
                        className="p-1.5 sm:p-2 text-gray-700 hover:bg-teal-50 rounded-lg transition-colors flex items-center gap-1 sm:gap-1.5"
                        title={selectedLeague ? selectedLeague.league.name : "Ligue"}
                      >
                        {selectedLeague ? (
                          <img
                            src={selectedLeague.league.logo || ''}
                            alt={selectedLeague.league.name}
                            className="w-4 h-4 sm:w-5 sm:h-5 object-contain flex-shrink-0"
                            onError={(e) => {
                              e.currentTarget.style.display = 'none';
                            }}
                          />
                        ) : (
                          <span className="text-base sm:text-lg">🏆</span>
                        )}
                        <ChevronDownIcon className="w-3 h-3 sm:w-3.5 sm:h-3.5 flex-shrink-0" />
                      </button>

                      {/* League Dropdown - Same as welcome screen */}
                      {showLeagueDropdown && (
                        <div className="absolute left-0 bottom-full mb-2 w-80 bg-white border border-gray-200 rounded-lg shadow-xl z-[200] overflow-hidden" style={{ maxHeight: "260px" }}>
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
                          <div
                            className="overflow-y-auto scrollbar-thin"
                            style={{ maxHeight: "200px" }}
                            onMouseDown={(e) => e.stopPropagation()}
                          >
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
                        className="p-1.5 sm:p-2 text-gray-700 hover:bg-teal-50 rounded-lg transition-colors flex items-center gap-1 sm:gap-1.5"
                        title={selectedMatch ? `${selectedMatch.teams.home.name} vs ${selectedMatch.teams.away.name}` : "Match"}
                      >
                        {selectedMatch ? (
                          <div className="flex items-center gap-1 flex-shrink-0">
                            <img
                              src={selectedMatch.teams.home.logo || ''}
                              alt={selectedMatch.teams.home.name}
                              className="w-4 h-4 sm:w-5 sm:h-5 object-contain"
                              onError={(e) => {
                                e.currentTarget.style.display = 'none';
                              }}
                            />
                            <span className="text-xs font-semibold text-gray-500">vs</span>
                            <img
                              src={selectedMatch.teams.away.logo || ''}
                              alt={selectedMatch.teams.away.name}
                              className="w-4 h-4 sm:w-5 sm:h-5 object-contain"
                              onError={(e) => {
                                e.currentTarget.style.display = 'none';
                              }}
                            />
                          </div>
                        ) : (
                          <span className="text-sm">⚽</span>
                        )}
                        <ChevronDownIcon className="w-3 h-3 sm:w-3.5 sm:h-3.5 flex-shrink-0" />
                      </button>

                      {/* Match Dropdown - Same structure as welcome screen */}
                      {showMatchDropdown && (
                        <div className="absolute left-0 bottom-full mb-2 w-80 sm:w-96 bg-white border border-gray-200 rounded-lg shadow-xl z-[250] overflow-hidden" style={{ maxHeight: "310px" }}>
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
                                🔴 Live
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
                                    ? "bg-blue-500 text-white"
                                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                                }`}
                              >
                                À venir
                              </button>
                            </div>
                          </div>
                          <div
                            className="overflow-y-auto scrollbar-thin"
                            style={{ maxHeight: "190px" }}
                            onMouseDown={(e) => e.stopPropagation()}
                          >
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
                                    return <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-semibold rounded">À venir</span>;
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

                {/* Text Input */}
                <textarea
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Posez votre question..."
                  rows={1}
                  className="w-full py-3 sm:py-4 bg-transparent focus:outline-none resize-none text-gray-900 placeholder-gray-400 text-sm sm:text-base"
                  style={{
                    minHeight: "48px",
                    maxHeight: "200px",
                    paddingLeft: selectedMatch ? "210px" : selectedLeague ? "140px" : selectedCountry ? "100px" : "12px",
                    paddingRight: "90px"
                  }}
                />

                {/* Right Icons - Actions */}
                <div className="absolute right-2 sm:right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 sm:gap-2">
                  <button
                    type="button"
                    className="p-1.5 sm:p-2 text-gray-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors hidden sm:block"
                    title="Commande vocale"
                  >
                    <MicrophoneIcon className="w-4 h-4 sm:w-5 sm:h-5" />
                  </button>

                  <button
                    onClick={handleSend}
                    disabled={!inputValue.trim() || isLoading}
                    className="p-2 bg-teal-600 text-white rounded-lg hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
                    title="Envoyer"
                  >
                    <PaperAirplaneIcon className="w-4 h-4 sm:w-5 sm:h-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
