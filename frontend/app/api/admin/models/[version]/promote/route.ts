/** route 파일은 브라우저와 백엔드 사이의 BFF 기능을 담당한다. */

import { proxyAdminRequest } from "../../../../../../lib/admin-proxy";

/** RouteContext 인터페이스는 브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다.에서 교환하는 필드 계약을 정의합니다. */
interface RouteContext {
  params: Promise<{ version: string }>;
}

/** `POST`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export async function POST(_: Request, context: RouteContext): Promise<Response> {
  const { version } = await context.params;
  return proxyAdminRequest(
    `/api/v1/admin/models/${encodeURIComponent(version)}/promote`,
    { method: "POST" },
  );
}
