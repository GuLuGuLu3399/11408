# 11408 Vault Agent Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the Vault use one read-only Python RAG MCP, add durable memory, and enforce a concise, non-duplicated guidance and note-format contract.

**Architecture:** Keep note meaning in existing frontmatter types and move only durable Tolaria/data rules into `AGENTS.md`. Keep the main prompt as the authority for assistant behavior and MCP boundaries; make each skill own one task workflow. A small Python checker validates project guidance and only the Markdown paths explicitly passed to it, so historical notes are not mass-migrated.

**Tech Stack:** JSON, Markdown, Python standard library, `unittest`, PowerShell, git.

---

## File Structure

| Path | Responsibility |
|---|---|
| `.mcp.json` | Vault-local stdio MCP definitions |
| `.claude/settings.local.json` | Enabled Vault-local MCP server names only |
| `AGENTS.md` | Tolaria and note data contract |
| `CLAUDE.md` | Short navigation entry point |
| `.claude/tolaria-11408-prompt.md` | Assistant behavior, routing, RAG and memory boundaries |
| `.claude/references/note-format.md` | Shared note-type and choice-format examples |
| `.claude/skills/*/SKILL.md` | Small task-specific workflows without repeated global policy |
| `scripts/check_agent_contract.py` | Read-only contract checker |
| `tests/test_agent_contract.py` | Unit and configuration regression tests |

### Task 1: Add the Contract Checker With Tests

**Files:**
- Create: `tests/test_agent_contract.py`
- Create: `scripts/check_agent_contract.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_agent_contract.py` using `unittest` and load the script with `importlib.util`, following `tests/test_weekly_context_builder.py`. Define these tests:

```python
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
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
python -m unittest tests/test_agent_contract.py -v
```

Expected: failure because `scripts/check_agent_contract.py` does not exist.

- [ ] **Step 3: Implement the minimal read-only checker**

Create `scripts/check_agent_contract.py` with these exact public functions:

```python
def scan_markdown(path: Path, text: str) -> list[str]: ...
def scan_guidance_text(path: Path, text: str) -> list[str]: ...
def main(argv: list[str] | None = None) -> int: ...
```

Use compiled regular expressions for four choice labels on one physical line, accepting `.` `、` `．` `:` and `：` after each label. The error string must be exactly `"{path}:<line>: horizontal multiple-choice options"`.

Scan these legacy identifiers as whole tokens: `local-rag`, `study_query`, `query_documents`, `read_chunk_neighbors`, `ingest_file`, and `delete_file`. Return one stable, source-order error per matched identifier using `"{path}: legacy RAG identifier '{identifier}'"`.

The CLI accepts zero or more Markdown paths. It always scans the guidance files below; it scans Markdown layout only for passed paths, reads UTF-8, prints every violation to stderr, and returns `1` on a violation and `0` otherwise:

```python
GUIDANCE_FILES = (
    Path("CLAUDE.md"),
    Path(".claude/tolaria-11408-prompt.md"),
    Path(".claude/skills/11408-study-coach/SKILL.md"),
    Path(".claude/skills/11408-rag-query/SKILL.md"),
    Path(".claude/skills/11408-mistake-review/SKILL.md"),
    Path(".claude/skills/11408-flashcard/SKILL.md"),
    Path(".claude/skills/11408-markdown-rendering/SKILL.md"),
)
```

Do not modify any content in this script. It is a validator only.

- [ ] **Step 4: Run the checker tests to verify the helper behavior**

Run:

```powershell
python -m unittest tests/test_agent_contract.py -v
```

Expected: every helper test passes.

- [ ] **Step 5: Commit the checker foundation**

```powershell
git add scripts/check_agent_contract.py tests/test_agent_contract.py
git commit -m "test: add vault agent contract checker"
```

### Task 2: Replace Legacy MCP Configuration

**Files:**
- Modify: `.mcp.json`
- Modify: `.claude/settings.local.json`
- Test: `tests/test_agent_contract.py`

- [ ] **Step 1: Extend the failing configuration test**

