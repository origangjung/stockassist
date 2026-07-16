import { proxyAdminRequest } from "../../../../lib/admin-proxy";

export async function GET(request: Request): Promise<Response> {
  const query = new URL(request.url).search;
  return proxyAdminRequest(`/api/v1/admin/provider-audits${query}`);
}
