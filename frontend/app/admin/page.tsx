/** page 파일은 Next.js 페이지와 레이아웃 기능을 담당한다. */

import { AdminWorkspace } from "../../components/admin/admin-workspace";

/** `AdminPage`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다. */
export default function AdminPage() {
  return (
    <main className="admin-page">
      <a className="skip-link" href="#admin-workspace">관리자 작업 영역으로 바로가기</a>
      <header>
        <nav aria-label="관리자 주요 메뉴">
          <strong>StockPilot <span>OPS</span></strong>
          <div><span>운영 콘솔</span><b>INTERNAL</b><a href="/">시장 분석</a></div>
        </nav>
      </header>
      <section aria-label="관리자 작업 영역" id="admin-workspace">
        <AdminWorkspace />
      </section>
      <footer className="site-footer">
        <span>StockPilot OPS · Internal operations workspace</span>
        <span>운영 변경 전에는 입력값과 영향 범위를 다시 확인하세요.</span>
      </footer>
    </main>
  );
}
