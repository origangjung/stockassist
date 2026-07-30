export default function NotFound() {
  return (
    <main>
      <nav>
        <strong>StockPilot <span>AI</span></strong>
        <a href="/">시장 분석</a>
      </nav>
      <section aria-labelledby="not-found-title" className="analysis-panel">
        <div className="analysis-empty">
          <div aria-hidden="true" className="agent-orbit">
            <i>404</i>
            <i>PATH</i>
            <b>AI</b>
            <i>HOME</i>
            <i>BACK</i>
          </div>
          <div className="analysis-empty-copy">
            <span>PAGE NOT FOUND</span>
            <strong id="not-found-title">요청한 화면을 찾을 수 없습니다.</strong>
            <p>주소를 다시 확인하거나 시장 분석 화면에서 종목 검색을 시작해 주세요.</p>
            <div><a className="share-result" href="/">시장 분석으로 돌아가기</a></div>
          </div>
        </div>
      </section>
    </main>
  );
}
