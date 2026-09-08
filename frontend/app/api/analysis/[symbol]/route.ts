/** route 파일은 브라우저와 백엔드 사이의 BFF 기능을 담당한다. */

import { NextResponse } from "next/server";
import { createSafeMockAnalysis } from "../../../../features/office/analysis-contract";

/** `dynamic`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export const dynamic = "force-dynamic";

/** `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export async function GET(
  _request: Request,
  context: { params: Promise<{ symbol: string }> },
) {
  const { symbol } = await context.params;
  return NextResponse.json(createSafeMockAnalysis(symbol), {
    headers: {
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}