Add `test_mcp_config_uses_new_rag_and_memory_servers`, which parses the real `.mcp.json`, asserts server names equal `{"study-rag", "memory", "tolaria"}`, asserts `study-rag["command"]` equals `D:\\dev\\study-rag\\python\\.venv\\Scripts\\python.exe`, and asserts:

```python
self.assertEqual(["-m", "study_rag.mcp_server"], study_rag["args"])
self.assertEqual("1", study_rag["env"]["HF_HUB_OFFLINE"])
self.assertEqual("cuda", study_rag["env"]["STUDY_RAG_DEVICE"])
self.assertEqual("cmd", memory["command"])
self.assertEqual(["/c", "npx", "-y", "@modelcontextprotocol/server-memory"], memory["args"])
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
python -m unittest tests/test_agent_contract.py -v
```

Expected: failure because `.mcp.json` has `local-rag`, a Node `study-rag` launcher, and no `memory` entry.

- [ ] **Step 3: Replace `.mcp.json` contents**

Keep `tolaria` unchanged. Remove `local-rag`. Replace `study-rag` with:

```json
{
  "type": "stdio",
  "command": "D:\\dev\\study-rag\\python\\.venv\\Scripts\\python.exe",
  "args": ["-m", "study_rag.mcp_server"],
  "env": {
    "STUDY_RAG_KB_ROOT": "C:\\Users\\GuLuGuLu\\Desktop\\11408\\11408-kb",
    "STUDY_RAG_DERIVED_ROOT": "C:\\Users\\GuLuGuLu\\Desktop\\11408\\11408-kb\\derived",
    "STUDY_RAG_NOTES_ROOT": "C:\\Users\\GuLuGuLu\\Desktop\\11408\\11408-vault\\docs",
    "STUDY_RAG_DB_URI": "C:\\Users\\GuLuGuLu\\Desktop\\11408\\11408-kb\\.rag-lancedb",
    "STUDY_RAG_CACHE_DIR": "C:\\Users\\GuLuGuLu\\Desktop\\11408\\11408-kb\\model-cache",
    "STUDY_RAG_DEVICE": "cuda",
    "STUDY_RAG_BATCH_SIZE": "16",
    "HF_HUB_OFFLINE": "1"
  }
}
```

Add `memory` with the user-approved command and args. In `.claude/settings.local.json`, remove the stale Node/WebGPU environment variables and set `enabledMcpjsonServers` to `study-rag`, `memory`, and `tolaria`.

- [ ] **Step 4: Verify JSON and configuration tests**

Run:

```powershell
Get-Content -Raw .mcp.json | ConvertFrom-Json | Out-Null
python -m unittest tests/test_agent_contract.py -v
```

Expected: JSON parses and every configuration assertion passes.

- [ ] **Step 5: Commit the MCP migration**

```powershell
git add .mcp.json .claude/settings.local.json tests/test_agent_contract.py
git commit -m "feat: use Python study-rag MCP in vault"
```

### Task 3: Establish the Shared Note Contract

**Files:**
- Modify: `AGENTS.md`
- Create: `.claude/references/note-format.md`
- Modify: `tests/test_agent_contract.py`

- [ ] **Step 1: Write failing documentation assertions**

Add tests that read `AGENTS.md` and `.claude/references/note-format.md` and require all five type literals, the exact vertical option example `- **A.**`, and the phrase `horizontal multiple-choice options` in the reference.

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```powershell
python -m unittest tests/test_agent_contract.py -v
```

Expected: failure because no shared note-format reference exists and `AGENTS.md` does not define the study-note body contract.

- [ ] **Step 3: Update the data-contract documents**

Add a compact `Study Note Contract` section to `AGENTS.md`. Preserve existing Tolaria rules and make these statements explicit:

- supported types are `note`, `mistake`, `flashcard`, `progress`, and `summary`;
- use existing key styles; add `subject`, `status`, `topics`, `related_to`, and `source` only when meaningful;
- preserve the first H1 as title;
- do not bulk-normalize historical notes.

Create `.claude/references/note-format.md` as the sole shared template reference. Include one short body-outline table for every type, the exact vertical choice block from the design, the compact option-analysis table, and the forbidden same-line format. State that it applies to new or edited notes only.

