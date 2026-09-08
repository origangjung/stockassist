"""Python 선언과 TypeScript 인터페이스·공개 함수의 한글 설명 누락을 보완한다."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
import re
import sys

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPOSITORY_ROOT))
from scripts.generate_korean_code_reference import (  # noqa: E402
    ROOT,
    TYPESCRIPT_ROOTS,
    _callable_description,
    _class_description,
    _module_role,
)


PYTHON_ROOTS = (ROOT / "backend" / "app", ROOT / "scripts")
TS_DECLARATION = re.compile(
    r"^(?P<indent>\s*)(?:(?P<export>export)\s+)?"
    r"(?:(?P<interface>interface)|(?P<class>class)|"
    r"(?:(?:default\s+)?(?:async\s+)?function)|"
    r"(?P<const>const)\s+)\s*(?P<name>[A-Za-z_$][\w$]*)"
)


def parse_args() -> argparse.Namespace:
    """점검 또는 실제 보완 모드를 선택한다."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def python_description(node: ast.AST) -> str:
    """AST 선언 종류와 이름을 기반으로 호출자 관점의 설명을 만든다."""

    if isinstance(node, ast.ClassDef):
        return _class_description(node)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return _callable_description(
            node.name,
            async_function=isinstance(node, ast.AsyncFunctionDef),
        )
    raise TypeError("unsupported declaration")


def document_python(path: Path, *, apply: bool) -> int:
    """본문 첫 줄에 docstring이 없는 다중 행 Python 선언을 보완한다."""

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    insertions: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if ast.get_docstring(node) or not node.body:
            continue
        first_statement = node.body[0]
        if (
            isinstance(first_statement, ast.Expr)
            and isinstance(first_statement.value, ast.Constant)
            and first_statement.value.value is Ellipsis
        ):
            # ``def contract(...): ...`` 형태는 본문과 선언이 같은 줄일 수 있어 외부 코드 사전에서 설명한다.
            continue
        if isinstance(node, ast.ClassDef):
            decorators = getattr(first_statement, "decorator_list", ())
            insertion_line = min(
                [first_statement.lineno, *(decorator.lineno for decorator in decorators)]
            )
        else:
            insertion_line = first_statement.lineno
        if insertion_line <= node.lineno:
            continue
        indentation = " " * (node.col_offset + 4)
        text = python_description(node).replace('"""', "'''")
        insertions.append((insertion_line - 1, f'{indentation}"""{text}"""\n\n'))
    if apply and insertions:
        lines = source.splitlines(keepends=True)
        for index, text in sorted(insertions, reverse=True):
            lines.insert(index, text)
        path.write_text("".join(lines), encoding="utf-8", newline="")
    return len(insertions)


def has_jsdoc(lines: list[str], index: int) -> bool:
    """선언 바로 앞의 공백을 건너뛴 마지막 블록이 JSDoc인지 확인한다."""

    cursor = index - 1
    while cursor >= 0 and not lines[cursor].strip():
        cursor -= 1
    return cursor >= 0 and lines[cursor].strip().endswith("*/")


def typescript_description(path: Path, match: re.Match[str]) -> str:
    """TypeScript 선언 종류에 맞는 외부 계약 설명을 만든다."""

    name = match.group("name")
    if match.group("interface"):
        return f"{name} 인터페이스는 {_module_role(path)}에서 교환하는 필드 계약을 정의합니다."
    if match.group("class"):
        return f"{name} 클래스는 {_module_role(path)}의 상태와 동작을 캡슐화합니다."
    return _callable_description(name, async_function="async" in match.group(0))


def document_typescript(path: Path, *, apply: bool) -> int:
    """인터페이스·클래스·공개 함수 선언 바로 위에 JSDoc을 추가한다."""

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    insertions: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = TS_DECLARATION.match(line)
        if not match or has_jsdoc(lines, index):
            continue
        if match.group("const") and not match.group("export"):
            continue
        indentation = match.group("indent")
        insertions.append(
            (index, f"{indentation}/** {typescript_description(path, match)} */\n")
        )
    if apply and insertions:
        for index, text in sorted(insertions, reverse=True):
            lines.insert(index, text)
        path.write_text("".join(lines), encoding="utf-8", newline="")
    return len(insertions)


def files(roots: tuple[Path, ...], patterns: tuple[str, ...]):
    """생성물과 의존성 디렉터리를 제외한 소스 파일을 반환한다."""

    for root in roots:
        for pattern in patterns:
            for path in sorted(root.rglob(pattern)):
                if not {"node_modules", ".next", "__pycache__"}.intersection(path.parts):
                    yield path


def main() -> int:
    """선언 설명 누락 수를 보고하고 apply 모드에서는 소스를 보완한다."""

    args = parse_args()
    count = sum(document_python(path, apply=args.apply) for path in files(PYTHON_ROOTS, ("*.py",)))
    count += sum(
        document_typescript(path, apply=args.apply)
        for path in files(TYPESCRIPT_ROOTS, ("*.ts", "*.tsx"))
    )
    print(f"declaration_docs={'updated' if args.apply else 'missing'} count={count}")
    return 0 if args.apply or count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
