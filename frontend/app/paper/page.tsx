/** page 파일은 Next.js 페이지와 레이아웃 기능을 담당한다. */

import type { Metadata } from "next";
import { PaperPortfolioDashboard } from "../../components/paper/paper-portfolio-dashboard";

/** `metadata`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export const metadata: Metadata = {
  title: "내 모의투자 | StockPilot AI",
  description: "가상 자산과 보유 종목 수익률을 확인하는 모의투자 계좌",
};

/** `PaperPortfolioPage`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export default function PaperPortfolioPage() {
  return <PaperPortfolioDashboard />;
}
