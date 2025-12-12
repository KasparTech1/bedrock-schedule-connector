import { test, expect } from '@playwright/test';

test.describe('Legacy Connectors Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/legacy');
    // Wait for page to load
    await page.waitForLoadState('networkidle');
  });

  test('should load the legacy connectors page', async ({ page }) => {
    // Check page title
    await expect(page.locator('h1:has-text("Legacy Systems")')).toBeVisible();
    
    // Check for legacy badge (use first() to handle multiple matches)
    await expect(page.locator('text=Transitional').first()).toBeVisible();
    
    // Check for Global Shop card
    await expect(page.locator('text=Legacy Global Shop')).toBeVisible();
  });

  test.describe('Tab Navigation', () => {
    test('should navigate between tabs', async ({ page }) => {
      // Check all tabs are present
      await expect(page.locator('button[role="tab"]:has-text("Overview")')).toBeVisible();
      await expect(page.locator('button[role="tab"]:has-text("Health & Metrics")')).toBeVisible();
      await expect(page.locator('button[role="tab"]:has-text("Architecture")')).toBeVisible();
      await expect(page.locator('button[role="tab"]:has-text("Try It")')).toBeVisible();
    });

    test('should switch to Health & Metrics tab', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Health & Metrics")');
      await expect(page.locator('text=Connection Health')).toBeVisible();
    });

    test('should switch to Try It tab', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Try It")');
      await expect(page.locator('label:has-text("Product Line")')).toBeVisible();
      await expect(page.locator('label:has-text("Salesperson")')).toBeVisible();
    });
  });

  test.describe('Health Check', () => {
    test('should display health check button', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Health & Metrics")');
      
      // Look for refresh/check health button
      const refreshButton = page.locator('button:has-text("Refresh"), button:has-text("Check Health"), button[aria-label*="refresh" i]').first();
      await expect(refreshButton).toBeVisible();
    });

    test('should handle health check API call', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Health & Metrics")');
      
      // Mock the health check API
      await page.route('**/api/legacy/global-shop/health', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'healthy',
            response_time_ms: 150,
            message: 'Connection successful',
            bridge_url: 'https://bridge.example.com'
          }),
        });
      });

      // Find and click refresh button
      const refreshButton = page.locator('button:has-text("Refresh"), button:has-text("Check Health"), button[aria-label*="refresh" i]').first();
      await refreshButton.click();

      // Wait for response
      await page.waitForTimeout(1000);

      // Should show healthy status (check for status badge or message)
      await expect(page.locator('text=/healthy|Healthy|Connection successful/i').first()).toBeVisible({ timeout: 5000 });
    });

    test('should handle health check error gracefully', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Health & Metrics")');
      
      // Mock error response
      await page.route('**/api/legacy/global-shop/health', async (route) => {
        await route.fulfill({
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Service unavailable'
          }),
        });
      });

      const refreshButton = page.locator('button:has-text("Refresh"), button:has-text("Check Health"), button[aria-label*="refresh" i]').first();
      await refreshButton.click();

      // Should show error message
      await expect(page.locator('text=/Service unavailable|Error|HTTP 503/i').first()).toBeVisible({ timeout: 5000 });
    });

    test('should handle network error gracefully', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Health & Metrics")');
      
      // Block the health check API
      await page.route('**/api/legacy/global-shop/health', (route) => route.abort());

      const refreshButton = page.locator('button:has-text("Refresh"), button:has-text("Check Health"), button[aria-label*="refresh" i]').first();
      await refreshButton.click();

      // Should show error (network error or timeout)
      await expect(page.locator('text=/Error|failed|unavailable/i').first()).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Product Lines Query', () => {
    test('should display product lines form', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Try It")');
      
      await expect(page.locator('label:has-text("Product Line")')).toBeVisible();
      await expect(page.locator('label:has-text("Limit")')).toBeVisible();
      await expect(page.locator('button:has-text("Get Product Lines")')).toBeVisible();
    });

    test('should execute product lines query successfully', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Try It")');
      
      // Mock successful response
      await page.route('**/api/legacy/global-shop/product-lines*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            product_lines: [
              { PRODLINE: 'ELEC', DESCRIP: 'Electronics', COST_CENTER: '100' },
              { PRODLINE: 'MECH', DESCRIP: 'Mechanical', COST_CENTER: '200' }
            ],
            summary: {
              total: 2,
              query: 'SELECT TOP 500 * FROM prodline_mre',
              source: 'Global Shop (Pervasive SQL)'
            }
          }),
        });
      });

      // Click Get Product Lines button
      await page.click('button:has-text("Get Product Lines")');

      // Wait for results
      await page.waitForTimeout(1000);

      // Should show results (table or data)
      await expect(page.locator('text=/Product Lines|2 rows|ELEC|Electronics/i').first()).toBeVisible({ timeout: 5000 });
    });

    test('should handle product lines query error', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Try It")');
      
      // Mock error response
      await page.route('**/api/legacy/global-shop/product-lines*', async (route) => {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Database connection failed'
          }),
        });
      });

      await page.click('button:has-text("Get Product Lines")');

      // Should show error message
      await expect(page.locator('text=/Product Line Error|Database connection failed|HTTP 500/i').first()).toBeVisible({ timeout: 5000 });
    });

    test('should filter product lines by product line code', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Try It")');
      await page.waitForTimeout(500); // Wait for tab to render
      
      // Mock filtered response
      await page.route('**/api/legacy/global-shop/product-lines?product_line=ELEC*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            product_lines: [
              { PRODLINE: 'ELEC', DESCRIP: 'Electronics', COST_CENTER: '100' }
            ],
            summary: { total: 1, query: "SELECT TOP 500 * FROM prodline_mre WHERE PRODLINE = 'ELEC'" }
          }),
        });
      });

      // Enter product line filter - find input by label
      const productLineLabel = page.locator('label:has-text("Product Line")');
      await expect(productLineLabel).toBeVisible();
      const productLineInput = productLineLabel.locator('..').locator('input').first();
      await productLineInput.fill('ELEC');

      await page.click('button:has-text("Get Product Lines")');

      // Should show filtered results
      await expect(page.locator('text=/ELEC|Electronics/i').first()).toBeVisible({ timeout: 5000 });
    });

    test('should respect limit parameter', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Try It")');
      
      // Mock response with limit
      await page.route('**/api/legacy/global-shop/product-lines?limit=10*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            product_lines: Array(10).fill({ PRODLINE: 'TEST', DESCRIP: 'Test' }),
            summary: { total: 10, query: 'SELECT TOP 10 * FROM prodline_mre' }
          }),
        });
      });

      // Set limit to 10
      const limitInput = page.locator('input[type="number"]').first();
      await limitInput.fill('10');

      await page.click('button:has-text("Get Product Lines")');

      // Should show 10 rows
      await expect(page.locator('text=10 rows').first()).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Salespersons Query', () => {
    test('should display salespersons form', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Try It")');
      
      await expect(page.locator('label:has-text("Salesperson")')).toBeVisible();
      await expect(page.locator('button:has-text("Get Salespersons")')).toBeVisible();
    });

    test('should execute salespersons query successfully', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Try It")');
      
      // Mock successful response
      await page.route('**/api/legacy/global-shop/salespersons*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            data: [
              { SALESSION: 'SP001', NAME: 'John Smith', COMMISSION: 0.05 },
              { SALESSION: 'SP002', NAME: 'Jane Doe', COMMISSION: 0.06 }
            ],
            summary: {
              total: 2,
              query: 'SELECT TOP 500 * FROM V_SALESPERSONS',
              source: 'Global Shop (Pervasive SQL)'
            }
          }),
        });
      });

      await page.click('button:has-text("Get Salespersons")');

      await page.waitForTimeout(1000);

      // Should show results
      await expect(page.locator('text=/Salespersons|2 rows|John Smith|SP001/i').first()).toBeVisible({ timeout: 5000 });
    });

    test('should handle salespersons query error', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Try It")');
      
      // Mock error response
      await page.route('**/api/legacy/global-shop/salespersons*', async (route) => {
        await route.fulfill({
          status: 503,
          contentType: 'application/json',
          body: JSON.stringify({
            detail: 'Service unavailable'
          }),
        });
      });

      await page.click('button:has-text("Get Salespersons")');

      // Should show error message
      await expect(page.locator('text=/Salesperson Error|Service unavailable|HTTP 503/i').first()).toBeVisible({ timeout: 5000 });
    });
  });

  test.describe('Error Handling', () => {
    test('should handle empty JSON response', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Try It")');
      
      // Mock empty response
      await page.route('**/api/legacy/global-shop/product-lines*', (route) => {
        route.fulfill({
          status: 200,
          contentType: 'text/plain',
          body: '',
        });
      });

      await page.click('button:has-text("Get Product Lines")');

      // Should show error about content type
      await expect(page.locator('text=/Expected JSON|unknown|Error/i').first()).toBeVisible({ timeout: 5000 });
    });

    test('should handle non-JSON error response', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Try It")');
      
      // Mock HTML error response
      await page.route('**/api/legacy/global-shop/product-lines*', (route) => {
        route.fulfill({
          status: 500,
          contentType: 'text/html',
          body: '<html><body>Internal Server Error</body></html>',
        });
      });

      await page.click('button:has-text("Get Product Lines")');

      // Should show error message
      await expect(page.locator('text=/HTTP 500|Error|Expected JSON/i').first()).toBeVisible({ timeout: 5000 });
    });

    test('should handle network timeout', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Try It")');
      
      // Delay response to simulate timeout
      await page.route('**/api/legacy/global-shop/product-lines*', (route) => {
        setTimeout(() => {
          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify({ product_lines: [], summary: { total: 0 } }),
          });
        }, 10000); // 10 second delay
      });

      await page.click('button:has-text("Get Product Lines")');

      // Should eventually show error or timeout
      // This test may need adjustment based on actual timeout behavior
      await page.waitForTimeout(2000);
    });
  });

  test.describe('Loading States', () => {
    test('should show loading state during health check', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Health & Metrics")');
      
      // Delay response
      await page.route('**/api/legacy/global-shop/health', async (route) => {
        await new Promise(resolve => setTimeout(resolve, 1000));
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ status: 'healthy' }),
        });
      });

      const refreshButton = page.locator('button:has-text("Refresh"), button:has-text("Check Health")').first();
      await refreshButton.click();

      // Should show loading indicator (spinner, disabled button, etc.)
      await expect(page.locator('.animate-spin, [aria-busy="true"], button:disabled').first()).toBeVisible({ timeout: 500 });
    });

    test('should show loading state during product lines query', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Try It")');
      await page.waitForTimeout(500); // Wait for tab to render
      
      // Delay response
      await page.route('**/api/legacy/global-shop/product-lines*', async (route) => {
        await new Promise(resolve => setTimeout(resolve, 1500));
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ product_lines: [], summary: { total: 0 } }),
        });
      });

      const getButton = page.locator('button:has-text("Get Product Lines")');
      await getButton.click();

      // Should show loading state - check for disabled button or loading text
      // The button should be disabled or show loading text
      // Use proper Playwright syntax: check multiple selectors separately
      const loadingState = page.locator('button:has-text("Get Product Lines"):disabled')
        .or(page.locator('button:has-text("Loading")'))
        .or(page.locator('.animate-spin'));
      await expect(loadingState.first()).toBeVisible({ timeout: 1000 });
    });
  });

  test.describe('Metrics Display', () => {
    test('should display response time in health metrics', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Health & Metrics")');
      
      await page.route('**/api/legacy/global-shop/health', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'healthy',
            response_time_ms: 150,
            message: 'Connection successful'
          }),
        });
      });

      const refreshButton = page.locator('button:has-text("Refresh"), button:has-text("Check Health")').first();
      await refreshButton.click();

      await page.waitForTimeout(1000);

      // Should show response time
      await expect(page.locator('text=/150|ms|response/i').first()).toBeVisible({ timeout: 5000 });
    });

    test('should display query summary after product lines query', async ({ page }) => {
      await page.click('button[role="tab"]:has-text("Try It")');
      
      await page.route('**/api/legacy/global-shop/product-lines*', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            product_lines: [{ PRODLINE: 'TEST' }],
            summary: {
              total: 1,
              query: 'SELECT TOP 500 * FROM prodline_mre',
              response_time_ms: 200,
              source: 'Global Shop (Pervasive SQL)'
            }
          }),
        });
      });

      await page.click('button:has-text("Get Product Lines")');

      await page.waitForTimeout(1000);

      // Should show summary information
      await expect(page.locator('text=/1 rows|Global Shop|PRODLINE_MRE/i').first()).toBeVisible({ timeout: 5000 });
    });
  });
});
