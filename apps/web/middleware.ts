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

function unavailable(message: string): NextResponse {
  return new NextResponse(message, {
    status: 503,
    headers: {
      "Cache-Control": "no-store, private",
      "Content-Type": "text/plain; charset=utf-8",
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
    },
  });
}

function unauthorized(): NextResponse {
  return new NextResponse("관리자 인증이 필요합니다.", {
    status: 401,
    headers: {
      "Cache-Control": "no-store, private",
      "Content-Type": "text/plain; charset=utf-8",
      "WWW-Authenticate": 'Basic realm="StockPilot Admin", charset="UTF-8"',
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
    },
  });
}

export function middleware(request: NextRequest): NextResponse {
  const username = process.env.ADMIN_UI_USERNAME ?? "";
  const password = process.env.ADMIN_UI_PASSWORD ?? "";
  const production = process.env.APP_ENVIRONMENT === "production";

  if (!username || !password) {
    return production
      ? unavailable("운영 환경의 관리자 UI 인증 정보가 설정되지 않았습니다.")
      : NextResponse.next();
  }
  if (production && password.length < 16) {
    return unavailable("운영 환경의 관리자 UI 비밀번호는 16자 이상이어야 합니다.");
  }

  const authorization = request.headers.get("authorization");
  if (!authorization?.startsWith("Basic ")) {
    return unauthorized();
  }
  try {
    const decoded = atob(authorization.slice(6));
    const separator = decoded.indexOf(":");
    if (separator < 0) {
      return unauthorized();
    }
    const actualUsername = decoded.slice(0, separator);
    const actualPassword = decoded.slice(separator + 1);
    if (
      !constantTimeEqual(actualUsername, username) ||
      !constantTimeEqual(actualPassword, password)
    ) {
      return unauthorized();
    }
  } catch {
    return unauthorized();
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/admin/:path*", "/api/admin/:path*"],
};
