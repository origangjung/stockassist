/** route 파일은 브라우저와 백엔드 사이의 BFF 기능을 담당한다. */

import { proxyMarketRequest } from "../../../../lib/market-proxy";

/** `GET`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export async function GET(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const { path } = await context.params;
  return proxyMarketRequest(request, path);
}
