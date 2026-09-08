/** CatalogStock 인터페이스는 프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다.에서 교환하는 필드 계약을 정의합니다. */
export interface CatalogStock {
  /** 정확한 종목명·티커를 몰라도 후보를 찾게 해 주는 검색 별칭 목록이다. */
  aliases: readonly string[];
  /** 시세와 가격 표시 형식을 결정하는 거래 통화다. */
  currency: "KRW" | "USD";
  /** 사용자에게 표시할 거래소 또는 시장 이름이다. */
  market: string;
  /** 자동완성과 결과 제목에 표시할 대표 종목명이다. */
  name: string;
  /** 시세 API 조회와 공유 URL에 사용하는 정규화된 종목 코드다. */
  symbol: string;
}

/**
 * 공급자 요청 전에 즉시 표시하는 로컬 종목 검색 목록이다.
 *
 * 전체 상장 종목 원장이 아니라 탐색 편의를 위한 목록이다. 목록에 없는 티커는 시세 API로
 * 확인하며, 대표 한국·미국 종목과 한글 별칭은 정확한 티커를 몰라도 선택할 수 있게 한다.
 */
export const stockCatalog: readonly CatalogStock[] = [
  { symbol: "005930", name: "삼성전자", market: "KOSPI", currency: "KRW", aliases: ["삼전", "samsung", "samsung electronics"] },
  { symbol: "000660", name: "SK하이닉스", market: "KOSPI", currency: "KRW", aliases: ["하이닉스", "sk hynix"] },
  { symbol: "035420", name: "NAVER", market: "KOSPI", currency: "KRW", aliases: ["네이버"] },
  { symbol: "035720", name: "카카오", market: "KOSPI", currency: "KRW", aliases: ["kakao"] },
  { symbol: "005380", name: "현대차", market: "KOSPI", currency: "KRW", aliases: ["현대자동차", "hyundai motor"] },
  { symbol: "000270", name: "기아", market: "KOSPI", currency: "KRW", aliases: ["kia", "기아차"] },
  { symbol: "068270", name: "셀트리온", market: "KOSPI", currency: "KRW", aliases: ["celltrion"] },
  { symbol: "373220", name: "LG에너지솔루션", market: "KOSPI", currency: "KRW", aliases: ["엘지에너지솔루션", "lg energy solution"] },
  { symbol: "207940", name: "삼성바이오로직스", market: "KOSPI", currency: "KRW", aliases: ["삼바", "samsung biologics"] },
  { symbol: "105560", name: "KB금융", market: "KOSPI", currency: "KRW", aliases: ["국민은행", "kb financial"] },
  { symbol: "055550", name: "신한지주", market: "KOSPI", currency: "KRW", aliases: ["신한금융", "shinhan"] },
  { symbol: "012330", name: "현대모비스", market: "KOSPI", currency: "KRW", aliases: ["hyundai mobis"] },
  { symbol: "005490", name: "POSCO홀딩스", market: "KOSPI", currency: "KRW", aliases: ["포스코", "posco"] },
  { symbol: "006400", name: "삼성SDI", market: "KOSPI", currency: "KRW", aliases: ["삼성에스디아이"] },
  { symbol: "051910", name: "LG화학", market: "KOSPI", currency: "KRW", aliases: ["엘지화학", "lg chem"] },
  { symbol: "247540", name: "에코프로비엠", market: "KOSDAQ", currency: "KRW", aliases: ["ecopro bm"] },
  { symbol: "086520", name: "에코프로", market: "KOSDAQ", currency: "KRW", aliases: ["ecopro"] },
  { symbol: "AAPL", name: "Apple", market: "NASDAQ", currency: "USD", aliases: ["애플", "아이폰", "apple inc"] },
  { symbol: "MSFT", name: "Microsoft", market: "NASDAQ", currency: "USD", aliases: ["마이크로소프트", "마소", "windows"] },
  { symbol: "ORCL", name: "Oracle", market: "NYSE", currency: "USD", aliases: ["오라클", "oracle corporation"] },
  { symbol: "NVDA", name: "NVIDIA", market: "NASDAQ", currency: "USD", aliases: ["엔비디아", "nvidia"] },
  { symbol: "TSLA", name: "Tesla", market: "NASDAQ", currency: "USD", aliases: ["테슬라"] },
  { symbol: "AMZN", name: "Amazon", market: "NASDAQ", currency: "USD", aliases: ["아마존"] },
  { symbol: "GOOGL", name: "Alphabet", market: "NASDAQ", currency: "USD", aliases: ["구글", "google", "알파벳"] },
  { symbol: "META", name: "Meta Platforms", market: "NASDAQ", currency: "USD", aliases: ["메타", "페이스북", "instagram"] },
  { symbol: "NFLX", name: "Netflix", market: "NASDAQ", currency: "USD", aliases: ["넷플릭스"] },
  { symbol: "AMD", name: "AMD", market: "NASDAQ", currency: "USD", aliases: ["에이엠디", "advanced micro devices"] },
  { symbol: "AVGO", name: "Broadcom", market: "NASDAQ", currency: "USD", aliases: ["브로드컴", "브라"] },
  { symbol: "PLTR", name: "Palantir", market: "NASDAQ", currency: "USD", aliases: ["팔란티어"] },
  { symbol: "COIN", name: "Coinbase", market: "NASDAQ", currency: "USD", aliases: ["코인베이스"] },
  { symbol: "JPM", name: "JPMorgan Chase", market: "NYSE", currency: "USD", aliases: ["제이피모건", "jp morgan"] },
  { symbol: "BRK.B", name: "Berkshire Hathaway", market: "NYSE", currency: "USD", aliases: ["버크셔", "워런 버핏", "berkshire"] },
  { symbol: "LLY", name: "Eli Lilly", market: "NYSE", currency: "USD", aliases: ["일라이릴리", "릴리"] },
  { symbol: "V", name: "Visa", market: "NYSE", currency: "USD", aliases: ["비자"] },
  { symbol: "WMT", name: "Walmart", market: "NYSE", currency: "USD", aliases: ["월마트"] },
  { symbol: "SPY", name: "SPDR S&P 500 ETF", market: "NYSE ARCA", currency: "USD", aliases: ["에스앤피500", "s&p 500", "미국 대표 etf"] },
  { symbol: "QQQ", name: "Invesco QQQ ETF", market: "NASDAQ", currency: "USD", aliases: ["나스닥100", "nasdaq 100"] },
  { symbol: "VOO", name: "Vanguard S&P 500 ETF", market: "NYSE ARCA", currency: "USD", aliases: ["뱅가드", "s&p500 etf"] },
  { symbol: "SCHD", name: "Schwab US Dividend ETF", market: "NYSE ARCA", currency: "USD", aliases: ["슈드", "미국 배당 etf", "배당"] },
  { symbol: "TLT", name: "iShares 20+ Year Treasury ETF", market: "NASDAQ", currency: "USD", aliases: ["미국 장기채", "채권 etf"] },
];
