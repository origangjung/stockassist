const DEFAULT_TIMEOUT_MS = 15_000;
const DEFAULT_MAX_RESPONSE_BYTES = 2_000_000;
const MAX_REQUEST_BYTES = 65_536;

function boundedInteger(
  value: string | undefined,
  fallback: number,
  minimum: number,
  maximum: number,
): number {
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed >= minimum && parsed <= maximum
    ? parsed
    : fallback;
}

function errorResponse(status: number, message: string): Response {
  return Response.json(
    { success: false, error: { code: `HTTP_${status}`, message } },
    {
      status,
      headers: {
        "Cache-Control": "no-store, private",
        "X-Content-Type-Options": "nosniff",
      },
    },
  );
}

async function boundedResponseBody(response: Response, maximumBytes: number): Promise<string> {
  const declaredLength = Number(response.headers.get("content-length"));
  if (Number.isFinite(declaredLength) && declaredLength > maximumBytes) {
    throw new AdminProxyResponseError("response-too-large");
  }
  if (!response.body) return "";

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let size = 0;
  let body = "";
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    size += value.byteLength;
    if (size > maximumBytes) {
      await reader.cancel();
      throw new AdminProxyResponseError("response-too-large");
    }
    body += decoder.decode(value, { stream: true });
  }
  return body + decoder.decode();
}

class AdminProxyResponseError extends Error {}

interface AdminProxyOptions {
  method?: "GET" | "POST" | "DELETE";
  body?: string;
}

export async function proxyAdminRequest(
  pathAndQuery: string,
  options: AdminProxyOptions = {},
): Promise<Response> {
  const adminKey = process.env.ADMIN_API_KEY;
  if (!adminKey) {
    return errorResponse(503, "관리자 API 키가 설정되지 않았습니다.");
  }
  if (options.body && new TextEncoder().encode(options.body).byteLength > MAX_REQUEST_BYTES) {
    return errorResponse(413, "관리자 요청 본문이 허용 크기를 초과했습니다.");
  }

  const backendUrl = (
    process.env.BACKEND_INTERNAL_URL ??
    process.env.NEXT_PUBLIC_API_URL ??
    "http://127.0.0.1:8000"
  ).replace(/\/$/, "");
  const timeoutMs = boundedInteger(
    process.env.ADMIN_PROXY_TIMEOUT_MS,
    DEFAULT_TIMEOUT_MS,
    1_000,
    60_000,
  );
  const maximumResponseBytes = boundedInteger(
    process.env.ADMIN_PROXY_MAX_RESPONSE_BYTES,
    DEFAULT_MAX_RESPONSE_BYTES,
    65_536,
    10_000_000,
  );
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const upstream = await fetch(`${backendUrl}${pathAndQuery}`, {
      method: options.method ?? "GET",
      body: options.body,
      headers: {
        "X-Admin-Key": adminKey,
        ...(process.env.ANALYSIS_API_KEY
          ? { "X-Analysis-Key": process.env.ANALYSIS_API_KEY }
          : {}),
        ...(options.body ? { "Content-Type": "application/json" } : {}),
      },
      cache: "no-store",
      signal: controller.signal,
    });
    const contentType = upstream.headers.get("content-type")?.toLowerCase() ?? "";
    if (!contentType.includes("application/json") && !contentType.includes("+json")) {
      return errorResponse(502, "백엔드 관리자 API가 JSON이 아닌 응답을 반환했습니다.");
    }

    const body = await boundedResponseBody(upstream, maximumResponseBytes);
    try {
      JSON.parse(body);
    } catch {
      return errorResponse(502, "백엔드 관리자 API 응답 형식이 올바르지 않습니다.");
    }

    const headers = new Headers({
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store, private",
      "X-Content-Type-Options": "nosniff",
    });
    for (const name of [
      "retry-after",
      "x-ratelimit-limit",
      "x-ratelimit-remaining",
      "x-request-id",
    ]) {
      const value = upstream.headers.get(name);
      if (value) headers.set(name, value);
    }
    return new Response(body, { status: upstream.status, headers });
  } catch (reason) {
    if (reason instanceof AdminProxyResponseError) {
      return errorResponse(502, "백엔드 관리자 API 응답이 허용 크기를 초과했습니다.");
    }
    if (controller.signal.aborted) {
      return errorResponse(504, "백엔드 관리자 API 응답 시간이 초과되었습니다.");
    }
    return errorResponse(502, "백엔드 관리자 API에 연결할 수 없습니다.");
  } finally {
    clearTimeout(timeout);
  }
}
