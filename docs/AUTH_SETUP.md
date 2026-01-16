# MarketGPS Authentication & Billing Setup Guide

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Squarespace   │     │    Streamlit    │     │    FastAPI      │
│  afristocks.eu  │────▶│ app.afristocks  │────▶│ api.afristocks  │
│   (Marketing)   │     │   (Frontend)    │     │   (Backend)     │
└─────────────────┘     └────────┬────────┘     └────────┬────────┘
                                 │                       │
                                 ▼                       ▼
                        ┌─────────────────────────────────────────┐
                        │              SUPABASE                    │
                        │  ┌─────────┐  ┌─────────┐  ┌─────────┐  │
                        │  │  Auth   │  │Postgres │  │   RLS   │  │
                        │  │ (Users) │  │ (Data)  │  │(Security│  │
                        │  └─────────┘  └─────────┘  └─────────┘  │
                        └─────────────────────────────────────────┘
                                                │
                                                ▼
                        ┌─────────────────────────────────────────┐
                        │              STRIPE                      │
                        │    Checkout | Portal | Webhooks         │
                        └─────────────────────────────────────────┘
```

## Setup Steps

### 1. Supabase Configuration

#### 1.1 Create Project
1. Go to [supabase.com](https://supabase.com)
2. Create new project
3. Note your **Project URL** and **API Keys**

#### 1.2 Run SQL Migrations
Execute these files in order in **SQL Editor**:

```bash
supabase/sql/001_tables.sql      # Create tables
supabase/sql/002_rls_policies.sql # Enable RLS
supabase/sql/003_triggers.sql     # Auto-create profiles
```

#### 1.3 Configure Auth Settings
Go to **Authentication > URL Configuration**:

- **Site URL**: `https://app.afristocks.eu`
- **Redirect URLs**:
  - `https://app.afristocks.eu/auth/callback`
  - `https://app.afristocks.eu/reset-password`
  - `http://localhost:8501/auth/callback` (dev)
  - `http://localhost:8501/reset-password` (dev)

#### 1.4 Enable Email Confirmations
Go to **Authentication > Email Templates**:
- Enable "Confirm signup"
- Customize email templates if needed

### 2. Stripe Configuration

#### 2.1 Create Products & Prices
In [Stripe Dashboard](https://dashboard.stripe.com):

1. Go to **Products > Add Product**
2. Create "MarketGPS Monthly":
   - Price: €9.99/month
   - Note the `price_xxx` ID
3. Create "MarketGPS Annual":
   - Price: €50/year
   - Note the `price_xxx` ID

#### 2.2 Configure Webhook
1. Go to **Developers > Webhooks**
2. Add endpoint: `https://api.afristocks.eu/billing/webhook`
3. Select events:
   - `checkout.session.completed`
   - `invoice.paid`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
4. Note the **Signing secret** (`whsec_xxx`)

#### 2.3 Customer Portal
1. Go to **Settings > Billing > Customer portal**
2. Enable and configure options

### 3. Environment Variables

Create `.env` files:

**Streamlit App (.env)**:
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
BACKEND_API_BASE_URL=https://api.afristocks.eu
APP_BASE_URL=https://app.afristocks.eu
```

**Backend API (.env)**:
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_MONTHLY_ID=price_xxx
STRIPE_PRICE_YEARLY_ID=price_xxx
FRONTEND_SUCCESS_URL=https://app.afristocks.eu/billing?success=1
FRONTEND_CANCEL_URL=https://app.afristocks.eu/billing?canceled=1
```

### 4. Deployment

#### 4.1 Backend (FastAPI)
Deploy to Railway, Render, or Fly.io:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port $PORT
```

#### 4.2 Frontend (Streamlit)
Deploy to Streamlit Cloud or your own server:

```bash
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

### 5. Testing Checklist

#### Auth Flow
- [ ] Sign up with new email
- [ ] Receive confirmation email
- [ ] Click confirmation link
- [ ] Login with confirmed account
- [ ] Forgot password request
- [ ] Reset password via email link
- [ ] Logout

#### Billing Flow
- [ ] View pricing page
- [ ] Click subscribe button
- [ ] Complete Stripe Checkout
- [ ] Verify webhook updates entitlements
- [ ] Access premium features
- [ ] Open customer portal
- [ ] Cancel subscription
- [ ] Verify downgrade to FREE

#### Security
- [ ] Cannot access premium without subscription
- [ ] Cannot modify own entitlements via API
- [ ] Webhook signature verification works
- [ ] Token refresh works automatically

## Troubleshooting

### Email not received
1. Check spam folder
2. Verify Supabase email settings
3. Check Supabase logs

### Webhook not working
1. Verify endpoint URL
2. Check webhook signing secret
3. Check backend logs
4. Use Stripe CLI for local testing:
   ```bash
   stripe listen --forward-to localhost:8000/billing/webhook
   ```

### Auth errors
1. Check Supabase URL/key
2. Verify redirect URLs
3. Check browser console for CORS errors

## Security Notes

⚠️ **Never expose**:
- `SUPABASE_SERVICE_ROLE_KEY`
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`

These should only be in the backend `.env` file.
