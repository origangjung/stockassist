import { proxyAdminRequest } from "../../../../lib/admin-proxy";

export async function GET(request: Request): Promise<Response> {
  const query = new URL(request.url).search;
  return proxyAdminRequest(`/api/v1/admin/alerts${query}`);
}

export async function POST(request: Request): Promise<Response> {
  return proxyAdminRequest("/api/v1/admin/alerts", {
    method: "POST",
    body: await request.text(),
  });
}
