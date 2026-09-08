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

test("builds an allocation proposal and applies only a confirmed paper order", async ({ page }, testInfo) => {
  let paperOrderCount = 0;
  const portfolio = {
    account: { account_id: "00000000-0000-4000-8000-000000000001", cash_krw: "10000000", cash_usd: "10000" },
    persistence_status: "saved",
    saved_at: "2026-09-08T12:00:00Z",
    totals: {
      KRW: { initial_cash: "10000000", cash: "10000000", market_value: "0", unrealized_pnl: "0", equity: "10000000", total_pnl: "0", return_percent: "0" },
      USD: { initial_cash: "10000", cash: "10000", market_value: "0", unrealized_pnl: "0", equity: "10000", total_pnl: "0", return_percent: "0" },
    },
    risk: Object.fromEntries(["KRW", "USD"].map((currency) => [currency, {
      status: "stable", invested_ratio: "0", cash_ratio: "1", largest_position_symbol: null,
      largest_position_ratio: "0", warnings: [], limits: { max_order_ratio: "0.30", max_position_ratio: "0.40", max_invested_ratio: "0.95" },
    }])),
    positions: [], orders: [], commission_rate: "0.001",
    execution_policy: "현재 조회가로 즉시 체결되는 모의 시장가 주문", is_real_order: false,
  };

  await page.route("**/api/paper/**", async (route) => {
    const request = route.request();
    if (request.url().endsWith("/allocation-proposals")) {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ success: true, data: {
        account_id: portfolio.account.account_id, currency: "USD", objective: "min_volatility",
        optimizer: "PyPortfolioOpt-1.6", lookback_days: 180, observation_count: 180, equity: "10000",
        target_weights: { AAPL: "0.30", MSFT: "0.30", NVDA: "0.30" }, target_cash_weight: "0.10",
        current_weights: {}, estimated_turnover: "0.9", warnings: [], execution_enabled: false,
        is_real_order: false, rebalance_actions: [
          { symbol: "AAPL", side: "buy", quantity: "14", notional: "3000", target_weight: "0.30", reason: "target_allocation_gap" },
        ],
      } }) });
      return;
    }
    if (request.method() === "POST" && request.url().endsWith("/orders")) paperOrderCount += 1;
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ success: true, data: portfolio }) });
  });

  await page.goto("/paper", { waitUntil: "domcontentloaded" });
  await expect(page.getByText("모든 거래 자동 저장됨")).toBeVisible();
  await page.getByRole("tab", { name: "달러 계좌" }).click();
  await expect(page.getByRole("tab", { name: "달러 계좌" })).toHaveAttribute("aria-selected", "true");
  await page.getByRole("button", { name: "목표 비중 계산하기" }).click();
  await expect(page.getByText("변동성을 낮춘 배분")).toBeVisible();
  const layout = await page.evaluate(() => ({
    documentOverflow: document.documentElement.scrollWidth - window.innerWidth,
    bodyOverflow: document.body.scrollWidth - window.innerWidth,
  }));
  expect(layout.documentOverflow).toBeLessThanOrEqual(1);
  expect(layout.bodyOverflow).toBeLessThanOrEqual(1);
  await page.screenshot({ path: testInfo.outputPath("fund-allocation.png"), fullPage: true });
  expect(paperOrderCount).toBe(0);
  await page.getByRole("button", { name: "모의주문" }).click();
  await expect.poll(() => paperOrderCount).toBe(1);
});
