# Backend

FastAPI 기반 API, 데이터 공급자, 직접 학습 AI, 저장소와 운영 작업을 관리합니다.

## 폴더 책임

- `app/api/`: HTTP 경로와 입력·출력 계약
- `app/services/`: 사용 사례의 실행 순서
- `app/providers/`: Toss, KIS, mock 등 외부 데이터 경계
- `app/repositories/`: PostgreSQL 또는 메모리 저장 구현
- `app/models/`: SQLAlchemy 영속 모델
- `app/local_ai/`: 직접 학습 모델의 특성, 품질 게이트와 런타임
- `app/realtime/`: WebSocket 연결과 내부 실시간 시세 전달
- `app/paper_trading/`: 실제 주문과 격리된 모의투자 규칙
- `app/backtest/`: 전략 시뮬레이션과 성과 측정
- `tests/`: 단위·통합·보안 회귀 테스트

계층 방향은 `api -> services -> providers/repositories`입니다. provider나 repository가 API 계층을 import하지 않도록 유지합니다.

## 주석 원칙

공개 클래스·메서드에는 계약과 부작용을 docstring으로 기록합니다. 단순 getter보다 시점 정합성, 원자성, 재시도, 보안 제한처럼 코드만 보고 이유를 알기 어려운 부분을 우선 설명합니다. 전체 선언 목록은 `docs/maintenance/code-reference-ko.md`가 보완합니다.

## 검증

```powershell
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\ruff.exe check backend scripts
```
