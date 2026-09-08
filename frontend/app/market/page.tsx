/** page 파일은 Next.js 페이지와 레이아웃 기능을 담당한다. */

import { BarChart3, CircleUserRound, Search, Sparkles, WalletCards } from "lucide-react";
import { MarketOverviewDashboard } from "../../components/market/market-overview-dashboard";

/** `MarketPage`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export default function MarketPage() {
  return (
    <main className="app-shell">
      <header className="app-header">
        <nav aria-label="주요 메뉴">
          <a aria-label="StockPilot AI 홈" className="brand" href="/"><span aria-hidden="true" className="brand-mark">SP</span><strong>StockPilot <em>AI</em></strong></a>
          <div className="app-primary-navigation">
            <a href="/#market-search"><Search size={15} />종목 찾기</a>
            <a href="/#agents"><Sparkles size={15} />AI 분석</a>
            <a aria-current="page" href="/market"><BarChart3 size={15} />시장</a>
            <a href="/paper"><WalletCards size={15} />모의투자</a>
          </div>
          <div className="app-header-actions"><a aria-label="운영 프로필" className="admin-link admin-link--profile" href="/admin"><CircleUserRound size={19} /></a></div>
        </nav>
      </header>
      <MarketOverviewDashboard />
    </main>
  );
}
