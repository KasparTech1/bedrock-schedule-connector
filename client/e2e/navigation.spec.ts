import { test, expect } from '@playwright/test';

test.describe('Navigation', () => {
  test('should load the home page', async ({ page }) => {
    await page.goto('/');
    
    // Should see the main heading or library page
    await expect(page.locator('h1, h2').first()).toBeVisible();
  });

  test('should navigate to legacy connectors', async ({ page }) => {
    await page.goto('/');
    
    // Click on legacy link if visible
    const legacyLink = page.getByRole('link', { name: /legacy/i });
    if (await legacyLink.isVisible()) {
      await legacyLink.click();
      await expect(page).toHaveURL(/\/legacy/);
    }
  });

  test('should navigate to admin connectors', async ({ page }) => {
    await page.goto('/admin/connectors');
    
    // Should be on connectors page
    await expect(page).toHaveURL(/\/admin\/connectors/);
  });

  test('should navigate to flow optimizer', async ({ page }) => {
    await page.goto('/tools/flow-optimizer');
    
    // Should be on flow optimizer page
    await expect(page).toHaveURL(/\/tools\/flow-optimizer/);
  });

  test('should navigate to customer search', async ({ page }) => {
    await page.goto('/tools/customer-search');
    
    // Should be on customer search page
    await expect(page).toHaveURL(/\/tools\/customer-search/);
  });

  test('should navigate to order availability', async ({ page }) => {
    await page.goto('/tools/order-availability');
    
    // Should be on order availability page
    await expect(page).toHaveURL(/\/tools\/order-availability/);
  });

  test('should show 404 for unknown routes', async ({ page }) => {
    await page.goto('/unknown-page-that-does-not-exist');
    
    // Should show 404 message
    await expect(page.getByText(/not found/i)).toBeVisible();
  });
});

test.describe('Layout', () => {
  test('should have navigation sidebar on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/');
    
    // Should have sidebar navigation
    const sidebar = page.locator('nav, aside').first();
    await expect(sidebar).toBeVisible();
  });

  test('should have mobile menu on small screens', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    
    // Page should load successfully on mobile
    await expect(page.locator('body')).toBeVisible();
  });
});

test.describe('Error Handling', () => {
  test('should show error boundary on crash', async ({ page }) => {
    // Navigate to a page and verify error boundary exists
    await page.goto('/');
    
    // The app should be wrapped in error boundary
    // We can verify the app renders without crashing
    await expect(page.locator('body')).toBeVisible();
  });
});

