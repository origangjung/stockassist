/** page 파일은 Next.js 페이지와 레이아웃 기능을 담당한다. */

import { MarketDashboard } from "../components/market/market-dashboard";
import { BarChart3, CircleUserRound, Search, Sparkles, WalletCards } from "lucide-react";

/** `Dashboard`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export default function Dashboard() {
  return (
    <main className="app-shell">
      <a className="skip-link" href="#market-search">종목 검색으로 바로가기</a>
      <header className="app-header">
        <nav aria-label="주요 메뉴">
          <a aria-label="StockPilot AI 홈" className="brand" href="/">
            <span aria-hidden="true" className="brand-mark">SP</span>
            <strong>StockPilot <em>AI</em></strong>
          </a>
          <div className="app-primary-navigation">
            <a href="#market-search"><Search aria-hidden="true" size={15} />종목 찾기</a>
            <a href="#agents"><Sparkles aria-hidden="true" size={15} />AI 분석</a>
            <a href="/market"><BarChart3 aria-hidden="true" size={15} />시장</a>
            <a href="/paper"><WalletCards aria-hidden="true" size={15} />모의투자</a>
          </div>
          <div className="app-header-actions">
            <a aria-label="운영 프로필" className="admin-link admin-link--profile" href="/admin"><CircleUserRound aria-hidden="true" size={19} /></a>
          </div>
        </nav>
      </header>
      <section aria-label="종목 검색과 분석" className="office-explore" id="market-search">
        <MarketDashboard />
      </section>
      <section className="notice">
        <b>Reference Signal</b>
        <span>모든 점수와 참고 시그널은 충분한 백테스트 검증을 통과하기 전까지 experimental 상태로 표시됩니다.</span>
      </section>
      <footer className="site-footer">
        <span>StockPilot AI · Investment decision support</span>
        <span>시장 데이터와 분석 결과는 참고용입니다.</span>
      </footer>
    </main>
  );
}
