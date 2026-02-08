// i18n configuration
export const defaultLocale = 'fr';
export const locales = ['fr', 'en'] as const;
export type Locale = typeof locales[number];
