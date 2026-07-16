import { AdminWorkspace } from "../../components/admin-workspace";

export default function AdminPage() {
  return (
    <main>
      <nav>
        <strong>StockPilot <span>OPS</span></strong>
        <a href="/">시장 분석으로 돌아가기</a>
      </nav>
      <AdminWorkspace />
    </main>
  );
}
