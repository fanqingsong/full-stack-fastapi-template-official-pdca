const { chromium } = require('@playwright/test');

(async () => {
  // Launch browser
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    console.log('Opening login page...');
    await page.goto('http://localhost:5173/login');

    // Wait for page to load
    await page.waitForLoadState('networkidle');

    // Fill in login form
    console.log('Filling login form...');
    await page.getByTestId('email-input').fill('admin@example.com');
    await page.getByTestId('password-input').fill('changethis');

    // Click login button
    console.log('Clicking login button...');
    await page.getByRole('button', { name: 'Log In' }).click();

    // Wait for redirect to home page
    await page.waitForURL('/', { timeout: 5000 });
    console.log('✓ Login successful! Redirected to home page.');

    // Wait a bit to see the logged-in state
    await page.waitForTimeout(2000);

    // Logout
    console.log('Logging out...');
    await page.getByTestId('user-menu').click();
    await page.waitForTimeout(500); // Wait for menu to appear
    await page.getByRole('menuitem', { name: 'Log out' }).click();

    // Wait for redirect back to login page
    await page.waitForURL('/login', { timeout: 5000 });
    console.log('✓ Logout successful! Redirected to login page.');

    // Wait a bit to see the logged-out state
    await page.waitForTimeout(2000);

  } catch (error) {
    console.error('Error during execution:', error);
  } finally {
    // Close browser
    await browser.close();
    console.log('Browser closed.');
  }
})();
