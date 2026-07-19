"use client";

import { useQuery } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { fetchDataQualityHistory } from "../lib/admin-api";

const PAGE_SIZE = 25;

const ruleLabels: Record<string, string> = {
  duplicate_timestamp: "중복 캔들",
  invalid_ohlc: "OHLC 범위 오류",
  negative_volume: "음수 거래량",
  out_of_order: "시간 순서 오류",
  missing_daily_candles: "장기간 캔들 공백",
  mixed_price_basis: "가격 기준 혼합",
};

function date(value: string | null): string {
  if (!value) return "시각 정보 없음";
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString("ko-KR");
}

export function DataQualityHistoryPanel() {
  const [symbolInput, setSymbolInput] = useState("");
  const [symbol, setSymbol] = useState("");
  const [severity, setSeverity] = useState<"" | "error" | "warning">("");
  const [offset, setOffset] = useState(0);
  const query = useQuery({
    queryKey: ["admin", "data-quality", symbol, severity, offset],
    queryFn: () => fetchDataQualityHistory(symbol, severity, PAGE_SIZE, offset),
    staleTime: 30_000,
    retry: 1,
  });
  const data = query.data;

  const submit = (event: FormEvent) => {
    event.preventDefault();
    setSymbol(symbolInput.trim().toUpperCase());
    setOffset(0);
  };

  const changeSeverity = (value: "" | "error" | "warning") => {
    setSeverity(value);
    setOffset(0);
  };

  return (
    <section className="admin-shell quality-admin">
      <header className="admin-heading">
        <div><p>PIPELINE / DATA QUALITY</p><h1>데이터 품질 이력</h1></div>
        <form onSubmit={submit}>
          <input aria-label="품질 로그 종목 코드" maxLength={16} onChange={(event) => setSymbolInput(event.target.value)} placeholder="전체 종목" value={symbolInput} />
          <select aria-label="품질 로그 심각도" onChange={(event) => changeSeverity(event.target.value as "" | "error" | "warning")} value={severity}>
            <option value="">전체 심각도</option><option value="error">오류</option><option value="warning">경고</option>
          </select>
          <button type="submit">조회</button>
        </form>
      </header>
      {query.isPending && <div className="admin-state">품질 로그를 불러오는 중입니다.</div>}
      {query.isError && <div className="admin-state error"><b>품질 로그 조회 실패</b><span>{query.error.message}</span></div>}
      {data?.persistence_status === "disabled" && <div className="admin-state">DB 저장이 비활성화되어 품질 이력이 보존되지 않습니다.</div>}
      {data?.persistence_status === "enabled" && (
        <>
          <div className="quality-summary">
            <article><span>필터 결과</span><strong>{data.total}</strong><small>전체 저장 로그</small></article>
            <article className="error"><span>오류</span><strong>{data.severity_counts.error}</strong><small>정제 과정에서 제외 가능</small></article>
            <article className="warning"><span>경고</span><strong>{data.severity_counts.warning}</strong><small>운영자 검토 대상</small></article>
          </div>
          {data.items.length === 0 ? <div className="admin-state">조건에 해당하는 데이터 품질 로그가 없습니다.</div> : (
            <div className="admin-table-wrap">
              <table className="admin-table quality-table">
                <thead><tr><th>심각도</th><th>종목</th><th>규칙</th><th>내용</th><th>관측 시각</th><th>저장 시각</th></tr></thead>
                <tbody>{data.items.map((item) => (
                  <tr key={item.log_id}>
                    <td><span className={`quality-severity ${item.severity}`}>{item.severity}</span></td>
                    <td><b>{item.symbol}</b></td><td><b className="quality-rule">{ruleLabels[item.rule] ?? "기타 규칙"}</b><code>{item.rule}</code></td><td className="quality-message">{item.message}</td>
                    <td>{date(item.observed_at)}</td><td>{date(item.created_at)}</td>
                  </tr>
                ))}</tbody>
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
