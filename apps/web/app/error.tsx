"use client";

interface PageErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error: _error, reset }: PageErrorProps) {
  return (
    <main>
      <nav>
        <strong>StockPilot <span>AI</span></strong>
        <a href="/">첫 화면</a>
      </nav>
      <section aria-labelledby="page-error-title" className="analysis-panel">
        <div aria-live="assertive" className="analysis-error" role="alert">
          <b id="page-error-title">화면을 불러오지 못했습니다.</b>
          <span>일시적인 연결 문제일 수 있습니다. 다시 시도하거나 첫 화면으로 돌아가 주세요.</span>
          <div className="meeting-actions">
            <button onClick={reset} type="button">다시 시도</button>
            <a className="share-result" href="/">첫 화면으로</a>
          </div>
        </div>
      </section>
    </main>
  );
}
