
import React, { useState, useMemo } from 'react';
import { SearchIcon } from '../icons/ContextIcons';
import type { Zone } from '@/types/context';

interface CountryDropdownProps {
    zones: Zone[];
    onSelect: (zone: Zone) => void;
}

// Composant bouton de zone
function ZoneButton({ zone, onSelect }: { zone: Zone; onSelect: (z: Zone) => void }) {
    const isUrl = zone.flag?.startsWith('http');

    return (
        <button
            onClick={() => onSelect(zone)}
            className="w-full flex items-center gap-3 px-3 py-2 hover:bg-slate-50 transition-colors rounded-xl text-left"
        >
            {isUrl ? (
                <img src={zone.flag} alt={zone.name} className="w-5 h-5 object-cover rounded" />
            ) : (
                <span className="text-xl leading-none">{zone.flag}</span>
            )}
            <div className="flex-1 text-left">
                <div className="text-sm font-medium text-slate-700">{zone.name}</div>
            </div>
        </button>
    );
}

export const CountryDropdown: React.FC<CountryDropdownProps> = ({
    zones,
    onSelect
}) => {
    const [searchTerm, setSearchTerm] = useState('');

    const filteredZones = useMemo(() => {
        return zones.filter(zone =>
            zone.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (zone.full_name && zone.full_name.toLowerCase().includes(searchTerm.toLowerCase()))
        );
    }, [zones, searchTerm]);

    const groupedZones = useMemo(() => {
        // Dédupliquer les zones par code + zone_type
        const seen = new Set<string>();
        const deduplicated = filteredZones.filter(z => {
            const key = `${z.code}-${z.zone_type || 'national'}`;
            if (seen.has(key)) {
                return false;
            }
            seen.add(key);
            return true;
        });

        // Grouper par type
        const national = deduplicated.filter(z => !z.zone_type || z.zone_type === 'national');
        const continental = deduplicated.filter(z => z.zone_type === 'continental');
        const international = deduplicated.filter(z => z.zone_type === 'international');

        return { national, continental, international };
    }, [filteredZones]);

    return (
        <div className="w-72 max-h-[28rem] bg-white rounded-2xl shadow-xl border border-slate-100 flex flex-col overflow-hidden">
            {/* Search Header */}
            <div className="p-3 border-b border-slate-50">
                <div className="relative flex items-center bg-slate-50 rounded-xl px-3 py-2">
                    <SearchIcon className="w-4 h-4 text-slate-400 mr-2" />
                    <input
                        type="text"
                        placeholder="Rechercher..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="bg-transparent border-none outline-none text-sm text-slate-700 placeholder-slate-400 w-full"
                        autoFocus
                    />
                </div>
            </div>

            <div className="overflow-y-auto flex-1 p-1 space-y-2">

                {/* Section International */}
                {groupedZones.international.length > 0 && (
                    <div>
                        <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                            International
                        </div>
                        {groupedZones.international.map(zone => (
                            <ZoneButton key={`${zone.code}-${zone.zone_type || 'international'}`} zone={zone} onSelect={onSelect} />
                        ))}
                    </div>
                )}

                {/* Section Confédérations continentales */}
                {groupedZones.continental.length > 0 && (
                    <div>
                        <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-t border-slate-50 pt-2 mt-1">
                            Confédérations
                        </div>
                        {groupedZones.continental.map(zone => (
                            <ZoneButton key={`${zone.code}-${zone.zone_type || 'continental'}`} zone={zone} onSelect={onSelect} />
                        ))}
                    </div>
                )}

                {/* Section Pays nationaux */}
                {groupedZones.national.length > 0 && (
                    <div>
                        <div className="px-3 py-1 text-[10px] font-bold text-slate-400 uppercase tracking-wider border-t border-slate-50 pt-2 mt-1">
                            Pays
                        </div>
                        {groupedZones.national.map(zone => (
                            <ZoneButton key={`${zone.code}-${zone.zone_type || 'national'}`} zone={zone} onSelect={onSelect} />
                        ))}
                    </div>
                )}

                {filteredZones.length === 0 && (
                    <div className="p-4 text-center text-sm text-slate-400">
                        Aucune zone trouvée
                    </div>
                )}
            </div>
        </div>
    );
};
