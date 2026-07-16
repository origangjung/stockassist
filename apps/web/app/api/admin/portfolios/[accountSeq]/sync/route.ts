import { proxyAdminRequest } from "../../../../../../lib/admin-proxy";

export async function POST(
  _request: Request,
  context: { params: Promise<{ accountSeq: string }> },
): Promise<Response> {
  const { accountSeq } = await context.params;
  return proxyAdminRequest(`/api/v1/portfolios/${encodeURIComponent(accountSeq)}/sync`, {
    method: "POST",
  });
}
