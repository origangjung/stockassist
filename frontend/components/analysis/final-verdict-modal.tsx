"use client";

/** final-verdict-modal 파일은 AI 분석 진행과 결과 화면 기능을 담당한다. */

import { useEffect, useId, useRef } from "react";
import type { AIAnalysisReport, ReferenceSignal } from "../../lib/market-api";
import { humanizeAnalysisText, localConfidenceLabel } from "../../lib/local-ai-presentation";
import { agentDisplayName } from "../../lib/agent-labels";
import { PixelAnalyst } from "./analysis-progress";
import type { MeetingAgentKey } from "./agent-meeting-stage";

/** VerdictTranscript 인터페이스는 AI 분석 진행과 결과 표현을 담당합니다.에서 교환하는 필드 계약을 정의합니다. */
interface VerdictTranscript {
  agent: MeetingAgentKey;
  experimental: boolean;
  name: string;
  role: string;
  headline: string;
}

/** FinalVerdictModalProps 인터페이스는 AI 분석 진행과 결과 표현을 담당합니다.에서 교환하는 필드 계약을 정의합니다. */
interface FinalVerdictModalProps {
  currency: string;
  currentPrice?: string;
  inline?: boolean;
  name: string;
  onClose?: () => void;
  open: boolean;
  report: AIAnalysisReport;
  transcript: VerdictTranscript[];
}

const verdictLabels: Record<ReferenceSignal, string> = {
  positive_watch: "상승 우위 참고 신호",
  neutral_watch: "중립 참고 신호",
  defensive_watch: "하락 우위 참고 신호",
  risk_aware: "위험 우선 관망",
  data_insufficient: "판단 보류",
};

const statusLabels: Record<string, string> = {
  available: "사용 가능",
  model_missing: "모델 없음",
  data_unavailable: "데이터 부족",
  artifact_invalid: "검증 실패",
  quality_rejected: "품질 기준 미달",
  insufficient_specialists: "참여 모델 부족",
};
const requiredDisclaimer = "본 분석은 투자 자문이 아닌 참고 정보입니다. 투자 판단과 책임은 본인에게 있습니다.";

const signalLabels: Record<string, string> = {
  positive: "긍정",
  neutral: "중립",
  negative: "부정",
};

