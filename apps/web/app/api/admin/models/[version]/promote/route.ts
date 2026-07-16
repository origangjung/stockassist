import { proxyAdminRequest } from "../../../../../../lib/admin-proxy";

interface RouteContext {
  params: Promise<{ version: string }>;
}

export async function POST(_: Request, context: RouteContext): Promise<Response> {
  const { version } = await context.params;
  return proxyAdminRequest(
    `/api/v1/admin/models/${encodeURIComponent(version)}/promote`,
    { method: "POST" },
  );
}
