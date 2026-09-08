"use client";

/** 직접 학습 AI의 표본 수와 품질 게이트 상태를 관리자에게 보여준다. */

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CheckCircle2, Database, RefreshCw } from "lucide-react";
import { fetchLocalAiReadiness, type LocalAiReadinessItem } from "../../lib/admin-api";

const reasonLabels: Record<string, string> = {
  "accuracy<0.50": "정확도 50% 미만",
  "accuracy<0.55": "종합 정확도 55% 미만",
  "balanced_accuracy<=0.50": "균형 정확도 50% 이하",
  "balanced_accuracy<=0.52": "균형 정확도 52% 이하",
  "brier_score>=0.25": "확률 오차가 큼",
  "calibration_error>0.10": "확률 보정 오차가 큼",
  "baseline_improvement<=0": "다수 클래스 기준보다 개선 없음",
  "roc_auc<=0.50": "방향 구분력이 무작위 수준",
  artifact_missing: "학습 artifact 없음",
  artifact_integrity_check_failed: "artifact 무결성 검증 실패",
};

const statusLabels: Record<LocalAiReadinessItem["status"], string> = {
  available: "사용 가능",
  quality_rejected: "개선 필요",
  missing: "미학습",
  artifact_invalid: "검증 실패",
};

/** 0~1 지표를 읽기 쉬운 백분율로 표시한다. */
function percent(value?: number): string {
  return value == null ? "-" : `${(value * 100).toFixed(1)}%`;
}

/** 품질 게이트의 기계 판정 사유를 한국어 운영 문구로 바꾼다. */
function reasonText(reason: string): string {
  if (reason.startsWith("validation_samples<")) {
    return `검증 표본 ${reason.split("<")[1]}건 미만`;
  }
  return reasonLabels[reason] ?? reason;
}

/** 직접 학습 AI 모델들의 현재 검증 상태를 자동 갱신하는 패널이다. */
export function LocalAiReadinessPanel() {
  const query = useQuery({
    queryKey: ["admin", "local-ai-readiness"],
    queryFn: fetchLocalAiReadiness,
    refetchInterval: 60_000,
    staleTime: 30_000,
    retry: 1,
  });
  const data = query.data;

  return (
    <section className="admin-shell local-ai-readiness">
      <header className="admin-heading">
        <div>
          <p>LOCAL AI / QUALITY GATE</p>
          <h1>직접 학습 AI 준비도</h1>
        </div>
        <button
          aria-label="AI 준비도 새로고침"
          disabled={query.isFetching}
          onClick={() => { void query.refetch(); }}
          title="새로고침"
          type="button"
        >
          <RefreshCw aria-hidden="true" size={16} />
          {query.isFetching ? "확인 중" : "새로고침"}
        </button>
      </header>

      {query.isPending && <div className="admin-state">모델 artifact를 검증하는 중입니다.</div>}
      {query.isError && (
        <div className="admin-state error">
          <b>AI 준비도를 확인하지 못했습니다.</b>
          <span>{query.error.message}</span>
        </div>
      )}

      {data && (
        <>
          <div className={`local-ai-banner ${data.summary.core_ready ? "ready" : "review"}`}>
            {data.summary.core_ready
              ? <CheckCircle2 aria-hidden="true" size={20} />
              : <AlertTriangle aria-hidden="true" size={20} />}
            <div>
              <b>{data.summary.core_ready ? "핵심 AI 품질 기준 통과" : "일부 AI는 품질 개선이 필요합니다"}</b>
              <span>
                런타임 {data.enabled ? "활성" : "비활성"} · 사용 가능 {data.summary.available}개 · 개선 필요 {data.summary.quality_rejected}개
              </span>
            </div>
          </div>

          <div className="local-ai-summary" aria-label="AI 학습 상태 요약">
            <div><Database aria-hidden="true" size={17} /><span>전체 모델</span><b>{data.summary.total}</b></div>
            <div><CheckCircle2 aria-hidden="true" size={17} /><span>사용 가능</span><b>{data.summary.available}</b></div>
            <div><AlertTriangle aria-hidden="true" size={17} /><span>개선 필요</span><b>{data.summary.quality_rejected}</b></div>
            <div><Database aria-hidden="true" size={17} /><span>미학습·무효</span><b>{data.summary.missing + data.summary.artifact_invalid}</b></div>
          </div>

          <div className="admin-table-wrap local-ai-table-wrap">
            <table className="admin-table local-ai-table">
              <thead>
                <tr><th>AI 역할</th><th>상태</th><th>학습 / 검증</th><th>정확도</th><th>균형 정확도</th><th>AUC</th><th>Brier</th><th>판정 근거</th></tr>
              </thead>
              <tbody>
                {data.items.map((item) => (
                  <tr key={item.agent}>
                    <td><b>{item.label}</b><small>{item.scope === "etf" ? "ETF" : item.agent === "synthesis" ? "종합" : "전문 AI"}</small></td>
                    <td><span className={`local-ai-status ${item.status}`}>{statusLabels[item.status]}</span></td>
                    <td>
                      <b>{item.training_samples.toLocaleString("ko-KR")} / {item.validation_samples.toLocaleString("ko-KR")}</b>
                      {item.remaining_validation_samples > 0 && <small>{item.remaining_validation_samples.toLocaleString("ko-KR")}건 더 필요</small>}
                    </td>
                    <td>{percent(item.metrics.accuracy)}</td>
                    <td>{percent(item.metrics.balanced_accuracy)}</td>
                    <td>{item.metrics.roc_auc?.toFixed(3) ?? "-"}</td>
                    <td>{item.metrics.brier_score?.toFixed(3) ?? "-"}</td>
                    <td className="local-ai-reasons">
                      {item.reasons.length === 0 ? "모든 기준 통과" : item.reasons.map(reasonText).join(" · ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="local-ai-footnote">정확도만으로 승인하지 않으며, 기준선 개선폭·균형 정확도·AUC·확률 보정·검증 표본을 함께 검사합니다.</p>
        </>
      )}
    </section>
  );
}
