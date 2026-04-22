const { test, expect } = require('@playwright/test');

test('login and logout', async ({ page }) => {
  // Go to login page
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
  await page.waitForURL('**/', { timeout: 10000 });
  console.log('✓ Login successful! Redirected to home page.');

  // Verify login success message
  await expect(page.getByText('Welcome back, nice to see you again!')).toBeVisible();

  // Wait a bit to see the logged-in state
  await page.waitForTimeout(2000);

  // Logout
  console.log('Logging out...');
  await page.getByTestId('user-menu').click();
  await page.waitForTimeout(500); // Wait for menu to appear
  await page.getByRole('menuitem', { name: 'Log out' }).click();

  // Wait for redirect back to login page
  await page.waitForURL('**/login', { timeout: 10000 });
  console.log('✓ Logout successful! Redirected to login page.');

  // Verify we're back on login page
  await expect(page.getByRole('button', { name: 'Log In' })).toBeVisible();

  // Wait a bit to see the logged-out state
  await page.waitForTimeout(2000);
});
