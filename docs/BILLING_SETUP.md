# MarketGPS Billing Setup Guide

## Overview

MarketGPS uses Stripe for subscription billing with two plans:
- **Monthly**: 9.99€/month
- **Annual**: 99.99€/year (saves ~17%)

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend    │────▶│   SQLite    │
│  (Next.js)  │     │  (FastAPI)   │     │ (subscriptions)
└─────────────┘     └──────────────┘     └─────────────┘
       │                   ▲
       │                   │ Webhook
       ▼                   │
┌─────────────┐     ┌──────────────┐
│   Stripe    │────▶│   Stripe     │
│  Checkout   │     │  Dashboard   │
└─────────────┘     └──────────────┘
```

## Environment Variables

### Backend (.env or Dokploy)

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_live_xxx...
STRIPE_WEBHOOK_SECRET=whsec_xxx...

# Price IDs (get from Stripe Dashboard > Products)
STRIPE_PRICE_ID_MONTHLY=price_xxx...
STRIPE_PRICE_ID_ANNUAL=price_xxx...

# Alternative naming (also supported for backward compatibility)
# STRIPE_PRICE_MONTHLY_ID=price_xxx...
# STRIPE_PRICE_YEARLY_ID=price_xxx...

# Frontend URL (for Checkout redirects)
FRONTEND_URL=https://app.marketgps.online

# Grace period for past_due subscriptions (default: 48 hours)
BILLING_GRACE_PERIOD_HOURS=48

# Supabase (required for user authentication)
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJxxx...
SUPABASE_JWT_SECRET=xxx...
```

### Frontend (.env.local or Vercel)

```bash
NEXT_PUBLIC_API_URL=https://api.marketgps.online
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJxxx...
```

## Stripe Dashboard Setup

### 1. Create Products

1. Go to https://dashboard.stripe.com/products
2. Click **"+ Add product"**

**Product 1: Monthly**
- Name: `MarketGPS Pro Monthly`
- Pricing: `9.99 EUR`, Recurring, Monthly
- Save and copy the **Price ID**

**Product 2: Annual**
- Name: `MarketGPS Pro Annual`
- Pricing: `99.99 EUR`, Recurring, Yearly
- Save and copy the **Price ID**

### 2. Configure Webhook

1. Go to https://dashboard.stripe.com/webhooks
2. Click **"+ Add endpoint"**
3. Endpoint URL: `https://api.marketgps.online/api/billing/stripe/webhook`
4. Select events:
   - `checkout.session.completed`
   - `invoice.paid`
   - `invoice.payment_failed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `charge.refunded`
   - `charge.dispute.created`
5. Click **"Add endpoint"**
6. Copy the **Signing secret** (starts with `whsec_`)

### 3. Configure Customer Portal

1. Go to https://dashboard.stripe.com/settings/billing/portal
2. Enable:
   - Update payment method
   - View invoice history
   - Cancel subscription
3. Configure cancellation options as needed

## API Endpoints

### POST /api/billing/checkout-session
Create a Stripe Checkout session.

**Request:**
```json
{
  "plan": "monthly" | "annual"
}
```

**Response:**
```json
{
  "url": "https://checkout.stripe.com/..."
}
```

### GET /api/billing/me
Get current subscription status.

**Response:**
```json
{
  "user_id": "uuid",
  "plan": "free" | "monthly" | "annual",
  "status": "active" | "past_due" | "canceled" | "inactive",
  "current_period_end": "2025-02-15T00:00:00Z",
  "cancel_at_period_end": false,
  "is_active": true,
  "grace_period_remaining_hours": null
}
```

### POST /api/billing/portal-session
Create a Stripe Customer Portal session.

**Response:**
```json
{
  "url": "https://billing.stripe.com/..."
}
```

### POST /api/billing/stripe/webhook
Stripe webhook endpoint (signature-verified).

## User Flow

1. **New User Signup**
   - User creates account via Supabase Auth
   - Redirected to `/billing/choose-plan`
   - Selects plan → Stripe Checkout

2. **Payment Success**
   - Stripe redirects to `/billing/success?session_id=xxx`
   - Page polls `/api/billing/me` until `is_active=true`
   - User redirected to `/dashboard`

3. **Accessing Protected Content**
   - All routes under `/dashboard/*` check subscription
   - No active subscription → redirect to `/billing/choose-plan`
   - Settings (`/settings/*`) bypass paywall

4. **Managing Subscription**
   - User goes to `/settings/billing`
   - Clicks "Manage on Stripe" → Customer Portal
   - Can cancel, change payment method, view invoices

## Testing

### Test Mode
1. Use Stripe test keys (`sk_test_xxx`)
2. Use test card: `4242 4242 4242 4242`
3. Any future expiry, any CVC

### Test Scenarios
1. ✅ New user → choose plan → checkout → access granted
2. ✅ Payment failed → status=past_due → 48h grace period
3. ✅ Cancel subscription → access until period end
4. ✅ Duplicate webhook → idempotent (no double processing)

## Troubleshooting

### Webhook returning 400
- Check `STRIPE_WEBHOOK_SECRET` matches dashboard
- Verify endpoint URL is correct
- Check backend logs for signature errors

### User stuck on "Activation en cours..."
- Check webhook is receiving events (Stripe Dashboard)
- Verify backend can write to SQLite
- Check `/api/billing/me` response

### 503 "Billing services not configured"
- Ensure `STRIPE_SECRET_KEY` is set
- Restart backend after adding env vars

## Database Schema

```sql
-- subscriptions table
CREATE TABLE subscriptions (
    user_id TEXT PRIMARY KEY,
    stripe_customer_id TEXT,
    stripe_subscription_id TEXT,
    plan TEXT DEFAULT 'free',
    status TEXT DEFAULT 'inactive',
    current_period_start TEXT,
    current_period_end TEXT,
    cancel_at_period_end INTEGER DEFAULT 0,
    canceled_at TEXT,
    grace_period_end TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);

-- stripe_events table (idempotency)
CREATE TABLE stripe_events (
    event_id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    processed_at TEXT DEFAULT (datetime('now')),
    payload_hash TEXT,
    status TEXT DEFAULT 'processed'
);
```

## Security Notes

- Webhook signature verification is mandatory
- JWT tokens verified via Supabase
- No user data exposed without authentication
- Grace period protects against payment hiccups
