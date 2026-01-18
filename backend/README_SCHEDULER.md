# MarketGPS Pipeline Scheduler

> Automatisation de l'exécution du pipeline US_EU à l'ouverture et fermeture du marché US.

## 📋 Vue d'ensemble

Le scheduler exécute le pipeline de scoring deux fois par jour:

| Mode | Heure (ET) | Description |
|------|------------|-------------|
| **open** | 09:35 | Rotation + scoring rapide |
| **close** | 16:10 | Full pipeline + publish production |

### Caractéristiques

- ✅ Heure basée sur **America/New_York** (DST automatique)
- ✅ Vérification calendrier boursier NYSE (skip week-ends + jours fériés)
- ✅ Lock pour éviter les exécutions doubles
- ✅ Logs rotatifs par mode (open/close)
- ✅ Compatible macOS + Linux

---

## 🚀 Installation

### 1. Installer les dépendances

```bash
cd /Users/cyrilsohnde/Documents/MarketGPS
source venv/bin/activate
pip install exchange-calendars
```

> `exchange-calendars` est une librairie pure Python compatible arm64.

### 2. Rendre le script exécutable

```bash
chmod +x backend/scripts/run_pipeline_us_eu.sh
```

### 3. Tester en dry-run

```bash
# Test mode open
backend/scripts/run_pipeline_us_eu.sh open --dry-run

# Test mode close
backend/scripts/run_pipeline_us_eu.sh close --dry-run
```

---

## ⚙️ Configuration Cron (macOS)

### Afficher le crontab actuel

```bash
crontab -l
```

### Éditer le crontab

```bash
crontab -e
```

### Entrées cron à ajouter

```cron
# MarketGPS Pipeline Scheduler
# Timezone: America/New_York (DST géré par le guard Python)

# Market Open - 09:35 ET (Lun-Ven)
35 9 * * 1-5 TZ=America/New_York /Users/cyrilsohnde/Documents/MarketGPS/backend/scripts/run_pipeline_us_eu.sh open >> /Users/cyrilsohnde/Documents/MarketGPS/backend/logs/cron_open.log 2>&1

# Market Close - 16:10 ET (Lun-Ven)
10 16 * * 1-5 TZ=America/New_York /Users/cyrilsohnde/Documents/MarketGPS/backend/scripts/run_pipeline_us_eu.sh close >> /Users/cyrilsohnde/Documents/MarketGPS/backend/logs/cron_close.log 2>&1
```

### Vérifier l'activation

```bash
crontab -l | grep MarketGPS
```

---

## 🧪 Tests

### Dry-run (vérification sans exécution)

```bash
# Vérifie tous les guards sans exécuter le pipeline
./backend/scripts/run_pipeline_us_eu.sh open --dry-run
./backend/scripts/run_pipeline_us_eu.sh close --dry-run
```

### Status du scheduler

```bash
python backend/scripts/scheduler_guard.py --status
```

Affiche:
- Heure actuelle en ET
- État du marché (ouvert/fermé)
- État du lock
- Fenêtres d'exécution

### Simuler un jour férié

```bash
# Noël 2025
python backend/scripts/scheduler_guard.py --mode open --force-date 2025-12-25 --dry-run
# Devrait retourner: exit code 10 (market closed)
echo "Exit code: $?"
```

### Simuler un week-end

```bash
# Un samedi
python backend/scripts/scheduler_guard.py --mode open --force-date 2025-01-18 --dry-run
# Devrait retourner: exit code 10 (weekend)
echo "Exit code: $?"
```

### Tester le lock

```bash
# Terminal 1: Simuler un pipeline en cours
echo '{"pid": 99999999, "mode": "open", "started_at": "2025-01-17T10:00:00"}' > backend/.pipeline_us_eu.lock

# Terminal 2: Essayer de lancer
python backend/scripts/scheduler_guard.py --mode open --skip-time-check --skip-calendar-check
# Devrait retourner: exit code 20 (lock active)

# Nettoyer
rm backend/.pipeline_us_eu.lock
```

### Force run (ignorer tous les checks)

```bash
./backend/scripts/run_pipeline_us_eu.sh open --force
```

---

## 📁 Structure des fichiers

```
backend/
├── scripts/
│   ├── scheduler_guard.py    # Guard Python (source de vérité)
│   └── run_pipeline_us_eu.sh # Orchestrateur shell
├── logs/
│   ├── pipeline_us_eu_open.log   # Logs mode open
│   ├── pipeline_us_eu_close.log  # Logs mode close
│   ├── cron_open.log             # Logs cron (stdout/stderr)
│   └── cron_close.log
├── .pipeline_us_eu.lock      # Lock file (auto-créé/supprimé)
└── README_SCHEDULER.md       # Cette doc
```

