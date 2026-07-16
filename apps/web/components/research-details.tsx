"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import {
  fetchDisclosures,
  fetchFinancials,
  fetchInvestorFlow,
  fetchNews,
  type DisclosureAnalysis,
  type FinancialSnapshot,
  type InvestorFlow,
  type NewsAnalysis,
} from "../lib/market-api";

type ResearchTab = "financials" | "flow" | "news" | "disclosures";

const tabs: Array<{ id: ResearchTab; label: string; note: string }> = [
  { id: "financials", label: "재무", note: "연간 주요 계정" },
  { id: "flow", label: "수급", note: "투자자별 순매매" },
  { id: "news", label: "뉴스", note: "기사 감성 요약" },
  { id: "disclosures", label: "공시", note: "최근 90일" },
];

const flowSignalLabels: Record<InvestorFlow["reference_signal"], string> = {
  net_inflow: "외국인·기관 합산 순유입",
  net_outflow: "외국인·기관 합산 순유출",
  balanced: "외국인·기관 수급 균형",
};

const sentimentLabels: Record<NewsAnalysis["sentiment_label"], string> = {
  positive: "긍정 비중 우세",
  negative: "부정 비중 우세",
  neutral: "중립",
};

function finite(value: string | number | null | undefined): number | null {
  if (value == null) return null;
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatAmount(value: string | number | null, currency: string): string {
  const parsed = finite(value);
  if (parsed == null) return "자료 없음";
  const formatter = new Intl.NumberFormat(currency === "KRW" ? "ko-KR" : "en-US", {
    notation: "compact",
    maximumFractionDigits: 2,
  });
  return `${currency === "USD" ? "$" : "₩"}${formatter.format(parsed)}`;
}

function formatQuantity(value: string | number | null): string {
  const parsed = finite(value);
  if (parsed == null) return "자료 없음";
  const sign = parsed > 0 ? "+" : "";
  return `${sign}${new Intl.NumberFormat("ko-KR", { notation: "compact", maximumFractionDigits: 2 }).format(parsed)}주`;
}

function formatDate(value: string): string {
  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleString("ko-KR");
}

function safeExternalUrl(value: string): string | undefined {
  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:" ? url.toString() : undefined;
  } catch {
    return undefined;
  }
}

function ResearchState({
  kind,
  message,
  retry,
}: {
  kind: "loading" | "error" | "empty";
  message: string;
  retry?: () => void;
}) {
  return (
    <div className={`research-state ${kind}`}>
      <span>{message}</span>
      {retry && <button type="button" onClick={retry}>다시 시도</button>}
    </div>
  );
}

function FinancialPanel({ data }: { data: FinancialSnapshot }) {
  const metrics = [
    ["매출액", data.revenue],
    ["영업이익", data.operating_income],
    ["당기순이익", data.net_income],
    ["자산총계", data.total_assets],
    ["부채총계", data.total_liabilities],
    ["자본총계", data.total_equity],
  ] as const;
  return (
    <>
      <div className="research-metrics">
        {metrics.map(([label, value]) => (
          <article key={label}><span>{label}</span><strong>{formatAmount(value, data.currency)}</strong></article>
        ))}
      </div>
      <ResearchFooter provider={data.provider} dataAsOf={data.data_as_of} detail={`${data.fiscal_year}년 · ${data.statement_type}`} />
    </>
  );
}

function FlowPanel({ data }: { data: InvestorFlow }) {
  const signalClass = data.reference_signal === "net_inflow" ? "positive" : data.reference_signal === "net_outflow" ? "negative" : "neutral";
  return (
    <>
      <div className={`research-signal ${signalClass}`}>
        <span>REFERENCE FLOW</span><strong>{flowSignalLabels[data.reference_signal]}</strong>
        <small>수급 방향을 설명하는 실험 상태 참고 정보이며 매매 지시가 아닙니다.</small>
      </div>
      <div className="research-metrics flow">
        <article><span>외국인 순매매</span><strong>{formatQuantity(data.foreign_net_quantity)}</strong></article>
        <article><span>기관 순매매</span><strong>{formatQuantity(data.institution_net_quantity)}</strong></article>
        <article><span>개인 순매매</span><strong>{formatQuantity(data.individual_net_quantity)}</strong></article>
        <article><span>외국인·기관 합산</span><strong>{formatQuantity(data.foreign_institution_net_quantity)}</strong></article>
        <article><span>외국인 보유율</span><strong>{finite(data.foreign_holding_rate) == null ? "자료 없음" : `${finite(data.foreign_holding_rate)?.toFixed(2)}%`}</strong></article>
      </div>
      <ResearchFooter provider={data.provider} dataAsOf={data.data_as_of} detail={`${data.as_of_date} 기준 · 국내 종목 데이터`} />
    </>
  );
}

function NewsPanel({ data }: { data: NewsAnalysis }) {
  return (
    <>
      <div className={`research-signal ${data.sentiment_label}`}>
        <span>EXPERIMENTAL SENTIMENT</span><strong>{sentimentLabels[data.sentiment_label]}</strong>
        <small>감성 점수 {data.sentiment_score.toFixed(3)} · 제목과 요약에 대한 규칙 기반 분석</small>
      </div>
      {data.articles.length === 0 ? <ResearchState kind="empty" message="최근 수집된 뉴스가 없습니다." /> : (
        <div className="research-list">
          {data.articles.map((article) => {
            const href = safeExternalUrl(article.url);
            return (
              <article key={`${article.url}-${article.published_at}`}>
                <div><span>{article.publisher} · {formatDate(article.published_at)}</span><small>감성 {article.sentiment_score.toFixed(2)}</small></div>
                {href ? <a href={href} target="_blank" rel="noopener noreferrer">{article.title}</a> : <strong>{article.title}</strong>}
                {article.summary && <p>{article.summary}</p>}
              </article>
            );
          })}
        </div>
      )}
      <ResearchFooter provider={data.provider} detail={`${data.articles.length}건 · 데이터 저장 ${data.persistence_status}`} />
    </>
  );
}

