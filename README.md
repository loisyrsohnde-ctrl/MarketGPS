# MarketGPS v12.0 — Premium Fintech Dashboard

**Score d'Analyse /100** — Outil d'analyse statistique institutionnel avec Landing Page Premium, Authentification et Abonnements.

> ⚠️ Cet outil ne constitue pas un conseil en investissement.

---

## Nouveautés v12.0

- 🎨 **Landing Page Premium** - Design institutionnel avec glassmorphism
- 🔐 **Authentification** - Signup/Login sécurisé avec hachage PBKDF2
- 💳 **Abonnements** - Plans Free/Pro avec quotas (mode dev + Stripe ready)
- 🌍 **Multi-marchés** - USA, Europe, Afrique (scopes séparés)
- 📊 **Score Card Live** - Données réelles depuis la DB sur la landing

---

## Architecture

```
marketgps/
├── app/                    # Application Streamlit
│   ├── streamlit_app.py    # Point d'entrée principal
│   ├── landing.py          # Landing page premium HTML/CSS
│   ├── auth.py             # Authentification (signup/login)
│   └── company_info.py     # Infos entreprises
├── assets/                 # Assets statiques
│   ├── css/theme.css       # Styles CSS
│   └── landing/            # Images landing (world_map.png, market_bg.png)
├── core/                   # Modules centraux
│   ├── config.py           # Configuration (+ BillingConfig)
│   ├── models.py           # Modèles de données
│   └── compliance.py       # Filtre de conformité
├── providers/              # Providers de données
│   ├── base.py             # Interface abstraite
│   └── eodhd.py            # Implémentation EODHD
├── storage/                # Stockage
│   ├── sqlite_store.py     # SQLite (+ users, subscriptions)
│   └── parquet_store.py    # Parquet (OHLCV)
├── pipeline/               # Pipeline de données
│   ├── universe.py         # Gestion de l'univers
│   ├── gating.py           # Filtrage qualité
│   ├── rotation.py         # Mise à jour incrémentale
│   ├── scoring.py          # Calcul des scores
│   └── jobs.py             # CLI pour les jobs
├── data/                   # Données (généré)
│   ├── sqlite/             # Base SQLite
│   └── parquet/            # Fichiers Parquet
├── schema.sql              # Schéma SQLite v12
├── requirements.txt        # Dépendances
└── .env.example            # Variables d'environnement
```

---

## Installation

### 1. Prérequis

