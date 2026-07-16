import { proxyAdminRequest } from "../../../../../lib/admin-proxy";

export async function GET(
  _request: Request,
  context: { params: Promise<{ runId: string }> },
): Promise<Response> {
  const { runId } = await context.params;
  return proxyAdminRequest(`/api/v1/admin/backtests/${encodeURIComponent(runId)}`);
}
