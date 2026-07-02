#!/usr/bin/env python3
"""
11408 Vault C 档清洗脚本（数据卫生，配合 lint_vault.py 使用）。

作用：对所有"文件名 ≠ slug"的笔记，把被引用处（wikilink + frontmatter）
统一改成 slug 形式，并生成 git mv 命令清单（大小写敏感的 case-only 自动两段式）。

- 只改 docs/ 下 .md 的文本内容，不动文件名、不碰 git。
- 幂等：清洗完再跑，零改动。
- slugify 与 site/src/lib/markdown/slugify.mjs（SSOT）/ lint_vault.py 完全一致。

流程：python scripts/wash_vault.py  →  bash scripts/_rename.sh  →  python scripts/lint_vault.py
"""

import os
import re
import sys

VAULT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "docs"))
RENAME_SH = os.path.join(os.path.dirname(__file__), "_rename.sh")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def slugify_segment(value: str) -> str:
    """与 slugify.mjs / lint_vault.py 同源。"""
    s = value.strip().lower()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"[^a-z0-9一-龥-]", "", s)
    s = re.sub(r"-+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s


def main() -> int:
    if not os.path.isdir(VAULT_DIR):
        print(f"❌ 找不到 vault: {VAULT_DIR}", file=sys.stderr)
        return 1

    repo_root = os.path.dirname(VAULT_DIR)

    # 1. 重命名映射：stem != slug 的文件
    rename_map: dict[str, str] = {}
    file_renames: list[tuple[str, str, str]] = []  # (rel_path_with_md, old_stem, new_stem)
    for root, _, names in os.walk(VAULT_DIR):
        for name in names:
            if not name.endswith(".md"):
                continue
            old_stem = name[:-3]
            new_stem = slugify_segment(old_stem)
            if new_stem != old_stem:
                rename_map[old_stem] = new_stem
                rel = os.path.relpath(os.path.join(root, name), repo_root).replace("\\", "/")
                file_renames.append((rel, old_stem, new_stem))

    if not rename_map:
        print("✅ 没有需要清洗的文件名（所有 stem 已等于 slug）。")
        # 清掉可能残留的 _rename.sh
        if os.path.exists(RENAME_SH):
            os.remove(RENAME_SH)
        return 0

    print(f"📦 重命名映射（{len(rename_map)} 项）：")
    for old, new in sorted(rename_map.items()):
        print(f"    «{old}»  →  «{new}»")
    print()

    # 2. 重写所有文档引用：[[old]] / [[old|alias]] / [[old#anchor]] / frontmatter "[[old]]"
    # lookahead (?=[\]|#]) 保证整词匹配，不会把 [[TCP 三次握手]] 误当 [[TCP 拥塞控制]] 的前缀。
    total_edits = 0
    edited_files: list[tuple[str, int]] = []
    for root, _, names in os.walk(VAULT_DIR):
        for name in names:
            if not name.endswith(".md"):
                continue
            path = os.path.join(root, name)
            with open(path, encoding="utf-8") as fh:
                content = fh.read()
            file_edits = 0
            for old, new in rename_map.items():
                pattern = re.compile(r"\[\[" + re.escape(old) + r"(?=[\]|#])")
                content, n = pattern.subn("[[" + new, content)
                file_edits += n
            if file_edits:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(content)
                edited_files.append((os.path.relpath(path, repo_root), file_edits))
                total_edits += file_edits

    print(f"✏️  引用改写：共 {total_edits} 处，涉及 {len(edited_files)} 个文件")
    for rel, n in sorted(edited_files):
        print(f"    {rel}: {n} 处")
    print()

    # 3. 生成 git mv 命令（case-only 两段式，绕过 Windows 大小写盲区）
    lines = ["#!/usr/bin/env bash", "set -euo pipefail", 'cd "$(git rev-parse --show-toplevel)"', ""]
    print("🔧 生成 git mv 命令 → scripts/_rename.sh")
    for rel, old, new in sorted(file_renames):
        new_rel = os.path.join(os.path.dirname(rel), new + ".md").replace("\\", "/")
        if old.lower() == new.lower():
            # case-only：两段式（Windows NTFS 大小写不敏感，直接改 git 不记录）
            tmp_rel = os.path.join(os.path.dirname(rel), f"__tmp_{new}.md").replace("\\", "/")
            lines.append(f'git mv -f "{rel}" "{tmp_rel}"')
            lines.append(f'git mv -f "{tmp_rel}" "{new_rel}"')
            print(f'    [两段式] {rel}  →  {new_rel}')
        else:
            lines.append(f'git mv -f "{rel}" "{new_rel}"')
            print(f'    [单步]   {rel}  →  {new_rel}')
    with open(RENAME_SH, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print()
    print("▶️  下一步：bash scripts/_rename.sh  然后  python scripts/lint_vault.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
