import { expect, test } from "@playwright/test";

test("토스 시장 지표와 랭킹이 화면 폭 안에서 표시된다", async ({ page }, testInfo) => {
  await page.goto("/market");

  await expect(page.getByRole("heading", { name: "오늘 시장 한눈에 보기" })).toBeVisible();
  await expect(page.getByRole("region", { name: "주요 시장 지표" })).toBeVisible({ timeout: 30_000 });
  await expect(page.locator(".market-ranking-list > a").first()).toBeVisible({ timeout: 30_000 });

  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(1);

  await page.screenshot({ path: testInfo.outputPath("market-overview.png"), fullPage: true });
});

test("한글 종목명 자동완성에서 오라클을 선택해 분석한다", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name !== "desktop-chrome", "전체 종목 검색 동작은 화면 폭과 무관합니다.");
  await page.goto("/");
  const search = page.getByRole("combobox", { name: "종목명 또는 종목 코드 검색" });
  await search.fill("오라클");
  const oracle = page.getByRole("option", { name: /오라클 ORCL/ });
  await expect(oracle).toBeVisible({ timeout: 30_000 });
  await oracle.click();
  await expect(page).toHaveURL(/symbol=ORCL/, { timeout: 30_000 });
  await expect(page.locator(".market-results")).toBeVisible({ timeout: 30_000 });
});
