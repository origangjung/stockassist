# Scripts

반복 가능한 데이터·학습·운영 명령만 둡니다. 생성 데이터와 모델은 각각 Git 제외 경로인 `datasets/`, `artifacts/`에 저장합니다.

- `ai/data/`: 원천 데이터 수집, 시점 기준 결합, 파생 특성 생성, 라벨 생성
- `ai/training/`: 학습, 데이터 감사, 중첩 워크포워드 검증, 후보 승인
- `operations/`: 환경·보안 점검, Docker 백업, 예약 작업, 공급자 smoke/soak 검증
- `generate_korean_code_reference.py`: 소스 선언을 읽어 한글 코드 사전 생성

AI 학습 순서는 `docs/AI_TRAINING_GUIDE_KO.md`를 따릅니다.
