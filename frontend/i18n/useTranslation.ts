'use client';

import { useState, useEffect, useCallback } from 'react';
import { defaultLocale, type Locale } from './config';

type NestedKeyOf<T> = T extends object
  ? { [K in keyof T & string]: T[K] extends object
      ? `${K}.${NestedKeyOf<T[K]>}`
      : K
    }[keyof T & string]
  : never;

export function useTranslation() {
  // Store locale in localStorage, default to 'fr'
  const [locale, setLocale] = useState<Locale>(defaultLocale);
  const [dictionary, setDictionary] = useState<Record<string, any>>({});

  // Load locale from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem('locale') as Locale;
    if (stored && (stored === 'fr' || stored === 'en')) {
      setLocale(stored);
    }
  }, []);

  // Load dictionary on locale change
  useEffect(() => {
    import(`./dictionaries/${locale}.json`).then((m) => setDictionary(m.default));
  }, [locale]);

  const t = useCallback(
    (key: string, params?: Record<string, string>): string => {
      const keys = key.split('.');
      let value: any = dictionary;
      for (const k of keys) {
        value = value?.[k];
      }
      if (typeof value !== 'string') return key;
      if (params) {
        return Object.entries(params).reduce(
          (str, [k, v]) => str.replace(`{{${k}}}`, v),
          value
        );
      }
      return value;
    },
    [dictionary]
  );

  const changeLocale = useCallback((newLocale: Locale) => {
    setLocale(newLocale);
    localStorage.setItem('locale', newLocale);
  }, []);

  return {
    t,
    locale,
    changeLocale,
    isLoaded: Object.keys(dictionary).length > 0,
  };
}
