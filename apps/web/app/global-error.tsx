"use client";

interface GlobalErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

const pageStyle = {
  background: "#07101f",
  color: "#e8edf8",
  fontFamily: "Arial, sans-serif",
  minHeight: "100vh",
  padding: "24px",
} as const;

const panelStyle = {
  background: "linear-gradient(145deg, #0d1829, #08111f 70%)",
  border: "1px solid #273750",
  borderRadius: "14px",
  margin: "48px auto",
  maxWidth: "720px",
  padding: "40px 28px",
  textAlign: "center",
} as const;

const retryStyle = {
  background: "#1877ce",
  border: "1px solid #4da9ff",
  borderRadius: "8px",
  color: "white",
  cursor: "pointer",
  font: "inherit",
  fontWeight: 700,
  padding: "11px 18px",
} as const;

const homeStyle = {
  border: "1px solid #334d6b",
  borderRadius: "999px",
  color: "#a7bdd6",
  fontSize: "14px",
  padding: "10px 14px",
  textDecoration: "none",
} as const;

export default function GlobalError({ error: _error, reset }: GlobalErrorProps) {
  return (
    <html lang="ko">
      <body style={pageStyle}>
        <main>
          <div style={panelStyle}>
            <p style={{ color: "#72b8ff", fontSize: "12px", letterSpacing: "0.12em" }}>
              STOCKPILOT AI
            </p>
            <h1 id="global-error-title" style={{ fontSize: "clamp(28px, 6vw, 42px)", margin: "12px 0" }}>
              예기치 않은 문제가 발생했습니다.
            </h1>
            <p style={{ color: "#a7b4c7", lineHeight: 1.65, margin: "0 auto 24px", maxWidth: "520px" }}>
              개인 정보나 분석 데이터는 표시하지 않았습니다. 다시 시도하거나 첫 화면으로 돌아가 주세요.
            </p>
            <div aria-labelledby="global-error-title" aria-live="assertive" role="alert" style={{ display: "flex", flexWrap: "wrap", gap: "10px", justifyContent: "center" }}>
              <button onClick={reset} style={retryStyle} type="button">다시 시도</button>
              <a href="/" style={homeStyle}>첫 화면으로</a>
            </div>
          </div>
        </main>
      </body>
    </html>
  );
}
