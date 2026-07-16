import { proxyAdminRequest } from "../../../../../lib/admin-proxy";

export async function DELETE(
  _request: Request,
  context: { params: Promise<{ symbol: string }> },
): Promise<Response> {
  const { symbol } = await context.params;
  return proxyAdminRequest(`/api/v1/admin/watchlist/${encodeURIComponent(symbol)}`, {
    method: "DELETE",
  });
}
