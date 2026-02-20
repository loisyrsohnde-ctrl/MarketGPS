'use client';

import React from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { ChevronDown, LayoutDashboard, BookOpen, Users, Zap, Upload, ArrowLeft } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LayoutProps {
  children: React.ReactNode;
}

const ADMIN_MENU_ITEMS = [
  {
    label: 'Tableau de bord',
    href: '/academy/admin',
    icon: LayoutDashboard,
  },
  {
    label: 'Contenu',
    href: '/academy/admin/contenu',
    icon: BookOpen,
  },
  {
    label: 'Étudiants',
    href: '/academy/admin/etudiants',
    icon: Users,
  },
  {
    label: 'Exercices',
    href: '/academy/admin/exercices',
    icon: Zap,
  },
  {
    label: 'Importer des données',
    href: '/academy/admin/seed',
    icon: Upload,
  },
];

export default function AdminLayout({ children }: LayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const [isSidebarOpen, setIsSidebarOpen] = React.useState(true);

  // Determine breadcrumb
  const getBreadcrumb = () => {
    const parts = pathname.split('/').filter(Boolean);
    if (parts[parts.length - 1] === 'admin') return 'Tableau de bord';
    const lastPart = parts[parts.length - 1];
    const menuItem = ADMIN_MENU_ITEMS.find((item) => item.href.endsWith(lastPart));
    return menuItem?.label || 'Admin';
  };

  return (
    <div className="flex h-screen bg-bg-primary">
      {/* Sidebar */}
      <aside
        className={cn(
          'fixed left-0 top-0 h-screen border-r border-glass-border bg-bg-primary transition-all duration-300 lg:relative z-40',
          isSidebarOpen ? 'w-64' : 'w-0 lg:w-64 lg:overflow-hidden'
        )}
      >
        <div className="flex h-full flex-col">
          {/* Sidebar Header */}
          <div className="border-b border-glass-border p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center">
                  <LayoutDashboard className="h-5 w-5 text-bg-primary" />
                </div>
                <div className="text-sm font-semibold text-text-primary">QuantAI Admin</div>
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex-1 space-y-1 p-4 overflow-y-auto">
            {ADMIN_MENU_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href || pathname.startsWith(item.href + '/');

              return (
                <button
                  key={item.href}
                  onClick={() => router.push(item.href)}
                  className={cn(
                    'w-full flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-medium transition-all duration-200',
                    isActive
                      ? 'bg-accent-dim border border-accent text-accent'
                      : 'text-text-muted hover:bg-surface-hover hover:text-text-secondary'
                  )}
                >
                  <Icon className="h-5 w-5 flex-shrink-0" />
                  <span className="truncate">{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Back to Academy */}
          <div className="border-t border-glass-border p-4">
            <button
              onClick={() => router.push('/academy')}
              className="w-full flex items-center gap-2 rounded-lg px-4 py-3 text-sm font-medium text-text-muted hover:bg-surface-hover hover:text-text-secondary transition-all duration-200"
            >
              <ArrowLeft className="h-5 w-5" />
              <span>Retour à l'Académie</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="border-b border-glass-border bg-bg-primary/50 backdrop-blur-sm px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Mobile Menu Toggle */}
              <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="lg:hidden p-2 text-text-secondary hover:text-text-primary transition-colors"
              >
                <ChevronDown className="h-5 w-5" />
              </button>

              {/* Breadcrumb */}
              <div className="flex items-center gap-2 text-sm">
                <span className="text-text-muted">QuantAI Academy</span>
                <span className="text-text-dim">/</span>
                <span className="text-text-secondary font-medium">{getBreadcrumb()}</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto">
          <div className="p-6 max-w-7xl mx-auto">{children}</div>
        </main>
      </div>
    </div>
  );
}
