# Frontend

Next.js 기반 사용자 화면과 서버 전용 BFF를 관리합니다. 브라우저에는 토스·KIS·관리자 API 키를 전달하지 않습니다.

## 폴더 책임

- `app/`: 페이지, 레이아웃, 오류 화면과 BFF Route Handler
- `components/market/`: 종목 검색, 차트, 호가, 시장 현황
- `components/analysis/`: AI 진행 과정, 전문 AI 근거, 최종 진단
- `components/paper/`: 모의 주문과 저장된 포트폴리오
- `components/admin/`: 데이터·모델·계좌 운영 화면
- `components/shared/`: 여러 화면에서 재사용하는 표현 컴포넌트
- `features/`: 기능 단위 상태와 이벤트 흐름
- `lib/`: API 계약, BFF client, 순수 유틸리티
- `e2e/`: 실제 브라우저 사용자 흐름 검증

## 주석 원칙

파일 상단에는 화면의 책임을, 인터페이스에는 데이터 경계를, 복잡한 effect와 보안 처리에는 이유를 적습니다. JSX 호출마다 같은 설명을 반복하지 않습니다. 전체 선언의 기능은 `docs/maintenance/code-reference-ko.md`에서 검색할 수 있습니다.

## 검증

```powershell
cd frontend
..\node_modules\.bin\tsc.cmd --noEmit
npm.cmd test
npx.cmd playwright test
```
