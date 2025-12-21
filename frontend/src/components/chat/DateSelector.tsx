import React from 'react';
import { addDays, subDays, isToday, format } from 'date-fns';
import { fr } from 'date-fns/locale';

interface DateSelectorProps {
    selectedDate: Date;
    onDateChange: (date: Date) => void;
}

export const DateSelector: React.FC<DateSelectorProps> = ({
    selectedDate,
    onDateChange,
}) => {
    const normalize = (d: Date) => new Date(d.getFullYear(), d.getMonth(), d.getDate());
    const today = normalize(new Date());
    const minDate = subDays(today, 7);
    const maxDate = addDays(today, 7);

    const clampDate = (d: Date) => {
        const n = normalize(d);
        if (n < minDate) return minDate;
        if (n > maxDate) return maxDate;
        return n;
    };

    const normalizedSelected = clampDate(selectedDate);

    const goToPreviousDay = () => onDateChange(clampDate(subDays(normalizedSelected, 1)));
    const goToToday = () => onDateChange(today);
    const goToNextDay = () => onDateChange(clampDate(addDays(normalizedSelected, 1)));

    const formatChip = (date: Date) => {
        const label = isToday(date) ? "Aujourd'hui" : format(date, 'dd/MM', { locale: fr });
        const sub = isToday(date) ? format(date, 'dd/MM', { locale: fr }) : '';
        return { label, sub };
    };

    const prev = formatChip(subDays(normalizedSelected, 1));
    const curr = formatChip(normalizedSelected);
    const next = formatChip(addDays(normalizedSelected, 1));
    const canGoPrev = normalize(normalizedSelected) > minDate;
    const canGoNext = normalize(normalizedSelected) < maxDate;

    return (
        <div className="px-3 py-2 border-b border-slate-100 bg-slate-50/50">
            <div className="flex items-center justify-center gap-2">
                <button
                    onClick={goToPreviousDay}
                    disabled={!canGoPrev}
                    className="px-3 py-2 text-xs font-medium text-slate-600 hover:bg-white hover:text-teal-600 rounded-lg transition-colors border border-transparent hover:border-slate-100 flex flex-col items-center disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <span>{prev.label}</span>
                    {prev.sub && <span className="text-[10px] text-slate-400">{prev.sub}</span>}
                </button>

                <button
                    onClick={goToToday}
                    className={`px-3 py-2 text-xs font-medium rounded-lg transition-colors flex flex-col items-center ${isToday(normalizedSelected)
                        ? 'bg-teal-500 text-white cursor-default'
                        : 'text-slate-600 hover:bg-white hover:text-teal-600 border border-transparent hover:border-slate-100'
                        }`}
                >
                    <span>{curr.label}</span>
                    {curr.sub && <span className="text-[10px] text-slate-100">{curr.sub}</span>}
                </button>

                <button
                    onClick={goToNextDay}
                    disabled={!canGoNext}
                    className="px-3 py-2 text-xs font-medium text-slate-600 hover:bg-white hover:text-teal-600 rounded-lg transition-colors border border-transparent hover:border-slate-100 flex flex-col items-center disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <span>{next.label}</span>
                    {next.sub && <span className="text-[10px] text-slate-400">{next.sub}</span>}
                </button>
            </div>

            {!isToday(normalizedSelected) && (
                <div className="flex justify-center mt-2">
                    <button
                        onClick={goToToday}
                        className="text-[11px] text-teal-600 hover:text-teal-700 font-semibold underline-offset-2 hover:underline"
                    >
                        Revenir à aujourd'hui
                    </button>
                </div>
            )}
        </div>
    );
};
