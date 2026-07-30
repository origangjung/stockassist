"use client";

import dynamic from "next/dynamic";
import {
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

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
const CandlePriceBasisInventoryPanel = dynamic(
  () =>
    import("./candle-price-basis-inventory").then(
      (module) => module.CandlePriceBasisInventoryPanel,
    ),
  { loading },
);
const CorporateActionHistoryPanel = dynamic(
  () =>
    import("./corporate-action-history").then(
      (module) => module.CorporateActionHistoryPanel,
    ),
  { loading },
);
const ProviderAuditHistoryPanel = dynamic(
  () =>
    import("./provider-audit-history").then((module) => module.ProviderAuditHistoryPanel),
  { loading },
);
const DataLifecycleMaintenancePanel = dynamic(
  () =>
    import("./data-lifecycle-maintenance").then(
      (module) => module.DataLifecycleMaintenancePanel,
    ),
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

function tabFromHash(hash: string): WorkspaceTab | null {
  const value = hash.replace(/^#/, "");
  return tabs.some((tab) => tab.id === value) ? value as WorkspaceTab : null;
}

export function AdminWorkspace() {
  const [activeTab, setActiveTab] = useState<WorkspaceTab>("operations");
  const tabRefs = useRef<Array<HTMLButtonElement | null>>([]);
  const active = tabs.find((tab) => tab.id === activeTab) ?? tabs[0];

  useEffect(() => {
    const syncFromUrl = () => {
      const requestedTab = tabFromHash(window.location.hash);
      if (requestedTab) setActiveTab(requestedTab);
    };

    syncFromUrl();
    window.addEventListener("hashchange", syncFromUrl);
    window.addEventListener("popstate", syncFromUrl);
    return () => {
      window.removeEventListener("hashchange", syncFromUrl);
      window.removeEventListener("popstate", syncFromUrl);
    };
  }, []);

  const activateTab = (
    nextTab: WorkspaceTab,
    { focus = false, updateUrl = true }: { focus?: boolean; updateUrl?: boolean } = {},
  ) => {
    setActiveTab(nextTab);
    if (updateUrl && window.location.hash !== `#${nextTab}`) {
      const url = new URL(window.location.href);
      url.hash = nextTab;
      window.history.pushState({ workspace: nextTab }, "", url);
    }
    if (focus) {
      const index = tabs.findIndex((tab) => tab.id === nextTab);
      window.requestAnimationFrame(() => tabRefs.current[index]?.focus());
    }
  };

  const handleTabKeyDown = (event: KeyboardEvent<HTMLButtonElement>, index: number) => {
    let nextIndex: number | null = null;
    if (event.key === "ArrowRight") nextIndex = (index + 1) % tabs.length;
    if (event.key === "ArrowLeft") nextIndex = (index - 1 + tabs.length) % tabs.length;
    if (event.key === "Home") nextIndex = 0;
    if (event.key === "End") nextIndex = tabs.length - 1;
    if (nextIndex == null) return;

    event.preventDefault();
    activateTab(tabs[nextIndex].id, { focus: true });
  };

  return (
    <div className="admin-workspace">
      <p aria-live="polite" className="sr-only">{active.label} 탭을 표시합니다.</p>
      <div aria-label="관리자 작업 영역" className="admin-workspace-tabs" role="tablist">
        {tabs.map((tab, index) => (
          <button
            aria-controls={`workspace-${tab.id}`}
            aria-selected={activeTab === tab.id}
            className={activeTab === tab.id ? "active" : ""}
            id={`workspace-tab-${tab.id}`}
            key={tab.id}
            onClick={() => activateTab(tab.id)}
            onKeyDown={(event) => handleTabKeyDown(event, index)}
            ref={(element) => { tabRefs.current[index] = element; }}
            role="tab"
            tabIndex={activeTab === tab.id ? 0 : -1}
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
        tabIndex={0}
      >
        {activeTab === "operations" && (
          <>
            <OperationsStatusPanel />
            <IngestionControlPanel />
            <DataQualityHistoryPanel />
            <CandlePriceBasisInventoryPanel />
            <CorporateActionHistoryPanel />
            <ProviderAuditHistoryPanel />
            <DataLifecycleMaintenancePanel />
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
