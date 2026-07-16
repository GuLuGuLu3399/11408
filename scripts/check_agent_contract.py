import sys
import re
from pathlib import Path


GUIDANCE_FILES = (
    Path("CLAUDE.md"),
    Path(".claude/tolaria-11408-prompt.md"),
    Path(".claude/skills/11408-study-coach/SKILL.md"),
    Path(".claude/skills/11408-rag-query/SKILL.md"),
    Path(".claude/skills/11408-mistake-review/SKILL.md"),
    Path(".claude/skills/11408-flashcard/SKILL.md"),
    Path(".claude/skills/11408-markdown-rendering/SKILL.md"),
)

HORIZONTAL_OPTIONS_PATTERN = re.compile(
    r"(?<![A-Za-z0-9_])A[.、．:：].*?B[.、．:：].*?C[.、．:：].*?D[.、．:：]"
)
LEGACY_IDENTIFIER_PATTERN = re.compile(
    r"(?<![\w-])(?P<identifier>local-rag|study_query|query_documents|"
    r"read_chunk_neighbors|ingest_file|delete_file)(?![\w-])"
)


def scan_markdown(path: Path, text: str) -> list[str]:
    violations = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if HORIZONTAL_OPTIONS_PATTERN.search(line):
            violations.append(f"{path}:{line_number}: horizontal multiple-choice options")
    return violations


def scan_guidance_text(path: Path, text: str) -> list[str]:
    return [
        f"{path}: legacy RAG identifier '{match.group('identifier')}'"
        for match in LEGACY_IDENTIFIER_PATTERN.finditer(text)
    ]


def main(argv: list[str] | None = None) -> int:
    repository_root = Path(__file__).resolve().parents[1]
    markdown_paths = [Path(argument) for argument in (sys.argv[1:] if argv is None else argv)]
    violations = []

    for guidance_path in GUIDANCE_FILES:
        path = repository_root / guidance_path
        violations.extend(scan_guidance_text(guidance_path, path.read_text(encoding="utf-8")))

    for path in markdown_paths:
        violations.extend(scan_markdown(path, path.read_text(encoding="utf-8")))

    for violation in violations:
        print(violation, file=sys.stderr)
    return int(bool(violations))


if __name__ == "__main__":
    raise SystemExit(main())
