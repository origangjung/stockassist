import { expect, test, type Page } from "@playwright/test";

async function openReadyApplication(page: Page) {
  const search = page.getByRole("combobox");

  await expect(async () => {
    const response = await page.goto("/", { waitUntil: "domcontentloaded" });
    expect(response?.status()).toBeLessThan(500);
    await expect(search).toBeVisible({ timeout: 5_000 });
  }).toPass({ intervals: [500, 1_000, 2_000], timeout: 15_000 });

  await expect(page.getByText("어떤 종목이 궁금하세요?", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "종목 찾기" })).toBeVisible();
  await expect(page.getByRole("link", { name: "AI 분석" })).toBeVisible();

  return search;
}

test("searches a US stock and renders a usable AI analysis", async ({ page }, testInfo) => {
  if (testInfo.project.name === "desktop-chrome") {
    await page.setViewportSize({ width: 2560, height: 1440 });
  }
  const browserErrors: string[] = [];
  const failedResponses: string[] = [];
  page.on("console", (message) => {
    if (message.type() === "error") browserErrors.push(message.text());
  });
  page.on("pageerror", (error) => browserErrors.push(error.name));
  page.on("response", (response) => {
    if (response.status() >= 400) {
      failedResponses.push(`${response.status()} ${new URL(response.url()).pathname}`);
    }
  });

  const search = await openReadyApplication(page);
  failedResponses.length = 0;
  browserErrors.length = 0;
  await search.fill("AAPL");
  await search.press("Enter");

  await expect(page.locator(".market-results")).toBeVisible({
    timeout: 15_000,
  });
  const analysis = page.locator("section.analysis-panel");
  await expect(analysis).toBeVisible();

  const verdict = page.locator(".final-verdict-modal");
  await expect(verdict).toBeVisible({ timeout: 90_000 });
  await expect(verdict.getByText("FINAL VERDICT", { exact: false })).toBeVisible();
  await expect(verdict.getByText("본 분석은 투자 자문이 아닌 참고 정보입니다.", { exact: false })).toBeVisible();
  const verdictDetails = verdict.getByText("회의록과 모델 상태 보기", { exact: true });
  await expect(verdictDetails).toBeVisible();
  await expect(verdict.getByRole("heading", { name: "모델 상태" })).toBeHidden();
  await verdictDetails.click();
  await expect(verdict.getByRole("heading", { name: "모델 상태" })).toBeVisible();

  const researchDetails = analysis.getByText("전문 AI 근거와 반대 의견 보기", { exact: true });
  await expect(researchDetails).toBeVisible();
  await researchDetails.click();
  const reportNavigation = analysis.locator("nav.analysis-jump-nav");
  await expect(reportNavigation).toBeVisible();
  await page.screenshot({ path: testInfo.outputPath("final-verdict.png"), fullPage: true });

  await expect(verdict).toHaveAttribute("role", "region");
  await expect(verdict.getByRole("button", { name: "최종 분석 닫기" })).toHaveCount(0);
  await expect(page.locator(".final-verdict-backdrop")).toHaveCount(0);
  if (testInfo.project.name === "desktop-chrome") {
    const chart = page.locator("#market-chart");
    const positions = await Promise.all([chart, analysis].map((element) => element.boundingBox()));
    expect(positions[0]).not.toBeNull();
    expect(positions[1]).not.toBeNull();
    expect(positions[0]!.x).toBeLessThan(positions[1]!.x);
    expect(Math.abs(positions[0]!.y - positions[1]!.y)).toBeLessThanOrEqual(2);
    const panelOverflow = await analysis.evaluate((element) => element.scrollWidth - element.clientWidth);
    expect(panelOverflow).toBeLessThanOrEqual(1);
  }
  const office = analysis.locator(".broker-office");
  await expect(office).toBeVisible();
  await expect(office.locator(".office-room")).toHaveCount(5);
  await expect(office.locator(".office-character")).toHaveCount(12);
  const eventFeed = office.locator(".office-event-feed");
  await expect(eventFeed).toBeVisible();
  await expect.poll(async () => Number(await eventFeed.getAttribute("data-event-count"))).toBeGreaterThanOrEqual(12);
  await expect(eventFeed.locator("li")).toHaveCount(1);
  await expect(eventFeed.locator("li.is-verdict")).toHaveCount(1);
  await eventFeed.getByRole("button", { name: /이전 이벤트/ }).click();
  await expect(eventFeed.locator("li")).toHaveCount(5);
  await expect(eventFeed.locator("li.is-verdict")).toHaveCount(1);
  const officeGeometry = await office.evaluate((element) => {
    const scene = element.querySelector<HTMLElement>(".broker-office__scene");
    const viewport = element.querySelector<HTMLElement>(".broker-office__viewport");
    if (!scene || !viewport) throw new Error("office geometry is unavailable");
    const bounds = scene.getBoundingClientRect();
    return {
      internalOverflow: viewport.scrollWidth - viewport.clientWidth,
      ratio: bounds.width / bounds.height,
    };
  });
  expect(officeGeometry.internalOverflow).toBeLessThanOrEqual(1);
  expect(officeGeometry.ratio).toBeGreaterThan(1.48);
  expect(officeGeometry.ratio).toBeLessThan(1.52);
  await office.getByRole("button", { name: /차트, 기술 AI/ }).click();
  const profile = page.getByRole("dialog", { name: "차트 소개" });
  await expect(profile).toBeVisible();
  await expect(profile.getByText("가격과 거래량에서 추세와 모멘텀을 점검합니다.")).toBeVisible();
  await profile.getByRole("button", { name: "소개 닫기" }).click();

  const mockResponse = await page.request.get("/api/analysis/AAPL");
  expect(mockResponse.ok()).toBe(true);
  const mock = await mockResponse.json();
  expect(mock.verdict.signal).toBe("DATA_INSUFFICIENT");
  expect(mock.agents).toHaveLength(6);
  expect(mock.is_investment_advice).toBe(false);

  const pageState = await page.evaluate(() => ({
    horizontalOverflow: document.documentElement.scrollWidth - window.innerWidth,
    bodyHorizontalOverflow: document.body.scrollWidth - window.innerWidth,
    replacementCharacters: (document.body.innerText.match(/\uFFFD/g) ?? []).length,
  }));
  expect(pageState.horizontalOverflow).toBeLessThanOrEqual(1);
  expect(pageState.bodyHorizontalOverflow).toBeLessThanOrEqual(1);
  expect(pageState.replacementCharacters).toBe(0);
  expect(failedResponses).toEqual([]);
  expect(browserErrors).toEqual([]);

  await page.screenshot({
    path: testInfo.outputPath("office-analysis.png"),
    fullPage: true,
  });
});