/** `validationSamples`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function validationSamples(evidence: string[]) {
  const raw = evidence.find((item) => item.startsWith("validation_samples="))?.split("=", 2)[1];
  const samples = Number(raw);
  return Number.isFinite(samples) ? new Intl.NumberFormat("ko-KR").format(samples) : "-";
}

/** `probabilityBand`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function probabilityBand(probability: number | null, confidence: number | null) {
  if (probability == null) return "판단 보류";
  return `${Math.round(probability * 100)}% · 신뢰도 ${localConfidenceLabel(confidence)}`;
}

/** `formatPrice`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function formatPrice(value: string | number, currency: string) {
  const amount = Number(value);
  if (!Number.isFinite(amount)) return String(value);
  return `${currency === "USD" ? "$" : "₩"} ${new Intl.NumberFormat(currency === "KRW" ? "ko-KR" : "en-US", {
    maximumFractionDigits: currency === "KRW" ? 0 : 2,
  }).format(amount)}`;
}

/** `FinalVerdictModal`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function FinalVerdictModal({
  currency,
  currentPrice,
  inline = false,
  name,
  onClose,
  open,
  report,
  transcript,
}: FinalVerdictModalProps) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const modalRef = useRef<HTMLElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);
  const synthesisApproved = report.local_ai_synthesis?.status === "available";
  const modelEntries = Object.entries(report.local_ai_findings ?? {});
  const showValidationSamples = modelEntries.some(([, finding]) => validationSamples(finding.evidence) !== "-");
  const levels = report.support_resistance;
  const current = Number(currentPrice);
  const support = Number(levels?.support);
  const resistance = Number(levels?.resistance);
  const riskReward = Number.isFinite(current) && Number.isFinite(support) && Number.isFinite(resistance) && current > support
    ? (resistance - current) / (current - support)
    : null;
  const strengthLabel = report.signal_strength >= 65 ? "STRONG" : "WEAK";

  useEffect(() => {
    if (!open || inline) return;
    previousFocusRef.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    closeRef.current?.focus({ preventScroll: true });
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose?.();
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = Array.from(modalRef.current?.querySelectorAll<HTMLElement>(
        'button:not([disabled]), a[href], [tabindex]:not([tabindex="-1"])',
      ) ?? []);
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
      if (previousFocusRef.current?.isConnected) previousFocusRef.current.focus({ preventScroll: true });
    };
  }, [inline, onClose, open]);

  if (!open) return null;

  const verdict = (
    <section
      aria-labelledby={titleId}
      aria-modal={inline ? undefined : true}
      /** Name 클래스는 AI 분석 진행과 결과 표현을 담당합니다.의 상태와 동작을 캡슐화합니다. */
      className={`final-verdict-modal signal-${report.reference_signal}${inline ? " final-verdict-panel" : ""}`}
      onMouseDown={inline ? undefined : (event) => event.stopPropagation()}
      ref={modalRef}
      role={inline ? "region" : "dialog"}
    >
        <header className="final-verdict-modal__header">
          <div><span>{report.symbol} · FINAL VERDICT</span><h2 id={titleId}>{name}</h2></div>
          {!inline && <button aria-label="최종 분석 닫기" onClick={onClose} ref={closeRef} type="button">×</button>}
        </header>

        <div className="final-verdict-signal">
          <div><small>{strengthLabel} · REFERENCE SIGNAL</small><strong>{verdictLabels[report.reference_signal]}</strong></div>
          <dl>
            <div><dt>신뢰도</dt><dd>{report.confidence === "high" ? "높음" : report.confidence === "medium" ? "보통" : "낮음"}</dd></div>
            <div><dt>분석 기간</dt><dd>{report.prediction_horizon_days ? `${report.prediction_horizon_days}거래일` : "단기"}</dd></div>
          </dl>
        </div>

        {!synthesisApproved && (
          <p className="final-verdict-quality" role="status">
            자체 종합 AI는 현재 품질 기준을 통과하지 못해 점수와 확률을 표시하지 않습니다. 아래 결과는 구조화된 참고 진단입니다.
          </p>
        )}

        <div className="final-verdict-modal__body">
          <section className="final-verdict-comment">
            <PixelAnalyst agent="director" size="message" />
            <div><span>회장님 · 종합 코멘트</span><p>{humanizeAnalysisText(report.summary)}</p></div>
          </section>

          <section className="final-verdict-section">
            <h3>핵심 근거</h3>
            <ul>{report.key_points.slice(0, 3).map((point) => <li key={point}>{humanizeAnalysisText(point)}</li>)}</ul>
          </section>

          <section className="final-verdict-section">
            <h3>참고 레벨</h3>
            <div className="final-verdict-levels">
              <span><small>관찰 진입 구간</small><b>{levels && currentPrice ? `${formatPrice(levels.support, currency)} – ${formatPrice(currentPrice, currency)}` : "데이터 없음"}</b></span>
              <span className="level-down"><small>손절 참고선</small><b>{levels ? formatPrice(levels.support, currency) : "데이터 없음"}</b></span>
              <span className="level-up"><small>익절 참고선 · R/R {riskReward == null ? "계산 불가" : riskReward.toFixed(2)}</small><b>{levels ? formatPrice(levels.resistance, currency) : "데이터 없음"}</b></span>
            </div>
          </section>

          <section className="final-verdict-section final-verdict-note">
            <h3>최종 판단 요약</h3>
            <p>{humanizeAnalysisText(report.counterpoints[0] ?? report.signal_basis[0] ?? "현재 공개 데이터 범위에서 추가 반대 근거가 확인되지 않았습니다.")}</p>
          </section>

          <details className="final-verdict-details">
            <summary><span>DETAILS</span><b>회의록과 모델 상태 보기</b></summary>
            <div>
              <section className="final-verdict-section">
                <h3>회의록</h3>
                <ol className="final-verdict-transcript">
                  {transcript.map((entry) => (
                    <li className={`agent-${entry.agent}`} key={entry.agent}><PixelAnalyst agent={entry.agent} /><div><b>{entry.name}</b><small>{entry.role}</small>{entry.experimental && <span className="experimental-model-badge">실험 모델</span>}<p>{humanizeAnalysisText(entry.headline)}</p></div></li>
                  ))}
                </ol>
              </section>

              <section className="final-verdict-section">
                <h3>모델 상태</h3>
                <div className="final-verdict-table-wrap">
                  <table><thead><tr><th>AI</th><th>상태</th><th>신호</th><th>확률·신뢰도</th>{showValidationSamples && <th>검증 표본</th>}<th>판정 반영</th></tr></thead><tbody>
                    {modelEntries.map(([agent, finding]) => (
                      <tr key={agent}>
                        <td><b>{agentDisplayName(agent)}</b>{(["financial", "news"].includes(agent) || finding.status !== "available") && <small className="experimental-model-badge">실험 모델</small>}</td>
                        <td>{statusLabels[finding.status] ?? "상태 확인 중"}</td>
                        <td>{finding.signal == null ? "판단 보류" : signalLabels[finding.signal]}</td>
                        <td>{probabilityBand(finding.probability, finding.confidence)}</td>
                        {showValidationSamples && <td>{validationSamples(finding.evidence) === "-" ? "자료 없음" : validationSamples(finding.evidence)}</td>}
                        <td>{finding.status === "available" ? "후보 근거" : "종합 판단 미반영"}</td>
                      </tr>
                    ))}
                    <tr><td><b>종합 판단</b></td><td>{statusLabels[report.local_ai_synthesis?.status ?? "data_unavailable"] ?? "판단 보류"}</td><td>{report.local_ai_synthesis?.signal == null ? "판단 보류" : signalLabels[report.local_ai_synthesis.signal]}</td><td>{probabilityBand(report.local_ai_synthesis?.probability ?? null, report.local_ai_synthesis?.confidence ?? null)}</td>{showValidationSamples && <td>전문 AI {report.local_ai_synthesis?.available_agents ?? 0}개</td>}<td>{synthesisApproved ? "참고 진단 반영" : "종합 판단 미반영"}</td></tr>
                  </tbody></table>
                </div>
              </section>
            </div>
          </details>
        </div>

        <footer><p>{requiredDisclaimer}</p><small>{report.model_version} · {new Date(report.data_as_of).toLocaleString("ko-KR")}</small></footer>
    </section>
  );

  if (inline) return verdict;
  return <div className="final-verdict-backdrop" onMouseDown={onClose}>{verdict}</div>;
}
