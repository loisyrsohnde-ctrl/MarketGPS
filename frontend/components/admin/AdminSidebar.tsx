'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  Newspaper,
  FileText,
  Users,
  Settings,
  LogOut,
  CreditCard,
  MessageSquare,
  Cpu,
  Activity,
  Globe2,
  Star,
  ChevronLeft,
  ChevronRight,
  Rss,
  ScrollText,
} from 'lucide-react';

interface NavSection {
  title: string;
  items: Array<{
    label: string;
    href: string;
    icon: React.ComponentType<{ className?: string }>;
  }>;
}

const navSections: NavSection[] = [
  {
    title: 'Principal',
    items: [
      {
        label: 'Dashboard',
        href: '/admin',
        icon: LayoutDashboard,
      },
      {
        label: 'Actualités',
        href: '/admin/news',
        icon: Newspaper,
      },
      {
        label: 'Scripts Vidéo',
        href: '/admin/scripts',
        icon: FileText,
      },
    ],
  },
  {
    title: 'Gestion',
    items: [
      {
        label: 'Utilisateurs',
        href: '/admin/users',
        icon: Users,
      },
      {
        label: 'Abonnements',
        href: '/admin/subscriptions',
        icon: CreditCard,
      },
      {
        label: 'Feedbacks',
        href: '/admin/feedbacks',
        icon: MessageSquare,
      },
      {
        label: 'Quotas AI',
        href: '/admin/quotas',
        icon: Cpu,
      },
    ],
  },
  {
    title: 'Contenu',
    items: [
      {
        label: 'Sources',
        href: '/admin/sources',
        icon: Rss,
      },
      {
        label: 'Allemagne',
        href: '/admin/germany',
        icon: Globe2,
      },
      {
        label: 'Top Articles',
        href: '/admin/top',
        icon: Star,
      },
    ],
  },
  {
    title: 'Système',
    items: [
      {
        label: 'Diagnostics',
        href: '/admin/diagnostics',
        icon: Activity,
      },
      {
        label: 'Paramètres',
        href: '/admin/settings',
        icon: Settings,
      },
      {
        label: 'Journal d\'activité',
        href: '/admin/activity',
        icon: ScrollText,
      },
    ],
  },
];

interface AdminSidebarProps {
  isOpen?: boolean;
  onToggle?: (isOpen: boolean) => void;
}

export function AdminSidebar({ isOpen: initialOpen = true, onToggle }: AdminSidebarProps) {
  const pathname = usePathname();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isOpen, setIsOpen] = useState(initialOpen);

  // Load collapsed state from localStorage on mount
  useEffect(() => {
    const savedState = localStorage.getItem('adminSidebarCollapsed');
    if (savedState !== null) {
      const collapsed = JSON.parse(savedState);
      setIsCollapsed(collapsed);
    }
  }, []);

  const toggleCollapsed = () => {
    const newState = !isCollapsed;
    setIsCollapsed(newState);
    localStorage.setItem('adminSidebarCollapsed', JSON.stringify(newState));
  };

  const handleToggleOpen = () => {
    const newOpen = !isOpen;
    setIsOpen(newOpen);
    onToggle?.(newOpen);
  };

  const handleLogout = async () => {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/login';
  };

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          onClick={() => handleToggleOpen()}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed left-0 top-0 h-screen bg-white dark:bg-gray-950 border-r border-gray-200 dark:border-gray-800 transition-all duration-300 ease-in-out z-40 lg:relative lg:z-0 lg:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } ${isCollapsed ? 'w-16' : 'w-64'}`}
      >
        {/* Logo Section */}
        <div
          className={`border-b border-gray-200 dark:border-gray-800 transition-all duration-300 ${
            isCollapsed ? 'p-3' : 'p-6'
          }`}
        >
          <div className="flex items-center justify-between">
            {!isCollapsed && (
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-white">
                  MarketGPS
                </h1>
                <p className="text-xs text-gray-600 dark:text-gray-400">Admin Panel</p>
              </div>
            )}
            <button
              onClick={toggleCollapsed}
              className="hidden lg:flex items-center justify-center p-1 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              aria-label="Toggle sidebar"
            >
              {isCollapsed ? (
                <ChevronRight className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              ) : (
                <ChevronLeft className="h-5 w-5 text-gray-600 dark:text-gray-400" />
              )}
            </button>
          </div>
        </div>

        {/* Navigation */}
        <nav className={`flex-1 overflow-y-auto transition-all duration-300 ${isCollapsed ? 'p-2' : 'p-4'}`}>
          {navSections.map((section) => (
            <div key={section.title} className="mb-6">
              {!isCollapsed && (
                <h2 className="mb-3 px-4 text-xs font-semibold uppercase tracking-wider text-gray-500 dark:text-gray-400">
                  {section.title}
                </h2>
              )}
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = item.href === '/admin'
                    ? pathname === '/admin'
                    : pathname === item.href || pathname.startsWith(item.href + '/');

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center gap-3 rounded-lg transition-all duration-200 ${
                        isCollapsed ? 'justify-center p-2' : 'px-4 py-2'
                      } text-sm font-medium ${
                        isActive
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                          : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800'
                      }`}
                      title={isCollapsed ? item.label : undefined}
                    >
                      <Icon className="h-5 w-5 flex-shrink-0" />
                      {!isCollapsed && <span>{item.label}</span>}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Footer - Logout */}
        <div className={`border-t border-gray-200 dark:border-gray-800 transition-all duration-300 ${isCollapsed ? 'p-2' : 'p-4'}`}>
          <button
            onClick={handleLogout}
            className={`flex w-full items-center gap-3 rounded-lg transition-all duration-200 ${
              isCollapsed ? 'justify-center p-2' : 'px-4 py-2'
            } text-sm font-medium text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-800`}
            title={isCollapsed ? 'Déconnexion' : undefined}
          >
            <LogOut className="h-5 w-5 flex-shrink-0" />
            {!isCollapsed && <span>Déconnexion</span>}
          </button>
        </div>
      </aside>
    </>
  );
}
