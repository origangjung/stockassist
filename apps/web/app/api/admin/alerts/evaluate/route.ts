import { proxyAdminRequest } from "../../../../../lib/admin-proxy";

export async function POST(): Promise<Response> {
  return proxyAdminRequest("/api/v1/admin/alerts/evaluate", { method: "POST" });
}
