import React, { useEffect, useState } from 'react';

interface MatchContext {
  context_id: string;
  context_type: 'match';
  status: 'live' | 'finished' | 'upcoming';
  fixture_id: number;
  match_date: string;
  home_team: string;
  away_team: string;
  league: string;
  updated_at: string;
}

interface LeagueContext {
  context_id: string;
  context_type: 'league';
  status: 'past' | 'current' | 'upcoming';
  league_id: number;
  league_name: string;
  country: string;
  season: number;
  updated_at: string;
}

type Context = MatchContext | LeagueContext;

interface ContextHeaderProps {
  fixtureId?: number;
  leagueId?: number;
  season?: number;
}

export default function ContextHeader({ fixtureId, leagueId, season }: ContextHeaderProps) {
  const [context, setContext] = useState<Context | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchContext = async () => {
      if (!fixtureId && !leagueId) {
        setContext(null);
        return;
      }

      setLoading(true);
      setError(null);

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';
        let url = '';

        if (fixtureId) {
          url = `${apiUrl}/api/context/match/${fixtureId}`;
        } else if (leagueId) {
          url = `${apiUrl}/api/context/league/${leagueId}${season ? `?season=${season}` : ''}`;
        }

        const response = await fetch(url);
        if (!response.ok) {
          throw new Error('Failed to fetch context');
        }

        const data = await response.json();
        setContext(data.context);
      } catch (err) {
        console.error('Error fetching context:', err);
        setError('Failed to load context');
      } finally {
        setLoading(false);
      }
    };

    fetchContext();

    // Auto-refresh for live matches every 30 seconds
    let interval: NodeJS.Timeout | null = null;
    if (fixtureId && context && context.context_type === 'match' && context.status === 'live') {
      interval = setInterval(fetchContext, 30000);
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [fixtureId, leagueId, season, context]);

  if (loading && !context) {
    return (
      <div className="w-full bg-gradient-to-r from-teal-50 to-teal-100 border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="animate-pulse flex items-center space-x-4">
            <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-full bg-red-50 border-b border-red-200">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!context) {
    return null;
  }

  const getStatusBadge = (status: string, isLive: boolean = false) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";

    if (isLive && status === 'live') {
      return (
        <span className={`${baseClasses} bg-red-100 text-red-800`}>
          <span className="w-2 h-2 bg-red-500 rounded-full mr-1.5 animate-pulse"></span>
          EN DIRECT
        </span>
      );
    }

    if (status === 'finished') {
      return <span className={`${baseClasses} bg-gray-100 text-gray-800`}>TERMINÉ</span>;
    }

    if (status === 'upcoming') {
      return <span className={`${baseClasses} bg-teal-50 text-teal-700`}>À VENIR</span>;
    }

    if (status === 'current') {
      return <span className={`${baseClasses} bg-teal-100 text-teal-800`}>EN COURS</span>;
    }

    if (status === 'past') {
      return <span className={`${baseClasses} bg-gray-100 text-gray-800`}>PASSÉ</span>;
    }

    return <span className={`${baseClasses} bg-gray-100 text-gray-800`}>{status.toUpperCase()}</span>;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="w-full bg-gradient-to-r from-teal-50 to-teal-100 border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 py-3">
        {context.context_type === 'match' ? (
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <span className="text-sm font-semibold text-gray-900">
                  {context.home_team}
                </span>
                <span className="text-sm text-gray-500">vs</span>
                <span className="text-sm font-semibold text-gray-900">
                  {context.away_team}
                </span>
              </div>
              {getStatusBadge(context.status, true)}
            </div>
            <div className="flex items-center space-x-3 text-sm text-gray-600">
              <span>{context.league}</span>
              <span className="text-gray-400">•</span>
              <span>{formatDate(context.match_date)}</span>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center space-x-3">
              <span className="text-sm font-semibold text-gray-900">
                {context.league_name}
              </span>
              {getStatusBadge(context.status)}
            </div>
            <div className="flex items-center space-x-3 text-sm text-gray-600">
              <span>{context.country}</span>
              <span className="text-gray-400">•</span>
              <span>Saison {context.season}/{context.season + 1}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
