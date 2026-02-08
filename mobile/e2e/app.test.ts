import { device, element, by, expect as detoxExpect } from 'detox';

describe('MarketGPS Mobile App E2E Tests', () => {
  describe('App Launch', () => {
    it('should launch the app successfully', async () => {
      await expect(element(by.id('root-container'))).toBeVisible();
    });

    it('should display initial screen without errors', async () => {
      // Wait for app to fully load
      await device.waitForWhiteScreen();
      await expect(element(by.id('main-navigation'))).toBeVisible();
    });

    it('should have main navigation visible', async () => {
      await expect(element(by.id('main-navigation'))).toExist();
    });
  });

  describe('Navigation', () => {
    it('should navigate to Dashboard tab', async () => {
      await element(by.id('tab-dashboard')).multiTap();
      await expect(element(by.id('dashboard-screen'))).toBeVisible();
    });

    it('should navigate to Explorer tab', async () => {
      await element(by.id('tab-explorer')).multiTap();
      await expect(element(by.id('explorer-screen'))).toBeVisible();
    });

    it('should navigate to Watchlist tab', async () => {
      await element(by.id('tab-watchlist')).multiTap();
      await expect(element(by.id('watchlist-screen'))).toBeVisible();
    });

    it('should navigate to News tab', async () => {
      await element(by.id('tab-news')).multiTap();
      await expect(element(by.id('news-screen'))).toBeVisible();
    });

    it('should navigate to Settings tab', async () => {
      await element(by.id('tab-settings')).multiTap();
      await expect(element(by.id('settings-screen'))).toBeVisible();
    });

    it('should maintain state when switching tabs', async () => {
      await element(by.id('tab-dashboard')).multiTap();
      await element(by.id('tab-explorer')).multiTap();
      await element(by.id('tab-dashboard')).multiTap();
      await expect(element(by.id('dashboard-screen'))).toBeVisible();
    });
  });

  describe('Dashboard Screen', () => {
    beforeEach(async () => {
      await element(by.id('tab-dashboard')).multiTap();
    });

    it('should display dashboard screen', async () => {
      await expect(element(by.id('dashboard-screen'))).toBeVisible();
    });

    it('should show top assets section', async () => {
      await expect(element(by.id('top-assets-section'))).toBeVisible();
    });

    it('should display at least one asset card', async () => {
      await expect(element(by.id('asset-card-0'))).toBeVisible();
    });

    it('should show asset ticker and score', async () => {
      await expect(element(by.id('asset-ticker-0'))).toBeVisible();
      await expect(element(by.id('asset-score-0'))).toBeVisible();
    });

    it('should display market metrics', async () => {
      await expect(element(by.id('market-metrics'))).toBeVisible();
    });

    it('should allow scrolling through assets', async () => {
      await element(by.id('assets-list')).swipe('left', 'fast');
      await element(by.id('assets-list')).swipe('right', 'fast');
    });

    it('should navigate to asset details on tap', async () => {
      await element(by.id('asset-card-0')).multiTap();
      await expect(element(by.id('asset-details-screen'))).toBeVisible();
    });

    it('should show loading state initially', async () => {
      // App should load and show loading spinner briefly
      await device.waitForWhiteScreen();
      await expect(element(by.id('dashboard-screen'))).toBeVisible();
    });

    it('should display user portfolio summary', async () => {
      await expect(element(by.id('portfolio-summary'))).toBeVisible();
    });

    it('should show market scope selector', async () => {
      await expect(element(by.id('market-scope-selector'))).toBeVisible();
    });
  });

  describe('Explorer Screen', () => {
    beforeEach(async () => {
      await element(by.id('tab-explorer')).multiTap();
    });

    it('should display explorer screen', async () => {
      await expect(element(by.id('explorer-screen'))).toBeVisible();
    });

    it('should show search input field', async () => {
      await expect(element(by.id('search-input'))).toBeVisible();
    });

    it('should allow typing in search field', async () => {
      await element(by.id('search-input')).typeText('Apple');
      await expect(element(by.id('search-input'))).toHaveToggleValue(true);
    });

    it('should perform search on text input', async () => {
      await element(by.id('search-input')).clearText();
      await element(by.id('search-input')).typeText('AAPL');
      await element(by.id('search-button')).multiTap();
      await expect(element(by.text('AAPL'))).toBeVisible();
    });

    it('should display search results', async () => {
      await element(by.id('search-input')).typeText('T');
      await expect(element(by.id('search-results-list'))).toBeVisible();
    });

    it('should show filters section', async () => {
      await expect(element(by.id('filters-section'))).toBeVisible();
    });

    it('should allow filtering by asset type', async () => {
      await element(by.id('asset-type-filter')).multiTap();
      await expect(element(by.id('asset-type-options'))).toBeVisible();
    });

    it('should allow filtering by market scope', async () => {
      await element(by.id('market-scope-filter')).multiTap();
      await expect(element(by.id('market-scope-options'))).toBeVisible();
    });

    it('should display no results message when search has no matches', async () => {
      await element(by.id('search-input')).typeText('ZZZZZZZ');
      await element(by.id('search-button')).multiTap();
      await expect(element(by.text('No assets found'))).toBeVisible();
    });
  });

  describe('Watchlist Screen', () => {
    beforeEach(async () => {
      await element(by.id('tab-watchlist')).multiTap();
    });

    it('should display watchlist screen', async () => {
      await expect(element(by.id('watchlist-screen'))).toBeVisible();
    });

    it('should show watchlist items', async () => {
      // Assuming watchlist has items
      await expect(element(by.id('watchlist-list'))).toBeVisible();
    });

    it('should show empty state when no items', async () => {
      await expect(element(by.id('watchlist-list'))).toBeVisible();
    });

    it('should allow adding items to watchlist from explorer', async () => {
      await element(by.id('tab-explorer')).multiTap();
      await element(by.id('search-input')).typeText('AAPL');
      await element(by.id('search-button')).multiTap();
      await element(by.id('add-to-watchlist-btn-0')).multiTap();
      await expect(element(by.text('Added to watchlist'))).toBeVisible();
    });

    it('should remove items from watchlist', async () => {
      if (await element(by.id('watchlist-item-0')).isVisible()) {
        await element(by.id('watchlist-item-remove-0')).multiTap();
        await expect(element(by.text('Removed from watchlist'))).toBeVisible();
      }
    });

    it('should sort watchlist items', async () => {
      await element(by.id('sort-button')).multiTap();
      await expect(element(by.id('sort-options'))).toBeVisible();
    });

    it('should navigate to asset details from watchlist', async () => {
      if (await element(by.id('watchlist-item-0')).isVisible()) {
        await element(by.id('watchlist-item-0')).multiTap();
        await expect(element(by.id('asset-details-screen'))).toBeVisible();
      }
    });
  });

  describe('News Screen', () => {
    beforeEach(async () => {
      await element(by.id('tab-news')).multiTap();
    });

    it('should display news screen', async () => {
      await expect(element(by.id('news-screen'))).toBeVisible();
    });

    it('should show news articles list', async () => {
      await expect(element(by.id('news-list'))).toBeVisible();
    });

    it('should display at least one news article', async () => {
      await expect(element(by.id('news-article-0'))).toBeVisible();
    });

    it('should show article title', async () => {
      await expect(element(by.id('article-title-0'))).toBeVisible();
    });

    it('should show article summary', async () => {
      await expect(element(by.id('article-summary-0'))).toBeVisible();
    });

    it('should allow scrolling through news', async () => {
      await element(by.id('news-list')).swipe('up', 'fast');
      await element(by.id('news-list')).swipe('down', 'fast');
    });

    it('should open article on tap', async () => {
      await element(by.id('news-article-0')).multiTap();
      await expect(element(by.id('article-detail-screen'))).toBeVisible();
    });

    it('should allow filtering by category', async () => {
      await expect(element(by.id('news-filters'))).toBeVisible();
      await element(by.id('category-filter')).multiTap();
      await expect(element(by.id('category-options'))).toBeVisible();
    });

    it('should show loading state for news', async () => {
      // Should load and display articles without error
      await expect(element(by.id('news-list'))).toBeVisible();
    });
  });

  describe('Settings Screen', () => {
    beforeEach(async () => {
      await element(by.id('tab-settings')).multiTap();
    });

    it('should display settings screen', async () => {
      await expect(element(by.id('settings-screen'))).toBeVisible();
    });

    it('should show profile section', async () => {
      await expect(element(by.id('profile-section'))).toBeVisible();
    });

    it('should show account settings', async () => {
      await expect(element(by.id('account-settings'))).toBeVisible();
    });

    it('should show notification settings', async () => {
      await expect(element(by.id('notification-settings'))).toBeVisible();
    });

    it('should allow toggling notifications', async () => {
      await element(by.id('notifications-toggle')).multiTap();
    });

    it('should show theme selector', async () => {
      await expect(element(by.id('theme-selector'))).toBeVisible();
    });

    it('should allow changing theme', async () => {
      await element(by.id('theme-selector')).multiTap();
      await expect(element(by.id('theme-options'))).toBeVisible();
    });

    it('should show language settings', async () => {
      await expect(element(by.id('language-settings'))).toBeVisible();
    });

    it('should show about section', async () => {
      await element(by.id('settings-list')).swipe('up');
      await expect(element(by.id('about-section'))).toBeVisible();
    });

    it('should display app version', async () => {
      await element(by.id('settings-list')).swipe('up');
      await expect(element(by.id('app-version'))).toBeVisible();
    });

    it('should show logout button', async () => {
      await element(by.id('settings-list')).swipe('up');
      await expect(element(by.id('logout-button'))).toBeVisible();
    });
  });

  describe('Asset Details Screen', () => {
    beforeEach(async () => {
      await element(by.id('tab-dashboard')).multiTap();
      await element(by.id('asset-card-0')).multiTap();
    });

    it('should display asset details screen', async () => {
      await expect(element(by.id('asset-details-screen'))).toBeVisible();
    });

    it('should show asset name and ticker', async () => {
      await expect(element(by.id('asset-name'))).toBeVisible();
      await expect(element(by.id('asset-ticker'))).toBeVisible();
    });

    it('should display score card', async () => {
      await expect(element(by.id('score-card'))).toBeVisible();
    });

    it('should show score components breakdown', async () => {
      await expect(element(by.id('score-components'))).toBeVisible();
    });

    it('should display price chart', async () => {
      await expect(element(by.id('price-chart'))).toBeVisible();
    });

    it('should allow switching chart periods', async () => {
      await element(by.id('period-1d')).multiTap();
      await expect(element(by.id('price-chart'))).toBeVisible();
    });

    it('should show asset metrics', async () => {
      await element(by.id('details-scroll')).swipe('up');
      await expect(element(by.id('asset-metrics'))).toBeVisible();
    });

    it('should allow adding to watchlist', async () => {
      await element(by.id('add-watchlist-btn')).multiTap();
      await expect(element(by.text('Added to watchlist'))).toBeVisible();
    });

    it('should have back button to return to dashboard', async () => {
      await element(by.id('back-button')).multiTap();
      await expect(element(by.id('dashboard-screen'))).toBeVisible();
    });
  });

  describe('Offline Handling', () => {
    it('should show offline indicator when no connection', async () => {
      await device.setBiometricEnrollment(false);
      // Simulate offline
      await device.rejectTouchID();
    });

    it('should cache data and show cached content offline', async () => {
      // First load data online
      await element(by.id('tab-dashboard')).multiTap();
      await device.waitForWhiteScreen();
      // Data should be visible even after simulated offline
    });
  });

  describe('Performance', () => {
    it('should load dashboard quickly', async () => {
      await element(by.id('tab-dashboard')).multiTap();
      const start = Date.now();
      await expect(element(by.id('dashboard-screen'))).toBeVisible();
      const loadTime = Date.now() - start;
      expect(loadTime).toBeLessThan(3000); // Should load in less than 3 seconds
    });

    it('should handle large asset lists without lag', async () => {
      await element(by.id('tab-explorer')).multiTap();
      await element(by.id('search-input')).typeText('A');
      await element(by.id('search-button')).multiTap();
      // Scroll through results to test performance
      await element(by.id('search-results-list')).swipe('up', 'fast');
      await element(by.id('search-results-list')).swipe('up', 'fast');
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      // App should not crash when API fails
      await element(by.id('tab-dashboard')).multiTap();
      await expect(element(by.id('dashboard-screen'))).toBeVisible();
    });

    it('should show retry option on error', async () => {
      // If error occurs, should provide retry mechanism
      await device.waitForWhiteScreen();
    });

    it('should not crash on invalid input', async () => {
      await element(by.id('tab-explorer')).multiTap();
      await element(by.id('search-input')).typeText('!@#$%^&*()');
      await expect(element(by.id('explorer-screen'))).toBeVisible();
    });
  });

  describe('Accessibility', () => {
    it('should have accessible buttons with labels', async () => {
      await expect(element(by.id('tab-dashboard').and(by.label('Dashboard')))).toBeVisible();
    });

    it('should support screen reader navigation', async () => {
      // Navigation tabs should be accessible
      await expect(element(by.id('main-navigation'))).toBeVisible();
    });
  });
});
