"use client";

/** 국내 종목의 투자자·프로그램·공매도·신용·대차 흐름을 같은 표 형식으로 보여준다. */

import { useQuery } from "@tanstack/react-query";
import { Activity, RefreshCw } from "lucide-react";
import { useState } from "react";
import { fetchTossStockTrends, type TossStockTrends } from "../../lib/market-api";

type TrendKey = Exclude<keyof TossStockTrends, "provider">;

const tabs: Array<{ key: TrendKey; label: string }> = [
  { key: "investor_trading", label: "투자자" },
  { key: "program_trades", label: "프로그램" },
  { key: "short_selling", label: "공매도" },
  { key: "credit_trades", label: "신용" },
  { key: "securities_lending", label: "대차" },
];

/** `findRows`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function findRows(payload: Record<string, unknown>): Array<Record<string, unknown>> {
  for (const value of Object.values(payload)) {
    if (Array.isArray(value)) return value.filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object");
  }
  return [];
}

/** `visibleEntries`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
function visibleEntries(row: Record<string, unknown>): Array<[string, unknown]> {
  return Object.entries(row)
    .filter(([, value]) => ["string", "number"].includes(typeof value))
    .slice(0, 5);
}

/** `TossStockTrendsPanel`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export function TossStockTrendsPanel({ symbol }: { symbol: string }) {
  const [active, setActive] = useState<TrendKey>("investor_trading");
  const query = useQuery({
    queryKey: ["toss-stock-trends", symbol],
    queryFn: ({ signal }) => fetchTossStockTrends(symbol, signal),
    enabled: /^\d{6}$/.test(symbol),
    staleTime: 60_000,
    retry: 1,
  });

  if (!/^\d{6}$/.test(symbol)) return null;
  const rows = query.data ? findRows(query.data[active]) : [];

  return (
    <section className="toss-trends" aria-label={`${symbol} 국내 수급 상세`}>
      <header><div><span>KR FLOW</span><b>국내 수급 상세</b></div><Activity size={17} /></header>
      <div className="toss-trends__tabs" role="tablist" aria-label="수급 데이터 종류">
        {tabs.map((tab) => <button aria-selected={active === tab.key} key={tab.key} onClick={() => setActive(tab.key)} role="tab" type="button">{tab.label}</button>)}
      </div>
      {query.isPending && <p className="toss-trends__state"><RefreshCw className="spin" size={14} /> 수급 데이터를 확인하고 있습니다.</p>}
      {query.isError && <p className="toss-trends__state">현재 수급 상세를 표시할 수 없습니다.</p>}
      {query.data && rows.length > 0 && (
        <div className="toss-trends__table" role="tabpanel">
          {rows.slice(0, 7).map((row, index) => (
            <div key={`${active}-${String(row.date ?? row.timestamp ?? index)}`}>
              {visibleEntries(row).map(([key, value]) => <span key={key}><small>{key}</small><b>{String(value)}</b></span>)}
            </div>
          ))}
        </div>
      )}
      {query.data && rows.length === 0 && <p className="toss-trends__state">현재 집계된 데이터가 없습니다.</p>}
    </section>
  );
}
