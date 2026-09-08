import { expect, test } from "@playwright/test";

test("executes an isolated paper order without horizontal overflow", async ({ page }, testInfo) => {
  await page.goto("/", { waitUntil: "domcontentloaded" });
  const search = page.getByRole("combobox");
  await expect(search).toBeVisible();
  await search.fill("AAPL");
  await search.press("Enter");

  const panel = page.locator("#paper-trading");
  await expect(panel).toBeVisible({ timeout: 20_000 });
  await expect(panel.getByText("실제 주문이 아닌 현재 조회가 기준의 연습 거래입니다.")).toBeVisible();
  await expect(panel.getByText("포트폴리오 위험")).toBeVisible();
  await expect(panel.getByText(/1회 30%/)).toBeVisible();
  await expect(panel.getByText(/10,000\.00/).first()).toBeVisible();

  await panel.getByRole("button", { name: "매수 주문" }).click();
  await expect(panel.getByRole("cell", { name: /AAPL/ })).toBeVisible({ timeout: 20_000 });
  await expect(panel.getByText("매수", { exact: true }).last()).toBeVisible();
  await page.goto("/paper", { waitUntil: "domcontentloaded" });
  await expect(page.getByRole("heading", { name: "내 모의투자" })).toBeVisible();
  await page.getByRole("tab", { name: "달러 계좌" }).click();
  await expect(page.getByText("애플", { exact: true }).first()).toBeVisible({ timeout: 20_000 });
  await expect(page.getByText(/처음보다/)).toBeVisible();
  await expect(page.getByText(/AAPL/).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "위험 관리" })).toBeVisible();
  await expect(page.getByText(/전체 투자 비중/)).toBeVisible();

  const layout = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - window.innerWidth,
    bodyOverflow: document.body.scrollWidth - window.innerWidth,
    replacementCharacters: (document.body.innerText.match(/\uFFFD/g) ?? []).length,
  }));
  expect(layout.overflow).toBeLessThanOrEqual(1);
  expect(layout.bodyOverflow).toBeLessThanOrEqual(1);
  expect(layout.replacementCharacters).toBe(0);
  await page.screenshot({ path: testInfo.outputPath("paper-portfolio.png"), fullPage: true });
});
