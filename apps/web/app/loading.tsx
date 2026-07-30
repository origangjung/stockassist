export default function Loading() {
  return (
    <main aria-busy="true" aria-live="polite">
      <nav>
        <strong>StockPilot <span>AI</span></strong>
        <div>시장 분석</div>
      </nav>
      <section aria-label="화면을 준비하는 중" className="analysis-panel">
        <div className="analysis-loading">
          <div aria-hidden="true" className="agent-orbit">
            <i>DATA</i>
            <i>RISK</i>
            <b>AI</b>
            <i>NEWS</i>
            <i>FLOW</i>
          </div>
          <div className="analysis-empty-copy" role="status">
            <span>STOCKPILOT · LOADING</span>
            <strong>분석 화면을 준비하고 있습니다.</strong>
            <p>네트워크 상태에 따라 잠시 시간이 걸릴 수 있습니다.</p>
          </div>
        </div>
      </section>
    </main>
  );
}
