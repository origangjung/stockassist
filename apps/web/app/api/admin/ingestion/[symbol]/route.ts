import { proxyAdminRequest } from "../../../../../lib/admin-proxy";

export async function POST(
  request: Request,
  context: { params: Promise<{ symbol: string }> },
): Promise<Response> {
  const { symbol } = await context.params;
  const query = new URL(request.url).search;
  return proxyAdminRequest(
    `/api/v1/admin/ingestion/${encodeURIComponent(symbol)}${query}`,
    { method: "POST" },
  );
}
