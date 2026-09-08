"""애플리케이션 소스의 클래스·메서드·함수·인터페이스 한글 사전을 생성한다.

코드에 의미 없는 반복 주석을 삽입하지 않으면서도 전체 공개 구조를 검색할 수 있게 한다.
Python은 AST로, TypeScript는 선언 구문을 기준으로 읽으며 생성 결과는
``docs/maintenance/code-reference-ko.md``에 저장한다.
"""

from __future__ import annotations

import ast
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "maintenance" / "code-reference-ko.md"
PYTHON_ROOTS = (ROOT / "backend" / "app", ROOT / "scripts")
TYPESCRIPT_ROOTS = (
    ROOT / "frontend" / "app",
    ROOT / "frontend" / "components",
    ROOT / "frontend" / "features",
    ROOT / "frontend" / "lib",
)

KOREAN_PATTERN = re.compile(r"[가-힣]")
DECLARATION_PATTERN = re.compile(
    r"^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)"
    r"|^(?:export\s+)?const\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\("
)
INTERFACE_PATTERN = re.compile(
    r"^(?:export\s+)?interface\s+([A-Za-z_$][\w$]*)(?:\s+extends\s+([^\{]+))?"
)
TYPE_PATTERN = re.compile(r"^(?:export\s+)?type\s+([A-Za-z_$][\w$]*)\s*=")
CLASS_PATTERN = re.compile(r"^(?:export\s+)?class\s+([A-Za-z_$][\w$]*)")
FIELD_PATTERN = re.compile(r"^\s*(?:readonly\s+)?([A-Za-z_$][\w$]*)(?:\?)?\s*:")


def _relative(path: Path) -> str:
    """`_relative`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    return path.relative_to(ROOT).as_posix()


def _module_role(path: Path) -> str:
    """파일 경로를 이용해 유지보수자가 알아야 할 계층 책임을 설명한다."""

    value = _relative(path)
    rules = (
        ("backend/app/api/", "HTTP 요청·응답 계약과 입력 검증을 담당합니다."),
        ("backend/app/services/", "애플리케이션 사용 사례와 도메인 호출 순서를 조율합니다."),
        ("backend/app/providers/", "외부 시세 공급자 계약 또는 구현을 담당합니다."),
        ("backend/app/repositories/", "데이터 저장과 조회 경계를 구현합니다."),
        ("backend/app/models/", "데이터베이스 ORM 모델을 정의합니다."),
        ("backend/app/local_ai/", "직접 학습 AI의 특성·모델·품질·실행을 담당합니다."),
        ("backend/app/prediction/", "예측 엔진과 모델 artifact를 관리합니다."),
        ("backend/app/ai_reports/", "계산된 사실을 리포트로 조합하고 준법 규칙을 검증합니다."),
        ("backend/app/backtest/", "전략 백테스트와 성과 평가를 담당합니다."),
        ("backend/app/core/", "보안·오류·요청 문맥 같은 공통 기반 기능을 담당합니다."),
        ("backend/app/pipeline/", "원시 시장 데이터를 검증하고 정제합니다."),
        ("backend/app/realtime/", "실시간 시세 연결과 메시지 전달을 담당합니다."),
        ("backend/app/", "백엔드 도메인 기능을 구현합니다."),
        ("frontend/app/api/", "브라우저와 FastAPI 사이의 서버 전용 BFF 경로입니다."),
        ("frontend/app/", "Next.js 화면 진입점과 전역 오류·레이아웃을 담당합니다."),
        ("frontend/components/admin/", "관리자 운영 화면과 상태 조회 기능을 렌더링합니다."),
        ("frontend/components/analysis/", "AI 분석 진행과 결과 표현을 담당합니다."),
        ("frontend/components/market/", "종목 검색·차트·시장 데이터 화면을 담당합니다."),
        ("frontend/components/paper/", "모의투자 주문과 자산 화면을 담당합니다."),
        ("frontend/components/", "공통 사용자 화면과 상호작용을 렌더링합니다."),
        ("frontend/features/", "화면 기능별 상태와 도메인 이벤트를 관리합니다."),
        ("frontend/lib/", "프론트에서 재사용하는 타입 계약과 순수 함수·API client입니다."),
        ("scripts/ai/data/", "AI 학습 데이터를 수집·결합·보강합니다."),
        ("scripts/ai/training/", "로컬 AI 모델을 학습·검증하고 후보를 관리합니다."),
        ("scripts/operations/", "개발·운영·보안 점검 작업을 수행합니다."),
        ("scripts/", "저장소 문서 자동화 작업을 수행합니다."),
    )
    return next(description for prefix, description in rules if value.startswith(prefix))


def _first_korean_doc(node: ast.AST) -> str | None:
    """기존 한글 docstring이 있으면 첫 문단을 재사용한다."""

    raw = ast.get_docstring(node, clean=True)
    if not raw or not KOREAN_PATTERN.search(raw):
        return None
    return " ".join(raw.split("\n\n", 1)[0].split())


def _class_description(node: ast.ClassDef) -> str:
    """`_class_description`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    documented = _first_korean_doc(node)
    if documented:
        return documented
    name = node.name
    bases = {ast.unparse(base) for base in node.bases}
    if any("Protocol" in base or "ABC" in base for base in bases):
        return f"`{name}` 구현체가 제공해야 하는 메서드 계약을 정의합니다."
    suffixes = (
        ("Adapter", "서로 다른 외부 제공자의 기능 차이를 공통 호출 방식으로 맞추는 어댑터입니다."),
        ("Service", "사용 사례의 처리 순서와 하위 의존성 호출을 조율하는 서비스입니다."),
        ("Provider", "외부 또는 모의 데이터 원천을 동일한 계약으로 제공하는 구현체입니다."),
        ("Repository", "도메인 객체의 저장·조회 방식을 캡슐화하는 저장소입니다."),
        ("Middleware", "요청과 응답 사이에서 공통 정책을 적용하는 미들웨어입니다."),
        ("Engine", "입력 데이터로부터 결정론적 결과를 계산하는 엔진입니다."),
        ("Client", "외부 서비스의 인증·요청·응답 검증을 캡슐화하는 client입니다."),
        ("Request", "API 요청 본문의 필드와 검증 규칙을 정의합니다."),
        ("Response", "API 응답으로 전달하는 필드 계약을 정의합니다."),
        ("Model", "데이터베이스에 저장되는 필드와 관계를 정의하는 ORM 모델입니다."),
        ("Error", "해당 실패 조건을 호출 계층에 구분해 전달하는 예외입니다."),
        ("Result", "계산 또는 처리 결과를 묶어 전달하는 값 객체입니다."),
        ("Config", "실행 또는 계산에 필요한 설정 값을 묶는 객체입니다."),
        ("Batch", "한 번에 처리할 데이터 묶음과 처리 상태를 전달하는 값 객체입니다."),
        ("Snapshot", "특정 시점에 관측된 데이터 상태를 변경 없이 전달하는 값 객체입니다."),
        ("Finding", "전문 분석 과정에서 확인한 결과와 근거를 묶어 전달합니다."),
        ("Context", "여러 처리 단계가 함께 사용하는 실행 문맥과 입력 정보를 묶습니다."),
        ("Record", "저장하거나 전송할 한 건의 구조화된 데이터를 나타냅니다."),
        ("Point", "시계열 또는 차트에서 사용하는 한 시점의 값을 나타냅니다."),
        ("Item", "목록에서 사용하는 한 건의 구조화된 항목을 나타냅니다."),
    )
    return next(
        (description for suffix, description in suffixes if name.endswith(suffix)),
        f"`{name}` 관련 상태와 동작을 하나의 객체로 묶습니다.",
    )


