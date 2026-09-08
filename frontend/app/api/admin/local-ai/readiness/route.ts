/** 직접 학습 AI 준비도 요청을 인증된 백엔드 관리자 API로 전달한다. */

import { proxyAdminRequest } from "../../../../../lib/admin-proxy";

/** 관리자 세션을 유지한 채 AI 품질 요약을 조회한다. */
export async function GET(): Promise<Response> {
  return proxyAdminRequest("/api/v1/admin/local-ai/readiness");
}