test("stops REST quote polling while the realtime socket is live", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chrome", "Realtime polling policy is viewport-independent.");
  let quoteRequests = 0;
  page.on("request", (request) => {
    if (/\/api\/v1\/stocks\/AAPL\/quote(?:\?|$)/.test(request.url())) quoteRequests += 1;
  });

  const response = await page.goto("/?symbol=AAPL", { waitUntil: "domcontentloaded" });
  expect(response?.status()).toBeLessThan(500);
  await expect(page.locator(".market-results")).toBeVisible({ timeout: 15_000 });

  const liveStatus = page.locator(".live-status.live");
  try {
    await expect(liveStatus).toBeVisible({ timeout: 15_000 });
  } catch {
    test.skip(true, "The configured realtime provider is unavailable in this environment.");
  }

  // 초기 REST 요청이 끝난 뒤에도 과거처럼 5초 주기 요청이 다시 생기는지 관찰한다.
  await page.waitForTimeout(500);
  quoteRequests = 0;
  await page.waitForTimeout(6_500);
  expect(quoteRequests).toBe(0);
});

test("offers Korean aliases, ETF discovery, and keyboard autocomplete", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chrome", "Autocomplete behavior is viewport-independent.");
  const search = await openReadyApplication(page);

  await search.fill("애플");
  const suggestions = page.getByRole("listbox", { name: "연관 검색" });
  await expect(suggestions).toBeVisible();
  await expect(suggestions.getByRole("option", { name: /Apple.*AAPL/ })).toBeVisible();

  await search.fill("배당");
  await expect(suggestions.getByRole("option", { name: /Schwab US Dividend ETF.*SCHD/ })).toBeVisible();

  await search.press("ArrowDown");
  await search.press("Enter");
  await expect(page).toHaveURL(/symbol=SCHD/);

  await search.fill("브라");
  const broadcom = suggestions.getByRole("option", { name: /Broadcom.*AVGO/ });
  await expect(broadcom).toBeVisible();
  await broadcom.click();
  await expect(search).toHaveValue("Broadcom");
  await expect(page).toHaveURL(/symbol=AVGO/);

  await search.fill("오라클");
  const oracle = suggestions.getByRole("option", { name: /Oracle.*ORCL/ });
  await expect(oracle).toBeVisible();
  await oracle.click();
  await expect(page).toHaveURL(/symbol=ORCL/);

  await page.getByRole("button", { name: "새 종목 찾기" }).click();
  await search.fill("테슬라");
  await page.getByRole("button", { name: "검색어 지우기" }).click();
  await expect(search).toHaveValue("");
  await expect(page.locator("#stock-search-suggestion-label")).toHaveText("최근 검색");
});

test("keeps semantic analysis events when reduced motion is enabled", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chrome", "one browser profile covers this behavior");
  await page.emulateMedia({ reducedMotion: "reduce" });
  const search = await openReadyApplication(page);
  await search.fill("AAPL");
  await search.press("Enter");

  const verdict = page.locator(".final-verdict-modal");
  await expect(verdict).toBeVisible({ timeout: 25_000 });
  await expect(verdict).toHaveAttribute("role", "region");
  const eventFeed = page.locator(".office-event-feed");
  await expect.poll(async () => Number(await eventFeed.getAttribute("data-event-count"))).toBeGreaterThanOrEqual(12);
  await expect(eventFeed.locator("li.is-verdict")).toHaveCount(1);
});

test("recovers in place after the analysis network request fails", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chrome", "one browser profile covers recovery");
  let rejectAnalysis = true;
  await page.route("**/api/market/api/v1/stocks/AAPL/ai-report?**", async (route) => {
    if (rejectAnalysis) {
      await route.abort("connectionfailed");
      return;
    }
    await route.continue();
  });

  const search = await openReadyApplication(page);
  await search.fill("AAPL");
  await search.press("Enter");

  const alert = page.locator("section.analysis-panel").getByRole("alert");
  await expect(alert).toBeVisible({ timeout: 20_000 });
  await expect(alert).toContainText("분석을 완료하지 못했습니다");

  rejectAnalysis = false;
  await alert.getByRole("button", { name: "재시도" }).click();
  await expect(page.locator(".final-verdict-modal")).toBeVisible({ timeout: 90_000 });
  await expect(alert).toHaveCount(0);
});
