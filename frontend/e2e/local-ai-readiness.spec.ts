import { expect, test } from "@playwright/test";

const username = process.env.ADMIN_UI_USERNAME ?? "";
const password = process.env.ADMIN_UI_PASSWORD ?? "";

test.use({ httpCredentials: { username, password } });

test("관리자 화면에서 직접 학습 AI 품질과 표본 부족을 확인한다", async ({ page }, testInfo) => {
  test.skip(!username || !password, "관리자 UI 인증 정보가 필요합니다.");

  await page.goto("/admin#models", { waitUntil: "domcontentloaded" });
  await page.getByRole("tab", { name: /모델 관리/ }).click();

  await expect(page.getByRole("heading", { name: "직접 학습 AI 준비도" })).toBeVisible();
  await expect(page.getByText(/사용 가능 2개/)).toBeVisible({ timeout: 20_000 });
  await expect(page.getByRole("cell", { name: "수급 분석" })).toBeVisible();
  await expect(page.getByRole("cell", { name: /133건 더 필요/ })).toBeVisible();
  await expect(page.getByRole("cell", { name: /151건 더 필요/ })).toBeVisible();

  const layout = await page.evaluate(() => ({
    overflow: document.documentElement.scrollWidth - window.innerWidth,
    replacementCharacters: (document.body.innerText.match(/\uFFFD/g) ?? []).length,
  }));
  expect(layout.overflow).toBeLessThanOrEqual(1);
  expect(layout.replacementCharacters).toBe(0);

  await page.screenshot({ path: testInfo.outputPath("local-ai-readiness.png"), fullPage: true });
});
