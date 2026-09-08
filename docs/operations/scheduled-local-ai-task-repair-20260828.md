# 로컬 AI 자동 작업 경로 복구: 2026-08-28

## 발견한 문제

Windows 작업 스케줄러의 로컬 AI 작업 두 개가 폴더 정리 전 실행기 경로를 계속 사용하고 있었다.

- 잘못된 수집 경로: `C:\insat\scripts\run_local_ai_collection.ps1`
- 잘못된 후보 검증 경로: `C:\insat\scripts\run_local_ai_candidate_validation.ps1`

두 파일은 현재 존재하지 않으므로 최근 작업 결과가 `FFFD0000`으로 기록되고 실제 작업이 시작되지 않았다.

## 복구

기존 등록 스크립트를 다시 실행해 현재 경로로 작업을 갱신했다.

- 수집 실행기: `scripts/operations/run_local_ai_collection.ps1`
- 후보 검증 실행기: `scripts/operations/run_local_ai_candidate_validation.ps1`
- 두 실행기 파일의 존재 여부 확인 완료
- 수집 일정: 매일 18:30
- 후보 검증 일정: 매주 토요일 19:30

두 작업은 현재 로그인한 일반 사용자 권한으로 실행되고 자동 모델 승격은 수행하지 않는다.

## 종료 코드와 로그 보완

두 PowerShell 실행기가 실패를 다시 예외로 던지지 않고 작업 스케줄러가 해석할 수 있는 숫자 코드를
반환하도록 보완했다.

- 정상 완료: `0`
- 수집기·검증기 작업 실패: 해당 프로세스의 숫자 종료 코드
- Docker CLI나 실행 환경 문제: `3`
- 실패 로그: `failure_stage=collector`, `validator`, `runner` 중 하나와 종료 코드만 기록
- Docker 출력에서 secret, token, API key, authorization 형태의 값은 로그에 저장하지 않음
- 후보 검증은 계속 `automatic_promotion=false`로 실행

정상 DryRun은 두 실행기 모두 코드 `0`을 반환했다. Docker CLI를 제거한 격리 자식 환경에서는 두
실행기 모두 코드 `3`을 반환했고 로그에는 `failure_stage=runner`만 남았다.

## 재발 방지 테스트

`backend/tests/test_scheduled_task_scripts.py`에 다음 계약 검사 6개를 추가했다.

- KIS, 로컬 AI 수집, 후보 검증 등록 스크립트가 현재 운영 폴더의 실제 실행기를 가리키는지 확인
- 각 실행기가 정상 종료 코드 `0`과 변수 기반 실패 종료 코드를 명시하는지 확인

개별 검사 6개와 전체 백엔드 테스트 476개, Ruff 검사가 모두 통과했다. 이후 실행기 파일을 이동하면서
등록 스크립트를 갱신하지 않으면 테스트가 실패한다.

## DryRun 검증

서버 컨테이너를 켜지 않고 두 실행기를 직접 검증했다.

- 데이터 수집 DryRun: 종료 코드 0
- 수집 대상: 시장, 뉴스, 재무, FINRA 수급, KIS 수급
- 전체 종목 85개, KIS 종목 30개 인식
- 후보 검증 DryRun: 종료 코드 0
- 재무 데이터 1,261행 인식
- 일반 수급 데이터 17,360행 인식
- KIS 수급 데이터 12,746행 인식
- 뉴스 데이터는 검증 74행·시점 그룹 3개라 품질 기준에 따라 학습 보류

검증에 사용한 임시 Docker 컨테이너는 `--rm`으로 제거됐고 API, 웹, PostgreSQL, Redis, Nginx 서버는
계속 정지 상태다. 다음 예약 실행이 끝나면 작업 스케줄러의 최근 결과가 `00000000`인지 확인한다.
