# 프로젝트 구조

```text
stockassist/
|- frontend/          Next.js 화면과 BFF
|- backend/           FastAPI, 도메인, 저장소, 직접 학습 AI
|- scripts/
|  |- ai/data/        데이터 수집·결합·라벨링
|  |- ai/training/    학습·검증·승격
|  `- operations/     운영·보안·백업
|- datasets/          로컬 학습 데이터(Git 제외)
|- artifacts/         모델·검증 결과(Git 제외)
|- infrastructure/    Nginx와 관측 설정
|- docs/              아키텍처·운영·유지보수 문서
`- docker-compose.yml 로컬 실행 환경
```

## 변경 위치 찾기

| 변경하려는 기능 | 시작 위치 |
|---|---|
| 검색·차트·시장 화면 | `frontend/components/market/` |
| AI 결과·애니메이션 | `frontend/components/analysis/` |
| 모의투자 | `frontend/components/paper/`, `backend/app/paper_trading/` |
| 토스 API | `backend/app/providers/toss/`, `backend/app/services/toss_open_api.py` |
| 직접 학습 AI | `backend/app/local_ai/`, `scripts/ai/` |
| DB 저장 | `backend/app/repositories/`, `backend/app/models/` |
| 관리자 운영 | `frontend/components/admin/`, `backend/app/services/operations.py` |

선언 단위 설명은 `docs/maintenance/code-reference-ko.md`, AI 재학습은 `docs/AI_TRAINING_GUIDE_KO.md`를 봅니다.
