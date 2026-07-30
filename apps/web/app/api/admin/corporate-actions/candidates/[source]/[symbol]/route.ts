import { proxyAdminRequest } from "../../../../../../../lib/admin-proxy";

export async function GET(
  request: Request,
  context: { params: Promise<{ source: string; symbol: string }> },
): Promise<Response> {
  const { source, symbol } = await context.params;
  const query = new URL(request.url).search;
  return proxyAdminRequest(
    `/api/v1/admin/corporate-actions/candidates/${encodeURIComponent(source)}/${encodeURIComponent(symbol)}${query}`,
  );
}
