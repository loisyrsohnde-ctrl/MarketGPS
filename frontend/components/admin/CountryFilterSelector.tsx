'use client';

import { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';

interface CountryFilterSelectorProps {
  selected: string[];
  onChange: (countries: string[]) => void;
}

const COUNTRY_TIERS = {
  'Tier 1 (Priorité)': [
    { code: 'CI', name: 'Côte d\'Ivoire', flag: '🇨🇮' },
    { code: 'CM', name: 'Cameroun', flag: '🇨🇲' },
    { code: 'SN', name: 'Sénégal', flag: '🇸🇳' },
    { code: 'NG', name: 'Nigeria', flag: '🇳🇬' },
    { code: 'KE', name: 'Kenya', flag: '🇰🇪' },
    { code: 'ZA', name: 'Afrique du Sud', flag: '🇿🇦' },
    { code: 'MA', name: 'Maroc', flag: '🇲🇦' },
  ],
  'Tier 2 (Francophone)': [
    { code: 'BJ', name: 'Bénin', flag: '🇧🇯' },
    { code: 'TG', name: 'Togo', flag: '🇹🇬' },
    { code: 'GA', name: 'Gabon', flag: '🇬🇦' },
    { code: 'ML', name: 'Mali', flag: '🇲🇱' },
    { code: 'BF', name: 'Burkina Faso', flag: '🇧🇫' },
    { code: 'GH', name: 'Ghana', flag: '🇬🇭' },
    { code: 'CD', name: 'RDC', flag: '🇨🇩' },
    { code: 'TN', name: 'Tunisie', flag: '🇹🇳' },
    { code: 'DZ', name: 'Algérie', flag: '🇩🇿' },
  ],
  'Europe': [
    { code: 'DE', name: 'Allemagne', flag: '🇩🇪' },
    { code: 'FR', name: 'France', flag: '🇫🇷' },
  ],
};

export function CountryFilterSelector({
  selected,
  onChange,
}: CountryFilterSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleToggleCountry = (code: string) => {
    const newSelected = selected.includes(code)
      ? selected.filter((c) => c !== code)
      : [...selected, code];
    onChange(newSelected);
  };

  const handleSelectAll = () => {
    const allCountries = Object.values(COUNTRY_TIERS).flatMap((tier) =>
      tier.map((c) => c.code)
    );
    onChange(allCountries);
  };

  const handleClearAll = () => {
    onChange([]);
  };

  const getAllCountries = () => {
    return Object.values(COUNTRY_TIERS).flatMap((tier) =>
      tier.map((c) => c.code)
    );
  };

  const displayText =
    selected.length === 0
      ? 'Sélectionner pays'
      : selected.length === getAllCountries().length
        ? 'Tous les pays'
        : `${selected.length} pays sélectionnés`;

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full rounded-lg border border-gray-300 px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none dark:border-gray-600 dark:bg-gray-800 dark:text-white flex items-center justify-between gap-2"
      >
        <span className="text-sm">{displayText}</span>
        <ChevronDown
          className={`h-4 w-4 transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {isOpen && (
        <div className="absolute right-0 left-0 top-full z-50 mt-1 rounded-lg border border-gray-300 bg-white shadow-lg dark:border-gray-600 dark:bg-gray-800">
          {/* Action Buttons */}
          <div className="border-b border-gray-200 px-4 py-3 flex gap-2 dark:border-gray-700">
            <button
              onClick={handleSelectAll}
              className="flex-1 rounded-md bg-blue-600 px-3 py-1 text-xs font-medium text-white hover:bg-blue-700 transition-colors dark:bg-blue-500 dark:hover:bg-blue-600"
            >
              Tous
            </button>
            <button
              onClick={handleClearAll}
              className="flex-1 rounded-md border border-gray-300 px-3 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700"
            >
              Effacer
            </button>
          </div>

          {/* Country Tiers */}
          <div className="max-h-96 overflow-y-auto">
            {Object.entries(COUNTRY_TIERS).map(([tierName, countries]) => (
              <div key={tierName}>
                <div className="sticky top-0 bg-gray-50 px-4 py-2 text-xs font-semibold text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                  {tierName}
                </div>
                <div className="space-y-1 px-4 py-2">
                  {countries.map((country) => (
                    <label
                      key={country.code}
                      className="flex items-center gap-3 rounded px-2 py-2 hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer"
                    >
                      <input
                        type="checkbox"
                        checked={selected.includes(country.code)}
                        onChange={() => handleToggleCountry(country.code)}
                        className="w-4 h-4 rounded border-gray-300 cursor-pointer dark:bg-gray-700 dark:border-gray-600"
                      />
                      <span className="text-sm text-gray-700 dark:text-gray-300">
                        {country.flag} {country.code} - {country.name}
                      </span>
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