def _callable_description(name: str, *, async_function: bool = False) -> str:
    """함수 이름의 동사를 기준으로 부작용과 반환 목적을 한글로 설명한다."""

    lowered = name.lstrip("_").lower()
    if name == "__init__":
        return "`__init__`은(는) 의존성과 초기 상태를 저장해 객체를 사용할 수 있게 초기화합니다."
    if lowered == "main":
        return "`main`은(는) 명령행 인자를 해석하고 이 스크립트의 전체 작업 순서를 실행합니다."
    if lowered in {"health", "liveness", "readiness"}:
        return f"`{name}`은(는) 서비스와 핵심 의존성의 현재 동작 가능 상태를 반환합니다."
    if lowered in {
        "quote", "candles", "trades", "orderbook", "stock_info", "financials", "news", "disclosures"
    }:
        return f"`{name}`은(는) 이름에 해당하는 시장 또는 기업 데이터를 조회해 공통 형식으로 반환합니다."
    if lowered.endswith("_for"):
        return f"`{name}`은(는) 입력 조건을 지원하는 제공자나 처리 대상을 선택해 반환합니다."
    verbs = (
        (("get_", "fetch_", "load_", "read_", "latest_", "find_"), "필요한 데이터를 조회해 반환합니다."),
        (("build_", "create_", "make_"), "입력 값과 설정을 결합해 새 결과 객체를 생성합니다."),
        (("calculate_", "compute_", "score_", "predict"), "입력 데이터를 기준으로 모델 또는 규칙의 결과 값을 계산해 반환합니다."),
        (("validate_", "verify_", "check_", "is_", "has_"), "입력 또는 현재 상태가 규칙을 만족하는지 검증합니다."),
        (("format_", "serialize_", "to_"), "내부 값을 전송·표시 가능한 형식으로 변환합니다."),
        (("parse_", "normalize_", "extract_"), "원시 입력을 해석하고 필요한 값을 정규화해 추출합니다."),
        (("save_", "store_", "add_", "insert_", "upsert_"), "데이터를 저장하거나 기존 상태에 추가합니다."),
        (("update_", "set_", "replace_", "promote_"), "기존 상태를 검증된 새 값으로 변경합니다."),
        (("delete_", "remove_", "clear_", "cleanup_"), "대상 데이터나 만료된 상태를 안전하게 제거합니다."),
        (("run_", "execute_", "train", "analyze", "synthesize"), "해당 작업의 전체 처리 흐름을 실행하고 결과를 반환합니다."),
        (("handle_", "on_"), "발생한 이벤트 또는 요청 상태 변화를 처리합니다."),
        (("connect", "disconnect", "subscribe", "publish"), "연결 또는 메시지 전달 생명주기를 관리합니다."),
    )
    description = next(
        (text for prefixes, text in verbs if lowered.startswith(prefixes)),
        "이름과 시그니처에 해당하는 단일 작업을 수행합니다.",
    )
    if async_function:
        description = "비동기로 " + description
    return f"`{name}`은(는) {description}"


