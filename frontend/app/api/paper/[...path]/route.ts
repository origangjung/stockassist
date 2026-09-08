/** 모의투자 경로만 허용하고 서버 비밀키를 숨기는 제한형 BFF다. */
import { NextRequest } from "next/server";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const MAX_REQUEST_BYTES = 4096;

/** `publicError`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function publicError(status: number, message: string) {
  return Response.json(
    { success: false, request_id: "paper-bff", error: { message } },
    { status, headers: { "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff" } },
  );
}

/** `upstreamPath`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function upstreamPath(parts: string[]): string | null {
  if (!UUID_PATTERN.test(parts[0] ?? "")) return null;
  if (parts.length === 1) return `/api/v1/paper-portfolios/${parts[0]}`;
  if (parts.length === 2 && ["orders", "reset", "allocation-proposals"].includes(parts[1])) {
    return `/api/v1/paper-portfolios/${parts[0]}/${parts[1]}`;
  }
  return null;
}

/** `proxy`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
async function proxy(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const { path } = await context.params;
  const target = upstreamPath(path);
  if (!target) return publicError(404, "허용되지 않은 모의투자 경로입니다.");
  if (request.method === "GET" && path.length !== 1) return publicError(405, "허용되지 않은 요청입니다.");
  if (request.method === "POST" && path.length !== 2) return publicError(405, "허용되지 않은 요청입니다.");

  let body: string | undefined;
  if (request.method === "POST" && ["orders", "allocation-proposals"].includes(path[1])) {
    if (!request.headers.get("content-type")?.toLowerCase().includes("application/json")) {
      return publicError(415, "JSON 요청만 허용됩니다.");
    }
    body = await request.text();
    if (new TextEncoder().encode(body).byteLength > MAX_REQUEST_BYTES) {
      return publicError(413, "모의투자 요청이 너무 큽니다.");
    }
    try { JSON.parse(body); } catch { return publicError(400, "모의투자 JSON 형식이 올바르지 않습니다."); }
  }

  const base = (
    process.env.BACKEND_INTERNAL_URL
    ?? process.env.API_URL
    ?? process.env.NEXT_PUBLIC_API_URL
    ?? "http://127.0.0.1:8000"
  ).replace(/\/$/, "");
  const controller = new AbortController();
  const timeoutMs = path[1] === "allocation-proposals" ? 45_000 : 15_000;
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const headers: Record<string, string> = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (process.env.ANALYSIS_API_KEY) headers["X-Analysis-Key"] = process.env.ANALYSIS_API_KEY;
    const response = await fetch(`${base}${target}`, {
      method: request.method,
      body,
      headers,
      cache: "no-store",
      signal: controller.signal,
    });
    const contentType = response.headers.get("content-type")?.toLowerCase() ?? "";
    if (!contentType.includes("json")) return publicError(502, "모의투자 API 응답 형식이 올바르지 않습니다.");
    const text = await response.text();
    if (new TextEncoder().encode(text).byteLength > 1_000_000) return publicError(502, "모의투자 API 응답이 너무 큽니다.");
    return new Response(text, {
      status: response.status,
      headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store, private", "X-Content-Type-Options": "nosniff" },
    });
  } catch {
    return publicError(controller.signal.aborted ? 504 : 502, "모의투자 서버에 연결하지 못했습니다.");
  } finally {
    clearTimeout(timeout);
  }
}

/** `GET`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export const GET = proxy;
/** `POST`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export const POST = proxy;
