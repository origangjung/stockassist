/** market-proxy 파일은 프론트 타입 계약과 API client 기능을 담당한다. */

const DEFAULT_TIMEOUT_MS = 120_000;
const DEFAULT_MAX_RESPONSE_BYTES = 3_000_000;
const SYMBOL_PATTERN = /^[0-9A-Z.-]{1,16}$/;
const SAFE_SEGMENT_PATTERN = /^[a-z0-9.-]{1,32}$/;
const ALLOWED_QUERY_KEYS = new Set([
  "days",
  "count",
  "duration",
  "fiscal_year",
  "horizon_days",
  "interval",
  "limit",
  "market_country",
  "q",
  "trade_limit",
  "type",
]);
const ALLOWED_STOCK_TAILS = new Set([
  "",
  "ai-report",
  "candles",
  "candles/processed",
  "disclosures",
  "financials",
  "indicators",
  "investor-flow",
  "microstructure",
  "news",
  "orderbook",
  "patterns",
  "prediction",
  "quote",
  "score",
  "trades",
  "toss-trends",
  "valuation",
  "warnings",
]);

/** `errorResponse`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
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

/** `boundedInteger`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
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

/** `allowedPath`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function allowedPath(parts: string[]): boolean {
  const joined = parts.join("/");
  if (joined === "api/v1/market/overview" || joined === "api/v1/market/rankings") return true;
  if (joined === "api/v1/stocks/search") return true;
  if (
    parts.length === 5
    && parts.slice(0, 4).join("/") === "api/v1/market/indicators"
    && /^(KOSPI|KOSDAQ|KR_BOND_(2Y|3Y|5Y|10Y|20Y|30Y))$/.test(parts[4] ?? "")
  ) return true;
  if (
    parts.length < 4 ||
    parts[0] !== "api" ||
    parts[1] !== "v1" ||
    parts[2] !== "stocks" ||
    !SYMBOL_PATTERN.test(parts[3])
  ) return false;
  const tail = parts.slice(4).join("/");
  return ALLOWED_STOCK_TAILS.has(tail);
}

/** `allowedQuery`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function allowedQuery(searchParams: URLSearchParams): boolean {
  if (searchParams.toString().length > 1024) return false;
  return [...searchParams.keys()].every((key) => (
    ALLOWED_QUERY_KEYS.has(key) && searchParams.getAll(key).length === 1
  ));
}

/** `boundedBody`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
async function boundedBody(response: Response, maximumBytes: number): Promise<string> {
  const declaredLength = Number(response.headers.get("content-length"));
  if (Number.isFinite(declaredLength) && declaredLength > maximumBytes) {
    throw new MarketProxyResponseError();
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
      throw new MarketProxyResponseError();
    }
    body += decoder.decode(value, { stream: true });
  }
  return body + decoder.decode();
}

/** MarketProxyResponseError 클래스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.의 상태와 동작을 캡슐화합니다. */
class MarketProxyResponseError extends Error {}

/** `proxyMarketRequest`은(는) 비동기로 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export async function proxyMarketRequest(request: Request, parts: string[]): Promise<Response> {
  const normalized = parts.map((part) => part.trim());
  if (normalized.some((part) => !SAFE_SEGMENT_PATTERN.test(part.toLowerCase()))) {
    return errorResponse(404, "허용되지 않은 시장 데이터 경로입니다.");
  }
  if (
    normalized[0] === "api"
    && normalized[1] === "v1"
    && normalized[2] === "stocks"
    && normalized[3]?.toLowerCase() !== "search"
  ) {
    normalized[3] = normalized[3]?.toUpperCase();
  }
  if (!allowedPath(normalized)) {
    return errorResponse(404, "허용되지 않은 시장 데이터 경로입니다.");
  }
  const requestUrl = new URL(request.url);
  if (!allowedQuery(requestUrl.searchParams)) {
    return errorResponse(400, "허용되지 않은 시장 데이터 조회 조건입니다.");
  }

  const backendUrl = (process.env.BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
  const upstreamPath = `/${normalized.map(encodeURIComponent).join("/")}${requestUrl.search}`;
  const timeoutMs = boundedInteger(
    process.env.MARKET_PROXY_TIMEOUT_MS,
    DEFAULT_TIMEOUT_MS,
    1_000,
    180_000,
  );
  const maximumBytes = boundedInteger(
    process.env.MARKET_PROXY_MAX_RESPONSE_BYTES,
    DEFAULT_MAX_RESPONSE_BYTES,
    65_536,
    10_000_000,
  );
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const analysisKey = process.env.ANALYSIS_API_KEY;
    const upstream = await fetch(`${backendUrl}${upstreamPath}`, {
      headers: analysisKey ? { "X-Analysis-Key": analysisKey } : {},
      cache: "no-store",
      signal: controller.signal,
    });
    const contentType = upstream.headers.get("content-type")?.toLowerCase() ?? "";
    if (!contentType.includes("application/json") && !contentType.includes("+json")) {
      return errorResponse(502, "백엔드 시장 API가 JSON이 아닌 응답을 반환했습니다.");
    }
    const body = await boundedBody(upstream, maximumBytes);
    try {
      JSON.parse(body);
    } catch {
      return errorResponse(502, "백엔드 시장 API 응답 형식이 올바르지 않습니다.");
    }
    const headers = new Headers({
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store, private",
      "X-Content-Type-Options": "nosniff",
    });
    for (const name of ["retry-after", "x-ratelimit-limit", "x-ratelimit-remaining", "x-request-id"]) {
      const value = upstream.headers.get(name);
      if (value) headers.set(name, value);
    }
    return new Response(body, { status: upstream.status, headers });
  } catch (reason) {
    if (reason instanceof MarketProxyResponseError) {
      return errorResponse(502, "백엔드 시장 API 응답이 허용 크기를 초과했습니다.");
    }
    if (controller.signal.aborted) {
      return errorResponse(504, "백엔드 시장 API 응답 시간이 초과되었습니다.");
    }
    return errorResponse(502, "백엔드 시장 API에 연결할 수 없습니다.");
  } finally {
    clearTimeout(timeout);
  }
}
