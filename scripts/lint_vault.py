#!/usr/bin/env python3
"""
11408 Vault 体检扫描器（A 档护城河）。

只读、只报告，绝不修改任何文件。
检测两类隐患，作为未来 C 档数据清洗的指南针：

  1. 命名隐患：文件名含大写字母或空格 → slug 后与原文件名不一致，
     在 Windows（大小写不敏感）↔ Linux（严格）部署间会引发断链。
     （这正是刚修过的"小何的OS / CPU 与流水线"那一类问题。）
  2. 双链漂移：[[X]] 的大小写与目标文件实际文件名不一致。

slugify 规则与 site/src/lib/markdown/slugify.mjs（SSOT）保持一致。
运行：python scripts/lint_vault.py
"""

import os
import re
import sys

# 脚本位于 <repo>/scripts/lint_vault.py，笔记在 <repo>/docs
VAULT_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "docs"))

# [[target]]、[[target|alias]]、[[target#anchor]]，取 target 部分
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:\|[^\]]*)?(?:#[^\]]*)?\]\]")


# Windows 控制台默认 GBK，强制 stdout 用 UTF-8，避免 emoji/中文输出时编码崩溃
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def slugify_segment(value: str) -> str:
    """与 slugify.mjs 的 slugifySegment 完全一致——SSOT 的 Python 镜像。"""
    s = value.strip().lower()
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"[^a-z0-9一-龥-]", "", s)
    s = re.sub(r"-+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s


def main() -> int:
    if not os.path.isdir(VAULT_DIR):
        print(f"❌ 找不到 vault 目录: {VAULT_DIR}", file=sys.stderr)
        return 1

    repo_root = os.path.dirname(VAULT_DIR)

    # 1. 全库文件名登记（小写 stem → 实际 stem），用于双链漂移检测
    registry: dict[str, str] = {}
    files: list[tuple[str, str]] = []  # (abspath, stem)
    for root, _, names in os.walk(VAULT_DIR):
        for name in names:
            if not name.endswith(".md"):
                continue
            stem = name[:-3]
            files.append((os.path.join(root, name), stem))
            registry.setdefault(stem.lower(), stem)

    naming_issues: list[tuple[str, str, str]] = []   # (rel, stem, slug)
    drift_issues: list[tuple[str, str, str]] = []    # (rel, link_target, actual_stem)

    # 2. 命名隐患：slug(stem) != stem 即存在跨平台断链风险
    for abspath, stem in files:
        slug = slugify_segment(stem)
        if slug != stem:
            naming_issues.append((os.path.relpath(abspath, repo_root), stem, slug))

    # 3. 双链大小写漂移：链接 target 与实际文件名大小写不一致
    for abspath, _ in files:
        with open(abspath, encoding="utf-8") as fh:
            content = fh.read()
        rel = os.path.relpath(abspath, repo_root)
        for m in WIKILINK_RE.finditer(content):
            target = m.group(1).strip()
            actual = registry.get(target.lower())
            if actual is not None and actual != target:
                drift_issues.append((rel, target, actual))

    # 报告
    print("🔍 11408 Vault 体检报告\n")
    print(f"扫描笔记数：{len(files)}")
    print(f"命名隐患：{len(naming_issues)} 处")
    print(f"双链漂移：{len(drift_issues)} 处\n")

    if naming_issues:
        print("── 命名隐患（文件名 ≠ slug，C 档清洗清单）──")
        for rel, stem, slug in sorted(naming_issues):
            print(f"  ⚠️  {rel}")
            print(f"       文件名 «{stem}»  →  slug «{slug}»")
        print()

    if drift_issues:
        print("── 双链大小写漂移 ──")
        for rel, target, actual in sorted(drift_issues):
            print(f"  🔗 {rel}: [[{target}]]  →  实际文件名 [[{actual}]]")
        print()

    print("💡 本脚本只报告、不修改。命名隐患清单 = Day 1 之后 C 档清洗的工作量。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
