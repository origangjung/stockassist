"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchOperationsStatus } from "../lib/admin-api";

const providerLabels: Record<string, string> = {
  market: "시장 데이터",
  financial: "재무",
  disclosure: "공시",
  news: "뉴스",
  investor_flow: "투자자 수급",
  ai_report: "AI 리포트",
  prediction: "예측 엔진",
};

const featureLabels: Record<string, string> = {
  persistence: "DB 저장",
  realtime: "실시간 시세",
  scheduler: "수집 스케줄러",
  reference_alerts: "참고 알림 자동 평가",
  account_sync: "계좌 동기화",
  metrics: "Prometheus 메트릭",
  sentry: "Sentry 오류 수집",
  partition_maintenance: "월별 파티션 관리",
  distributed_rate_limit: "Redis 분산 요청 제한",
  provider_audit_cleanup: "Provider 감사 로그 자동 정리",
  data_lifecycle_cleanup: "운영 데이터 자동 정리",
};

const dependencyLabels: Record<string, string> = {
  database: "PostgreSQL",
  redis: "Redis",
};

function checkedAt(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString("ko-KR");
}

export function OperationsStatusPanel() {
  const query = useQuery({
    queryKey: ["admin", "operations-status"],
    queryFn: fetchOperationsStatus,
    refetchInterval: 30_000,
    staleTime: 15_000,
    retry: 1,
  });
  const data = query.data;

  return (
    <section className="admin-shell operations-admin">
      <header className="admin-heading">
        <div><p>OPERATIONS / RUNTIME</p><h1>시스템 운영 상태</h1></div>
        <button disabled={query.isFetching} onClick={() => { void query.refetch(); }} type="button">
          {query.isFetching ? "확인 중" : "새로고침"}
        </button>
      </header>
      {query.isPending && <div className="admin-state">서비스와 의존성 상태를 확인하는 중입니다.</div>}
      {query.isError && <div className="admin-state error"><b>운영 상태 확인 실패</b><span>{query.error.message}</span></div>}
      {data && (
        <>
          <div className={`operations-banner ${data.ready ? "ready" : "degraded"}`}>
            <div><span>{data.environment} · {data.release}</span><strong>{data.ready ? "서비스 준비 완료" : "일부 필수 의존성 장애"}</strong></div>
            <small>마지막 점검 {checkedAt(data.checked_at)} · 30초마다 자동 갱신</small>
          </div>
          <div className="operations-grid">
            <article className="operations-card">
              <h2>의존성</h2>
              <div className="operations-items">
                {Object.entries(data.readiness.checks).map(([name, dependency]) => (
                  <div key={name}>
                    <span className={`status-dot ${dependency.status}`} />
                    <p><b>{dependencyLabels[name] ?? name}</b><small>{dependency.status === "disabled" ? "기능 비활성" : dependency.latency_ms == null ? dependency.status : `${dependency.latency_ms.toFixed(1)}ms`}</small></p>
                    <em>{dependency.status}</em>
                  </div>
                ))}
              </div>
            </article>
            <article className="operations-card">
              <h2>활성 Provider</h2>
              <div className="operations-items compact">
                {Object.entries(data.providers).map(([name, provider]) => (
                  <div key={name}><p><b>{providerLabels[name] ?? name}</b><small>{provider}</small></p></div>
                ))}
              </div>
            </article>
            <article className="operations-card">
              <h2>기능 플래그</h2>
              <div className="feature-flags">
                {Object.entries(data.features).map(([name, enabled]) => (
                  <span className={enabled ? "enabled" : "disabled"} key={name}><i />{featureLabels[name] ?? name}<b>{enabled ? "ON" : "OFF"}</b></span>
                ))}
              </div>
            </article>
          </div>
          <footer className="operations-realtime">
            <span>실시간 소스 <b>{data.realtime.source}</b></span>
            <span>최대 종목 <b>{data.realtime.max_symbols}</b></span>
            <span>최대 연결 <b>{data.realtime.max_connections}</b></span>
            <span>폴링 주기 <b>{data.realtime.poll_interval_seconds}초</b></span>
            <span>캔들 파티션 <b>{data.partitions.status}</b></span>
            <span>미리 생성 <b>{data.partitions.lookahead_months}개월</b></span>
            {data.partitions.status === "ready" && <span>현재 파티션 <b>{data.partitions.items.length}개</b></span>}
            <span>감사 로그 <b>{data.provider_audit.retention_days}일 보존</b></span>
            <span>자동 정리 <b>{data.provider_audit.status}</b></span>
            {data.provider_audit.last_deleted_count != null && (
              <span>최근 삭제 <b>{data.provider_audit.last_deleted_count}건</b></span>
            )}
            <span>데이터 수명주기 <b>{data.data_lifecycle.status}</b></span>
            {data.data_lifecycle.last_deleted_counts && (
              <span>
                최근 운영 데이터 정리{" "}
                <b>
                  {Object.values(data.data_lifecycle.last_deleted_counts).reduce(
                    (total, count) => total + count,
                    0,
                  )}건
                </b>
              </span>
            )}
          </footer>
        </>
      )}
    </section>
  );
}
