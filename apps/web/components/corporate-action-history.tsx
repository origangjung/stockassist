"use client";

import { useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { fetchCorporateActionHistory } from "../lib/admin-api";

const PAGE_SIZE = 25;
const actionLabels: Record<string, string> = {
  split: "액면분할",
  reverse_split: "주식병합",
  cash_dividend: "현금배당락",
  stock_dividend: "주식배당",
  rights_issue: "유상증자",
};

function date(value: string | null): string {
  if (!value) return "-";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString("ko-KR");
}

export function CorporateActionHistoryPanel() {
  const [symbolInput, setSymbolInput] = useState("");
  const [symbol, setSymbol] = useState("");
  const [offset, setOffset] = useState(0);
  const query = useQuery({
    queryKey: ["admin", "corporate-actions", symbol, offset],
    queryFn: () => fetchCorporateActionHistory(symbol, PAGE_SIZE, offset),
    staleTime: 30_000,
    retry: 1,
  });
  const data = query.data;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setSymbol(symbolInput.trim().toUpperCase());
    setOffset(0);
  };

  return (
    <section className="admin-shell corporate-action-admin">
      <header className="admin-heading">
        <div>
          <p>PIPELINE / CORPORATE ACTIONS</p>
          <h1>기업행동 보정 이력</h1>
        </div>
        <form onSubmit={submit}>
          <input
            aria-label="기업행동 종목 코드"
            maxLength={16}
            onChange={(event) => setSymbolInput(event.target.value)}
            placeholder="전체 종목"
            value={symbolInput}
          />
          <button type="submit">조회</button>
        </form>
      </header>
      <p className="corporate-action-safety">
        이 화면은 기준시점과 revision을 확인하는 읽기 전용 이력입니다. 보정 계산은 별도 뷰를
        만들며 raw·cleaned 캔들을 덮어쓰지 않습니다.
      </p>
      {query.isPending && <div className="admin-state">기업행동 이력을 불러오는 중입니다.</div>}
      {query.isError && (
        <div className="admin-state error">
          <b>기업행동 이력 조회 실패</b>
          <span>{query.error.message}</span>
        </div>
      )}
      {data?.persistence_status === "disabled" && (
        <div className="admin-state">DB 저장이 비활성화되어 기업행동 이력이 없습니다.</div>
      )}
      {data?.persistence_status === "enabled" && (
        <>
          <div className="corporate-action-meta">
            <span>보정 규칙 <b>{data.adjustment_version}</b></span>
            <span>모드 <b>{data.application_mode}</b></span>
            <span>raw 변경 <b>{data.raw_candles_mutated ? "예" : "아니오"}</b></span>
            <span>기준시점 <b>{date(data.data_as_of)}</b></span>
          </div>
          {data.items.length === 0 ? (
            <div className="admin-state">조건에 해당하는 기업행동 revision이 없습니다.</div>
          ) : (
            <div className="admin-table-wrap">
              <table className="admin-table corporate-action-table">
                <thead>
                  <tr><th>종목</th><th>유형</th><th>상태</th><th>효력일</th><th>알려진 시각</th><th>보정계수</th><th>출처 / revision</th></tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr key={`${item.source}:${item.event_id}:${item.revision}`}>
                      <td><b>{item.symbol}</b></td>
                      <td>{actionLabels[item.action_type] ?? item.action_type}</td>
                      <td><span className={`corporate-action-status ${item.status}`}>{item.status}</span></td>
                      <td>{date(item.effective_at)}</td>
                      <td>{date(item.known_at)}</td>
                      <td><code>P {item.price_factor}</code><code>V {item.volume_factor}</code></td>
                      <td><b>{item.source}</b><small>rev {item.revision} · {item.rule_version}</small><code>{item.event_id}</code></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <footer className="quality-pagination">
            <span>{data.total === 0 ? 0 : data.offset + 1}–{Math.min(data.offset + data.limit, data.total)} / {data.total}</span>
            <div>
              <button disabled={offset === 0 || query.isFetching} onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))} type="button">이전</button>
              <button disabled={offset + PAGE_SIZE >= data.total || query.isFetching} onClick={() => setOffset(offset + PAGE_SIZE)} type="button">다음</button>
            </div>
          </footer>
        </>
      )}
    </section>
  );
}
