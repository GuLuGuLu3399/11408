import importlib.util
import io
import json
import re
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_agent_contract.py"
MCP_CONFIG_PATH = Path(__file__).resolve().parents[1] / ".mcp.json"
SETTINGS_PATH = Path(__file__).resolve().parents[1] / ".claude" / "settings.local.json"
AGENTS_PATH = Path(__file__).resolve().parents[1] / "AGENTS.md"
NOTE_FORMAT_PATH = (
    Path(__file__).resolve().parents[1] / ".claude" / "references" / "note-format.md"
)
CLAUDE_PATH = Path(__file__).resolve().parents[1] / "CLAUDE.md"
PROMPT_PATH = Path(__file__).resolve().parents[1] / ".claude" / "tolaria-11408-prompt.md"


def load_module():
    spec = importlib.util.spec_from_file_location("agent_contract", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class AgentContractTests(unittest.TestCase):
    def setUp(self):
        self.module = load_module()

    def test_vertical_options_are_allowed(self):
        violations = self.module.scan_markdown(
            Path("valid.md"),
            "- **A.** first\n- **B.** second\n- **C.** third\n- **D.** fourth\n",
        )
        self.assertEqual([], violations)

    def test_horizontal_options_are_rejected(self):
        violations = self.module.scan_markdown(
            Path("bad.md"),
            "A. first | B. second | C. third | D. fourth\n",
        )
        self.assertEqual(["bad.md:1: horizontal multiple-choice options"], violations)

    def test_legacy_rag_tool_names_are_rejected(self):
        violations = self.module.scan_guidance_text(
            Path("CLAUDE.md"),
            "Use study-rag.study_query, then local-rag.query_documents.",
        )
        self.assertEqual(
            [
                "CLAUDE.md: legacy RAG identifier 'study_query'",
                "CLAUDE.md: legacy RAG identifier 'local-rag'",
                "CLAUDE.md: legacy RAG identifier 'query_documents'",
            ],
            violations,
        )

    def test_legacy_rag_tool_names_in_chinese_prose_are_rejected(self):
        violations = self.module.scan_guidance_text(
            Path("CLAUDE.md"),
            "调用study_query查询",
        )
        self.assertEqual(
            ["CLAUDE.md: legacy RAG identifier 'study_query'"],
            violations,
        )

    def test_legacy_rag_tool_names_in_ascii_identifiers_are_allowed(self):
        violations = self.module.scan_guidance_text(
            Path("CLAUDE.md"),
            "my_study_query_helper and local-rag-service",
        )
        self.assertEqual([], violations)

    def test_main_scans_guidance_with_zero_arguments(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            guidance_path = Path(temporary_directory) / "guidance.md"
            guidance_path.write_text("study_query", encoding="utf-8")
            original_guidance_files = self.module.GUIDANCE_FILES
            self.module.GUIDANCE_FILES = (guidance_path,)
            stderr = io.StringIO()
            try:
                with redirect_stderr(stderr):
                    exit_code = self.module.main([])
            finally:
                self.module.GUIDANCE_FILES = original_guidance_files

        self.assertEqual(1, exit_code)
        self.assertEqual(
            f"{guidance_path}: legacy RAG identifier 'study_query'\n",
            stderr.getvalue(),
        )

    def test_main_skips_missing_guidance_files(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            missing_paths = (
                Path(temporary_directory) / "missing-guidance.md",
                Path(temporary_directory) / "missing-skill.md",
            )
            original_guidance_files = self.module.GUIDANCE_FILES
            self.module.GUIDANCE_FILES = missing_paths
            stderr = io.StringIO()
            try:
                with redirect_stderr(stderr):
                    exit_code = self.module.main([])
            finally:
                self.module.GUIDANCE_FILES = original_guidance_files

        self.assertEqual(0, exit_code)
        self.assertEqual("", stderr.getvalue())

    def test_main_scans_positional_markdown_paths_in_line_order(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            markdown_path = Path(temporary_directory) / "questions.md"
            markdown_path.write_text(
                "A. first | B. second | C. third | D. fourth\n"
                "A: first | B: second | C: third | D: fourth\n",
                encoding="utf-8",
            )
            original_guidance_files = self.module.GUIDANCE_FILES
            self.module.GUIDANCE_FILES = ()
            stderr = io.StringIO()
            try:
                with redirect_stderr(stderr):
                    exit_code = self.module.main([str(markdown_path)])
            finally:
                self.module.GUIDANCE_FILES = original_guidance_files

        self.assertEqual(1, exit_code)
        self.assertEqual(
            f"{markdown_path}:1: horizontal multiple-choice options\n"
            f"{markdown_path}:2: horizontal multiple-choice options\n",
            stderr.getvalue(),
        )

    def test_mcp_config_uses_new_rag_and_memory_servers(self):
        if not MCP_CONFIG_PATH.is_file() or not SETTINGS_PATH.is_file():
            self.skipTest("local MCP configuration is unavailable")

        with (
            MCP_CONFIG_PATH.open(encoding="utf-8") as config_file,
            SETTINGS_PATH.open(encoding="utf-8") as settings_file,
        ):
            servers = json.load(config_file)["mcpServers"]
            settings = json.load(settings_file)

        expected_servers = ("study-rag", "memory", "tolaria")
        self.assertTrue(set(expected_servers).issubset(servers))
        self.assertNotIn("local-rag", servers)
        self.assertEqual(
            "D:\\dev\\study-rag\\python\\.venv\\Scripts\\python.exe",
            servers["study-rag"]["command"],
        )
        self.assertEqual(
            ["-m", "study_rag.mcp_server"],
            servers["study-rag"]["args"],
        )
        self.assertEqual("1", servers["study-rag"]["env"]["HF_HUB_OFFLINE"])
        self.assertEqual("cuda", servers["study-rag"]["env"]["STUDY_RAG_DEVICE"])
        self.assertEqual("cmd", servers["memory"]["command"])
        self.assertEqual(
            ["/c", "npx", "-y", "@modelcontextprotocol/server-memory"],
            servers["memory"]["args"],
        )

        enabled_servers = settings["enabledMcpjsonServers"]
        enabled_positions = [
            enabled_servers.index(server_name) for server_name in expected_servers
        ]
        self.assertEqual(sorted(enabled_positions), enabled_positions)
        self.assertNotIn("local-rag", enabled_servers)
        self.assertFalse(settings.get("env", {}))

    def test_local_study_note_contract_is_available(self):
        if not AGENTS_PATH.is_file() or not NOTE_FORMAT_PATH.is_file():
            self.skipTest("local study note guidance is unavailable")

        agents_text = AGENTS_PATH.read_text(encoding="utf-8")
        note_format_text = NOTE_FORMAT_PATH.read_text(encoding="utf-8")

        supported_types_match = re.search(
            r"^For study notes, the supported types are exactly (?P<types>.+)\.$",
            agents_text,
            re.MULTILINE,
        )
        self.assertIsNotNone(supported_types_match)
        assert supported_types_match is not None
        self.assertEqual(
            ("note", "mistake", "flashcard", "progress", "summary"),
            tuple(re.findall(r"`([^`]+)`", supported_types_match.group("types"))),
        )

        expected_outlines = (
            "| `note` | Conclusion; conditions or steps | Traps |",
            "| `mistake` | Problem; options where applicable; my answer; correct answer; "
            "error cause; recognition signal | - |",
            "| `flashcard` | Question; answer; common mistake; source | - |",
            "| `progress` | Completed work; blocker; next action | - |",
            "| `summary` | Scope; connections; unresolved gaps | - |",
        )
        for outline in expected_outlines:
            with self.subTest(outline=outline):
                self.assertIn(outline, note_format_text)

        self.assertIn(
            "Add `subject`, `status`, `topics`, `related_to`, and `source` only when "
            "they are meaningful for that note.",
            agents_text,
        )
        self.assertIn(
            "Preserve the existing frontmatter key style when editing a note.",
            agents_text,
        )
        self.assertIn("Use the first H1 as the note title.", agents_text)
        self.assertIn("Do not bulk-normalize historical notes.", agents_text)
        self.assertIn(".claude/references/note-format.md", agents_text)
        self.assertIn("This format applies only to new or edited notes.", note_format_text)
        for option in ("A", "B", "C", "D"):
            with self.subTest(option=option):
                self.assertIn(f"- **{option}.**", note_format_text)
        self.assertIn("| Option | Judgment | Reason |", note_format_text)
        self.assertIn("horizontal multiple-choice options", note_format_text)
        self.assertIn(
            "The same-line form `A. ... | B. ... | C. ... | D. ...` is forbidden.",
            note_format_text,
        )

    def test_local_vault_guidance_uses_current_read_only_rag_contract(self):
        if not CLAUDE_PATH.is_file() or not PROMPT_PATH.is_file():
            self.skipTest("local vault guidance is unavailable")

        claude_text = CLAUDE_PATH.read_text(encoding="utf-8")
        prompt_text = PROMPT_PATH.read_text(encoding="utf-8")

        for literal in (
            "study-rag.rag_query",
            "study-rag.rag_inspect",
            "strict RAG filter",
            "memory",
            "not an evidence source",
        ):
            with self.subTest(prompt_literal=literal):
                self.assertIn(literal, prompt_text)

        markdown_destinations = set(
            re.findall(r"\[[^]]+\]\(([^)]+)\)", claude_text)
        )
        for destination in (
            "AGENTS.md",
            ".claude/tolaria-11408-prompt.md",
            ".claude/references/note-format.md",
            ".claude/skills/11408-study-coach/SKILL.md",
            ".claude/skills/11408-rag-query/SKILL.md",
            ".claude/skills/11408-mistake-review/SKILL.md",
            ".claude/skills/11408-flashcard/SKILL.md",
            ".claude/skills/11408-markdown-rendering/SKILL.md",
        ):
            with self.subTest(markdown_destination=destination):
                self.assertIn(destination, markdown_destinations)
                self.assertTrue((CLAUDE_PATH.parent / destination).is_file())

        self.assertIn("保留用户原始中文和考试术语", prompt_text)

        for path, text in ((CLAUDE_PATH, claude_text), (PROMPT_PATH, prompt_text)):
            for legacy_identifier in (
                "local-rag",
                "study_query",
                "query_documents",
                "read_chunk_neighbors",
                "ingest_file",
                "delete_file",
            ):
                with self.subTest(path=path, legacy_identifier=legacy_identifier):
                    self.assertNotIn(legacy_identifier, text)


if __name__ == "__main__":
    unittest.main()
