"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  fetchModelVersions,
  ModelRegistryData,
  promoteModelVersion,
} from "../lib/admin-api";

export function ModelRegistryPanel() {
  const [registry, setRegistry] = useState<ModelRegistryData | null>(null);
  const [symbol, setSymbol] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [promoting, setPromoting] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const load = useCallback(async (filter = "") => {
    setLoading(true);
    setError(null);
    try {
      setRegistry(await fetchModelVersions(filter));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "모델 버전을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    void load(symbol.trim().toUpperCase());
  };

  const promote = async (version: string) => {
    setPromoting(version);
    setError(null);
    setNotice(null);
    try {
      const result = await promoteModelVersion(version);
      setNotice(result.notice);
      await load(symbol.trim().toUpperCase());
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Champion 승격에 실패했습니다.");
    } finally {
      setPromoting(null);
    }
  };

  return (
    <section className="admin-shell">
      <header className="admin-heading">
        <div><p>ML / MODEL REGISTRY</p><h1>Champion–Challenger</h1></div>
        <form onSubmit={submit}>
          <input aria-label="모델 종목 코드" maxLength={16} onChange={(event) => setSymbol(event.target.value)} placeholder="종목 코드 필터" value={symbol} />
          <button type="submit">조회</button>
        </form>
      </header>
      <div className="admin-state"><span>{registry?.runtime_activation_enabled ? "승격 전 artifact 체크섬과 모델 범위를 검증하고 원자적으로 런타임 포인터를 전환합니다." : "승격은 Registry 메타데이터만 변경합니다. 검증된 artifact 저장소를 설정하기 전에는 런타임 모델을 전환하지 않습니다."}</span></div>
      {notice && <div className="admin-state"><span>{notice}</span></div>}
      {loading && <div className="admin-state">모델 버전을 불러오는 중입니다.</div>}
      {error && <div className="admin-state error"><b>처리 실패</b><span>{error}</span></div>}
      {!loading && registry?.persistence_status === "disabled" && <div className="admin-state">DB 저장이 비활성화되어 있습니다.</div>}
      {!loading && registry?.persistence_status === "enabled" && registry.items.length === 0 && <div className="admin-state">등록된 모델 버전이 없습니다. 예측을 실행하면 Challenger가 등록됩니다.</div>}
      {registry && registry.items.length > 0 && (
        <div className="admin-table-wrap">
          <table className="admin-table">
            <thead><tr><th>종목</th><th>알고리즘</th><th>기간</th><th>단계</th><th>정확도</th><th>Brier</th><th>데이터 기준</th><th /></tr></thead>
            <tbody>{registry.items.map((model) => (
              <tr key={model.version}>
                <td><b>{model.symbol}</b></td><td>{model.algorithm}</td><td>{model.horizon_days}일</td>
                <td><span className={`engine-badge ${model.registry_stage === "champion" ? "event_driven" : "vectorized"}`}>{model.registry_stage}</span></td>
                <td>{model.validation_metrics.accuracy?.toFixed(4) ?? "-"}</td>
                <td>{model.validation_metrics.brier_score?.toFixed(4) ?? "-"}</td>
                <td>{new Date(model.data_as_of).toLocaleDateString("ko-KR")}</td>
                <td><button disabled={model.registry_stage === "champion" || promoting === model.version} onClick={() => void promote(model.version)} type="button">{promoting === model.version ? "승격 중" : "Champion"}</button></td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </section>
  );
}
