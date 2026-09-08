/** route 파일은 브라우저와 백엔드 사이의 BFF 기능을 담당한다. */

import { proxyAdminRequest } from "../../../../../../lib/admin-proxy";

/** `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export async function POST(
  _request: Request,
  context: { params: Promise<{ accountSeq: string }> },
): Promise<Response> {
  const { accountSeq } = await context.params;
  return proxyAdminRequest(`/api/v1/portfolios/${encodeURIComponent(accountSeq)}/sync`, {
    method: "POST",
  });
}