function DisclosurePanel({ data }: { data: DisclosureAnalysis }) {
  return (
    <>
      {data.risk_flags.length > 0 && <div className="risk-flags"><b>검토 필요</b>{data.risk_flags.map((flag) => <span key={flag}>{flag}</span>)}</div>}
      {data.disclosures.length === 0 ? <ResearchState kind="empty" message="최근 90일 내 수집된 공시가 없습니다." /> : (
        <div className="research-list disclosures">
          {data.disclosures.map((item) => {
            const href = safeExternalUrl(item.document_url);
            return (
              <article key={item.receipt_no}>
                <div><span>{formatDate(item.filed_at)} · {item.filer_name}</span><small className={item.risk_level}>{item.risk_level === "high" ? "위험 키워드 감지" : "일반"}</small></div>
                {href ? <a href={href} target="_blank" rel="noopener noreferrer">{item.report_name}</a> : <strong>{item.report_name}</strong>}
                {item.remarks && <p>{item.remarks}</p>}
              </article>
            );
          })}
        </div>
      )}
      <ResearchFooter provider={data.provider} detail={`${data.disclosures.length}건 · EXPERIMENTAL`} />
    </>
  );
}

function ResearchFooter({ provider, dataAsOf, detail }: { provider: string; dataAsOf?: string; detail: string }) {
  return <footer className="research-footer"><span>{provider} · {detail}</span>{dataAsOf && <span>기준 {formatDate(dataAsOf)}</span>}</footer>;
}

export function ResearchDetails({ symbol, currency }: { symbol: string; currency: string }) {
  const [activeTab, setActiveTab] = useState<ResearchTab>("financials");
  const fiscalYear = new Date().getFullYear() - 1;
  const financials = useQuery({
    queryKey: ["research", "financials", symbol, fiscalYear],
    queryFn: () => fetchFinancials(symbol, fiscalYear),
    enabled: activeTab === "financials",
    staleTime: 5 * 60_000,
    retry: 1,
  });
  const flow = useQuery({
    queryKey: ["research", "flow", symbol],
    queryFn: () => fetchInvestorFlow(symbol),
    enabled: activeTab === "flow" && currency === "KRW",
    staleTime: 60_000,
    retry: 1,
  });
  const news = useQuery({
    queryKey: ["research", "news", symbol],
    queryFn: () => fetchNews(symbol),
    enabled: activeTab === "news",
    staleTime: 5 * 60_000,
    retry: 1,
  });
  const disclosures = useQuery({
    queryKey: ["research", "disclosures", symbol],
    queryFn: () => fetchDisclosures(symbol),
    enabled: activeTab === "disclosures",
    staleTime: 5 * 60_000,
    retry: 1,
  });

  return (
    <section className="research-details">
      <header className="research-heading">
        <div><span>FUNDAMENTAL · CONTENT · FLOW</span><h3>기업·시장 리서치</h3></div>
        <small>선택한 탭만 조회해 데이터 사용량을 줄입니다.</small>
      </header>
      <div className="research-tabs" role="tablist" aria-label="기업 리서치 분류">
        {tabs.map((tab) => <button key={tab.id} type="button" role="tab" aria-selected={activeTab === tab.id} onClick={() => setActiveTab(tab.id)}><b>{tab.label}</b><small>{tab.note}</small></button>)}
      </div>
      <div className="research-panel" role="tabpanel">
        {activeTab === "financials" && (financials.isPending ? <ResearchState kind="loading" message="재무 정보를 불러오는 중입니다." /> : financials.isError ? <ResearchState kind="error" message={financials.error.message} retry={() => { void financials.refetch(); }} /> : <FinancialPanel data={financials.data} />)}
        {activeTab === "flow" && currency !== "KRW" && <ResearchState kind="empty" message="종목별 투자자 수급은 현재 국내 주식만 지원합니다." />}
        {activeTab === "flow" && currency === "KRW" && (flow.isPending ? <ResearchState kind="loading" message="투자자 수급을 불러오는 중입니다." /> : flow.isError ? <ResearchState kind="error" message={flow.error.message} retry={() => { void flow.refetch(); }} /> : <FlowPanel data={flow.data} />)}
        {activeTab === "news" && (news.isPending ? <ResearchState kind="loading" message="뉴스 분석을 불러오는 중입니다." /> : news.isError ? <ResearchState kind="error" message={news.error.message} retry={() => { void news.refetch(); }} /> : <NewsPanel data={news.data} />)}
        {activeTab === "disclosures" && (disclosures.isPending ? <ResearchState kind="loading" message="공시를 불러오는 중입니다." /> : disclosures.isError ? <ResearchState kind="error" message={disclosures.error.message} retry={() => { void disclosures.refetch(); }} /> : <DisclosurePanel data={disclosures.data} />)}
      </div>
    </section>
  );
}
