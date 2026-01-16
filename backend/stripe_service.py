"""
Stripe Service for MarketGPS
Handles all Stripe API interactions
"""

import os
import logging
from typing import Optional, Dict, Any

import stripe

logger = logging.getLogger(__name__)


class StripeService:
    """
    Service class for Stripe operations.
    """
    
    def __init__(self):
        """Initialize Stripe with API key."""
        self.api_key = os.environ.get('STRIPE_SECRET_KEY')
        self.webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        if not self.api_key:
            logger.warning("STRIPE_SECRET_KEY not set")
        else:
            stripe.api_key = self.api_key
    
    def create_customer(self, email: str, user_id: str) -> str:
        """
        Create a new Stripe customer.
        
        Returns: Stripe customer ID
        """
        try:
            customer = stripe.Customer.create(
                email=email,
                metadata={
                    'supabase_user_id': user_id,
                }
            )
            logger.info(f"Created Stripe customer: {customer.id}")
            return customer.id
        except stripe.error.StripeError as e:
            logger.error(f"Stripe customer creation error: {e}")
            raise
    
    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        client_reference_id: str,
    ) -> str:
        """
        Create a Stripe Checkout Session for subscription.
        
        Returns: Checkout session URL
        """
        try:
            session = stripe.checkout.Session.create(
                customer=customer_id,
                mode='subscription',
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                client_reference_id=client_reference_id,
                allow_promotion_codes=True,
                billing_address_collection='required',
                metadata={
                    'supabase_user_id': client_reference_id,
                }
            )
            logger.info(f"Created checkout session: {session.id}")
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Checkout session creation error: {e}")
            raise
    
    def create_portal_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> str:
        """
        Create a Stripe Customer Portal session.
        
        Returns: Portal session URL
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            logger.info(f"Created portal session for customer: {customer_id}")
            return session.url
        except stripe.error.StripeError as e:
            logger.error(f"Portal session creation error: {e}")
            raise
    
    def get_subscription(self, subscription_id: str) -> Optional[Dict[str, Any]]:
        """
        Get subscription details from Stripe.
        """
        try:
            subscription = stripe.Subscription.retrieve(
                subscription_id,
                expand=['items.data.price']
            )
            return {
                'id': subscription.id,
                'status': subscription.status,
                'current_period_end': subscription.current_period_end,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'items': {
                    'data': [
                        {
                            'price': {
                                'id': item.price.id,
                                'recurring': {
                                    'interval': item.price.recurring.interval if item.price.recurring else None,
                                }
                            }
                        }
                        for item in subscription['items']['data']
                    ]
                }
            }
        except stripe.error.StripeError as e:
            logger.error(f"Get subscription error: {e}")
            return None
    
    def cancel_subscription(self, subscription_id: str) -> bool:
        """
        Cancel a subscription at period end.
        """
        try:
            stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True,
            )
            logger.info(f"Subscription scheduled for cancellation: {subscription_id}")
            return True
        except stripe.error.StripeError as e:
            logger.error(f"Cancel subscription error: {e}")
            return False
    
    def verify_webhook(
        self, 
        payload: bytes, 
        signature: str
    ) -> Optional[Dict[str, Any]]:
        """
        Verify Stripe webhook signature and return event.
        
        Returns: Stripe event dict or None if verification fails
        """
        if not self.webhook_secret:
            logger.error("STRIPE_WEBHOOK_SECRET not configured")
            return None
        
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret,
            )
            return event
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Webhook signature verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Webhook verification error: {e}")
            return None
