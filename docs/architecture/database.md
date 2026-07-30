# Database baseline

`stocks`는 종목 마스터, `stock_candles`는 raw/cleaned OHLCV, `data_quality_logs`는 정합성 검사 결과를 저장한다.

관리자 데이터 품질 화면은 `data_quality_logs`를 최신순으로 조회하며 종목과 심각도 필터,
페이지 이동, 오류·경고 집계를 제공한다. 조회 API는 관리자 인증을 요구하고 메시지와 규칙,
관측 시각만 반환하며 DB 연결 정보는 노출하지 않는다.

검증 규칙과 장기간 캔들 공백 판정 기준은 [데이터 품질 파이프라인](data-quality.md)에
정리되어 있다.

PostgreSQL에서 `stock_candles`는 `timestamp` 기준 RANGE 파티션 테이블이다. 초기
마이그레이션은 누락 월의 적재 실패를 막기 위해 default 파티션을 만든다.
`PARTITION_MAINTENANCE_ENABLED=true`이면 서버 시작 직후와 매월 20일 03:00 KST에 다음
`PARTITION_LOOKAHEAD_MONTHS`개월(기본 3개월)의 파티션을 미리 생성한다. 기존 default
파티션의 과거 행은 자동 이동하지 않아 운영 중 장시간 잠금을 피한다. SQLite 개발 환경은
`unsupported` 상태로 안전하게 건너뛴다.

```powershell
alembic upgrade head
```

운영성 데이터의 보존·정리 범위와 제외 대상은
[Operational data lifecycle](data-lifecycle.md)에 정의한다. `20260719_0017` 마이그레이션은
데이터 품질 로그, 뉴스, 공시의 `created_at` 정리 작업을 위한 인덱스를 추가한다. 백업 및
격리 복구 절차는 [PostgreSQL backup and restore](../operations/postgresql-backup-restore.md)를
따른다.

장기 캔들은 자동 삭제하지 않는다. 관리자 운영 상태는
`PARTITION_ARCHIVE_AFTER_MONTHS`보다 오래된 완결 월 파티션을 검토 후보로만 표시하며,
실제 이동·분리·삭제 절차와 안전 조건은
[Candle partition archive policy](candle-partition-archive.md)에 정의한다.

`20260719_0018`은 기업행동의 불변 revision을 저장하는 `corporate_actions` 테이블과
`stock_candles.price_basis`를 추가한다. raw/cleaned 캔들을 덮어쓰지 않는 보정 원칙과
기준시점 재현 규칙은
[Point-in-time corporate action adjustments](corporate-action-adjustments.md)에 정의한다.

`20260720_0019` adds `corporate_action_approvals`, an immutable one-to-one evidence record for a
manually confirmed corporate-action revision. It stores no provider credential or response body.
The action row and evidence row are inserted atomically, and both action ID and canonical evidence
hash are unique to make retries idempotent.

`20260720_0020` adds `stock_candles.source_provider` and a bounded inventory index. Existing rows
receive the explicit sentinel `legacy_unknown`; neither their provider nor price basis is inferred.
New ingestion stores the selected Provider name. Operational review uses the read-only inventory
described in [Candle price-basis provenance and inventory](candle-price-basis-inventory.md).

`20260720_0021` adds `stock_candles.price_basis_rule_version`. Existing rows retain the sentinel
`legacy_unknown`; new ingestion persists the version declared by the validated Provider policy.

CI derives the single expected head from the revision graph and performs an empty-database
`upgrade head -> downgrade base -> upgrade head` round-trip on PostgreSQL 16. The backend test
suite runs the same full revision chain against an isolated temporary SQLite database. These checks
never target a developer database or persistent Docker volume and do not replace a backup/restore
rehearsal with production-like data.

Production candle ingestion uses one repository transaction for the stock master row, raw candles,
cleaned candles and data-quality logs. Any failure rolls back all four writes. The individual
repositories remain available for bounded read paths and focused tests, but the scheduler and
manual ingestion service are wired to the atomic repository.
