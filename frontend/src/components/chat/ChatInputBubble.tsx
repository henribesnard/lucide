
import React, { useRef, useEffect } from 'react';
import { SendIcon } from './icons/ContextIcons';
import { ContextBar } from './ContextBar';
import type { League, Match, Team, Player } from '@/types/context';

type ModelType = 'deepseek' | 'medium' | 'fast';

interface ChatInputBubbleProps {
    value: string;
    onChange: (value: string) => void;
    onSubmit: () => void;
    isLoading?: boolean;

    // Context props passed down
    league: League | null;
    match: Match | null;
    team: Team | null;
    player: Player | null;
    onLeagueSelect: (league: League | null) => void;
    onMatchSelect: (match: Match | null) => void;
    onTeamSelect: (team: Team | null) => void;
    onPlayerSelect: (player: Player | null) => void;

    leagues: League[];
    favoriteLeagueIds: number[];
    loadingLeagues?: boolean;
    contextLocked?: boolean;

    modelType?: ModelType;
    onModelTypeChange?: (modelType: ModelType) => void;
}

export const ChatInputBubble: React.FC<ChatInputBubbleProps> = ({
    value,
    onChange,
    onSubmit,
    isLoading,
    contextLocked,
    ...contextProps
}) => {
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
        }
    }, [value]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            onSubmit();
        }
    };

    return (
        <div className="bg-white rounded-2xl shadow-lg border border-slate-200 hover:border-slate-300 transition-all duration-200">
            {/* Input Area */}
            <div className="relative px-2 pt-2">
                <textarea
                    ref={textareaRef}
                    value={value}
                    onChange={(e) => onChange(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Posez une question sur le football..."
                    className="w-full pl-3 pr-14 py-4 text-slate-800 placeholder-slate-400 resize-none focus:outline-none text-base leading-relaxed bg-transparent min-h-[60px] rounded-t-xl"
                    rows={1}
                    disabled={isLoading}
                />

                <button
                    onClick={onSubmit}
                    disabled={!value.trim() || isLoading}
                    className="absolute right-5 top-5 p-2 bg-teal-600 text-white rounded-xl hover:bg-teal-700 transition-all shadow-md shadow-teal-600/20 disabled:opacity-40 disabled:shadow-none disabled:cursor-not-allowed"
                >
                    <SendIcon />
                </button>
            </div>

            {/* Subtle Separator */}
            <div className="h-4"></div>

            {/* Context Bar */}
            <ContextBar
                {...contextProps}
                disabled={contextLocked}
            />
        </div>
    );
};
