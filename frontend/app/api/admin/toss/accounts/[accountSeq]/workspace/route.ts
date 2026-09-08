/** route 파일은 브라우저와 백엔드 사이의 BFF 기능을 담당한다. */

import { proxyAdminRequest } from "../../../../../../../lib/admin-proxy";

/** `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export async function GET(
  request: Request,
  context: { params: Promise<{ accountSeq: string }> },
): Promise<Response> {
  const { accountSeq } = await context.params;
  if (!/^\d+$/.test(accountSeq) || Number(accountSeq) < 1) {
    return Response.json(
      { success: false, error: { code: "INVALID_ACCOUNT", message: "계좌 식별자가 올바르지 않습니다." } },
      { status: 400 },
    );
  }

  const query = new URL(request.url).searchParams;
  const currency = query.get("currency") === "USD" ? "USD" : "KRW";
  return proxyAdminRequest(
    `/api/v1/admin/toss/accounts/${accountSeq}/workspace?currency=${currency}`,
  );
}
