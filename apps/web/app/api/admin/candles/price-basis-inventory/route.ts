import { proxyAdminRequest } from "../../../../../lib/admin-proxy";

export async function GET(request: Request) {
  const query = new URL(request.url).search;
  return proxyAdminRequest(`/api/v1/admin/candles/price-basis-inventory${query}`);
}
