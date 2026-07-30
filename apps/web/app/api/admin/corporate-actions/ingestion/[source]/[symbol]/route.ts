import { proxyAdminRequest } from "../../../../../../../lib/admin-proxy";

export async function POST(
  request: Request,
  context: { params: Promise<{ source: string; symbol: string }> },
): Promise<Response> {
  const { source, symbol } = await context.params;
  const query = new URL(request.url).search;
  return proxyAdminRequest(
    `/api/v1/admin/corporate-actions/ingestion/${encodeURIComponent(source)}/${encodeURIComponent(symbol)}${query}`,
    { method: "POST" },
  );
}
