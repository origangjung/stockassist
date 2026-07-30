import { proxyMarketRequest } from "../../../../lib/market-proxy";

export async function GET(
  request: Request,
  context: { params: Promise<{ path: string[] }> },
): Promise<Response> {
  const { path } = await context.params;
  return proxyMarketRequest(request, path);
}
