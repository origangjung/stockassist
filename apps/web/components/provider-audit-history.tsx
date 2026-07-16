"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { fetchProviderAuditHistory, ProviderAuditOutcome } from "../lib/admin-api";

const PAGE_SIZE = 25;

const outcomeLabels: Record<ProviderAuditOutcome, string> = {
  success: "성공",
  error: "API 오류",
  transport_error: "연결 오류",
};

function date(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString("ko-KR");
}

function requestId(value: string | null): string {
  return value || "제공되지 않음";
}

export function ProviderAuditHistoryPanel() {
  const [provider, setProvider] = useState("");
  const [outcome, setOutcome] = useState<"" | ProviderAuditOutcome>("");
  const [offset, setOffset] = useState(0);
  const query = useQuery({
    queryKey: ["admin", "provider-audits", provider, outcome, offset],
    queryFn: () => fetchProviderAuditHistory(provider, outcome, PAGE_SIZE, offset),
    staleTime: 15_000,
    retry: 1,
  });
  const data = query.data;

  const changeProvider = (value: string) => {
    setProvider(value);
    setOffset(0);
  };

  const changeOutcome = (value: "" | ProviderAuditOutcome) => {
    setOutcome(value);
    setOffset(0);
  };

  return (
    <section className="admin-shell provider-audit-admin">
      <header className="admin-heading">
        <div>
          <p>PROVIDER / AUDIT TRAIL</p>
          <h1>외부 API 감사 이력</h1>
        </div>
        <form onSubmit={(event) => event.preventDefault()}>
          <select
            aria-label="Provider 필터"
            onChange={(event) => changeProvider(event.target.value)}
            value={provider}
          >
            <option value="">전체 Provider</option>
            <option value="toss">Toss</option>
          </select>
          <select
            aria-label="호출 결과 필터"
            onChange={(event) =>
              changeOutcome(event.target.value as "" | ProviderAuditOutcome)
            }
            value={outcome}
          >
            <option value="">전체 결과</option>
            <option value="success">성공</option>
            <option value="error">API 오류</option>
            <option value="transport_error">연결 오류</option>
          </select>
          <button disabled={query.isFetching} onClick={() => query.refetch()} type="button">
            새로고침
          </button>
        </form>
      </header>

      <p className="provider-audit-privacy">
        토큰, 계좌번호, 쿼리·요청 본문과 응답 본문은 저장하지 않습니다. 내부 요청 ID와
        Provider 요청 ID만 장애 추적에 사용합니다.
      </p>

      {query.isPending && (
        <div className="admin-state">외부 API 감사 이력을 불러오는 중입니다.</div>
      )}
      {query.isError && (
        <div className="admin-state error">
          <b>감사 이력 조회 실패</b>
          <span>{query.error.message}</span>
        </div>
      )}
      {data?.persistence_status === "disabled" && (
        <div className="admin-state">
          DB 저장이 비활성화되어 Provider 감사 이력을 보존하지 않습니다.
        </div>
      )}
      {data?.persistence_status === "enabled" && (
        <>
          <div className="provider-audit-summary">
            <span>필터 결과</span>
            <strong>{data.total}</strong>
            <small>저장된 최종 호출 결과</small>
          </div>

          {data.items.length === 0 ? (
            <div className="admin-state">조건에 해당하는 Provider 호출 이력이 없습니다.</div>
          ) : (
            <div className="admin-table-wrap">
              <table className="admin-table provider-audit-table">
                <thead>
                  <tr>
                    <th>결과</th>
                    <th>Provider / 그룹</th>
                    <th>요청</th>
                    <th>상태</th>
                    <th>요청 ID</th>
                    <th>시도 / 지연</th>
                    <th>발생 시각</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr key={item.audit_id}>
                      <td>
                        <span className={`provider-audit-outcome ${item.outcome}`}>
                          {outcomeLabels[item.outcome]}
                        </span>
                      </td>
                      <td>
                        <b>{item.provider}</b>
                        <small>{item.api_group}</small>
                      </td>
                      <td>
                        <b>{item.method}</b>
                        <code>{item.endpoint}</code>
                      </td>
                      <td>
                        <b>{item.status_code ?? "-"}</b>
                        <small>{item.error_code ?? "오류 없음"}</small>
                      </td>
                      <td className="provider-audit-ids">
                        <code title={requestId(item.provider_request_id)}>
                          EXT {requestId(item.provider_request_id)}
                        </code>
                        <code title={item.internal_request_id}>INT {item.internal_request_id}</code>
                      </td>
                      <td>
                        <b>{item.attempt_count}회</b>
                        <small>{item.duration_ms.toFixed(1)}ms</small>
                      </td>
                      <td>{date(item.occurred_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <footer className="quality-pagination">
            <span>
              {data.total === 0 ? 0 : data.offset + 1}–
              {Math.min(data.offset + data.limit, data.total)} / {data.total}
            </span>
            <div>
              <button
                disabled={offset === 0 || query.isFetching}
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                type="button"
              >
                이전
              </button>
              <button
                disabled={offset + PAGE_SIZE >= data.total || query.isFetching}
                onClick={() => setOffset(offset + PAGE_SIZE)}
                type="button"
              >
                다음
              </button>
            </div>
          </footer>
        </>
      )}
    </section>
  );
}
