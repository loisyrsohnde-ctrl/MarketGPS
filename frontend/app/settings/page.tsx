'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { GlassCard } from '@/components/ui/glass-card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';
import { useUserProfile } from '@/hooks/useUserProfile';
import type { NotificationSettings } from '@/lib/api-user';
import {
  User,
  Mail,
  Lock,
  CreditCard,
  Bell,
  Shield,
  LogOut,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Upload,
  Eye,
  EyeOff,
} from 'lucide-react';

export default function SettingsPage() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [activeTab, setActiveTab] = useState('profile');

  const {
    profile,
    notifications,
    entitlements,
    loading,
    error,
    updateProfile,
    uploadAvatar,
    updateNotifications,
    changePassword,
    logout,
    deleteAccount,
  } = useUserProfile();

  // Profile tab states
  const [displayName, setDisplayName] = useState('');
  const [displayNameError, setDisplayNameError] = useState('');
  const [avatarLoading, setAvatarLoading] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);

  // Security tab states
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPasswords, setShowPasswords] = useState({
    current: false,
    new: false,
    confirm: false,
  });
  const [passwordError, setPasswordError] = useState('');
  const [passwordSaved, setPasswordSaved] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);

  // Notification tab states
  const [notificationsSaved, setNotificationsSaved] = useState(false);
  const [notificationsLoading, setNotificationsLoading] = useState(false);

  // Delete account states
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deletePassword, setDeletePassword] = useState('');
  const [deleteError, setDeleteError] = useState('');
  const [deleteLoading, setDeleteLoading] = useState(false);

  // Sync form with profile data
  useEffect(() => {
    if (profile) {
      setDisplayName(profile.displayName || '');
    }
  }, [profile]);

  // ============================================================================
  // PROFILE TAB HANDLERS
  // ============================================================================

  const handleAvatarClick = () => {
    fileInputRef.current?.click();
  };

  const handleAvatarChange = async (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validation
    if (!file.type.startsWith('image/')) {
      setDisplayNameError('Le fichier doit être une image');
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      setDisplayNameError('La taille du fichier ne doit pas dépasser 2MB');
      return;
    }

    try {
      setAvatarLoading(true);
      setDisplayNameError('');
      await uploadAvatar(file);
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 3000);
    } catch (err) {
      setDisplayNameError(
        err instanceof Error ? err.message : 'Erreur lors du téléchargement'
      );
    } finally {
      setAvatarLoading(false);
      // Reset input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleUpdateProfile = async () => {
    if (!displayName.trim()) {
      setDisplayNameError('Le nom d\'affichage ne peut pas être vide');
      return;
    }

    try {
      setDisplayNameError('');
      await updateProfile({ displayName });
      setProfileSaved(true);
      setTimeout(() => setProfileSaved(false), 3000);
    } catch (err) {
      setDisplayNameError(
        err instanceof Error ? err.message : 'Erreur lors de la mise à jour'
      );
    }
  };

  // ============================================================================
  // SECURITY TAB HANDLERS
  // ============================================================================

  const handleChangePassword = async () => {
    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordError('Tous les champs sont obligatoires');
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('Les nouveaux mots de passe ne correspondent pas');
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError(
        'Le nouveau mot de passe doit contenir au moins 8 caractères'
      );
      return;
    }

    try {
      setPasswordError('');
      setPasswordLoading(true);
      await changePassword(currentPassword, newPassword);

      // Clear form
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setPasswordSaved(true);
      setTimeout(() => setPasswordSaved(false), 3000);
    } catch (err) {
      setPasswordError(
        err instanceof Error ? err.message : 'Erreur lors de la modification'
      );
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      // Le logout redirige automatiquement
    } catch (err) {
      console.error('Logout failed:', err);
    }
  };

  const handleDeleteAccount = async () => {
    if (!deletePassword) {
      setDeleteError('Veuillez entrer votre mot de passe');
      return;
    }

    try {
      setDeleteError('');
      setDeleteLoading(true);
      await deleteAccount(deletePassword);
      // La suppression redirige automatiquement
    } catch (err) {
      setDeleteError(
        err instanceof Error ? err.message : 'Erreur lors de la suppression'
      );
    } finally {
      setDeleteLoading(false);
    }
  };

  // ============================================================================
  // NOTIFICATIONS TAB HANDLERS
  // ============================================================================

  const handleNotificationChange = async (key: keyof NotificationSettings) => {
    if (!notifications) return;

    const updated = { ...notifications, [key]: !notifications[key] };
    try {
      setNotificationsLoading(true);
      await updateNotifications(updated);
      setNotificationsSaved(true);
      setTimeout(() => setNotificationsSaved(false), 3000);
    } catch (err) {
      console.error('Failed to update notifications:', err);
    } finally {
      setNotificationsLoading(false);
    }
  };

  // ============================================================================
  // TABS CONFIG
  // ============================================================================

  const tabs = [
    { id: 'profile', label: 'Profil', icon: User },
    { id: 'security', label: 'Sécurité', icon: Lock },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    {
      id: 'billing',
      label: 'Abonnement',
      icon: CreditCard,
      href: '/settings/billing',
    },
  ];

  // ============================================================================
  // RENDER
  // ============================================================================

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Paramètres</h1>
          <p className="text-text-secondary mt-1">
            Gérez votre compte et vos préférences
          </p>
        </div>
        <div className="flex items-center justify-center h-64">
          <Loader2 className="w-8 h-8 animate-spin text-accent" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-text-primary">Paramètres</h1>
        <p className="text-text-secondary mt-1">
          Gérez votre compte et vos préférences
        </p>
      </div>

      <div className="grid md:grid-cols-4 gap-6">
        {/* Sidebar navigation */}
        <div className="md:col-span-1">
          <GlassCard padding="sm">
            <nav className="space-y-1">
              {tabs.map((tab) => {
                const Icon = tab.icon;
                if (tab.href) {
                  return (
                    <Link
                      key={tab.id}
                      href={tab.href}
                      className="flex items-center gap-3 px-4 py-3 rounded-xl text-text-secondary hover:bg-surface hover:text-text-primary transition-all"
                    >
                      <Icon className="w-5 h-5" />
                      {tab.label}
                    </Link>
                  );
                }
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={cn(
                      'flex items-center gap-3 w-full px-4 py-3 rounded-xl transition-all',
                      activeTab === tab.id
                        ? 'bg-accent-dim text-accent'
                        : 'text-text-secondary hover:bg-surface hover:text-text-primary'
                    )}
                  >
                    <Icon className="w-5 h-5" />
                    {tab.label}
                  </button>
                );
              })}
            </nav>
          </GlassCard>
        </div>

        {/* Content */}
        <div className="md:col-span-3">
          <AnimatePresence mode="wait">
            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <motion.div
                key="profile"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <GlassCard className="space-y-6">
                  {/* Success message */}
                  {profileSaved && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-4 rounded-xl bg-score-green/10 border border-score-green/30 flex items-center gap-3"
                    >
                      <CheckCircle2 className="w-5 h-5 text-score-green" />
                      <p className="text-sm text-score-green">
                        Profil mis à jour ✓
                      </p>
                    </motion.div>
                  )}

                  {/* Error message */}
                  {displayNameError && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3"
                    >
                      <AlertCircle className="w-5 h-5 text-red-500" />
                      <p className="text-sm text-red-500">{displayNameError}</p>
                    </motion.div>
                  )}

                  <div>
                    <h2 className="text-lg font-semibold text-text-primary mb-1">
                      Informations personnelles
                    </h2>
                    <p className="text-sm text-text-secondary">
                      Mettez à jour vos informations de profil
                    </p>
                  </div>

                  {/* Avatar */}
                  <div className="flex items-center gap-6">
                    <div className="relative">
                      <div className="w-20 h-20 rounded-full bg-gradient-to-br from-accent to-accent-dark flex items-center justify-center text-2xl font-bold text-white border-4 border-accent overflow-hidden">
                        {profile?.avatar ? (
                          <img
                            src={profile.avatar}
                            alt="Avatar"
                            className="w-full h-full object-cover"
                          />
                        ) : (
                          displayName[0]?.toUpperCase() || 'U'
                        )}
                      </div>
                      {avatarLoading && (
                        <div className="absolute inset-0 rounded-full bg-black/50 flex items-center justify-center">
                          <Loader2 className="w-5 h-5 animate-spin text-white" />
                        </div>
                      )}
                    </div>
                    <div>
                      <Button
                        variant="secondary"
                        size="sm"
                        onClick={handleAvatarClick}
                        disabled={avatarLoading}
                        className="flex items-center gap-2"
                      >
                        <Upload className="w-4 h-4" />
                        Changer l&apos;avatar
                      </Button>
                      <p className="text-xs text-text-secondary mt-2">
                        JPG, PNG ou GIF. Max 2MB
                      </p>
                    </div>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept="image/*"
                      onChange={handleAvatarChange}
                      className="hidden"
                    />
                  </div>

                  {/* Form */}
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-text-secondary">
                        Nom d&apos;affichage
                      </label>
                      <Input
                        value={displayName}
                        onChange={(e) => setDisplayName(e.target.value)}
                        leftIcon={<User className="w-5 h-5" />}
                        placeholder="Votre nom"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="block text-sm font-medium text-text-secondary">
                        Adresse email
                      </label>
                      <Input
                        type="email"
                        value={profile?.email || ''}
                        disabled
                        leftIcon={<Mail className="w-5 h-5" />}
                      />
                      <p className="text-xs text-text-secondary">
                        L&apos;email ne peut pas être modifié
                      </p>
                    </div>
                  </div>

                  {/* Save button */}
                  <Button
                    onClick={handleUpdateProfile}
                    className="w-full"
                    size="lg"
                  >
                    Enregistrer les modifications
                  </Button>
                </GlassCard>
              </motion.div>
            )}

            {/* Security Tab */}
            {activeTab === 'security' && (
              <motion.div
                key="security"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <div className="space-y-6">
                  {/* Change Password Card */}
                  <GlassCard className="space-y-6">
                    {/* Success message */}
                    {passwordSaved && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-4 rounded-xl bg-score-green/10 border border-score-green/30 flex items-center gap-3"
                      >
                        <CheckCircle2 className="w-5 h-5 text-score-green" />
                        <p className="text-sm text-score-green">
                          Mot de passe changé ✓
                        </p>
                      </motion.div>
                    )}

                    {/* Error message */}
                    {passwordError && (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3"
                      >
                        <AlertCircle className="w-5 h-5 text-red-500" />
                        <p className="text-sm text-red-500">{passwordError}</p>
                      </motion.div>
                    )}

                    <div>
                      <h2 className="text-lg font-semibold text-text-primary mb-1">
                        Changer le mot de passe
                      </h2>
                      <p className="text-sm text-text-secondary">
                        Mettez à jour votre mot de passe pour sécuriser votre
                        compte
                      </p>
                    </div>

                    <div className="space-y-4">
                      {/* Current Password */}
                      <div className="space-y-2">
                        <label className="block text-sm font-medium text-text-secondary">
                          Mot de passe actuel
                        </label>
                        <div className="relative">
                          <Input
                            type={
                              showPasswords.current ? 'text' : 'password'
                            }
                            value={currentPassword}
                            onChange={(e) =>
                              setCurrentPassword(e.target.value)
                            }
                            leftIcon={<Lock className="w-5 h-5" />}
                            placeholder="••••••••"
                          />
                          <button
                            onClick={() =>
                              setShowPasswords({
                                ...showPasswords,
                                current: !showPasswords.current,
                              })
                            }
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary"
                          >
                            {showPasswords.current ? (
                              <EyeOff className="w-5 h-5" />
                            ) : (
                              <Eye className="w-5 h-5" />
                            )}
                          </button>
                        </div>
                      </div>

                      {/* New Password */}
                      <div className="space-y-2">
                        <label className="block text-sm font-medium text-text-secondary">
                          Nouveau mot de passe
                        </label>
                        <div className="relative">
                          <Input
                            type={showPasswords.new ? 'text' : 'password'}
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            leftIcon={<Lock className="w-5 h-5" />}
                            placeholder="••••••••"
                          />
                          <button
                            onClick={() =>
                              setShowPasswords({
                                ...showPasswords,
                                new: !showPasswords.new,
                              })
                            }
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary"
                          >
                            {showPasswords.new ? (
                              <EyeOff className="w-5 h-5" />
                            ) : (
                              <Eye className="w-5 h-5" />
                            )}
                          </button>
                        </div>
                      </div>

                      {/* Confirm Password */}
                      <div className="space-y-2">
                        <label className="block text-sm font-medium text-text-secondary">
                          Confirmer le mot de passe
                        </label>
                        <div className="relative">
                          <Input
                            type={
                              showPasswords.confirm ? 'text' : 'password'
                            }
                            value={confirmPassword}
                            onChange={(e) =>
                              setConfirmPassword(e.target.value)
                            }
                            leftIcon={<Lock className="w-5 h-5" />}
                            placeholder="••••••••"
                          />
                          <button
                            onClick={() =>
                              setShowPasswords({
                                ...showPasswords,
                                confirm: !showPasswords.confirm,
                              })
                            }
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary"
                          >
                            {showPasswords.confirm ? (
                              <EyeOff className="w-5 h-5" />
                            ) : (
                              <Eye className="w-5 h-5" />
                            )}
                          </button>
                        </div>
                      </div>
                    </div>

                    <Button
                      onClick={handleChangePassword}
                      disabled={passwordLoading}
                      className="w-full"
                      size="lg"
                    >
                      {passwordLoading ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Changement...
                        </>
                      ) : (
                        'Changer le mot de passe'
                      )}
                    </Button>
                  </GlassCard>

                  {/* Logout Card */}
                  <GlassCard className="space-y-4 border-yellow-500/20">
                    <div>
                      <h2 className="text-lg font-semibold text-text-primary mb-1">
                        Déconnexion
                      </h2>
                      <p className="text-sm text-text-secondary">
                        Vous serez déconnecté de tous vos appareils
                      </p>
                    </div>
                    <Button
                      onClick={handleLogout}
                      variant="secondary"
                      className="w-full"
                      size="lg"
                    >
                      <LogOut className="w-4 h-4 mr-2" />
                      Se déconnecter maintenant
                    </Button>
                  </GlassCard>

                  {/* Delete Account Card */}
                  <GlassCard className="space-y-4 border-red-500/20 bg-red-500/5">
                    <div>
                      <h2 className="text-lg font-semibold text-red-500 mb-1">
                        Zone de danger
                      </h2>
                      <p className="text-sm text-text-secondary">
                        Supprimer votre compte définitivement
                      </p>
                    </div>

                    {!showDeleteConfirm ? (
                      <Button
                        onClick={() => setShowDeleteConfirm(true)}
                        className="w-full bg-red-500 hover:bg-red-600"
                        size="lg"
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Supprimer mon compte
                      </Button>
                    ) : (
                      <motion.div
                        initial={{ opacity: 0, y: -10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="space-y-4"
                      >
                        {deleteError && (
                          <motion.div
                            initial={{ opacity: 0, y: -10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 flex items-center gap-3"
                          >
                            <AlertCircle className="w-5 h-5 text-red-500" />
                            <p className="text-sm text-red-500">{deleteError}</p>
                          </motion.div>
                        )}

                        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30">
                          <p className="text-sm text-red-500 font-semibold mb-3">
                            ⚠️ Cette action est définitive et irréversible
                          </p>
                          <p className="text-xs text-text-secondary mb-4">
                            Confirmez en entrant votre mot de passe:
                          </p>
                          <div className="space-y-3">
                            <Input
                              type="password"
                              value={deletePassword}
                              onChange={(e) =>
                                setDeletePassword(e.target.value)
                              }
                              placeholder="Votre mot de passe"
                            />
                            <div className="flex gap-2">
                              <Button
                                onClick={() => {
                                  setShowDeleteConfirm(false);
                                  setDeletePassword('');
                                  setDeleteError('');
                                }}
                                variant="secondary"
                                className="flex-1"
                              >
                                Annuler
                              </Button>
                              <Button
                                onClick={handleDeleteAccount}
                                disabled={deleteLoading}
                                className="flex-1 bg-red-500 hover:bg-red-600"
                              >
                                {deleteLoading ? (
                                  <>
                                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                    Suppression...
                                  </>
                                ) : (
                                  'Supprimer définitivement'
                                )}
                              </Button>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    )}
                  </GlassCard>
                </div>
              </motion.div>
            )}

            {/* Notifications Tab */}
            {activeTab === 'notifications' && (
              <motion.div
                key="notifications"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
              >
                <GlassCard className="space-y-6">
                  {/* Success message */}
                  {notificationsSaved && (
                    <motion.div
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="p-4 rounded-xl bg-score-green/10 border border-score-green/30 flex items-center gap-3"
                    >
                      <CheckCircle2 className="w-5 h-5 text-score-green" />
                      <p className="text-sm text-score-green">
                        Préférences mises à jour ✓
                      </p>
                    </motion.div>
                  )}

                  <div>
                    <h2 className="text-lg font-semibold text-text-primary mb-1">
                      Notifications
                    </h2>
                    <p className="text-sm text-text-secondary">
                      Gérez vos préférences de notifications
                    </p>
                  </div>

                  <div className="space-y-4">
                    {notifications && (
                      <>
                        {/* Email Notifications */}
                        <div className="flex items-center justify-between p-4 rounded-xl bg-surface">
                          <div className="flex-1">
                            <p className="font-medium text-text-primary">
                              Notifications par email
                            </p>
                            <p className="text-sm text-text-secondary mt-1">
                              Recevoir des mises à jour importantes par email
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={notifications.emailNotifications}
                              onChange={() =>
                                handleNotificationChange(
                                  'emailNotifications'
                                )
                              }
                              disabled={notificationsLoading}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-accent rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                          </label>
                        </div>

                        {/* Market Alerts */}
                        <div className="flex items-center justify-between p-4 rounded-xl bg-surface">
                          <div className="flex-1">
                            <p className="font-medium text-text-primary">
                              Alertes de marché
                            </p>
                            <p className="text-sm text-text-secondary mt-1">
                              Recevoir les alertes importantes du marché
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={notifications.marketAlerts}
                              onChange={() =>
                                handleNotificationChange('marketAlerts')
                              }
                              disabled={notificationsLoading}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-accent rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                          </label>
                        </div>

                        {/* Price Alerts */}
                        <div className="flex items-center justify-between p-4 rounded-xl bg-surface">
                          <div className="flex-1">
                            <p className="font-medium text-text-primary">
                              Alertes de prix
                            </p>
                            <p className="text-sm text-text-secondary mt-1">
                              Recevoir les alertes prix sur vos actifs suivis
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={notifications.priceAlerts}
                              onChange={() =>
                                handleNotificationChange('priceAlerts')
                              }
                              disabled={notificationsLoading}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-accent rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                          </label>
                        </div>

                        {/* Portfolio Updates */}
                        <div className="flex items-center justify-between p-4 rounded-xl bg-surface">
                          <div className="flex-1">
                            <p className="font-medium text-text-primary">
                              Mises à jour du portefeuille
                            </p>
                            <p className="text-sm text-text-secondary mt-1">
                              Recevoir les résumés de votre portefeuille
                            </p>
                          </div>
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              checked={notifications.portfolioUpdates}
                              onChange={() =>
                                handleNotificationChange(
                                  'portfolioUpdates'
                                )
                              }
                              disabled={notificationsLoading}
                              className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-700 peer-focus:outline-none peer-focus:ring-2 peer-focus:ring-accent rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-accent"></div>
                          </label>
                        </div>
                      </>
                    )}
                  </div>

                  <div className="p-4 rounded-xl bg-accent-dim/30">
                    <p className="text-xs text-text-secondary">
                      💡 Les modifications sont enregistrées automatiquement
                    </p>
                  </div>
                </GlassCard>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
