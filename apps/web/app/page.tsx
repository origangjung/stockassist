import { MarketDashboard } from "../components/market-dashboard";

export default function Dashboard() {
  return (
    <main>
      <nav><strong>StockPilot <span>AI</span></strong><div>시장 분석 <b>Mock data</b><a href="/admin">운영</a></div></nav>
      <section className="hero">
        <p>INVESTMENT DECISION SUPPORT</p><h1>데이터를 근거로,<br />더 선명한 투자 판단.</h1>
        <small>모든 정보는 참고용이며 투자 자문 또는 매매 지시가 아닙니다.</small>
      </section>
      <MarketDashboard />
      <section className="notice"><b>Reference Signal</b><span>모든 점수와 참고 시그널은 충분한 백테스트 검증을 통과하기 전까지 experimental 상태로 표시됩니다.</span></section>
    </main>
  );
}
