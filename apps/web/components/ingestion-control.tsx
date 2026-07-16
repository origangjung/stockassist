"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import { fetchIngestionStatus, triggerIngestion } from "../lib/admin-api";

export function IngestionControlPanel() {
  const queryClient = useQueryClient();
  const [symbol, setSymbol] = useState("");
  const status = useQuery({
    queryKey: ["admin", "ingestion-status"],
    queryFn: fetchIngestionStatus,
    staleTime: 30_000,
    retry: 1,
  });
  const ingestion = useMutation({
    mutationFn: (target: string) => triggerIngestion(target),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin", "data-quality"] });
    },
  });

  const run = (target: string) => {
    const normalized = target.trim().toUpperCase();
    if (normalized && !ingestion.isPending) ingestion.mutate(normalized);
  };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    run(symbol);
  };
  const data = status.data;

  return (
    <section className="admin-shell ingestion-admin">
      <header className="admin-heading">
        <div><p>PIPELINE / INGESTION</p><h1>캔들 수집 제어</h1></div>
        <form onSubmit={submit}>
          <input aria-label="수동 수집 종목 코드" disabled={!data?.manual_ingestion_available || ingestion.isPending} maxLength={16} onChange={(event) => setSymbol(event.target.value)} placeholder="종목 코드" value={symbol} />
          <button disabled={!symbol.trim() || !data?.manual_ingestion_available || ingestion.isPending} type="submit">{ingestion.isPending ? "수집 중" : "한 번 수집"}</button>
        </form>
      </header>
      {status.isPending && <div className="admin-state">수집 설정을 확인하는 중입니다.</div>}
      {status.isError && <div className="admin-state error"><b>수집 설정 조회 실패</b><span>{status.error.message}</span></div>}
      {data && (
        <>
          <div className="ingestion-config">
            <span>자동 스케줄러 <b className={data.scheduler_enabled ? "enabled" : "disabled"}>{data.scheduler_enabled ? "ON" : "OFF"}</b></span>
            <span>주기 <b>{data.interval_minutes}분</b></span><span>종목당 <b>{data.ingestion_limit}개</b></span>
            <span>DB 저장 <b className={data.persistence_enabled ? "enabled" : "disabled"}>{data.persistence_enabled ? "ON" : "OFF"}</b></span>
          </div>
          <div className="ingestion-symbols">
            <header><b>설정된 수집 유니버스</b><small>{data.symbols.length}종목 · 국내/미국 공통 Provider 계약</small></header>
            <div>{data.symbols.map((item) => (
              <button disabled={!data.manual_ingestion_available || ingestion.isPending} key={item} onClick={() => run(item)} type="button">{item}<small>수집</small></button>
            ))}</div>
          </div>
          {!data.manual_ingestion_available && <div className="ingestion-notice error">DB 저장이 비활성화되어 수동 수집을 실행할 수 없습니다.</div>}
          {ingestion.isError && <div className="ingestion-notice error">{ingestion.error.message}</div>}
          {ingestion.data && (
            <div className="ingestion-result">
              <strong>{ingestion.data.summary.symbol} 수집 완료</strong>
              <span>{ingestion.data.summary.provider} · 원본 {ingestion.data.summary.raw_count}개 · 정제 {ingestion.data.summary.cleaned_count}개 · 품질 로그 {ingestion.data.summary.quality_log_count}건</span>
              <small>수집은 시세 데이터 저장만 수행하며 주문이나 계좌 변경을 실행하지 않습니다.</small>
            </div>
          )}
        </>
      )}
    </section>
  );
}
