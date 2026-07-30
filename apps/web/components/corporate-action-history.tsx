"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import {
  CorporateActionCandidateItem,
  approveCorporateActionCandidate,
  fetchCorporateActionApprovalStatus,
  fetchCorporateActionCandidateStatus,
  fetchCorporateActionCandidates,
  fetchCorporateActionHistory,
  fetchCorporateActionIngestionStatus,
} from "../lib/admin-api";

const PAGE_SIZE = 25;
const CONFIRMATION_PHRASE = "CONFIRM_CORPORATE_ACTION";
const actionLabels: Record<string, string> = {
  split: "주식분할",
  reverse_split: "주식병합",
  cash_dividend: "현금배당",
  stock_dividend: "주식배당",
  rights_issue: "유상증자",
};

interface ApprovalSelection {
  candidate: CorporateActionCandidateItem;
  groupHint: string;
}

function formatDate(value: string | null): string {
  if (!value) return "-";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString("ko-KR");
}

export function CorporateActionHistoryPanel() {
  const queryClient = useQueryClient();
  const [symbolInput, setSymbolInput] = useState("");
  const [symbol, setSymbol] = useState("");
  const [offset, setOffset] = useState(0);
  const [approvalSelection, setApprovalSelection] = useState<ApprovalSelection | null>(null);
  const [effectiveAt, setEffectiveAt] = useState("");
  const [exchangeEvidenceUrl, setExchangeEvidenceUrl] = useState("");
  const [confirmation, setConfirmation] = useState("");

  const query = useQuery({
    queryKey: ["admin", "corporate-actions", "history", symbol, offset],
    queryFn: () => fetchCorporateActionHistory(symbol, PAGE_SIZE, offset),
    staleTime: 30_000,
    retry: 1,
  });
  const ingestionQuery = useQuery({
    queryKey: ["admin", "corporate-actions", "ingestion-status"],
    queryFn: fetchCorporateActionIngestionStatus,
    staleTime: 30_000,
    retry: 1,
  });
  const candidateStatusQuery = useQuery({
    queryKey: ["admin", "corporate-actions", "candidate-status"],
    queryFn: fetchCorporateActionCandidateStatus,
    staleTime: 30_000,
    retry: 1,
  });
  const approvalStatusQuery = useQuery({
    queryKey: ["admin", "corporate-actions", "approval-status"],
    queryFn: fetchCorporateActionApprovalStatus,
    staleTime: 30_000,
    retry: 1,
  });
  const candidateQuery = useMutation({
    mutationFn: (candidateSymbol: string) => {
      const end = new Date();
      const start = new Date(end);
      start.setUTCFullYear(start.getUTCFullYear() - 1);
      return fetchCorporateActionCandidates(
        "dart",
        candidateSymbol,
        start.toISOString().slice(0, 10),
        end.toISOString().slice(0, 10),
      );
    },
    onSuccess: () => setApprovalSelection(null),
  });
  const approvalMutation = useMutation({
    mutationFn: async () => {
      if (!approvalSelection || !candidateQuery.data) {
        throw new Error("승인할 후보를 다시 선택해 주세요.");
      }
      const parsedEffectiveAt = new Date(effectiveAt);
      if (Number.isNaN(parsedEffectiveAt.getTime())) {
        throw new Error("유효한 적용 시각을 입력해 주세요.");
      }
      return approveCorporateActionCandidate("dart", candidateQuery.data.symbol, {
        start: candidateQuery.data.requested_start,
        end: candidateQuery.data.requested_end,
        group_hint: approvalSelection.groupHint,
        receipt_no: approvalSelection.candidate.receipt_no,
        effective_at: parsedEffectiveAt.toISOString(),
        exchange_evidence_url: exchangeEvidenceUrl.trim(),
        confirmation: CONFIRMATION_PHRASE,
      });
    },
    onSuccess: async () => {
      setApprovalSelection(null);
      setEffectiveAt("");
      setExchangeEvidenceUrl("");
      setConfirmation("");
      await queryClient.invalidateQueries({
        queryKey: ["admin", "corporate-actions", "history"],
      });
    },
  });

  const data = query.data;
  const ingestion = ingestionQuery.data;
  const candidateStatus = candidateStatusQuery.data;
  const approvalStatus = approvalStatusQuery.data;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setSymbol(symbolInput.trim().toUpperCase());
    setOffset(0);
  };

  const previewCandidates = () => {
    const candidateSymbol = symbolInput.trim().toUpperCase();
    if (candidateSymbol) candidateQuery.mutate(candidateSymbol);
  };

  const selectApproval = (candidate: CorporateActionCandidateItem) => {
    const group = candidateQuery.data?.revision_groups.find((item) =>
      item.receipt_nos.includes(candidate.receipt_no),
    );
    if (!group) return;
    approvalMutation.reset();
    setApprovalSelection({ candidate, groupHint: group.group_hint });
    setEffectiveAt("");
    setExchangeEvidenceUrl("");
    setConfirmation("");
  };

  const approvalReady =
    Boolean(approvalSelection) &&
    Boolean(effectiveAt) &&
    exchangeEvidenceUrl.trim().startsWith("https://") &&
    confirmation === CONFIRMATION_PHRASE &&
    approvalStatus?.available === true;

  return (
    <section className="admin-shell corporate-action-admin">
      <header className="admin-heading">
        <div>
          <p>PIPELINE / CORPORATE ACTIONS</p>
          <h1>기업행위 보정 이력</h1>
        </div>
        <form onSubmit={submit}>
          <input
            aria-label="기업행위 종목 코드"
            maxLength={16}
            onChange={(event) => setSymbolInput(event.target.value)}
            placeholder="종목 코드"
            value={symbolInput}
          />
          <button type="submit">조회</button>
          <button
            disabled={!symbolInput.trim() || !candidateStatus?.available || candidateQuery.isPending}
            onClick={previewCandidates}
            type="button"
          >
            {candidateQuery.isPending ? "후보 확인 중" : "DART 후보"}
          </button>
        </form>
      </header>

      <p className="corporate-action-safety">
        이 화면은 기준 시점과 revision을 검토하는 운영 도구입니다. 보정 계산은 별도 뷰에서
        수행하며 raw·cleaned 캔들을 덮어쓰지 않습니다.
      </p>

      {ingestion && (
        <div className="corporate-action-ingestion">
          <span>
            수집 상태
            <b className={ingestion.ingestion_available ? "enabled" : "disabled"}>
              {ingestion.ingestion_available ? "사용 가능" : "공급자 미등록"}
            </b>
          </span>
          <span>검증 공급자 <b>{ingestion.verified_source_count}</b></span>
          <span>배치 한도 <b>{ingestion.max_batch_records}</b></span>
          <span>소비자 연결 <b>{ingestion.consumer_adjustment_mode}</b></span>
          {ingestion.sources.map((source) => (
            <span key={source.name}>
              {source.name} <b>{source.trust_status}</b> · {source.markets.join("/")}
            </span>
          ))}
          {ingestion.source_candidates.map((source) => (
            <span className="candidate" key={`candidate:${source.name}`}>
              후보 {source.name} <b>{source.trust_status}</b> · {source.markets.join("/")}
            </span>
          ))}
        </div>
      )}
      {ingestionQuery.isError && (
        <div className="ingestion-notice error">기업행위 수집 상태를 확인하지 못했습니다.</div>
      )}
      {candidateStatus && !candidateStatus.available && (
        <div className="corporate-action-candidate-note">
          DART_API_KEY가 없어 공시 후보 조회가 비활성화되어 있습니다.
        </div>
      )}
      {approvalStatus && !approvalStatus.available && (
        <div className="corporate-action-candidate-note">
          수동 승인은 기본적으로 비활성화됩니다. 서버에서 승인 기능과 DB 저장을 명시적으로
          켠 경우에만 사용할 수 있습니다.
        </div>
      )}
      {candidateQuery.isError && (
        <div className="ingestion-notice error">{candidateQuery.error.message}</div>
      )}

      {candidateQuery.data && (
        <div className="corporate-action-candidates">
          <header>
            <div>
              <span>READ-ONLY EVIDENCE</span>
              <h2>DART 검토 후보 · {candidateQuery.data.symbol}</h2>
            </div>
            <b>{candidateQuery.data.count}건</b>
          </header>
          <p>
            후보는 조회만으로 저장되지 않습니다. 승인 시 서버가 후보를 다시 조회하며, 거래소
            증빙 URL과 정확한 확인 문구가 모두 필요합니다.
          </p>
          {candidateQuery.data.items.length === 0 ? (
            <div className="admin-state">최근 1년간 구조화된 후보가 없습니다.</div>
          ) : (
            <div className="admin-table-wrap">
              <table className="admin-table corporate-action-table">
                <thead>
                  <tr>
                    <th>접수일</th><th>후보 유형</th><th>기준일</th><th>이론 계수</th>
                    <th>검토 항목</th><th>원문</th><th>수동 승인</th>
                  </tr>
                </thead>
                <tbody>
                  {candidateQuery.data.items.map((item) => {
                    const hasGroup = candidateQuery.data.revision_groups.some((group) =>
                      group.receipt_nos.includes(item.receipt_no),
                    );
                    const factorsReady =
                      item.proposed_price_factor != null && item.proposed_volume_factor != null;
                    return (
                      <tr key={item.event_id}>
                        <td>{item.filed_on}</td>
                        <td>{actionLabels[item.action_type] ?? item.action_type}</td>
                        <td>{item.record_date ?? "미확정"}</td>
                        <td>
                          <code>P {item.proposed_price_factor ?? "-"}</code>
                          <code>V {item.proposed_volume_factor ?? "-"}</code>
                        </td>
                        <td>
                          {item.report_name && <small>{item.report_name}</small>}
                          {item.warnings.map((warning) => <small key={warning}>{warning}</small>)}
                        </td>
                        <td>
                          <a href={item.evidence_url} rel="noreferrer" target="_blank">DART 원문</a>
                        </td>
                        <td>
                          <button
                            disabled={!approvalStatus?.available || !hasGroup || !factorsReady}
                            onClick={() => selectApproval(item)}
                            type="button"
                          >
                            승인 검토
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {candidateQuery.data.revision_groups.some((group) => group.receipt_nos.length > 1) && (
            <div className="corporate-action-reconciliation">
              <b>정정 revision 그룹 제안</b>
              {candidateQuery.data.revision_groups
                .filter((group) => group.receipt_nos.length > 1)
                .map((group) => (
                  <span key={group.group_hint}>
                    {group.confidence} · {group.receipt_nos.join(" → ")} · 수동 확인 필수
                  </span>
                ))}
            </div>
          )}

          {approvalSelection && (
            <form
              className="corporate-action-approval-form"
              onSubmit={(event) => {
                event.preventDefault();
                if (approvalReady) approvalMutation.mutate();
              }}
            >
              <header>
                <div>
                  <span>MANUAL APPROVAL / FAIL-CLOSED</span>
                  <h3>{approvalSelection.candidate.receipt_no} 승인 검토</h3>
                </div>
                <button onClick={() => setApprovalSelection(null)} type="button">닫기</button>
              </header>
              <p>
                DART 후보는 제출 시 다시 조회됩니다. 적용 시각과 KRX 증빙을 직접 대조한 뒤
                확인 문구를 입력하세요. 이 작업은 주문을 실행하거나 캔들을 변경하지 않습니다.
              </p>
              <label>
                적용 시각
                <input
                  onChange={(event) => setEffectiveAt(event.target.value)}
                  required
                  type="datetime-local"
                  value={effectiveAt}
                />
              </label>
              <label>
                KRX 증빙 URL
                <input
                  maxLength={2048}
                  onChange={(event) => setExchangeEvidenceUrl(event.target.value)}
                  placeholder="https://kind.krx.co.kr/..."
                  required
                  type="url"
                  value={exchangeEvidenceUrl}
                />
              </label>
              <label>
                확인 문구
                <input
                  autoComplete="off"
                  onChange={(event) => setConfirmation(event.target.value)}
                  placeholder={CONFIRMATION_PHRASE}
                  required
                  value={confirmation}
                />
              </label>
              <button disabled={!approvalReady || approvalMutation.isPending} type="submit">
                {approvalMutation.isPending ? "승인 기록 중" : "증빙과 함께 승인 기록"}
              </button>
            </form>
          )}
          {approvalMutation.isError && (
            <div className="ingestion-notice error">{approvalMutation.error.message}</div>
          )}
          {approvalMutation.data && (
            <div className="ingestion-notice success">
              승인 감사 이력이 {approvalMutation.data.created ? "생성" : "재확인"}되었습니다.
              revision {approvalMutation.data.action.revision} · {approvalMutation.data.evidence_hash}
            </div>
          )}
        </div>
      )}

      {query.isPending && <div className="admin-state">기업행위 이력을 불러오는 중입니다.</div>}
      {query.isError && (
        <div className="admin-state error">
          <b>기업행위 이력 조회 실패</b>
          <span>{query.error.message}</span>
        </div>
      )}
      {data?.persistence_status === "disabled" && (
        <div className="admin-state">DB 저장이 비활성화되어 기업행위 이력이 없습니다.</div>
      )}
      {data?.persistence_status === "enabled" && (
        <>
          <div className="corporate-action-meta">
            <span>보정 규칙 <b>{data.adjustment_version}</b></span>
            <span>모드 <b>{data.application_mode}</b></span>
            <span>raw 변경 <b>{data.raw_candles_mutated ? "예" : "아니요"}</b></span>
            <span>기준 시점 <b>{formatDate(data.data_as_of)}</b></span>
          </div>
          {data.items.length === 0 ? (
            <div className="admin-state">조건에 해당하는 기업행위 revision이 없습니다.</div>
          ) : (
            <div className="admin-table-wrap">
              <table className="admin-table corporate-action-table">
                <thead>
                  <tr>
                    <th>종목</th><th>유형</th><th>상태</th><th>적용일</th>
                    <th>알려진 시각</th><th>보정계수</th><th>출처 / revision</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr key={`${item.source}:${item.event_id}:${item.revision}`}>
                      <td><b>{item.symbol}</b></td>
                      <td>{actionLabels[item.action_type] ?? item.action_type}</td>
                      <td>
                        <span className={`corporate-action-status ${item.status}`}>
                          {item.status}
                        </span>
                      </td>
                      <td>{formatDate(item.effective_at)}</td>
                      <td>{formatDate(item.known_at)}</td>
                      <td><code>P {item.price_factor}</code><code>V {item.volume_factor}</code></td>
                      <td>
                        <b>{item.source}</b>
                        <small>rev {item.revision} · {item.rule_version}</small>
                        <code>{item.event_id}</code>
                      </td>
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
