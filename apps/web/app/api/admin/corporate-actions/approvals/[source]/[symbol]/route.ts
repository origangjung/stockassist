import { proxyAdminRequest } from "../../../../../../../lib/admin-proxy";

export async function POST(
  request: Request,
  context: { params: Promise<{ source: string; symbol: string }> },
): Promise<Response> {
  const { source, symbol } = await context.params;
  return proxyAdminRequest(
    `/api/v1/admin/corporate-actions/approvals/${encodeURIComponent(source)}/${encodeURIComponent(symbol)}`,
    { method: "POST", body: await request.text() },
  );
}
