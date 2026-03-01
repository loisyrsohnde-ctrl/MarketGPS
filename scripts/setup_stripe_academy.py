#!/usr/bin/env python3
"""
Setup QuantAI Academy product and coupon in Stripe.

Usage:
    # Option 1: Set env var then run
    export STRIPE_SECRET_KEY=sk_live_xxxxx
    python3 scripts/setup_stripe_academy.py

    # Option 2: Pass as argument
    python3 scripts/setup_stripe_academy.py sk_live_xxxxx

This script creates:
1. Product "QuantAI Academy" (one-time, 499 EUR)
2. Coupon "Academy Annual Subscriber Discount" (300 EUR off = 199 EUR final)

After running, add the output IDs to your environment variables:
    STRIPE_PRICE_ID_ACADEMY=price_xxxxx
    STRIPE_COUPON_ID_ACADEMY_ANNUAL=coupon_xxxxx
"""

import os
import sys

def main():
    import stripe

    # Get API key
    api_key = None
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    else:
        api_key = os.environ.get("STRIPE_SECRET_KEY")

    if not api_key:
        print("ERROR: STRIPE_SECRET_KEY not found.")
        print("Usage: python3 scripts/setup_stripe_academy.py <stripe_secret_key>")
        print("   or: export STRIPE_SECRET_KEY=sk_live_xxx && python3 scripts/setup_stripe_academy.py")
        sys.exit(1)

    stripe.api_key = api_key
    mode = "LIVE" if api_key.startswith("sk_live") else "TEST"
    print(f"\n{'='*60}")
    print(f"  Stripe Academy Setup ({mode} mode)")
    print(f"{'='*60}\n")

    # ── Step 1: Create Product ──────────────────────────────────────────
    print("1. Creating product 'QuantAI Academy'...")
    try:
        product = stripe.Product.create(
            name="QuantAI Academy",
            description="Formation complete en Trading Algorithmique & Intelligence Artificielle - 10 modules, acces a vie",
            metadata={
                "type": "academy",
                "access": "lifetime",
            },
        )
        print(f"   Product created: {product.id}")
    except stripe.error.StripeError as e:
        print(f"   ERROR creating product: {e}")
        sys.exit(1)

    # ── Step 2: Create Price (499 EUR one-time) ─────────────────────────
    print("2. Creating price (499 EUR one-time)...")
    try:
        price = stripe.Price.create(
            product=product.id,
            unit_amount=49900,  # 499.00 EUR in cents
            currency="eur",
            metadata={
                "plan": "academy",
                "type": "one_time",
            },
        )
        print(f"   Price created: {price.id}")
    except stripe.error.StripeError as e:
        print(f"   ERROR creating price: {e}")
        sys.exit(1)

    # ── Step 3: Create Coupon (300 EUR off) ─────────────────────────────
    print("3. Creating coupon (300 EUR off -> 199 EUR final)...")
    try:
        coupon = stripe.Coupon.create(
            name="Academy Annual Subscriber Discount",
            amount_off=30000,  # 300.00 EUR in cents
            currency="eur",
            duration="once",
            metadata={
                "target": "annual_subscribers",
                "product": "academy",
            },
        )
        print(f"   Coupon created: {coupon.id}")
    except stripe.error.StripeError as e:
        print(f"   ERROR creating coupon: {e}")
        sys.exit(1)

    # ── Summary ─────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Setup complete!")
    print(f"{'='*60}\n")
    print(f"  Add these to your environment variables (Dokploy):\n")
    print(f"  STRIPE_PRICE_ID_ACADEMY={price.id}")
    print(f"  STRIPE_COUPON_ID_ACADEMY_ANNUAL={coupon.id}")
    print(f"\n{'='*60}\n")

    # Also check webhook endpoint
    print("4. Checking webhook endpoints...")
    try:
        endpoints = stripe.WebhookEndpoint.list(limit=10)
        if endpoints.data:
            for ep in endpoints.data:
                status_icon = "OK" if ep.status == "enabled" else "WARN"
                print(f"   [{status_icon}] {ep.url}")
                if "/api/billing/stripe/webhook" in ep.url:
                    print(f"         ^ Correct endpoint")
                elif "/billing/webhook" in ep.url and "/api/" not in ep.url:
                    print(f"         ^ WARNING: Old endpoint! Should be /api/billing/stripe/webhook")
        else:
            print("   No webhook endpoints found. You need to create one:")
            print("   URL: https://api.marketgps.online/api/billing/stripe/webhook")
    except stripe.error.StripeError as e:
        print(f"   Could not list webhooks: {e}")

    print()


if __name__ == "__main__":
    main()
