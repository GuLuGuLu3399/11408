import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "check_agent_contract.py"


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


if __name__ == "__main__":
    unittest.main()
