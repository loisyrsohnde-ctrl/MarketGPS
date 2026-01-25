# MarketGPS Billing Configuration

## Environment Variables

Add these to your Dokploy environment (or `.env` file for local development):

### Required - Stripe

```bash
# Stripe API Keys
STRIPE_SECRET_KEY=sk_live_xxx          # or sk_test_xxx for testing
STRIPE_WEBHOOK_SECRET=whsec_xxx        # From Stripe dashboard > Webhooks

# Stripe Price IDs (create products in Stripe dashboard first)
STRIPE_PRICE_ID_MONTHLY=price_xxx      # Monthly subscription price
STRIPE_PRICE_ID_ANNUAL=price_xxx       # Annual subscription price
```

### Optional - Systeme.io (Marketing Only)

```bash
# Systeme.io API (for marketing automation - does NOT control access)
SYSTEMEIO_API_KEY=xxx

# Tag IDs (create in Systeme.io dashboard first)
SYSTEMEIO_TAG_MONTHLY=xxx
SYSTEMEIO_TAG_ANNUAL=xxx
SYSTEMEIO_TAG_ACTIVE=xxx
SYSTEMEIO_TAG_PAYMENT_FAILED=xxx
SYSTEMEIO_TAG_CHURNED=xxx
SYSTEMEIO_TAG_TRIAL=xxx
```

### Optional - Configuration

```bash
# Grace period for past_due status (hours)
BILLING_GRACE_PERIOD_HOURS=48

# Frontend URL for redirects
FRONTEND_URL=https://app.marketgps.online
```

## Stripe Dashboard Setup

### 1. Create Products

1. Go to Stripe Dashboard > Products
2. Create "MarketGPS Pro Monthly"
   - Price: €9.99/month
   - Copy the Price ID → `STRIPE_PRICE_ID_MONTHLY`
3. Create "MarketGPS Pro Annual"
   - Price: €99.99/year
   - Copy the Price ID → `STRIPE_PRICE_ID_ANNUAL`

### 2. Configure Webhook

1. Go to Stripe Dashboard > Developers > Webhooks
2. Add endpoint: `https://api.marketgps.online/api/billing/stripe/webhook`
3. Select events:
   - `checkout.session.completed`
   - `invoice.paid`
   - `invoice.payment_failed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `charge.refunded`
   - `charge.dispute.created`
4. Copy the Signing Secret → `STRIPE_WEBHOOK_SECRET`

### 3. Configure Customer Portal

1. Go to Stripe Dashboard > Settings > Billing > Customer Portal
2. Enable portal
3. Configure allowed actions:
   - Update payment method
   - Cancel subscription
   - View invoices

## Testing

### Test Cards

- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- Requires auth: `4000 0025 0000 3155`

### Test Webhook Locally

Use Stripe CLI:

```bash
# Install Stripe CLI
brew install stripe/stripe-cli/stripe

# Login
stripe login

# Forward webhooks to local
stripe listen --forward-to localhost:8501/api/billing/stripe/webhook

# Copy the webhook secret and set STRIPE_WEBHOOK_SECRET
```

### Manual Test Checklist

- [ ] Signup → Select plan → Checkout → Success → Dashboard (active)
- [ ] Subscription renewal (wait or trigger via Stripe dashboard)
- [ ] Payment failed → past_due → grace period active
- [ ] Cancel subscription → status=canceled after period end
- [ ] Refund → immediate access revoke
- [ ] Dispute → immediate access revoke

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                │
│  /signup → /billing/checkout → Stripe Checkout → /billing/success│
│                                                                 │
│  useSubscription() hook polls /api/billing/me                   │
│  SubscriptionGate component blocks premium content              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND                                 │
│                                                                 │
│  POST /api/billing/checkout-session                             │
│  POST /api/billing/stripe/webhook (signature verified)          │
│  GET  /api/billing/me                                           │
│  POST /api/billing/portal-session                               │
│                                                                 │
│  SQLite: subscriptions, stripe_events (idempotency)             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      STRIPE (Source of Truth)                   │
│                                                                 │
│  Customers, Subscriptions, Invoices, Payments                   │
│  Webhooks → Backend for state sync                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTEME.IO (Marketing Only)                  │
│                                                                 │
│  Contact sync, Tag management                                   │
│  ⚠️ NEVER decides access - purely for marketing automation      │
└─────────────────────────────────────────────────────────────────┘
```

## Subscription Status Flow

```
checkout.session.completed
         │
         ▼
    status=active ◀──────── invoice.paid
         │
         │ (payment fails)
         ▼
    status=past_due ───────► [48h grace period]
         │                          │
         │ (payment succeeds)       │ (grace expires)
         ▼                          ▼
    status=active            status=inactive
                                    │
                                    │ (subscription deleted)
                                    ▼
                             status=canceled
```
