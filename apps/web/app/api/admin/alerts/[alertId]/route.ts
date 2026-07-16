import { proxyAdminRequest } from "../../../../../lib/admin-proxy";

export async function DELETE(
  _request: Request,
  context: { params: Promise<{ alertId: string }> },
): Promise<Response> {
  const { alertId } = await context.params;
  return proxyAdminRequest(`/api/v1/admin/alerts/${encodeURIComponent(alertId)}`, {
    method: "DELETE",
  });
}
