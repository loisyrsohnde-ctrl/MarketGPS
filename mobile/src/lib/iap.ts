/**
 * MarketGPS - Apple In-App Purchase Service
 * Uses react-native-iap v14 for iOS subscription management
 */

import { Platform } from 'react-native';
import {
  initConnection,
  endConnection,
  fetchProducts,
  requestPurchase,
  getAvailablePurchases,
  finishTransaction,
  purchaseUpdatedListener,
  purchaseErrorListener,
  isUserCancelledError,
  type Purchase,
  type ProductSubscription,
  type FetchProductsResult,
  type PurchaseError,
} from 'react-native-iap';

// Product IDs matching App Store Connect
export const IAP_PRODUCTS = {
  MONTHLY: 'com.marketgps.pro.monthly',
  ANNUAL: 'com.marketgps.pro.annual',
} as const;

export const IAP_SKUS = [IAP_PRODUCTS.MONTHLY, IAP_PRODUCTS.ANNUAL];

export type IAPProduct = ProductSubscription;

/**
 * Initialize IAP connection
 */
export async function initIAP(): Promise<boolean> {
  try {
    if (Platform.OS !== 'ios') return false;
    await initConnection();
    return true;
  } catch (error) {
    if (__DEV__) console.error('[IAP] Init error:', error);
    return false;
  }
}

/**
 * End IAP connection (call on unmount)
 */
export async function closeIAP(): Promise<void> {
  try {
    await endConnection();
  } catch (error) {
    if (__DEV__) console.error('[IAP] Close error:', error);
  }
}

/**
 * Fetch subscription products from App Store
 */
export async function fetchIAPProducts(): Promise<ProductSubscription[]> {
  try {
    const result: FetchProductsResult = await fetchProducts({
      skus: IAP_SKUS,
      type: 'subs',
    });
    if (!result) return [];
    // Filter to only subscription products
    const subscriptions = (result as ProductSubscription[]).filter(
      (p) => p.type === 'subs'
    );
    return subscriptions;
  } catch (error) {
    if (__DEV__) console.error('[IAP] Fetch products error:', error);
    return [];
  }
}

/**
 * Request a subscription purchase
 */
export async function purchaseSubscription(sku: string): Promise<void> {
  try {
    await requestPurchase({
      request: {
        apple: { sku },
      },
      type: 'subs',
    });
  } catch (error) {
    if (__DEV__) console.error('[IAP] Purchase error:', error);
    throw error;
  }
}

/**
 * Get all active purchases (to restore)
 */
export async function restorePurchases(): Promise<Purchase[]> {
  try {
    const purchases = await getAvailablePurchases();
    return purchases ?? [];
  } catch (error) {
    if (__DEV__) console.error('[IAP] Restore error:', error);
    return [];
  }
}

/**
 * Check if user has an active Pro subscription
 */
export function hasProSubscription(purchases: Purchase[]): boolean {
  return purchases.some(
    (p) =>
      p.productId === IAP_PRODUCTS.MONTHLY ||
      p.productId === IAP_PRODUCTS.ANNUAL
  );
}

/**
 * Check if an error is a user cancellation
 */
export { isUserCancelledError };

/**
 * Setup purchase listeners - returns cleanup function
 */
export function setupPurchaseListeners(
  onPurchaseSuccess: (purchase: Purchase) => void,
  onPurchaseError: (error: PurchaseError) => void
): () => void {
  const purchaseUpdateSubscription = purchaseUpdatedListener(
    async (purchase: Purchase) => {
      // Finish the transaction
      try {
        await finishTransaction({ purchase, isConsumable: false });
      } catch (err) {
        if (__DEV__) console.error('[IAP] Finish transaction error:', err);
      }

      onPurchaseSuccess(purchase);
    }
  );

  const purchaseErrorSubscription = purchaseErrorListener(
    (error: PurchaseError) => {
      onPurchaseError(error);
    }
  );

  // Return cleanup function
  return () => {
    purchaseUpdateSubscription.remove();
    purchaseErrorSubscription.remove();
  };
}
