'use client';

import { AlertTriangle, Bell, TrendingUp, Zap, AlertCircle } from 'lucide-react';
import { MorningBriefCard } from './MorningBriefCard';
import { motion } from 'framer-motion';
import { formatRelativeTime } from '@/lib/utils';
import type { Alert, AlertType } from '@/types/morning-brief';

// ═══════════════════════════════════════════════════════════════════════════
// ALERTS PREVIEW
// Shows recent alerts and unread count
// ═══════════════════════════════════════════════════════════════════════════

interface AlertsPreviewProps {
  unreadCount: number;
  criticalCount: number;
  recentAlerts: Alert[];
  onViewAll?: () => void;
}

const getAlertIcon = (type: AlertType) => {
  switch (type) {
    case 'price':
      return <TrendingUp className="w-4 h-4" />;
    case 'score':
      return <Zap className="w-4 h-4" />;
    case 'news':
      return <Bell className="w-4 h-4" />;
    case 'risk':
      return <AlertTriangle className="w-4 h-4" />;
    case 'opportunity':
      return <AlertCircle className="w-4 h-4" />;
    default:
      return <Bell className="w-4 h-4" />;
  }
};

const getAlertColor = (type: AlertType, severity: Alert['severity']) => {
  if (severity === 'critical') return 'text-score-red';
  if (severity === 'high') return 'text-score-red';
  if (severity === 'medium') return 'text-score-yellow';
  return 'text-score-blue';
};

const getAlertBgColor = (type: AlertType, severity: Alert['severity']) => {
  if (severity === 'critical') return 'bg-score-red/10';
  if (severity === 'high') return 'bg-score-red/10';
  if (severity === 'medium') return 'bg-score-yellow/10';
  return 'bg-score-blue/10';
};

export function AlertsPreview({
  unreadCount,
  criticalCount,
  recentAlerts,
  onViewAll,
}: AlertsPreviewProps) {
  const alertsVariants = {
    container: {
      hidden: { opacity: 0 },
      show: {
        opacity: 1,
        transition: {
          staggerChildren: 0.08,
          delayChildren: 0.1,
        },
      },
    },
    item: {
      hidden: { opacity: 0, x: -15 },
      show: { opacity: 1, x: 0 },
    },
  };

  const variant = criticalCount > 0 ? 'alert' : 'default';

  return (
    <MorningBriefCard
      title="Alerts & Notifications"
      icon={
        criticalCount > 0 ? (
          <span className="text-lg animate-pulse">🚨</span>
        ) : (
          <span>🔔</span>
        )
      }
      actionLabel="View All"
      onAction={onViewAll}
      variant={variant}
    >
      <motion.div className="flex flex-col gap-3">
        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-2 mb-2">
          <div className="p-3 rounded-lg bg-surface/50">
            <p className="text-xs text-text-secondary mb-1">Unread</p>
            <p className="text-xl font-bold text-text-primary">{unreadCount}</p>
          </div>
          <div className="p-3 rounded-lg bg-surface/50">
            <p className="text-xs text-text-secondary mb-1">Critical</p>
            <p className={`text-xl font-bold ${
              criticalCount > 0 ? 'text-score-red' : 'text-text-primary'
            }`}>
              {criticalCount}
            </p>
          </div>
          <div className="p-3 rounded-lg bg-surface/50">
            <p className="text-xs text-text-secondary mb-1">Recent</p>
            <p className="text-xl font-bold text-text-primary">{recentAlerts.length}</p>
          </div>
        </div>

        {/* Recent Alerts List */}
        {recentAlerts.length > 0 ? (
          <motion.div
            variants={alertsVariants.container}
            initial="hidden"
            animate="show"
            className="space-y-2"
          >
            {recentAlerts.slice(0, 3).map((alert) => (
              <motion.div
                key={alert.id}
                variants={alertsVariants.item}
                className={`p-3 rounded-lg border border-surface ${getAlertBgColor(
                  alert.type,
                  alert.severity
                )}`}
              >
                <div className="flex items-start gap-3">
                  {/* Icon */}
                  <div className={`mt-0.5 ${getAlertColor(alert.type, alert.severity)}`}>
                    {getAlertIcon(alert.type)}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-1">
                      <p className="text-sm font-semibold text-text-primary line-clamp-1">
                        {alert.title}
                      </p>
                      {alert.severity === 'critical' && (
                        <span className="px-2 py-0.5 rounded text-xs font-bold bg-score-red text-white whitespace-nowrap">
                          Critical
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-text-secondary line-clamp-2 mb-2">
                      {alert.message}
                    </p>
                    {alert.metadata && (
                      <p className="text-xs text-text-muted">
                        {alert.metadata.oldValue && alert.metadata.newValue && (
                          <span>
                            {alert.metadata.oldValue.toFixed(2)} → {alert.metadata.newValue.toFixed(2)}
                          </span>
                        )}
                      </p>
                    )}
                    <p className="text-xs text-text-muted mt-1">
                      {formatRelativeTime(alert.createdAt)}
                    </p>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        ) : (
          <div className="py-8 text-center">
            <p className="text-sm text-text-secondary">✨ No new alerts</p>
            <p className="text-xs text-text-muted mt-1">You're all caught up!</p>
          </div>
        )}
      </motion.div>
    </MorningBriefCard>
  );
}

export default AlertsPreview;
