import React from 'react';

type ModelType = 'deepseek' | 'medium' | 'fast';

interface ModelOption {
    value: ModelType;
    label: string;
    description: string;
    badge: string;
    badgeColor: string;
}

interface ModelDropdownProps {
    onSelect: (modelType: ModelType) => void;
}

const modelOptions: ModelOption[] = [
    {
        value: 'deepseek',
        label: 'DeepSeek (Base)',
        description: 'DeepSeek - Meilleur rapport qualité/prix',
        badge: 'Économique',
        badgeColor: 'bg-green-100 text-green-600'
    },
    {
        value: 'medium',
        label: 'Medium (Équilibré)',
        description: 'GPT-4o-mini - Bon compromis vitesse/qualité',
        badge: 'Équilibré',
        badgeColor: 'bg-blue-100 text-blue-600'
    },
    {
        value: 'fast',
        label: 'Fast (Premium)',
        description: 'GPT-4o - Meilleure qualité et rapidité',
        badge: 'Premium',
        badgeColor: 'bg-purple-100 text-purple-600'
    }
];

export const ModelDropdown: React.FC<ModelDropdownProps> = ({ onSelect }) => {
    return (
        <div className="w-72 bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
            <div className="p-2 space-y-1">
                {modelOptions.map((option) => (
                    <button
                        key={option.value}
                        onClick={() => onSelect(option.value)}
                        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-slate-50 transition-colors rounded-xl text-left"
                    >
                        <div className="flex-1">
                            <div className="text-sm font-medium text-slate-700">
                                {option.label}
                            </div>
                            <div className="text-[11px] text-slate-400 mt-0.5">
                                {option.description}
                            </div>
                        </div>
                        <div className={`px-2 py-0.5 rounded text-[9px] font-medium uppercase ${option.badgeColor}`}>
                            {option.badge}
                        </div>
                    </button>
                ))}
            </div>
        </div>
    );
};
