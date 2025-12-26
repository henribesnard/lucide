
import React, { useState, useRef, useEffect } from 'react';
import { CloseIcon } from './icons/ContextIcons';

type ColorScheme = 'teal' | 'amber' | 'rose' | 'blue' | 'purple' | 'slate';

interface ContextSelectorProps<T> {
    type: 'country' | 'league' | 'match' | 'team' | 'player' | 'model';
    icon: React.ReactNode;
    selected: T | null;
    onClear: () => void;
    colorScheme: ColorScheme;
    dashed?: boolean;
    disabled?: boolean;
    renderSelected: (item: T) => React.ReactNode;
    children: (close: () => void) => React.ReactNode;
    // Function as child to pass close handler to dropdown
}

const colorStyles: Record<ColorScheme, { selected: string; hover: string }> = {
    teal: {
        selected: 'bg-teal-50 border-teal-200 hover:bg-teal-100 text-teal-700',
        hover: 'hover:border-teal-400 hover:bg-teal-50 hover:text-teal-600',
    },
    amber: {
        selected: 'bg-amber-50 border-amber-200 hover:bg-amber-100 text-amber-700',
        hover: 'hover:border-amber-400 hover:bg-amber-50 hover:text-amber-600',
    },
    rose: {
        selected: 'bg-rose-50 border-rose-200 hover:bg-rose-100 text-rose-700',
        hover: 'hover:border-rose-400 hover:bg-rose-50 hover:text-rose-500',
    },
    blue: {
        selected: 'bg-teal-50 border-teal-200 hover:bg-teal-100 text-teal-700',
        hover: 'hover:border-teal-400 hover:bg-teal-50 hover:text-teal-600',
    },
    purple: {
        selected: 'bg-purple-50 border-purple-200 hover:bg-purple-100 text-purple-700',
        hover: 'hover:border-purple-400 hover:bg-purple-50 hover:text-purple-600',
    },
    slate: {
        selected: 'bg-slate-50 border-slate-200 hover:bg-slate-100 text-slate-700',
        hover: 'hover:border-slate-400 hover:bg-slate-50 hover:text-slate-600',
    },
};

export function ContextSelector<T>({
    icon,
    selected,
    onClear,
    colorScheme,
    dashed,
    disabled,
    renderSelected,
    children
}: ContextSelectorProps<T>) {
    const [isOpen, setIsOpen] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    // Close on click outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };

        if (isOpen) {
            document.addEventListener('mousedown', handleClickOutside);
            return () => document.removeEventListener('mousedown', handleClickOutside);
        }
    }, [isOpen]);

    // Base styles
    const baseClasses = `relative flex items-center justify-center transition-all duration-200 ease-out group ${
        disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"
    }`;
    const sizeClasses = "h-10";

    // Conditionally render selected vs unselected styles
    const buttonClasses = selected
        ? `${baseClasses} ${sizeClasses} px-2 rounded-lg bg-transparent hover:bg-slate-50/50 border border-transparent`
        : `${baseClasses} w-10 h-10 rounded-xl text-slate-400 bg-transparent hover:bg-slate-100/50 transition-colors`;

    return (
        <div ref={containerRef} className="relative">
            <button
                type="button"
                onClick={() => {
                    if (disabled) return;
                    if (!selected) setIsOpen(!isOpen);
                }}
                disabled={disabled}
                // If selected, click usually clears or does nothing? 
                // Spec says: "Clic sur Pays -> Dropdown s'ouvre". 
                // Spec also says for Selected state: "Logo + bouton clear au hover".
                // Let's assume clicking selected also opens dropdown to change selection, unless we hit the X.
                className={buttonClasses}
            >
                {selected ? (
                    <>
                        <div
                            className="flex items-center gap-2.5"
                            onClick={() => {
                                if (disabled) return;
                                setIsOpen(!isOpen);
                            }}
                        >
                            {renderSelected(selected)}
                        </div>
                        <div
                            className={`ml-1.5 p-1 rounded-full hover:bg-slate-200/60 transition-all duration-150 ${
                                disabled ? "opacity-0" : "opacity-0 group-hover:opacity-100"
                            }`}
                            onClick={(e) => {
                                e.stopPropagation();
                                if (disabled) return;
                                onClear();
                            }}
                        >
                            <CloseIcon />
                        </div>
                    </>
                ) : (
                    <div
                        onClick={() => {
                            if (disabled) return;
                            setIsOpen(!isOpen);
                        }}
                    >
                        {icon}
                    </div>
                )}
            </button>

            {/* Dropdown with animation */}
            {isOpen && !disabled && (
                <div className="absolute top-full left-0 mt-2 z-50 animate-in fade-in slide-in-from-top-2 duration-200 origin-top-left">
                    {children(() => setIsOpen(false))}
                </div>
            )}
        </div>
    );
}
