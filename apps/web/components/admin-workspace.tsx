"use client";

import dynamic from "next/dynamic";
import { useState } from "react";

type WorkspaceTab = "operations" | "research" | "models" | "accounts";

const loading = () => (
  <div className="admin-state workspace-loading">
    <b>화면을 불러오는 중입니다.</b>
    <span>선택한 관리 기능만 로드하고 있습니다.</span>
  </div>
);

const OperationsStatusPanel = dynamic(
  () => import("./operations-status").then((module) => module.OperationsStatusPanel),
  { loading },
);
const IngestionControlPanel = dynamic(
  () => import("./ingestion-control").then((module) => module.IngestionControlPanel),
  { loading },
);
const DataQualityHistoryPanel = dynamic(
  () => import("./data-quality-history").then((module) => module.DataQualityHistoryPanel),
  { loading },
);
const ProviderAuditHistoryPanel = dynamic(
  () =>
    import("./provider-audit-history").then((module) => module.ProviderAuditHistoryPanel),
  { loading },
);
const EngineComparisonPanel = dynamic(
  () => import("./engine-comparison").then((module) => module.EngineComparisonPanel),
  { loading },
);
const StrategyComparisonPanel = dynamic(
  () => import("./strategy-comparison").then((module) => module.StrategyComparisonPanel),
  { loading },
);
const WalkForwardValidationPanel = dynamic(
  () => import("./walk-forward-validation").then((module) => module.WalkForwardValidationPanel),
  { loading },
);
const BacktestHistoryPanel = dynamic(
  () => import("./backtest-history").then((module) => module.BacktestHistoryPanel),
  { loading },
);
const ModelRegistryPanel = dynamic(
  () => import("./model-registry").then((module) => module.ModelRegistryPanel),
  { loading },
);
const WatchlistAlerts = dynamic(
  () => import("./watchlist-alerts").then((module) => module.WatchlistAlerts),
  { loading },
);
const PortfolioAnalysis = dynamic(
  () => import("./portfolio-analysis").then((module) => module.PortfolioAnalysis),
  { loading },
);

const tabs: Array<{ id: WorkspaceTab; label: string; description: string }> = [
  { id: "operations", label: "운영 상태", description: "의존성, 수집, 데이터 품질" },
  { id: "research", label: "연구·검증", description: "엔진, 전략, Walk-Forward" },
  { id: "models", label: "모델 관리", description: "모델 버전과 승격 이력" },
  { id: "accounts", label: "계좌·알림", description: "관심종목, 알림, 포트폴리오" },
];

export function AdminWorkspace() {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("operations");
  const active = tabs.find((tab) => tab.id === activeTab) ?? tabs[0];

  return (
    <div className="admin-workspace">
      <div aria-label="관리자 작업 영역" className="admin-workspace-tabs" role="tablist">
        {tabs.map((tab) => (
          <button
            aria-controls={`workspace-${tab.id}`}
            aria-selected={activeTab === tab.id}
            className={activeTab === tab.id ? "active" : ""}
            id={`workspace-tab-${tab.id}`}
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            role="tab"
            type="button"
          >
            <b>{tab.label}</b>
            <span>{tab.description}</span>
          </button>
        ))}
      </div>

      <header className="workspace-heading">
        <span>ADMIN WORKSPACE</span>
        <h1>{active.label}</h1>
        <p>{active.description} 영역만 실행하여 초기 요청과 메모리 사용을 줄입니다.</p>
      </header>

      <div
        aria-labelledby={`workspace-tab-${activeTab}`}
        id={`workspace-${activeTab}`}
        role="tabpanel"
      >
        {activeTab === "operations" && (
          <>
            <OperationsStatusPanel />
            <IngestionControlPanel />
            <DataQualityHistoryPanel />
            <ProviderAuditHistoryPanel />
          </>
        )}
        {activeTab === "research" && (
          <>
            <EngineComparisonPanel />
            <StrategyComparisonPanel />
            <WalkForwardValidationPanel />
            <BacktestHistoryPanel />
          </>
        )}
        {activeTab === "models" && <ModelRegistryPanel />}
        {activeTab === "accounts" && (
          <>
            <WatchlistAlerts />
            <PortfolioAnalysis />
          </>
        )}
      </div>
    </div>
  );
}
