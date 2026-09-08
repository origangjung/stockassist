"""소스 파일에 계층 책임을 설명하는 한글 헤더가 있는지 점검하고 보완한다.

선언 이름을 되풀이하는 주석은 만들지 않는다. 파일 단위 책임만 자동화하고 클래스·메서드의
구체적인 계약은 소스 docstring/JSDoc과 생성된 한글 코드 사전에서 관리한다.
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PYTHON_ROOTS = (ROOT / "backend" / "app", ROOT / "scripts")
TYPESCRIPT_ROOTS = (
    ROOT / "frontend" / "app",
    ROOT / "frontend" / "components",
    ROOT / "frontend" / "features",
    ROOT / "frontend" / "lib",
)

ROLES = (
    ("backend/app/api/", "HTTP 요청·응답과 접근 제어"),
    ("backend/app/services/", "애플리케이션 사용 사례"),
    ("backend/app/providers/", "외부 데이터 공급자 연동"),
    ("backend/app/repositories/", "데이터 저장과 조회"),
    ("backend/app/models/", "데이터베이스 영속 모델"),
    ("backend/app/local_ai/", "직접 학습 AI 특성과 실행"),
    ("backend/app/realtime/", "실시간 시세 연결"),
    ("backend/app/backtest/", "전략 검증과 성과 계산"),
    ("backend/app/", "백엔드 도메인"),
    ("scripts/ai/data/", "AI 학습 데이터 수집·결합"),
    ("scripts/ai/training/", "AI 학습·검증·승격"),
    ("scripts/operations/", "개발·운영·보안 점검"),
    ("scripts/", "저장소 자동화"),
    ("frontend/app/api/", "브라우저와 백엔드 사이의 BFF"),
    ("frontend/app/", "Next.js 페이지와 레이아웃"),
    ("frontend/components/admin/", "관리자 운영 화면"),
    ("frontend/components/analysis/", "AI 분석 진행과 결과 화면"),
    ("frontend/components/market/", "종목·시장 데이터 화면"),
    ("frontend/components/paper/", "모의투자 화면"),
    ("frontend/components/", "공유 화면 컴포넌트"),
    ("frontend/features/", "프론트 기능 상태와 이벤트"),
    ("frontend/lib/", "프론트 타입 계약과 API client"),
)


def parse_args() -> argparse.Namespace:
    """점검 전용 또는 실제 보완 모드를 선택한다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="누락된 파일 헤더를 직접 추가")
    return parser.parse_args()


def role(path: Path) -> str:
    """저장소 상대 경로를 가장 가까운 계층 책임으로 변환한다."""

    relative = path.relative_to(ROOT).as_posix()
    return next((description for prefix, description in ROLES if relative.startswith(prefix)), "프로젝트")


def description(path: Path) -> str:
    """파일 이름과 계층을 결합해 한 줄짜리 책임 설명을 만든다."""

    if path.stem == "__init__":
        package = ".".join(path.parent.relative_to(ROOT).parts)
        return f"{package} 패키지의 공개 구성 요소를 묶는다."
    return f"{path.stem} 파일은 {role(path)} 기능을 담당한다."


def document_python(path: Path, *, apply: bool) -> bool:
    """Python 모듈 docstring이 없을 때 파일 첫 부분에 한글 책임을 추가한다."""

    source = path.read_text(encoding="utf-8")
    if ast.get_docstring(ast.parse(source)):
        return False
    if not apply:
        return True
    lines = source.splitlines(keepends=True)
    index = 1 if lines and lines[0].startswith("#!") else 0
    lines[index:index] = [f'"""{description(path)}"""\n', "\n"]
    path.write_text("".join(lines), encoding="utf-8", newline="")
    return True


def document_typescript(path: Path, *, apply: bool) -> bool:
    """TypeScript 파일의 첫 import 앞에 모듈 책임 JSDoc이 없으면 추가한다."""

    source = path.read_text(encoding="utf-8")
    first_import = source.find("import ")
    prefix = source if first_import < 0 else source[:first_import]
    if "/**" in prefix:
        return False
    if not apply:
        return True
    header = f"/** {description(path)} */\n\n"
    directive = '"use client";'
    if source.startswith(directive):
        source = directive + "\n\n" + header + source[len(directive):].lstrip("\r\n")
    else:
        source = header + source
    path.write_text(source, encoding="utf-8", newline="")
    return True


def source_files(roots: tuple[Path, ...], patterns: tuple[str, ...]):
    """지정한 소스 루트에서 생성 디렉터리를 제외한 파일을 순서대로 반환한다."""

    for root in roots:
        for pattern in patterns:
            for path in sorted(root.rglob(pattern)):
                if not {"node_modules", ".next", "__pycache__"}.intersection(path.parts):
                    yield path


def main() -> int:
    """누락 목록을 점검하고 apply 모드에서는 같은 목록을 원자적 파일 쓰기로 보완한다."""

    args = parse_args()
    changed = [
        path
        for path in source_files(PYTHON_ROOTS, ("*.py",))
        if document_python(path, apply=args.apply)
    ]
    changed.extend(
        path
        for path in source_files(TYPESCRIPT_ROOTS, ("*.ts", "*.tsx"))
        if document_typescript(path, apply=args.apply)
    )
    print(f"source_headers={'updated' if args.apply else 'missing'} count={len(changed)}")
    return 0 if args.apply or not changed else 1


if __name__ == "__main__":
    raise SystemExit(main())
