import { proxyAdminRequest } from "../../../../../../lib/admin-proxy";

export async function POST(request: Request): Promise<Response> {
  return proxyAdminRequest("/api/v1/admin/backtests/strategies/compare", {
    method: "POST",
    body: await request.text(),
  });
}
