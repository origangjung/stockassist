"use client";

import { useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import {
  CandlePriceBasis,
  fetchCandlePriceBasisInventory,
} from "../lib/admin-api";

const basisLabels: Record<CandlePriceBasis, string> = {
  unknown: "미분류",
  unadjusted: "미보정",
  provider_adjusted: "공급자 보정",
  point_in_time_adjusted: "시점 보정",
};

const blockerLabels: Record<string, string> = {
  unknown_price_basis_requires_source_specific_evidence:
    "보정 기준을 확인하지 못한 캔들이 있습니다.",
  legacy_rows_lack_provider_provenance:
    "Provider 출처가 기록되기 전에 저장된 캔들이 있습니다.",
  legacy_rows_lack_price_basis_rule_version:
    "보정 기준 규칙 버전이 기록되기 전에 저장된 캔들이 있습니다.",
};

const evidenceLabels: Record<string, string> = {
  original_provider_identifier: "원본 Provider 식별자",
  provider_response_or_contract_reference: "원본 응답 또는 계약 근거",
  endpoint_adjustment_semantics: "엔드포인트 보정 의미",
  provider_contract_test: "Provider 계약 테스트",
  versioned_price_basis_rule: "버전화된 보정 규칙",
};

function formatDate(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString("ko-KR");
}

export function CandlePriceBasisInventoryPanel() {
  const [symbolInput, setSymbolInput] = useState("");
  const [symbol, setSymbol] = useState("");
  const query = useQuery({
    queryKey: ["admin", "candles", "price-basis-inventory", symbol],
    queryFn: () => fetchCandlePriceBasisInventory(symbol),
    enabled: Boolean(symbol),
    staleTime: 30_000,
    retry: 1,
  });
  const data = query.data;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setSymbol(symbolInput.trim().toUpperCase());
  };

  return (
    <section className="admin-shell candle-basis-admin">
      <header className="admin-heading">
        <div>
          <p>PIPELINE / PRICE BASIS</p>
          <h1>캔들 보정 기준 현황</h1>
        </div>
        <form onSubmit={submit}>
          <input
            aria-label="캔들 보정 기준 종목 코드"
            maxLength={16}
            onChange={(event) => setSymbolInput(event.target.value)}
            placeholder="종목 코드"
            value={symbolInput}
          />
          <button disabled={!symbolInput.trim() || query.isFetching} type="submit">
            {query.isFetching ? "확인 중" : "조회"}
          </button>
        </form>
      </header>

      <div className="reference-only candle-basis-notice">
        <b>읽기 전용</b>
        <span>
          이 화면은 저장된 분류 근거를 집계하며 캔들을 수정하거나 자동 재분류하지 않습니다.
        </span>
      </div>

      {!symbol && (
        <div className="admin-state">
          종목 코드를 입력하면 해당 종목만 안전하게 집계합니다.
        </div>
      )}
      {symbol && query.isPending && (
        <div className="admin-state">캔들 보정 기준을 집계하는 중입니다.</div>
      )}
      {query.isError && (
        <div className="admin-state error">
          <b>보정 기준 조회 실패</b>
          <span>{query.error.message}</span>
        </div>
      )}
      {data?.persistence_status === "disabled" && (
        <div className="admin-state">
          DB 저장이 비활성화되어 캔들 현황을 조회할 수 없습니다.
        </div>
      )}
      {data?.persistence_status === "enabled" && (
        <>
          <div className="candle-basis-summary">
            <article>
              <span>전체 캔들</span>
              <strong>{data.total_candles}</strong>
              <small>{data.total_groups}개 분류 그룹</small>
            </article>
            <article className={data.unknown_candles > 0 ? "warning" : "safe"}>
              <span>기준 미분류</span>
              <strong>{data.unknown_candles}</strong>
              <small>근거 확인 필요</small>
            </article>
            <article className={data.legacy_unknown_candles > 0 ? "warning" : "safe"}>
              <span>출처 미기록</span>
              <strong>{data.legacy_unknown_candles}</strong>
              <small>legacy Provider</small>
            </article>
            <article className={data.legacy_rule_candles > 0 ? "warning" : "safe"}>
              <span>규칙 미기록</span>
              <strong>{data.legacy_rule_candles}</strong>
              <small>legacy rule</small>
            </article>
          </div>

          {(data.classification_blockers?.length ?? 0) > 0 && (
            <div className="candle-basis-blockers" role="status">
              <b>자동 분류 차단 사유</b>
              <ul>
                {data.classification_blockers?.map((blocker) => (
                  <li key={blocker}>{blockerLabels[blocker] ?? blocker}</li>
                ))}
              </ul>
            </div>
          )}

          {data.items.length === 0 ? (
            <div className="admin-state">해당 종목의 저장된 캔들이 없습니다.</div>
          ) : (
            <div className="admin-table-wrap">
              <table className="admin-table candle-basis-table">
                <thead>
                  <tr>
                    <th>Provider</th>
                    <th>가격 기준</th>
                    <th>규칙 버전</th>
                    <th>단계</th>
                    <th>주기</th>
                    <th>집계 버전</th>
                    <th>건수</th>
                    <th>근거 검수</th>
                    <th>기간</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr
                      key={`${item.source_provider}:${item.price_basis}:${item.price_basis_rule_version}:${item.data_stage}:${item.interval}:${item.aggregation_version}`}
                    >
                      <td><b>{item.source_provider}</b></td>
                      <td>
                        <span className={`price-basis-badge ${item.price_basis}`}>
                          {basisLabels[item.price_basis]}
                        </span>
                        <code>{item.price_basis}</code>
                      </td>
                      <td><code>{item.price_basis_rule_version}</code></td>
                      <td>{item.data_stage}</td>
                      <td>{item.interval}</td>
                      <td>{item.aggregation_version}</td>
                      <td><b>{item.candle_count}</b></td>
                      <td>
                        <span className={`evidence-status ${item.review_status}`}>
                          {item.review_status === "evidence_recorded" ? "근거 기록됨" : "근거 필요"}
                        </span>
                        {item.required_evidence.map((requirement) => (
                          <small key={requirement}>{evidenceLabels[requirement] ?? requirement}</small>
                        ))}
                      </td>
                      <td>
                        <span>{formatDate(item.first_timestamp)}</span>
                        <small>{formatDate(item.last_timestamp)}</small>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {data.groups_truncated && (
            <div className="admin-state">
              분류 그룹이 많아 처음 200개만 표시합니다.
            </div>
          )}
        </>
      )}
    </section>
  );
}
