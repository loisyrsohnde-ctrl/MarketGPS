# Audit Billing & Stripe

**Date**: 2025-01-27  
**Status**: Problèmes critiques identifiés

---

## Résumé des Problèmes

| Problème | Sévérité | Impact |
|----------|----------|--------|
| Frontend web checkout non implémenté | 🔴 Critique | Paiement impossible |
| Backend user_id hardcodé "anonymous" | 🔴 Critique | Checkout ne lie pas au user |
| Mobile endpoint inexistant | ✅ Corrigé | Était `/api/billing/me` |
| Clé Stripe vide sur mobile | 🟡 Moyen | Pas de paiement natif |

---

## 1. Configuration Stripe

### Variables d'environnement requises

#### Backend (`backend/env.example`)
```bash
STRIPE_SECRET_KEY=sk_live_xxx ou sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_MONTHLY_ID=price_xxx  # ID du produit mensuel
STRIPE_PRICE_YEARLY_ID=price_xxx   # ID du produit annuel
FRONTEND_SUCCESS_URL=https://app.marketgps.online/billing?success=1
FRONTEND_CANCEL_URL=https://app.marketgps.online/billing?canceled=1
```

#### Frontend Web (`frontend/.env.local`)
```bash
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxx ou pk_test_xxx
```

#### Mobile (`mobile/.env`)
```bash
EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxx  # Actuellement VIDE!
```

---

## 2. Flux Checkout - État Actuel

### Backend Endpoints

#### POST `/api/billing/checkout-session` 

**Fichier**: `backend/main.py:305-379`

```python
@app.post("/billing/checkout-session")
async def create_checkout_session(plan: str = Body(...)):
    # PROBLÈME CRITIQUE:
    user_id = "anonymous"  # Ligne 319 - HARDCODÉ!
    
    # Le reste fonctionne...
    price_id = os.environ.get("STRIPE_PRICE_MONTHLY_ID")
    
    session = stripe.checkout.Session.create(
        success_url=success_url,
        cancel_url=cancel_url,
        # ...
    )
```

**Problème**: Le `user_id` est toujours "anonymous", donc l'abonnement ne sera jamais lié au bon utilisateur.

**Fix requis**:
```python
from backend.security import get_current_user_id

@app.post("/api/billing/checkout-session")
async def create_checkout_session(
    plan: str = Body(...),
    user_id: str = Depends(get_current_user_id)  # FIX
):
    # user_id maintenant correct
```

#### POST `/api/billing/webhook`

**Fichier**: `backend/main.py:463-516`

```python
@app.post("/billing/webhook")
async def stripe_webhook(request: Request):
    # Verify signature
    sig = request.headers.get("stripe-signature")
    event = stripe.Webhook.construct_event(payload, sig, webhook_secret)
    
    # Handle events
    if event["type"] == "checkout.session.completed":
        # Update entitlements in Supabase
```

**Status**: ✅ Implémenté correctement

---

## 3. Frontend Web - État Actuel

### Page Billing

**Fichier**: `frontend/app/settings/billing/page.tsx:42-49`

```typescript
const handleSubscribe = async (plan: 'monthly' | 'yearly') => {
  setLoading(plan);
  // PROBLÈME: Non implémenté!
  // In real implementation, this would call api.createCheckoutSession
  // For demo, just simulate
  await new Promise((resolve) => setTimeout(resolve, 2000));
  setLoading(null);
  // window.location.href = checkout_url;
};
```

**Problème**: Le checkout est une simulation, il n'appelle jamais l'API!

**Fix requis**:
```typescript
const handleSubscribe = async (plan: 'monthly' | 'yearly') => {
  setLoading(plan);
  try {
    const { data: session } = await supabase.auth.getSession();
    const token = session?.session?.access_token;
    
    if (!token) {
      router.push('/login?redirect=/settings/billing');
      return;
    }
    
    const { url } = await api.createCheckoutSession(plan, token);
    window.location.href = url;
  } catch (error) {
    console.error('Checkout error:', error);
    // Show error to user
  } finally {
    setLoading(null);
  }
};
```

### API Client

**Fichier**: `frontend/lib/api.ts:284-300`