def _python_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """`_python_signature`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    prefix = "async " if isinstance(node, ast.AsyncFunctionDef) else ""
    try:
        arguments = ast.unparse(node.args)
    except (AttributeError, ValueError):
        arguments = "..."
    return f"{prefix}{node.name}({arguments})"


def _python_sections() -> tuple[list[str], int]:
    """`_python_sections`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    lines = ["## Python 클래스·함수·메서드", ""]
    count = 0
    files = sorted(path for root in PYTHON_ROOTS for path in root.rglob("*.py"))
    for path in files:
        if "__pycache__" in path.parts:
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        declarations = [
            node
            for node in tree.body
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        ]
        if not declarations:
            continue
        lines.extend((f"### `{_relative(path)}`", "", _module_role(path), ""))
        for node in declarations:
            if isinstance(node, ast.ClassDef):
                count += 1
                lines.extend(
                    (
                        f"- **클래스 `{node.name}`** · {path.name}:{node.lineno}",
                        f"  - 기능: {_class_description(node)}",
                    )
                )
                for method in node.body:
                    if not isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        continue
                    count += 1
                    description = _first_korean_doc(method) or _callable_description(
                        method.name,
                        async_function=isinstance(method, ast.AsyncFunctionDef),
                    )
                    lines.extend(
                        (
                            f"  - 메서드 `{_python_signature(method)}` · {path.name}:{method.lineno}",
                            f"    - 기능: {description}",
                        )
                    )
            else:
                count += 1
                description = _first_korean_doc(node) or _callable_description(
                    node.name,
                    async_function=isinstance(node, ast.AsyncFunctionDef),
                )
                lines.extend(
                    (
                        f"- **함수 `{_python_signature(node)}`** · {path.name}:{node.lineno}",
                        f"  - 기능: {description}",
                    )
                )
        lines.append("")
    return lines, count


def _interface_fields(lines: list[str], start: int) -> list[str]:
    """`_interface_fields`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    fields: list[str] = []
    depth = 0
    opened = False
    for line in lines[start:]:
        depth += line.count("{") - line.count("}")
        opened = opened or "{" in line
        match = FIELD_PATTERN.match(line)
        if opened and match and match.group(1) not in fields:
            fields.append(match.group(1))
        if opened and depth <= 0:
            break
    return fields


def _preceding_korean_jsdoc(lines: list[str], start: int) -> str | None:
    """선언 바로 위의 한글 JSDoc 첫 문단을 찾아 코드 사전 설명으로 사용한다."""

    cursor = start - 1
    while cursor >= 0 and not lines[cursor].strip():
        cursor -= 1
    if cursor < 0 or not lines[cursor].strip().endswith("*/"):
        return None

    comment_lines: list[str] = []
    while cursor >= 0:
        stripped = lines[cursor].strip()
        comment_lines.append(stripped)
        if "/**" in stripped:
            break
        cursor -= 1
    if not comment_lines or "/**" not in comment_lines[-1]:
        return None

    raw = " ".join(reversed(comment_lines))
    cleaned = re.sub(r"^/\*\*|\*/$", "", raw).replace("*", " ")
    cleaned = " ".join(cleaned.split())
    if not cleaned or not KOREAN_PATTERN.search(cleaned):
        return None
    return cleaned


def _interface_description(name: str, path: Path, fields: list[str]) -> str:
    """`_interface_description`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    if name.endswith("Props"):
        purpose = "React 컴포넌트가 부모로부터 받는 속성 계약입니다."
    elif name.endswith("Request"):
        purpose = "서버로 전송하는 요청 데이터의 필드와 타입을 제한합니다."
    elif name.endswith("Response") or name.endswith("Result"):
        purpose = "처리 결과 또는 서버 응답을 소비하는 쪽에 전달하는 계약입니다."
    elif "api" in path.name.lower():
        purpose = "API 응답을 컴파일 시점에 검증하고 화면의 필드 접근을 제한하는 계약입니다."
    elif "office" in path.as_posix() or "analysis" in path.name:
        purpose = "AI 분석 화면의 상태와 이벤트 데이터 형태를 통일하는 계약입니다."
    else:
        purpose = "서로 다른 함수와 컴포넌트 사이에서 전달하는 데이터 형태를 통일합니다."
    if fields:
        purpose += " 주요 필드: " + ", ".join(f"`{field}`" for field in fields[:20]) + "."
    return f"`{name}` 인터페이스는 {purpose}"


