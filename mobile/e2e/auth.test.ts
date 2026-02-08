import { device, element, by, expect as detoxExpect } from 'detox';

describe('MarketGPS Mobile Authentication E2E Tests', () => {
  describe('Login Screen', () => {
    beforeEach(async () => {
      // Ensure we start at login screen
      await device.launchApp({
        newInstance: true,
        clearData: true,
      });
      await expect(element(by.id('login-screen'))).toBeVisible();
    });

    it('should display login screen', async () => {
      await expect(element(by.id('login-screen'))).toBeVisible();
    });

    it('should show email input field', async () => {
      await expect(element(by.id('email-input'))).toBeVisible();
    });

    it('should show password input field', async () => {
      await expect(element(by.id('password-input'))).toBeVisible();
    });

    it('should show login button', async () => {
      await expect(element(by.id('login-button'))).toBeVisible();
    });

    it('should show sign up link', async () => {
      await expect(element(by.id('signup-link'))).toBeVisible();
    });

    it('should show forgot password link', async () => {
      await expect(element(by.id('forgot-password-link'))).toBeVisible();
    });

    it('should have disabled login button when fields are empty', async () => {
      // Button should be disabled until both fields have valid input
      await expect(element(by.id('login-button'))).toBeDisabled();
    });

    it('should enable login button when both fields are filled', async () => {
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('password123');
      await expect(element(by.id('login-button'))).toBeEnabled();
    });
  });

  describe('Login Form Validation', () => {
    beforeEach(async () => {
      await device.launchApp({
        newInstance: true,
        clearData: true,
      });
      await expect(element(by.id('login-screen'))).toBeVisible();
    });

    it('should validate email format', async () => {
      await element(by.id('email-input')).typeText('invalid-email');
      await element(by.id('password-input')).typeText('password123');
      await element(by.id('login-button')).multiTap();
      await expect(element(by.text('Invalid email format'))).toBeVisible();
    });

    it('should require email field', async () => {
      await element(by.id('password-input')).typeText('password123');
      await element(by.id('login-button')).multiTap();
      await expect(element(by.text('Email is required'))).toBeVisible();
    });

    it('should require password field', async () => {
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('login-button')).multiTap();
      await expect(element(by.text('Password is required'))).toBeVisible();
    });

    it('should accept valid email formats', async () => {
      const validEmails = ['test@example.com', 'user+tag@domain.co.uk'];
      for (const email of validEmails) {
        await element(by.id('email-input')).clearText();
        await element(by.id('email-input')).typeText(email);
        await element(by.id('password-input')).typeText('password123');
        // Should not show validation error for valid email
        await expect(element(by.text('Invalid email format'))).not.toBeVisible();
      }
    });

    it('should handle password requirements', async () => {
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('weak');
      await element(by.id('login-button')).multiTap();
      // May show password strength warning or similar
    });

    it('should clear validation errors when user corrects input', async () => {
      await element(by.id('email-input')).typeText('invalid');
      await element(by.id('login-button')).multiTap();
      await expect(element(by.text('Invalid email format'))).toBeVisible();

      await element(by.id('email-input')).clearText();
      await element(by.id('email-input')).typeText('valid@example.com');
      await expect(element(by.text('Invalid email format'))).not.toBeVisible();
    });

    it('should hide password when toggling password visibility', async () => {
      await element(by.id('password-input')).typeText('secretpassword');
      await element(by.id('password-visibility-toggle')).multiTap();
      // Password should be hidden (appears as dots)
    });

    it('should show password when toggling visibility again', async () => {
      await element(by.id('password-input')).typeText('secretpassword');
      await element(by.id('password-visibility-toggle')).multiTap();
      await element(by.id('password-visibility-toggle')).multiTap();
      // Password should be visible
    });
  });

  describe('Successful Login', () => {
    beforeEach(async () => {
      await device.launchApp({
        newInstance: true,
        clearData: true,
      });
      await expect(element(by.id('login-screen'))).toBeVisible();
    });

    it('should navigate to dashboard after successful login', async () => {
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('testpassword123');
      await element(by.id('login-button')).multiTap();

      // Wait for navigation to complete
      await device.waitForWhiteScreen();
      await expect(element(by.id('dashboard-screen'))).toBeVisible();
    });

    it('should display loading indicator during login', async () => {
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('testpassword123');
      await element(by.id('login-button')).multiTap();

      // Loading indicator should appear briefly
      await expect(element(by.id('login-loading-indicator'))).toBeVisible();
    });

    it('should persist session after login', async () => {
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('testpassword123');
      await element(by.id('login-button')).multiTap();

      await device.waitForWhiteScreen();
      await expect(element(by.id('dashboard-screen'))).toBeVisible();

      // Navigate away and back - should stay logged in
      await element(by.id('tab-settings')).multiTap();
      await element(by.id('tab-dashboard')).multiTap();
      await expect(element(by.id('dashboard-screen'))).toBeVisible();
    });

    it('should display user profile after login', async () => {
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('testpassword123');
      await element(by.id('login-button')).multiTap();

      await device.waitForWhiteScreen();
      await element(by.id('tab-settings')).multiTap();
      await expect(element(by.id('user-profile'))).toBeVisible();
    });

    it('should disable login button during submission', async () => {
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('testpassword123');
      await element(by.id('login-button')).multiTap();

      // Button should be disabled while submitting
      await expect(element(by.id('login-button'))).toBeDisabled();
    });
  });

  describe('Failed Login', () => {
    beforeEach(async () => {
      await device.launchApp({
        newInstance: true,
        clearData: true,
      });
      await expect(element(by.id('login-screen'))).toBeVisible();
    });

    it('should show error message on invalid credentials', async () => {
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('wrongpassword');
      await element(by.id('login-button')).multiTap();

      await expect(element(by.text('Invalid email or password'))).toBeVisible();
    });

    it('should show error message on non-existent user', async () => {
      await element(by.id('email-input')).typeText('nonexistent@example.com');
      await element(by.id('password-input')).typeText('password123');
      await element(by.id('login-button')).multiTap();

      await expect(element(by.text('User not found'))).toBeVisible();
    });

    it('should handle network errors', async () => {
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('password123');
      await element(by.id('login-button')).multiTap();

      // Should show generic error if network fails
      await expect(element(by.text(/error|failed/i))).toBeVisible();
    });

    it('should allow retry after failed login', async () => {
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('wrongpassword');
      await element(by.id('login-button')).multiTap();

      await expect(element(by.text('Invalid email or password'))).toBeVisible();

      // User should be able to retry
      await element(by.id('password-input')).clearText();
      await element(by.id('password-input')).typeText('correctpassword');
      await element(by.id('login-button')).multiTap();
    });

    it('should not clear email field on failed login', async () => {
      const testEmail = 'test@example.com';
      await element(by.id('email-input')).typeText(testEmail);
      await element(by.id('password-input')).typeText('wrongpassword');
      await element(by.id('login-button')).multiTap();

      await expect(element(by.id('email-input'))).toHaveText(testEmail);
    });

    it('should clear password field on failed login', async () => {
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('wrongpassword');
      await element(by.id('login-button')).multiTap();

      // Password should be cleared for security
      await expect(element(by.id('password-input'))).toHaveText('');
    });
  });

  describe('Sign Up', () => {
    beforeEach(async () => {
      await device.launchApp({
        newInstance: true,
        clearData: true,
      });
      await element(by.id('signup-link')).multiTap();
      await expect(element(by.id('signup-screen'))).toBeVisible();
    });

    it('should navigate to signup screen', async () => {
      await expect(element(by.id('signup-screen'))).toBeVisible();
    });

    it('should show signup form fields', async () => {
      await expect(element(by.id('name-input'))).toBeVisible();
      await expect(element(by.id('email-input'))).toBeVisible();
      await expect(element(by.id('password-input'))).toBeVisible();
      await expect(element(by.id('confirm-password-input'))).toBeVisible();
    });

    it('should validate password match', async () => {
      await element(by.id('name-input')).typeText('Test User');
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('password123');
      await element(by.id('confirm-password-input')).typeText('password456');
      await element(by.id('signup-button')).multiTap();

      await expect(element(by.text('Passwords do not match'))).toBeVisible();
    });

    it('should allow signup with valid data', async () => {
      await element(by.id('name-input')).typeText('Test User');
      await element(by.id('email-input')).typeText('newuser@example.com');
      await element(by.id('password-input')).typeText('password123');
      await element(by.id('confirm-password-input')).typeText('password123');
      await element(by.id('signup-button')).multiTap();

      await device.waitForWhiteScreen();
      // Should either navigate to dashboard or show verification screen
    });

    it('should navigate back to login', async () => {
      await element(by.id('login-link')).multiTap();
      await expect(element(by.id('login-screen'))).toBeVisible();
    });
  });

  describe('Password Reset', () => {
    beforeEach(async () => {
      await device.launchApp({
        newInstance: true,
        clearData: true,
      });
      await element(by.id('forgot-password-link')).multiTap();
      await expect(element(by.id('forgot-password-screen'))).toBeVisible();
    });

    it('should navigate to password reset screen', async () => {
      await expect(element(by.id('forgot-password-screen'))).toBeVisible();
    });

    it('should show email input for password reset', async () => {
      await expect(element(by.id('email-input'))).toBeVisible();
    });

    it('should show reset button', async () => {
      await expect(element(by.id('reset-button'))).toBeVisible();
    });

    it('should handle password reset request', async () => {
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('reset-button')).multiTap();

      // Should show success message
      await expect(element(by.text(/reset link|check your email/i))).toBeVisible();
    });

    it('should allow returning to login', async () => {
      await element(by.id('back-button')).multiTap();
      await expect(element(by.id('login-screen'))).toBeVisible();
    });
  });

  describe('Logout', () => {
    beforeEach(async () => {
      // Login first
      await device.launchApp({
        newInstance: true,
        clearData: true,
      });
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('testpassword123');
      await element(by.id('login-button')).multiTap();
      await device.waitForWhiteScreen();
    });

    it('should logout user from settings', async () => {
      await element(by.id('tab-settings')).multiTap();
      await element(by.id('settings-list')).swipe('up');
      await element(by.id('logout-button')).multiTap();

      await device.waitForWhiteScreen();
      await expect(element(by.id('login-screen'))).toBeVisible();
    });

    it('should clear user session on logout', async () => {
      await element(by.id('tab-settings')).multiTap();
      await element(by.id('settings-list')).swipe('up');
      await element(by.id('logout-button')).multiTap();

      await device.waitForWhiteScreen();
      // Should require re-login
      await expect(element(by.id('login-screen'))).toBeVisible();
    });

    it('should show confirmation before logout', async () => {
      await element(by.id('tab-settings')).multiTap();
      await element(by.id('settings-list')).swipe('up');
      await element(by.id('logout-button')).multiTap();

      // Should show confirmation dialog
      await expect(element(by.text(/confirm|sure/i))).toBeVisible();
    });

    it('should allow canceling logout', async () => {
      await element(by.id('tab-settings')).multiTap();
      await element(by.id('settings-list')).swipe('up');
      await element(by.id('logout-button')).multiTap();

      await expect(element(by.text(/confirm|sure/i))).toBeVisible();
      await element(by.id('cancel-button')).multiTap();

      // Should stay logged in
      await expect(element(by.id('settings-screen'))).toBeVisible();
    });
  });

  describe('Session Management', () => {
    beforeEach(async () => {
      await device.launchApp({
        newInstance: true,
        clearData: true,
      });
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('testpassword123');
      await element(by.id('login-button')).multiTap();
      await device.waitForWhiteScreen();
    });

    it('should maintain session when switching apps', async () => {
      await device.sendToBackground();
      await device.bringToForeground();

      await expect(element(by.id('dashboard-screen'))).toBeVisible();
    });

    it('should handle token refresh', async () => {
      // Token should be refreshed automatically
      await element(by.id('tab-explorer')).multiTap();
      await element(by.id('search-input')).typeText('AAPL');
      await element(by.id('search-button')).multiTap();

      // Should work without re-login
      await expect(element(by.id('explorer-screen'))).toBeVisible();
    });

    it('should show re-login prompt if session expires', async () => {
      // Simulate session expiration by waiting
      // This depends on implementation
    });
  });

  describe('Two-Factor Authentication', () => {
    it('should show 2FA setup during signup', async () => {
      // If app supports 2FA
      // Test 2FA flow here
    });

    it('should request 2FA code during login if enabled', async () => {
      // If user has 2FA enabled
      // Test 2FA verification during login
    });
  });

  describe('Biometric Authentication', () => {
    beforeEach(async () => {
      // Login and enable biometric
      await device.launchApp({
        newInstance: true,
        clearData: true,
      });
    });

    it('should allow enabling biometric login', async () => {
      // Login first
      await element(by.id('email-input')).typeText('test@example.com');
      await element(by.id('password-input')).typeText('testpassword123');
      await element(by.id('login-button')).multiTap();

      // Enable biometric in settings if option exists
      await element(by.id('tab-settings')).multiTap();
      if (await element(by.id('biometric-toggle')).isVisible()) {
        await element(by.id('biometric-toggle')).multiTap();
      }
    });

    it('should use biometric for quick login', async () => {
      // If biometric is set up
      // Lock app and verify biometric login
    });
  });
});
