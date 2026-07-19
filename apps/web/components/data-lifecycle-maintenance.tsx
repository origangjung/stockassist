"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { cleanupDataLifecycle, fetchDataLifecyclePreview } from "../lib/admin-api";

const datasetLabels: Record<string, string> = {
  data_quality_logs: "데이터 품질 로그",
  news: "뉴스 원문 메타데이터",
  disclosures: "공시 원문 메타데이터",
};

function date(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString("ko-KR");
}

export function DataLifecycleMaintenancePanel() {
  const queryClient = useQueryClient();
  const preview = useQuery({
    queryKey: ["admin", "data-lifecycle", "preview"],
    queryFn: fetchDataLifecyclePreview,
    staleTime: 30_000,
    retry: 1,
  });
  const cleanup = useMutation({
    mutationFn: cleanupDataLifecycle,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin", "data-lifecycle"] }),
        queryClient.invalidateQueries({ queryKey: ["admin", "operations-status"] }),
        queryClient.invalidateQueries({ queryKey: ["admin", "data-quality"] }),
      ]);
    },
  });
  const data = preview.data;

  const runCleanup = () => {
    const eligible = Object.values(data?.eligible_counts ?? {}).reduce(
      (total, count) => total + count,
      0,
    );
    if (window.confirm(`미리보기에서 확인한 만료 데이터 ${eligible}건을 정리합니다. 계속할까요?`)) {
      cleanup.mutate();
    }
  };

  return (
    <section className="admin-shell data-lifecycle-admin">
      <header className="admin-heading">
        <div>
          <p>OPERATIONS / DATA LIFECYCLE</p>
          <h1>운영 데이터 보존 정책</h1>
        </div>
        <div className="data-lifecycle-actions">
          <button disabled={preview.isFetching} onClick={() => preview.refetch()} type="button">
            {preview.isFetching ? "확인 중" : "미리보기 갱신"}
          </button>
          <button
            disabled={
              cleanup.isPending ||
              !data?.enabled ||
              data?.preview_status !== "ready" ||
              !Object.values(data.eligible_counts ?? {}).some((count) => count > 0)
            }
            onClick={runCleanup}
            type="button"
          >
            {cleanup.isPending ? "정리 중" : "만료 데이터 정리"}
          </button>
        </div>
      </header>

      <p className="data-lifecycle-scope">
        이 작업은 데이터 품질 로그·뉴스·공시만 대상으로 합니다. 캔들, 거래, 백테스트,
        예측, AI 리포트, 포트폴리오 데이터는 재현성과 감사 추적을 위해 자동 삭제 대상에서
        제외됩니다.
      </p>

      {preview.isPending && <div className="admin-state">만료 대상 건수를 계산하는 중입니다.</div>}
      {preview.isError && (
        <div className="admin-state error">
          <b>보존 정책 미리보기 실패</b>
          <span>{preview.error.message}</span>
        </div>
      )}
      {data?.preview_status === "failed" && (
        <div className="admin-state error">
          <b>데이터베이스 미리보기 실패</b>
          <span>{data.preview_error_type ?? "unknown_error"}</span>
        </div>
      )}
      {data?.preview_status === "ready" && (
        <div className="data-lifecycle-grid">
          {Object.entries(data.retention_days).map(([dataset, retentionDays]) => (
            <article key={dataset}>
              <span>{datasetLabels[dataset] ?? dataset}</span>
              <strong>{data.eligible_counts?.[dataset] ?? 0}건</strong>
              <small>{retentionDays}일 보존</small>
              <small>
                기준 시각 {data.cutoffs?.[dataset] ? date(data.cutoffs[dataset]) : "-"}
              </small>
            </article>
          ))}
        </div>
      )}
      {!data?.enabled && (
        <p className="data-lifecycle-disabled">
          미리보기 전용 상태입니다. 정리를 실행하려면 DATA_LIFECYCLE_CLEANUP_ENABLED를
          활성화해야 합니다.
        </p>
      )}
      {cleanup.data && (
        <div className={`provider-audit-cleanup-result ${cleanup.data.status}`}>
          <b>정리 상태: {cleanup.data.status}</b>
          <span>
            삭제 {Object.values(cleanup.data.last_deleted_counts ?? {}).reduce(
              (total, count) => total + count,
              0,
            )}건
          </span>
        </div>
      )}
      {cleanup.isError && (
        <div className="admin-state error">
          <b>만료 데이터 정리 요청 실패</b>
          <span>{cleanup.error.message}</span>
        </div>
      )}
    </section>
  );
}
