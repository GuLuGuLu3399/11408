# 11408 Vault Agent Contract Design

## Status

Approved design, pending implementation.

## Goal

Replace the legacy Node/WebGPU RAG instructions with one read-only Python RAG contract, add the memory MCP, and make the Vault's guidance and skills concise, non-duplicated, and enforceable for future note edits.

## Scope

- Modify Vault-local MCP configuration, guidance, and skills only.
- Preserve the existing note types: `note`, `mistake`, `flashcard`, `progress`, and `summary`.
- Apply the new note format to newly created or edited notes. Do not bulk-rewrite existing notes in this change.
- Add a lightweight check for legacy RAG tool names and horizontal multiple-choice options.

## Decisions

### One RAG Service

Remove `local-rag` and replace the legacy Node launcher with one `study-rag` stdio server:

```text
D:\dev\study-rag\python\.venv\Scripts\python.exe -m study_rag.mcp_server
```

The service is read-only. Content questions use `study-rag.rag_query`; health and active-index questions use `study-rag.rag_inspect`. Index writes and rebuilds remain local CLI operations explicitly requested by the user.

Add the separate `memory` stdio server using `cmd /c npx -y @modelcontextprotocol/server-memory`. Memory stores durable user preferences and facts only. It is never evidence and cannot replace RAG retrieval.

### Documentation Ownership

Each rule has one owner:

| File or directory | Responsibility |
|---|---|
| `AGENTS.md` | Tolaria rules, note data contract, canonical note types, frontmatter conventions |
| `CLAUDE.md` | Project entry point and links to the local authority files and skills |
| `.claude/tolaria-11408-prompt.md` | Assistant role, intent routing, source priority, MCP boundaries, response integrity |
| `11408-study-coach` | Thin intent router to specialised skills |
| `11408-rag-query` | RAG tool contract, filters, strict misses, retrieval retry policy |
| `11408-mistake-review` | Mistake-review workflow and mistake-note template |
| `11408-flashcard` | Flashcard workflow and flashcard template |
| `11408-markdown-rendering` | Mobile-readable Markdown and formatting rules |
| `.claude/references/` | Long examples or field references required by multiple skills |

The main prompt must not repeat skill templates or low-level Markdown rules. Skills must not redefine MCP availability or source priority owned by the main prompt.

### Note Data Contract

All study notes retain one existing `type` value:

| Type | Purpose | Required body sections for new notes |
|---|---|---|
| `note` | Atomic knowledge note | conclusion, conditions or steps, traps when relevant |
| `mistake` | Wrong-problem record | problem, options when applicable, my answer, correct answer, error cause, recognition signal |
| `flashcard` | Active-recall card | question, answer, common mistake, source |
| `progress` | Daily or weekly study state | completed work, blocker, next action |
| `summary` | Cross-topic integration | scope, key connections, unresolved gaps |

New or edited notes use the existing frontmatter key style and first-H1 title. When the metadata applies, use `subject`, `status`, `topics`, `related_to`, and `source`; do not add empty fields merely to satisfy a template.

### Multiple-Choice Format

Multiple-choice options must be vertically readable and independently searchable:

```markdown
## Options

- **A.** First option.
- **B.** Second option.
- **C.** Third option.
- **D.** Fourth option.
```

For analysis, use one vertical item per option or a compact three-column table:

```markdown
| Option | Judgment | Reason |
|---|---|---|
| A | Wrong | ... |
| B | Correct | ... |
```

Forbidden forms include option chains on one line, such as `A. ... | B. ... | C. ... | D. ...`, and putting the question, all choices, and all analysis in one wide table cell.

### Validation

A Vault-local checker will fail when project guidance still references `local-rag`, `study_query`, `query_documents`, `read_chunk_neighbors`, `ingest_file`, or `delete_file`; it will also flag newly edited Markdown that contains a same-line A/B/C/D option chain. Validation is advisory for existing historical notes until those files are edited.

## Error Handling

- A strict RAG filter with no hits is a valid miss. Do not silently broaden it.
- An unhealthy active index is a tool error. Run `rag_inspect`; do not invent an answer from an empty result.
- After an appropriate retry has no evidence, state that the current RAG did not hit and clearly label any general-knowledge supplement.
- Never write, ingest, delete, migrate, or rebuild through MCP.

## Verification

1. Parse `.mcp.json` and verify exactly `study-rag`, `memory`, and `tolaria` are enabled.
2. Verify the Python MCP command and all `STUDY_RAG_*` paths.
3. Exercise the guidance checker with one valid vertical-choice fixture and one rejected horizontal-choice fixture.
4. Search project guidance for legacy RAG tools and confirm none remain.
5. Inspect the final diff to ensure no note content was mass-migrated.

## Non-Goals

- Rebuild the RAG index or change retrieval behavior.
- Bulk-normalize existing notes.
- Change Tolaria installation or global Codex/Claude configuration.