---

## 📊 Codes de sortie

| Code | Signification |
|------|---------------|
| 0 | Succès |
| 10 | Skip: marché fermé |
| 11 | Skip: hors fenêtre horaire |
| 20 | Skip: lock actif (pipeline en cours) |
| 1 | Erreur |

---

## 📋 Lecture des logs

### Logs du pipeline

```bash
# Dernières 50 lignes mode open
tail -50 backend/logs/pipeline_us_eu_open.log

# Suivre en temps réel mode close
tail -f backend/logs/pipeline_us_eu_close.log

# Chercher les erreurs
grep -i error backend/logs/pipeline_us_eu_*.log
```

### Logs cron

```bash
# Vérifier les exécutions cron
tail -100 backend/logs/cron_open.log
tail -100 backend/logs/cron_close.log
```

---

## 🐧 Portage Linux (systemd)

### 1. Créer le service

```bash
sudo nano /etc/systemd/system/marketgps-pipeline@.service
```

```ini
[Unit]
Description=MarketGPS Pipeline (%i)
After=network.target

[Service]
Type=oneshot
User=marketgps
Group=marketgps
WorkingDirectory=/opt/marketgps
Environment="PATH=/opt/marketgps/venv/bin:/usr/bin"
ExecStart=/opt/marketgps/backend/scripts/run_pipeline_us_eu.sh %i
StandardOutput=append:/opt/marketgps/backend/logs/pipeline_us_eu_%i.log
StandardError=append:/opt/marketgps/backend/logs/pipeline_us_eu_%i.log

[Install]
WantedBy=multi-user.target
```

### 2. Créer les timers

**Open timer** (`/etc/systemd/system/marketgps-pipeline-open.timer`):

```ini
[Unit]
Description=MarketGPS Pipeline Open Timer

[Timer]
OnCalendar=Mon-Fri 09:35 America/New_York
Persistent=true

[Install]
WantedBy=timers.target
```

**Close timer** (`/etc/systemd/system/marketgps-pipeline-close.timer`):

```ini
[Unit]
Description=MarketGPS Pipeline Close Timer

[Timer]
OnCalendar=Mon-Fri 16:10 America/New_York
Persistent=true

[Install]
WantedBy=timers.target
```

### 3. Activer les timers

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now marketgps-pipeline-open.timer
sudo systemctl enable --now marketgps-pipeline-close.timer
```

### 4. Vérifier le status

```bash
systemctl list-timers | grep marketgps
systemctl status marketgps-pipeline@open.service
```

---

## ⚠️ Troubleshooting

### Le cron ne s'exécute pas

1. Vérifier que cron est actif:
   ```bash
   # macOS
   sudo launchctl list | grep cron
   ```

2. Vérifier les permissions:
   ```bash
   ls -la backend/scripts/run_pipeline_us_eu.sh
   # Doit avoir: -rwxr-xr-x
   ```

3. Vérifier les chemins absolus dans le crontab

### Lock bloqué (stale)

```bash
# Voir le contenu du lock
cat backend/.pipeline_us_eu.lock

# Forcer la suppression
python backend/scripts/scheduler_guard.py --release-lock
# ou
rm backend/.pipeline_us_eu.lock
```

### Erreur "exchange_calendars not found"

```bash
source venv/bin/activate
pip install exchange-calendars
```

### Le pipeline s'exécute à la mauvaise heure

Le guard Python recalcule TOUJOURS l'heure en America/New_York. Vérifier:

```bash
python backend/scripts/scheduler_guard.py --status
```

Si l'heure affichée est incorrecte, vérifier la timezone système:
```bash
date
TZ=America/New_York date
```

---

## 🔧 Maintenance

### Rotation des logs (optionnel)

Créer `/etc/logrotate.d/marketgps` sur Linux:

```
/opt/marketgps/backend/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

Sur macOS, utiliser `newsyslog` ou un script custom.

### Purger les vieux logs

```bash
# Supprimer les logs > 30 jours
find backend/logs -name "*.log" -mtime +30 -delete
```

---

## 📞 Support

En cas de problème:
1. Vérifier les logs: `tail -100 backend/logs/pipeline_us_eu_*.log`
2. Vérifier le status: `python backend/scripts/scheduler_guard.py --status`
3. Dry-run: `./backend/scripts/run_pipeline_us_eu.sh open --dry-run`
