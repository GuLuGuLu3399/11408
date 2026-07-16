import importlib.util
import io
import json
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

        for note_type in ("note", "mistake", "flashcard", "progress", "summary"):
            with self.subTest(note_type=note_type):
                self.assertIn(note_type, agents_text)
                self.assertIn(note_type, note_format_text)

        self.assertIn(".claude/references/note-format.md", agents_text)
        self.assertIn("- **A.**", note_format_text)
        self.assertIn("horizontal multiple-choice options", note_format_text)


if __name__ == "__main__":
    unittest.main()
