import { NextRequest, NextResponse } from "next/server";

function constantTimeEqual(actual: string, expected: string): boolean {
  const encoder = new TextEncoder();
  const actualBytes = encoder.encode(actual);
  const expectedBytes = encoder.encode(expected);
  const length = Math.max(actualBytes.length, expectedBytes.length);
  let difference = actualBytes.length ^ expectedBytes.length;
  for (let index = 0; index < length; index += 1) {
    difference |= (actualBytes[index] ?? 0) ^ (expectedBytes[index] ?? 0);
  }
  return difference === 0;
}

function securedTextResponse(status: number, message: string, authenticate = false): NextResponse {
  return new NextResponse(message, {
    status,
    headers: {
      "Cache-Control": "no-store, private",
      "Content-Type": "text/plain; charset=utf-8",
      ...(authenticate
        ? { "WWW-Authenticate": 'Basic realm="StockPilot Admin", charset="UTF-8"' }
        : {}),
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
    },
  });
}

function unavailable(message: string): NextResponse {
  return securedTextResponse(503, message);
}

function unauthorized(): NextResponse {
  return securedTextResponse(401, "관리자 인증이 필요합니다.", true);
}

function forbidden(message: string): NextResponse {
  return securedTextResponse(403, message);
}

function requestHost(request: NextRequest): string {
  const host = request.headers.get("host")?.trim().toLowerCase() ?? "";
  if (host.startsWith("[")) return host.slice(0, host.indexOf("]") + 1);
  return host.split(":", 1)[0];
}

function isAllowedHost(request: NextRequest): boolean {
  const configured = process.env.ALLOWED_HOSTS ?? "localhost,127.0.0.1,testserver";
  const allowed = configured.split(",").map((host) => host.trim().toLowerCase()).filter(Boolean);
  const actual = requestHost(request);
  return allowed.some((host) => (
    host === actual || (host.startsWith("*.") && actual.endsWith(host.slice(1)))
  ));
}

function isUnsafeAdminApiRequest(request: NextRequest): boolean {
  return (
    request.nextUrl.pathname.startsWith("/api/admin/") &&
    !["GET", "HEAD", "OPTIONS"].includes(request.method)
  );
}

function hasSameOrigin(request: NextRequest): boolean {
  return request.headers.get("origin") === request.nextUrl.origin;
}

function hasValidBasicCredentials(
  request: NextRequest,
  username: string,
  password: string,
): boolean {
  const authorization = request.headers.get("authorization");
  if (!authorization?.startsWith("Basic ")) return false;
  try {
    const decoded = atob(authorization.slice(6));
    const separator = decoded.indexOf(":");
    if (separator < 0) return false;
    return (
      constantTimeEqual(decoded.slice(0, separator), username) &&
      constantTimeEqual(decoded.slice(separator + 1), password)
    );
  } catch {
    return false;
  }
}

export function middleware(request: NextRequest): NextResponse {
  const username = process.env.ADMIN_UI_USERNAME ?? "";
  const password = process.env.ADMIN_UI_PASSWORD ?? "";
  const production = process.env.APP_ENVIRONMENT === "production";
  const unsafeMutation = isUnsafeAdminApiRequest(request);

  if (!isAllowedHost(request)) {
    return forbidden("허용되지 않은 호스트입니다.");
  }
  const adminRequest = request.nextUrl.pathname.startsWith("/admin") ||
    request.nextUrl.pathname.startsWith("/api/admin/");
  if (!adminRequest) return NextResponse.next();

  if (!username || !password) {
    if (production) {
      return unavailable("운영 환경의 관리자 UI 인증 정보가 설정되지 않았습니다.");
    }
    return unsafeMutation && !hasSameOrigin(request)
      ? forbidden("관리자 변경 요청의 출처를 확인할 수 없습니다.")
      : NextResponse.next();
  }
  if (production && password.length < 16) {
    return unavailable("운영 환경의 관리자 UI 비밀번호는 16자 이상이어야 합니다.");
  }
  if (!hasValidBasicCredentials(request, username, password)) {
    return unauthorized();
  }
  if (unsafeMutation && !hasSameOrigin(request)) {
    return forbidden("관리자 변경 요청의 출처를 확인할 수 없습니다.");
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*", "/api/admin/:path*", "/api/market/:path*"],
};
