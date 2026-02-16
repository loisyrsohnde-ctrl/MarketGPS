'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Menu, Search, RefreshCw, User, Newspaper, FileText, Loader2 } from 'lucide-react';
import { useGlobalSearch } from '@/hooks/useGlobalSearch';
import { NotificationCenter } from './NotificationCenter';

interface AdminHeaderProps {
  onMenuToggle: () => void;
  onSearch: (query: string) => void;
}

export function AdminHeader({ onMenuToggle, onSearch }: AdminHeaderProps) {
  const router = useRouter();
  const { results, loading, search, clear } = useGlobalSearch();
  const [searchQuery, setSearchQuery] = useState('');
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const query = e.target.value;
    setSearchQuery(query);
    onSearch(query);

    if (query.trim()) {
      search(query);
      setShowDropdown(true);
    } else {
      clear();
      setShowDropdown(false);
    }
  };

  const handleRefresh = () => {
    window.location.reload();
  };

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'article':
        return <Newspaper className="h-4 w-4 text-blue-500" />;
      case 'script':
        return <FileText className="h-4 w-4 text-purple-500" />;
      case 'user':
        return <User className="h-4 w-4 text-green-500" />;
      default:
        return <Search className="h-4 w-4 text-gray-400" />;
    }
  };

  const handleResultClick = (result: any) => {
    if (result.type === 'article') {
      router.push(`/admin/news/${result.id}`);
    } else if (result.type === 'script') {
      router.push(`/admin/scripts/${result.id}`);
    } else if (result.type === 'user') {
      router.push('/admin/users');
    }
    setShowDropdown(false);
    setSearchQuery('');
    clear();
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setShowDropdown(false);
      }
    }

    if (showDropdown) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [showDropdown]);

  // Close dropdown on Escape key
  useEffect(() => {
    function handleEscapeKey(event: KeyboardEvent) {
      if (event.key === 'Escape' && showDropdown) {
        setShowDropdown(false);
      }
    }

    if (showDropdown) {
      document.addEventListener('keydown', handleEscapeKey);
      return () => {
        document.removeEventListener('keydown', handleEscapeKey);
      };
    }
  }, [showDropdown]);

  return (
    <header className="sticky top-0 z-30 flex items-center justify-between gap-4 border-b border-gray-200 bg-white px-6 py-3 dark:border-gray-800 dark:bg-gray-950">
      {/* Left: Hamburger menu (mobile only) */}
      <button
        onClick={onMenuToggle}
        className="lg:hidden inline-flex items-center justify-center p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        aria-label="Toggle menu"
      >
        <Menu className="h-5 w-5 text-gray-600 dark:text-gray-400" />
      </button>

      {/* Center: Search input */}
      <div className="flex-1 max-w-xl" ref={dropdownRef}>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={handleSearchChange}
            placeholder="Rechercher articles, scripts, pays..."
            className="w-full pl-9 pr-4 py-2 rounded-lg border border-gray-300 bg-white text-sm text-gray-900 placeholder-gray-500 transition-colors focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-gray-700 dark:bg-gray-900 dark:text-white dark:placeholder-gray-400"
          />

          {/* Search dropdown */}
          {showDropdown && (
            <div className="absolute top-full left-0 right-0 mt-2 bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-800 z-50 max-h-96 overflow-y-auto">
              {loading && (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
                </div>
              )}

              {!loading && results.length === 0 && searchQuery.trim() && (
                <div className="flex items-center justify-center py-6 px-4">
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Aucun résultat
                  </p>
                </div>
              )}

              {!loading && results.length > 0 && (
                <div className="divide-y divide-gray-100 dark:divide-gray-800">
                  {results.map(result => (
                    <button
                      key={result.id}
                      onClick={() => handleResultClick(result)}
                      className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-left"
                    >
                      <div className="flex-shrink-0">
                        {getResultIcon(result.type)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {result.title}
                        </p>
                        {result.description && (
                          <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
                            {result.description}
                          </p>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {/* Refresh button */}
        <button
          onClick={handleRefresh}
          className="inline-flex items-center justify-center p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
          aria-label="Refresh"
        >
          <RefreshCw className="h-5 w-5 text-gray-600 dark:text-gray-400" />
        </button>

        {/* Notification Center */}
        <NotificationCenter />

        {/* Admin badge */}
        <div className="flex items-center gap-2 pl-3 border-l border-gray-200 dark:border-gray-800">
          <div className="flex items-center justify-center h-8 w-8 rounded-full bg-blue-100 dark:bg-blue-900/30">
            <User className="h-4 w-4 text-blue-700 dark:text-blue-400" />
          </div>
          <span className="hidden sm:inline text-sm font-medium text-gray-700 dark:text-gray-300">Admin</span>
        </div>
      </div>
    </header>
  );
}
