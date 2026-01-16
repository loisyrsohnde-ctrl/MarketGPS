# MarketGPS - Manual Testing Checklist

## Prerequisites

- [ ] Supabase project created and configured
- [ ] Stripe account with test mode active
- [ ] Environment variables set in `.env`
- [ ] SQL migrations executed in Supabase

---

## 1. Authentication Flow

### 1.1 Sign Up
- [ ] Navigate to signup page from landing
- [ ] Enter valid email, password (8+ chars), confirm password
- [ ] Click "Créer mon compte"
- [ ] See success message "Vérifiez votre email"
- [ ] Receive confirmation email (check spam)
- [ ] Check Supabase Dashboard > Authentication > Users

### 1.2 Email Confirmation
- [ ] Click link in confirmation email
- [ ] Redirected to app with success message
- [ ] Session is created (user is logged in)
- [ ] Check profiles table has new row
- [ ] Check entitlements table has new row with plan=FREE

### 1.3 Login
- [ ] Navigate to login page
- [ ] Enter credentials of confirmed user
- [ ] Click "Se connecter"
- [ ] Redirected to dashboard
- [ ] Sidebar shows user info

### 1.4 Forgot Password
- [ ] Click "Mot de passe oublié?" on login page
- [ ] Enter email
- [ ] Click "Envoyer le lien"
- [ ] Receive reset email
- [ ] Click link in email
- [ ] Enter new password (8+ chars)
- [ ] Submit and see success
- [ ] Login with new password works

### 1.5 Logout
- [ ] Click "Déconnexion" in sidebar
- [ ] Redirected to landing page
- [ ] Session cleared (can't access protected pages)

---

## 2. Subscription Flow (Stripe)

### 2.1 View Pricing
- [ ] Navigate to billing page (from sidebar or landing)
- [ ] See Monthly (9.99€) and Annual (50€) options
- [ ] FREE vs PREMIUM comparison visible

### 2.2 Monthly Subscription
- [ ] Click "S'abonner Mensuel"
- [ ] Redirected to Stripe Checkout
- [ ] Use test card: `4242 4242 4242 4242`
- [ ] Complete payment
- [ ] Redirected back to app with success=1
- [ ] Entitlements updated: plan=MONTHLY, status=active
- [ ] Daily limit increased to 200

### 2.3 Annual Subscription
- [ ] Same flow as monthly with yearly plan
- [ ] Verify plan=YEARLY in entitlements

### 2.4 Customer Portal
- [ ] Click "Gérer mon abonnement"
- [ ] Redirected to Stripe Portal
- [ ] Can view invoices
- [ ] Can update payment method
- [ ] Can cancel subscription

### 2.5 Subscription Cancellation
- [ ] Cancel subscription via portal
- [ ] Webhook fires: customer.subscription.deleted
- [ ] Entitlements updated: plan=FREE, status=canceled
- [ ] Daily limit reduced to 10

---

## 3. Feature Gating

### 3.1 FREE User Restrictions
- [ ] Login as FREE user
- [ ] Africa markets show upgrade prompt
- [ ] Watchlist shows upgrade prompt
- [ ] Export CSV blocked
- [ ] Daily limit = 10 requests

### 3.2 PAID User Access
- [ ] Login as PAID user
- [ ] Africa markets accessible
- [ ] Watchlist accessible
- [ ] Export CSV works
- [ ] Daily limit = 200 requests

### 3.3 Usage Limits
- [ ] Make requests until limit reached
- [ ] See "quota exceeded" message
- [ ] Next day, quota resets

---

## 4. Webhook Verification

### 4.1 Local Testing (Stripe CLI)
```bash
stripe listen --forward-to localhost:8000/billing/webhook
```

- [ ] checkout.session.completed → entitlements updated
- [ ] invoice.paid → current_period_end updated
- [ ] customer.subscription.updated → status synced
- [ ] customer.subscription.deleted → plan=FREE

### 4.2 Production Webhook
- [ ] Webhook endpoint in Stripe Dashboard
- [ ] Events: checkout, invoice, subscription
- [ ] Signing secret configured
- [ ] Test event from Dashboard works

---

## 5. Error Handling

### 5.1 Auth Errors
- [ ] Invalid credentials → error message
- [ ] Unconfirmed email → "confirm your email" message
- [ ] Weak password → "minimum 8 chars" message
- [ ] Email already registered → appropriate error

### 5.2 Billing Errors
- [ ] Card declined → Stripe error shown
- [ ] Backend unreachable → connection error
- [ ] Invalid token → "please login" message

---

## 6. UI/UX Verification

### 6.1 Dark Theme
- [ ] All pages use dark background
- [ ] Text is readable (AA contrast)
- [ ] Green accent color consistent
- [ ] No white/light elements

### 6.2 Responsive
- [ ] Pages work on mobile viewport
- [ ] Forms are centered and readable
- [ ] Buttons are tappable

### 6.3 Loading States
- [ ] Spinner during API calls
- [ ] Button disabled during submission
- [ ] Error messages are clear

---

## 7. Security Checks

- [ ] Passwords never stored locally
- [ ] SERVICE_ROLE_KEY only in backend
- [ ] Webhook signature verified
- [ ] Tokens expire and refresh
- [ ] RLS policies prevent unauthorized access

---

## Test Cards for Stripe

| Card Number | Scenario |
|-------------|----------|
| 4242 4242 4242 4242 | Success |
| 4000 0000 0000 9995 | Declined |
| 4000 0027 6000 3184 | Requires 3DS |
| 4000 0000 0000 0341 | Attach fails |

Use any future date for expiry and any 3-digit CVC.