```typescript
async createCheckoutSession(
  plan: 'monthly' | 'yearly',
  token?: string
): Promise<{ url: string }> {
  return apiFetch('/api/billing/checkout-session', {
    method: 'POST',
    body: JSON.stringify({ plan }),
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });
}
```

**Status**: ✅ Méthode existe mais n'est pas appelée

---

## 4. Base de Données - Entitlements

### Table Supabase

**Fichier**: `supabase/sql/001_tables.sql`

```sql
CREATE TABLE IF NOT EXISTS entitlements (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  stripe_customer_id TEXT,
  stripe_subscription_id TEXT,
  plan TEXT DEFAULT 'FREE' CHECK (plan IN ('FREE', 'MONTHLY', 'YEARLY')),
  status TEXT DEFAULT 'inactive' CHECK (status IN ('active', 'past_due', 'canceled', 'inactive', 'trialing')),
  current_period_end TIMESTAMPTZ,
  daily_requests_limit INTEGER DEFAULT 10,
  daily_requests_used INTEGER DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

**Status**: ✅ Schema correct

### Mise à jour par Webhook

**Fichier**: `backend/supabase_admin.py:64-80`

```python
def update_entitlements(self, user_id: str, updates: Dict[str, Any]) -> bool:
    """Update user entitlements. Used by Stripe webhooks."""
    response = self.client.table('entitlements').upsert({
        'user_id': user_id,
        **updates
    }).execute()
```

**Status**: ✅ Correct

---

## 5. Checklist Stripe Ready

### Configuration Dokploy/VPS

```bash
# Dans les variables d'environnement du backend
STRIPE_SECRET_KEY=sk_live_xxxxx           # Clé secrète Stripe
STRIPE_WEBHOOK_SECRET=whsec_xxxxx         # Secret du webhook
STRIPE_PRICE_MONTHLY_ID=price_xxxxx       # ID prix mensuel
STRIPE_PRICE_YEARLY_ID=price_xxxxx        # ID prix annuel
FRONTEND_SUCCESS_URL=https://app.marketgps.online/billing?success=1
FRONTEND_CANCEL_URL=https://app.marketgps.online/billing?canceled=1

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...               # Clé service (pas anon)
```

### Webhook Stripe Dashboard

1. Aller sur https://dashboard.stripe.com/webhooks
2. Ajouter endpoint: `https://api.marketgps.online/api/billing/webhook`
3. Événements à écouter:
   - `checkout.session.completed`
   - `invoice.paid`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Copier le `whsec_xxx` dans `STRIPE_WEBHOOK_SECRET`

### Produits Stripe

1. Créer produit "MarketGPS Pro" dans Stripe Dashboard
2. Créer prix mensuel → copier `price_xxx` dans `STRIPE_PRICE_MONTHLY_ID`
3. Créer prix annuel → copier `price_xxx` dans `STRIPE_PRICE_YEARLY_ID`

---

## 6. Correctifs Requis

### Backend (Priorité 1)

**Fichier**: `backend/main.py`

```python
# Ligne 319 - Remplacer:
user_id = "anonymous"

# Par:
from backend.security import get_current_user_id
# Dans la signature de la fonction, ajouter:
user_id: str = Depends(get_current_user_id)
```

### Frontend Web (Priorité 2)

**Fichier**: `frontend/app/settings/billing/page.tsx`

Implémenter le vrai checkout (voir section 3).

### Mobile (Priorité 3)

Déjà corrigé: endpoint changé de `/api/billing/me` à `/users/entitlements`.

---

## 7. Test de Validation

1. **Pré-requis**:
   - Variables d'environnement configurées
   - Webhook Stripe configuré
   - Produits/prix créés

2. **Test checkout**:
   ```bash
   # Login et récupérer token
   # Appeler checkout
   curl -X POST https://api.marketgps.online/api/billing/checkout-session \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"plan": "monthly"}'
   
   # Devrait retourner: {"url": "https://checkout.stripe.com/..."}
   ```

3. **Test webhook** (local avec Stripe CLI):
   ```bash
   stripe listen --forward-to localhost:8000/api/billing/webhook
   stripe trigger checkout.session.completed
   ```

---

*Rapport généré lors de l'audit MarketGPS Billing*