def _typescript_sections() -> tuple[list[str], int]:
    """`_typescript_sections`은(는) 이름과 시그니처에 해당하는 단일 작업을 수행합니다."""

    lines_out = ["## TypeScript 인터페이스·타입·함수", ""]
    count = 0
    files = sorted(
        path
        for root in TYPESCRIPT_ROOTS
        for path in root.rglob("*")
        if path.suffix in {".ts", ".tsx"}
        and not {".next", "node_modules", "test-results"}.intersection(path.parts)
    )
    for path in files:
        try:
            source_lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        entries: list[tuple[int, str, str]] = []
        for index, line in enumerate(source_lines):
            stripped = line.strip()
            documented = _preceding_korean_jsdoc(source_lines, index)
            interface_match = INTERFACE_PATTERN.match(stripped)
            if interface_match:
                name = interface_match.group(1)
                fields = _interface_fields(source_lines, index)
                if documented:
                    field_summary = ""
                    if fields:
                        field_summary = " 주요 필드: " + ", ".join(
                            f"`{field}`" for field in fields[:20]
                        ) + "."
                    description = f"`{name}` 인터페이스는 {documented}{field_summary}"
                else:
                    description = _interface_description(name, path, fields)
                entries.append((index + 1, "인터페이스", description))
                continue
            class_match = CLASS_PATTERN.match(stripped)
            if class_match:
                name = class_match.group(1)
                description = documented or "관련 상태와 동작을 하나의 객체로 묶습니다."
                entries.append((index + 1, "클래스", f"`{name}` 클래스는 {description}"))
                continue
            type_match = TYPE_PATTERN.match(stripped)
            if type_match:
                name = type_match.group(1)
                description = documented or "허용되는 값의 범위나 여러 데이터 형태의 조합을 제한합니다."
                entries.append(
                    (
                        index + 1,
                        "타입",
                        f"`{name}` 타입은 {description}",
                    )
                )
                continue
            function_match = DECLARATION_PATTERN.match(stripped)
            if function_match:
                name = function_match.group(1) or function_match.group(2)
                description = documented or _callable_description(name)
                entries.append((index + 1, "함수", description))
        if not entries:
            continue
        lines_out.extend((f"### `{_relative(path)}`", "", _module_role(path), ""))
        for line_number, kind, description in entries:
            count += 1
            lines_out.append(f"- **{kind}** · {path.name}:{line_number} · {description}")
        lines_out.append("")
    return lines_out, count


def main() -> int:
    """현재 소스 선언을 읽어 한글 코드 사전을 재생성한다."""

    python_lines, python_count = _python_sections()
    typescript_lines, typescript_count = _typescript_sections()
    header = [
        "# StockPilot AI 한글 코드 사전",
        "",
        "> 이 문서는 `scripts/generate_korean_code_reference.py`가 생성합니다.",
        "> 수동으로 수정하지 말고 소스의 한글 docstring/JSDoc을 고친 뒤 다시 생성하세요.",
        "",
        "## 읽는 방법",
        "",
        "- 클래스는 책임과 포함된 메서드를 함께 표시합니다.",
        "- 메서드와 함수는 시그니처, 원본 줄 번호, 수행 기능을 표시합니다.",
        "- TypeScript 인터페이스는 어느 계층의 계약인지와 주요 필드를 표시합니다.",
        "- `_`로 시작하는 항목도 내부 동작 추적을 위해 포함합니다.",
        "",
        f"현재 수록 항목: Python {python_count}개, TypeScript {typescript_count}개.",
        "",
    ]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(header + python_lines + typescript_lines) + "\n", encoding="utf-8")
    print(f"generated {OUTPUT.relative_to(ROOT)} ({python_count + typescript_count} declarations)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
