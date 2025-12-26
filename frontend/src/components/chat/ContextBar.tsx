import React from 'react';
import { ContextSelector } from './ContextSelector';
import { LeagueDropdown } from './dropdowns/LeagueDropdown';
import { MatchDropdown } from './dropdowns/MatchDropdown';
import { TeamDropdown } from './dropdowns/TeamDropdown';
import { PlayerDropdown } from './dropdowns/PlayerDropdown';
import { ModelDropdown } from './dropdowns/ModelDropdown';
import { TrophyIcon, MatchIcon, TeamIcon, PlayerIcon, ModelIcon } from './icons/ContextIcons';
import type { League, Match, Team, Player } from '@/types/context';

type ModelType = 'deepseek' | 'medium' | 'fast';

// Mapping des modèles pour l'affichage
const modelLabels: Record<ModelType, string> = {
    'deepseek': 'Slow',
    'medium': 'Medium',
    'fast': 'Fast'
};

interface ContextBarProps {
    league: League | null;
    match: Match | null;
    team: Team | null;
    player: Player | null;
    leagues: League[];
    favoriteLeagueIds: number[];
    loadingLeagues?: boolean;
    disabled?: boolean;
    modelType?: ModelType;
    onLeagueSelect: (league: League | null) => void;
    onMatchSelect: (match: Match | null) => void;
    onTeamSelect: (team: Team | null) => void;
    onPlayerSelect: (player: Player | null) => void;
    onModelTypeChange?: (modelType: ModelType) => void;
}

export const ContextBar: React.FC<ContextBarProps> = ({
    league,
    match,
    team,
    player,
    leagues,
    favoriteLeagueIds,
    loadingLeagues,
    disabled,
    modelType = 'slow',
    onLeagueSelect,
    onMatchSelect,
    onTeamSelect,
    onPlayerSelect,
    onModelTypeChange,
}) => {
    const handleLeagueClear = () => {
        onLeagueSelect(null);
        onMatchSelect(null);
        onTeamSelect(null);
        onPlayerSelect(null);
    };

    const handleMatchClear = () => {
        onMatchSelect(null);
        onPlayerSelect(null);
    };

    const handleTeamClear = () => {
        onTeamSelect(null);
        onPlayerSelect(null);
    };

    const handlePlayerClear = () => {
        onPlayerSelect(null);
    };

    // V4 Visibility Rules
    const showMatchDropdown = (league !== null) && (team === null);
    const showTeamDropdown = (league !== null) && (match === null);
    const showPlayerDropdown = (match !== null) || (team !== null);

    return (
        <div className="px-3 py-3 bg-white flex items-center gap-1.5 rounded-b-2xl flex-wrap">
            <ContextSelector<League>
                type="league"
                icon={<TrophyIcon className="w-5 h-5 text-slate-600" />}
                selected={league}
                onClear={handleLeagueClear}
                colorScheme="amber"
                dashed={!league}
                disabled={disabled}
                renderSelected={(l) => (
                    <img
                        src={l.logo}
                        alt={l.name}
                        className="w-6 h-6 object-contain drop-shadow-sm"
                    />
                )}
            >
                {(close) => (
                    <LeagueDropdown
                        leagues={leagues}
                        favoriteIds={favoriteLeagueIds}
                        loading={loadingLeagues}
                        onSelect={(l) => {
                            onLeagueSelect(l);
                            close();
                        }}
                    />
                )}
            </ContextSelector>

            {showMatchDropdown && (
                <ContextSelector<Match>
                    type="match"
                    icon={<MatchIcon />}
                    selected={match}
                    onClear={handleMatchClear}
                    colorScheme="rose"
                    dashed={!match}
                    disabled={disabled}
                    renderSelected={(m) => (
                        <div className="flex items-center gap-2">
                            <img
                                src={m.teams.home.logo}
                                alt=""
                                className="w-5 h-5 object-contain drop-shadow-sm"
                            />
                            <div className="w-1 h-1 rounded-full bg-slate-300"></div>
                            <img
                                src={m.teams.away.logo}
                                alt=""
                                className="w-5 h-5 object-contain drop-shadow-sm"
                            />
                        </div>
                    )}
                >
                    {(close) => (
                        <MatchDropdown
                            leagueId={league!.id}
                            onSelect={(m) => {
                                onMatchSelect(m);
                                close();
                            }}
                        />
                    )}
                </ContextSelector>
            )}

            {showTeamDropdown && (
                <ContextSelector<Team>
                    type="team"
                    icon={<TeamIcon className="w-5 h-5 text-slate-600" />}
                    selected={team}
                    onClear={handleTeamClear}
                    colorScheme="teal"
                    dashed={!team}
                    disabled={disabled}
                    renderSelected={(t) => (
                        <img
                            src={t.logo}
                            alt={t.name}
                            className="w-6 h-6 object-contain drop-shadow-sm"
                        />
                    )}
                >
                    {(close) => (
                        <TeamDropdown
                            leagueId={league?.id}
                            season={league?.season}
                            onSelect={(t) => {
                                onTeamSelect(t);
                                close();
                            }}
                        />
                    )}
                </ContextSelector>
            )}

            {showPlayerDropdown && (
                <ContextSelector<Player>
                    type="player"
                    icon={<PlayerIcon className="w-5 h-5 text-slate-600" />}
                    selected={player}
                    onClear={handlePlayerClear}
                    colorScheme="purple"
                    dashed={!player}
                    disabled={disabled}
                    renderSelected={(p) => (
                        <img
                            src={p.photo}
                            alt={p.name}
                            className="w-6 h-6 object-cover rounded-full"
                        />
                    )}
                >
                    {(close) => (
                        <PlayerDropdown
                            matchId={match?.id}
                            teamId={team?.id}
                            leagueId={league?.id}
                            onSelect={(p) => {
                                onPlayerSelect(p);
                                close();
                            }}
                        />
                    )}
                </ContextSelector>
            )}

            {onModelTypeChange && (
                <div className="ml-auto">
                    <ContextSelector<ModelType>
                        type="model"
                        icon={<ModelIcon className="w-5 h-5 text-slate-600" />}
                        selected={modelType}
                        onClear={() => {}} // Pas de clear pour le modèle, toujours une sélection
                        colorScheme="slate"
                        dashed={false}
                        disabled={disabled}
                        renderSelected={(m) => (
                            <span className="text-xs font-medium text-slate-700">
                                {modelLabels[m]}
                            </span>
                        )}
                    >
                        {(close) => (
                            <ModelDropdown
                                onSelect={(m) => {
                                    onModelTypeChange(m);
                                    close();
                                }}
                            />
                        )}
                    </ContextSelector>
                </div>
            )}
        </div>
    );
};
