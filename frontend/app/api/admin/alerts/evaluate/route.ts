/** route 파일은 브라우저와 백엔드 사이의 BFF 기능을 담당한다. */

import { proxyAdminRequest } from "../../../../../lib/admin-proxy";

/** `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export async function POST(): Promise<Response> {
  return proxyAdminRequest("/api/v1/admin/alerts/evaluate", { method: "POST" });
}
