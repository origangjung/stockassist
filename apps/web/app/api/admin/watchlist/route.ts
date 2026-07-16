import { proxyAdminRequest } from "../../../../lib/admin-proxy";

export async function GET(): Promise<Response> {
  return proxyAdminRequest("/api/v1/admin/watchlist");
}

export async function POST(request: Request): Promise<Response> {
  return proxyAdminRequest("/api/v1/admin/watchlist", {
    method: "POST",
    body: await request.text(),
  });
}
