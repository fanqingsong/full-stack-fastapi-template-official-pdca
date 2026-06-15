/** E2E tests for causal analysis feature */

import { test, expect } from "@playwright/test";

test.describe("Causal Analysis", () => {
  test("should display causal analysis page", async ({ page }) => {
    await page.goto("/causal-analysis");
    await expect(page.locator("h1")).toContainText("Causal Analysis");
  });

  test("should show example queries", async ({ page }) => {
    await page.goto("/causal-analysis");
    const examples = page.locator("button:has-text('What causes my PDCA cycles')");
    await expect(examples.first()).toBeVisible();
  });

  test("should allow typing query", async ({ page }) => {
    await page.goto("/causal-analysis");
    await page.fill('[data-testid="causal-query"]', "What causes success?");

    const queryInput = page.locator('[data-testid="causal-query"]');
    await expect(queryInput).toHaveValue("What causes success?");
  });

  test("should enable analyze button with query", async ({ page }) => {
    await page.goto("/causal-analysis");
    await page.fill('[data-testid="causal-query"]', "What causes success?");

    const button = page.locator('[data-testid="analyze-button"]');
    await expect(button).toBeEnabled();
  });
});
