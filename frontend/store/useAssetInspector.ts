/**
 * MarketGPS - Asset Inspector Global Store
 * =========================================
 * Zustand store for managing the global asset inspector slide-over panel.
 * Allows any component to open the inspector without prop drilling.
 */

import { create } from 'zustand';

interface AssetInspectorState {
  // State
  isOpen: boolean;
  selectedTicker: string | null;
  selectedAssetId: string | null;
  
  // Actions
  openInspector: (ticker: string, assetId?: string) => void;
  closeInspector: () => void;
  setTicker: (ticker: string, assetId?: string) => void;
}

export const useAssetInspector = create<AssetInspectorState>((set) => ({
  // Initial state
  isOpen: false,
  selectedTicker: null,
  selectedAssetId: null,

  // Actions
  openInspector: (ticker: string, assetId?: string) => 
    set({ 
      isOpen: true, 
      selectedTicker: ticker,
      selectedAssetId: assetId || `${ticker}.US`  // Default to US if not specified
    }),

  closeInspector: () => 
    set({ 
      isOpen: false, 
      selectedTicker: null,
      selectedAssetId: null 
    }),

  setTicker: (ticker: string, assetId?: string) =>
    set({
      selectedTicker: ticker,
      selectedAssetId: assetId || `${ticker}.US`
    }),
}));

// Selector hooks for specific state slices
export const useInspectorOpen = () => useAssetInspector((state) => state.isOpen);
export const useSelectedTicker = () => useAssetInspector((state) => state.selectedTicker);
export const useSelectedAssetId = () => useAssetInspector((state) => state.selectedAssetId);

// Action hooks
export const useOpenInspector = () => useAssetInspector((state) => state.openInspector);
export const useCloseInspector = () => useAssetInspector((state) => state.closeInspector);