- [ ] **Step 4: Verify the shared contract**

Run:

```powershell
python -m unittest tests/test_agent_contract.py -v
```

Expected: all tests pass. Do not run the guidance checker yet: Task 4 intentionally has not removed legacy names from the main prompt and skills.

- [ ] **Step 5: Commit the data contract**

```powershell
git add AGENTS.md .claude/references/note-format.md tests/test_agent_contract.py
git commit -m "docs: define 11408 note contract"
```

### Task 4: Rewrite the Global Guidance Into One Authority Per Rule

**Files:**
- Modify: `CLAUDE.md`
- Modify: `.claude/tolaria-11408-prompt.md`
- Modify: `tests/test_agent_contract.py`

- [ ] **Step 1: Write failing behavior-contract tests**

Add assertions that the main prompt contains all of the following literals:

```text
study-rag.rag_query
study-rag.rag_inspect
strict RAG filter
memory
not an evidence source
```

Assert that `CLAUDE.md` links to `AGENTS.md`, `.claude/tolaria-11408-prompt.md`, `.claude/references/note-format.md`, and each of the five skills.

- [ ] **Step 2: Run the test to verify it fails**

Run:

```powershell
python -m unittest tests/test_agent_contract.py -v
```

Expected: failure because the prompt specifies `study_query`, raw `local-rag` fallbacks, and no memory contract.

- [ ] **Step 3: Replace the duplicated guidance**

Rewrite `CLAUDE.md` to a short project entry point: local-only scope, authority order, RAG read-only reminder, and links to each skill and shared reference.

Rewrite the main prompt to retain only:

- study-coach role and concise Chinese output style;
- intent order `maintenance > mistake_review > practice > concept > flashcard > organize > plan`;
- evidence priority: personal notes, references, clearly labeled general knowledge;
- new RAG behavior: `rag_query` for content, `rag_inspect` for diagnostics, strict misses are valid, no MCP writes, preserve original Chinese/exam terms, no `top_k`;
- memory behavior: durable preferences/facts only, never an evidence source;
- output requirements: evidence source title, uncertainty labeling, and vertical options;
- pointer to the specialised skills and shared format reference instead of copied templates.

Delete every legacy RAG identifier from both files.

- [ ] **Step 4: Verify guidance ownership**

Run:

```powershell
python -m unittest tests/test_agent_contract.py -v
python scripts/check_agent_contract.py
```

Expected: all tests pass and no legacy identifier is printed.

- [ ] **Step 5: Commit the guidance rewrite**

```powershell
git add CLAUDE.md .claude/tolaria-11408-prompt.md tests/test_agent_contract.py
git commit -m "docs: consolidate vault assistant guidance"
```

### Task 5: Make Each Skill Small and Non-Overlapping

**Files:**
- Modify: `.claude/skills/11408-study-coach/SKILL.md`
- Modify: `.claude/skills/11408-rag-query/SKILL.md`
- Modify: `.claude/skills/11408-mistake-review/SKILL.md`
- Modify: `.claude/skills/11408-flashcard/SKILL.md`
- Modify: `.claude/skills/11408-markdown-rendering/SKILL.md`
- Modify: `tests/test_agent_contract.py`

- [ ] **Step 1: Write failing skill-boundary tests**

Add a test that checks:

```python
required = {
    "11408-study-coach": "11408-rag-query",
    "11408-rag-query": "rag_inspect",
    "11408-mistake-review": "note-format.md",
    "11408-flashcard": "note-format.md",
    "11408-markdown-rendering": "horizontal multiple-choice options",
}
```

For every skill body, assert no legacy RAG identifier is present. Assert each YAML description starts with `Use when` and is below 500 characters.

- [ ] **Step 2: Run the tests to verify they fail**

Run:

```powershell
python -m unittest tests/test_agent_contract.py -v
```

Expected: the old skills still reference `study_query` and `local-rag` and duplicate global policy.

- [ ] **Step 3: Rewrite `11408-study-coach`**

Keep it as the thin entry router. It must link each intent to the right specialized skill, point content retrieval to `11408-rag-query`, and point all note writes to `11408-markdown-rendering`. It must not contain retrieval retry mechanics, diary templates, or flashcard templates.