- Python 3.10+
- Clé API EODHD (https://eodhd.com)

### 2. Installation des dépendances

```bash
cd marketgps
pip install -r requirements.txt
```

### 3. Configuration

Créer un fichier `.env` à partir de `.env.example`:

```bash
cp .env.example .env
```

Éditer `.env` et ajouter votre clé API EODHD:

```
EODHD_API_KEY=your_api_key_here
```

---

## Utilisation

### 1. Initialiser l'univers

```bash
python -m pipeline.jobs --init-universe
```

Crée la liste des actifs (60 par défaut: actions + ETFs US).

### 2. Lancer le gating (qualité des données)

```bash
python -m pipeline.jobs --run-gating
```

Évalue la qualité des données pour chaque actif:
- Coverage (jours de données disponibles)
- Liquidité (ADV)
- Détection de données stale

### 3. Lancer la rotation (calcul des scores)

```bash
python -m pipeline.jobs --run-rotation
```

Calcule les scores pour un batch d'actifs (ne scanne pas tout le marché).

### 4. Pipeline complet

```bash
python -m pipeline.jobs --full-pipeline
```

Exécute: universe → gating → rotation.

### 5. Statut du système

```bash
python -m pipeline.jobs --status
```

Affiche les statistiques des tables et du provider.

### 6. Lancer l'interface Streamlit

```bash
streamlit run app/streamlit_app.py
```

Ouvrir http://localhost:8501

---

## Pipeline de données

### Architecture "Rotation"

Le pipeline évite de rescanner tout le marché à chaque cycle:

1. **Universe** (hebdomadaire) — Liste complète des actifs
2. **Gating** (quotidien) — Filtrage qualité
3. **Rotation** (15 min) — Mise à jour incrémentale:
   - Top 50 actuel
   - N actifs les plus "stale"
   - Demandes utilisateur
   - Batch limité (configurable)

### Stockage

- **SQLite** : état du système, scores, rotation
- **Parquet** : données OHLCV historiques

---

## Scoring

### Piliers

| Pilier | Description | Poids (EQUITY) | Poids (ETF) |
|--------|-------------|----------------|-------------|
| Valeur | P/E, marges, ROE | 30% | N/A |
| Momentum | RSI, prix vs SMA200 | 40% | 60% |
| Sécurité | Volatilité, drawdown | 30% | 40% |

### Data Confidence

Indicateur de fiabilité des données (0-100%):
- Coverage des données
- Fraîcheur des données
- Disponibilité des fondamentaux

---

## Variables d'environnement

| Variable | Description | Défaut |
|----------|-------------|--------|
| `EODHD_API_KEY` | Clé API EODHD | (requis) |
| `EODHD_BASE_URL` | URL de l'API | https://eodhd.com/api |
| `DEFAULT_EXCHANGE` | Exchange par défaut | US |
| `ROTATION_BATCH_SIZE` | Taille du batch rotation | 50 |
| `DATA_DIR` | Répertoire des données | ./data |
| `SQLITE_PATH` | Chemin SQLite | ./data/sqlite/marketgps.db |
| `BILLING_MODE` | Mode facturation (`dev` ou `stripe`) | dev |
| `STRIPE_PUBLIC_KEY` | Clé publique Stripe | — |
| `STRIPE_SECRET_KEY` | Clé secrète Stripe | — |
| `STRIPE_WEBHOOK_SECRET` | Secret webhook Stripe | — |
| `STRIPE_PRICE_MONTHLY` | Price ID mensuel Stripe | — |
| `STRIPE_PRICE_YEARLY` | Price ID annuel Stripe | — |

---

## Billing / Abonnements

### Mode Dev (défaut)

En mode `BILLING_MODE=dev`, les abonnements sont activés directement sans paiement réel.
C'est le mode par défaut pour le développement.

### Plans disponibles

| Plan | Prix | Quota/jour | Features |
|------|------|------------|----------|
| `free` | 0€ | 3 calculs | Marchés US/EU |
| `monthly_9_99` | 9,99€/mois | 200 calculs | Tous marchés, alertes |
| `yearly_50` | 50€/an | 200 calculs | Tous marchés, alertes, support prioritaire |

### Intégration Stripe (Production)

Pour activer les paiements réels avec Stripe :

1. **Créer un compte Stripe** sur https://stripe.com

2. **Créer les produits** dans le Dashboard Stripe :
   - Produit "Pro Mensuel" : 9,99€/mois (récurrent)
   - Produit "Pro Annuel" : 50€/an (récurrent)

3. **Récupérer les Price IDs** depuis Stripe Dashboard

4. **Configurer les variables d'environnement** :

```bash
BILLING_MODE=stripe
STRIPE_PUBLIC_KEY=pk_live_xxx
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_MONTHLY=price_xxx_monthly
STRIPE_PRICE_YEARLY=price_xxx_yearly
```

5. **Configurer le Webhook** (pour les événements Stripe) :
   - URL : `https://votre-domaine.com/api/stripe/webhook`
   - Événements à écouter :
     - `checkout.session.completed`
     - `customer.subscription.updated`
     - `customer.subscription.deleted`
     - `invoice.payment_succeeded`
     - `invoice.payment_failed`

6. **Implémenter le handler webhook** (TODO) :
   - Parser les événements Stripe
   - Mettre à jour `subscriptions_state` dans SQLite
   - Gérer les renouvellements/annulations

### Code d'intégration Stripe (exemple)

```python
# À implémenter dans un fichier app/billing.py
import stripe
from core.config import get_config

config = get_config()
stripe.api_key = config.billing.stripe_secret_key

def create_checkout_session(user_id: str, plan: str) -> str:
    \"\"\"Créer une session Stripe Checkout.\"\"\"
    price_id = (
        config.billing.stripe_price_monthly 
        if plan == "monthly_9_99" 
        else config.billing.stripe_price_yearly
    )
    
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{'price': price_id, 'quantity': 1}],
        mode='subscription',
        success_url='https://votre-domaine.com/success?session_id={CHECKOUT_SESSION_ID}',
        cancel_url='https://votre-domaine.com/cancel',
        metadata={'user_id': user_id, 'plan': plan}
    )
    return session.url
```

---

## Images Landing Page

Pour un rendu optimal de la landing page, ajoutez les images suivantes :

```
assets/landing/
├── world_map.png     # Fond section "Marchés couverts" (1920x1080, style dark)
└── market_bg.png     # Fond hero section (1920x1080, chart/glow style)
```

**Spécifications recommandées :**
- Format : PNG ou JPEG
- Résolution : 1920x1080 minimum
- Style : Dark avec accents verts (#10B981)
- world_map.png : Carte du monde avec points lumineux (style tech)
- market_bg.png : Graphique financier avec effet glow

Si les images ne sont pas présentes, un fallback gradient sera utilisé.

---

## Conformité

Tous les textes de l'UI passent par un filtre de conformité:
- Aucun conseil financier
- Aucune recommandation d'action
- Vocabulaire neutre et statistique

---

## Licence

Usage personnel et éducatif uniquement.
