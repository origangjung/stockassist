import { MarketDashboard } from "../components/market-dashboard";

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
          <div className="app-header-actions">
            <span className="app-section-label">분석</span>
            <b>EXPERIMENTAL</b>
            <a className="admin-link" href="/admin">운영 <span aria-hidden="true">↗</span></a>
          </div>
        </nav>
      </header>
      <section className="hero" aria-labelledby="service-heading">
        <div className="hero-copy">
          <p><span aria-hidden="true" />REFERENCE-ONLY STOCK RESEARCH</p>
          <h1 id="service-heading">근거가 남는<br /><em>종목 분석.</em></h1>
          <small>한 종목의 숫자와 맥락을 나누어 보고, 판단에 필요한 반대 근거까지 함께 남깁니다.</small>
          <ul className="hero-principles" aria-label="서비스 원칙">
            <li>5개 관점</li>
            <li>반대 근거 포함</li>
            <li>매매 지시 없음</li>
          </ul>
        </div>
        <aside className="hero-status" aria-label="분석 서비스 안내">
          <header>
            <span>ANALYSIS DESK</span>
            <b><i aria-hidden="true" />준비됨</b>
          </header>
          <strong>한 종목을<br />다섯 관점으로 봅니다.</strong>
          <p>차트, 재무, 뉴스·공시, 수급, 위험 신호를 나누어 살핀 뒤 근거와 함께 정리합니다.</p>
          <div className="hero-course" aria-label="분석 순서">
            <i><b>01</b><span>입력</span></i>
            <i><b>02</b><span>검토</span></i>
            <i><b>03</b><span>정리</span></i>
          </div>
          <div className="hero-signal-plot" aria-hidden="true"><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /><i /></div>
        </aside>
      </section>
      <section className="experience-rail" aria-label="분석 경험 안내">
        <article>
          <span>01 · START</span>
          <b>종목명·티커로 바로 시작</b>
          <p>국내 종목 코드와 미국 티커, 한글 별칭까지 검색할 수 있습니다.</p>
        </article>
        <article>
          <span>02 · REVIEW</span>
          <b>한 화면에서 근거를 비교</b>
          <p>차트·재무·뉴스·수급·위험 신호를 같은 기준 시각으로 확인합니다.</p>
        </article>
        <article>
          <span>03 · DECIDE</span>
          <b>참고 신호는 결론이 아닙니다</b>
          <p>점수와 확률은 근거를 읽기 위한 참고 정보로만 제공합니다.</p>
        </article>
      </section>
      <section aria-label="종목 검색과 분석" id="market-search">
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
