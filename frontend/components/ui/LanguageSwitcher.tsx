'use client';

import { useTranslation } from '@/i18n';
import { Globe } from 'lucide-react';
import { useState, useEffect } from 'react';

export function LanguageSwitcher() {
  const { locale, changeLocale, isLoaded } = useTranslation();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || !isLoaded) {
    return null;
  }

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/5 border border-white/10 backdrop-blur-md">
      <Globe size={16} className="text-[#EAF2EE]" />
      <div className="flex gap-1">
        <button
          onClick={() => changeLocale('fr')}
          className={`px-2 py-1 rounded text-sm font-medium transition-colors ${
            locale === 'fr'
              ? 'bg-white/10 text-[#EAF2EE]'
              : 'text-white/60 hover:text-[#EAF2EE] hover:bg-white/5'
          }`}
          aria-label="Switch to French"
        >
          FR
        </button>
        <button
          onClick={() => changeLocale('en')}
          className={`px-2 py-1 rounded text-sm font-medium transition-colors ${
            locale === 'en'
              ? 'bg-white/10 text-[#EAF2EE]'
              : 'text-white/60 hover:text-[#EAF2EE] hover:bg-white/5'
          }`}
          aria-label="Switch to English"
        >
          EN
        </button>
      </div>
    </div>
  );
}
