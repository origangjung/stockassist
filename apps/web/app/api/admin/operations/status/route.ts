import { proxyAdminRequest } from "../../../../../lib/admin-proxy";

export async function GET(): Promise<Response> {
  return proxyAdminRequest("/api/v1/admin/operations/status");
}