- [ ] **Step 4: Rewrite `11408-rag-query`**

Use `study-rag.rag_query` for study content and `study-rag.rag_inspect` only for health/index diagnosis. Document the accepted filters `subject`, `source_doc`, `unit_type`, `note_type`, `status`, and `topics`; do not document `top_k`. Require exact filters for known metadata, no silent broadening after a strict miss, one focused retry only for ordinary noisy retrieval, and a general-knowledge label after no evidence.

- [ ] **Step 5: Rewrite `11408-mistake-review`**

Use `rag_query` through the RAG skill, then retain the five-part review. Replace the stale `mistake-diary` type with `mistake`, link the shared note reference, and require `## Options` with one `- **A.**` through `- **D.**` line whenever the problem is multiple choice. The template must include `## My Answer`, `## Correct Answer`, `## Error Cause`, `## Recognition Signal`, and `## Variant Self-Test`.

- [ ] **Step 6: Rewrite `11408-flashcard`**

Use RAG through the RAG skill, retain `type: flashcard`, require a real `source`, and link the shared reference. Keep one-card-one-idea, active recall, short checkable answer, and one trap/boundary. Do not repeat MCP policy or note-type catalog.

- [ ] **Step 7: Tighten `11408-markdown-rendering`**

Keep the mobile, frontmatter, heading, formula, table, and Mermaid rules. Add a dedicated `Multiple Choice` section containing the vertical option block, forbidden horizontal chain, and the compact three-column analysis table. Link the shared reference for type-specific bodies; do not copy mistake or flashcard templates.

- [ ] **Step 8: Verify each skill and the checker**

Run:

```powershell
python -m unittest tests/test_agent_contract.py -v
python scripts/check_agent_contract.py
```

Expected: all skills meet their scope assertions and no legacy RAG identifier remains.

- [ ] **Step 9: Commit the skill redesign**

```powershell
git add .claude/skills tests/test_agent_contract.py
git commit -m "docs: refine 11408 study skills"
```

### Task 6: Verify the Complete Vault Contract

**Files:**
- Verify: `.mcp.json`
- Verify: `.claude/settings.local.json`
- Verify: `AGENTS.md`
- Verify: `CLAUDE.md`
- Verify: `.claude/tolaria-11408-prompt.md`
- Verify: `.claude/references/note-format.md`
- Verify: `.claude/skills/`
- Verify: `scripts/check_agent_contract.py`
- Verify: `tests/test_agent_contract.py`

- [ ] **Step 1: Check a valid and an invalid choice fixture**

Run:

```powershell
$valid = Join-Path $env:TEMP "11408-valid-options.md"
$invalid = Join-Path $env:TEMP "11408-invalid-options.md"
Set-Content -Encoding utf8 $valid "- **A.** first`n- **B.** second`n- **C.** third`n- **D.** fourth"
Set-Content -Encoding utf8 $invalid "A. first | B. second | C. third | D. fourth"
python scripts/check_agent_contract.py $valid
python scripts/check_agent_contract.py $invalid
```

Expected: the valid fixture exits `0`; the invalid fixture exits `1` and prints `horizontal multiple-choice options`.

- [ ] **Step 2: Run the full regression suite and static checks**

Run:

```powershell
python -m unittest discover -s tests -v
python scripts/check_agent_contract.py
Get-Content -Raw .mcp.json | ConvertFrom-Json | Out-Null
git diff --check
git status --short
```

Expected: all tests pass, the checker prints no violation without paths, JSON parses, whitespace check is clean, and only intended changes are present before commit.

- [ ] **Step 3: Inspect changed note scope**

Run:

```powershell
git diff --name-only HEAD -- docs
```

Expected: only `docs/superpowers/` design and plan documents are changed; no historical study note is rewritten.

- [ ] **Step 4: Commit only a verification correction, if one was required**

Do not create a no-op commit. If any Step 1 or Step 2 command required a correction, stage only the corrected path or paths and commit with a focused `test:` or `fix:` message. Otherwise, preserve the commits from Tasks 1-5 unchanged.
