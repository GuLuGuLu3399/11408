#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
weekly-context-builder.py
=========================

收集本 Vault 最近 N 天的 git 活动并打印成 Markdown，供复习周报 Agent
（例如 LobeHub）直接读取终端输出后撰写
`docs/复习周报/YYYY-Wxx-复习周报.md`。

设计原则（stdout-first）
------------------------
- 默认输出到终端（stdout），不落盘。LobeHub Agent 跑这条命令、读 stdout 即可。
- 只有显式加 `--write` 时，才同时写一份原始上下文到
  `docs/复习周报/_weekly_raw_context.md`，用于排查“Agent 为什么这样总结”。
  该文件已在 `.gitignore` 中忽略，也不会作为正式周报提交。

这是一个工具脚本，不是 Tolaria 笔记。它只读取 git 历史，不触碰 RAG 索引
（笔记的 ingest/delete 仍由 commit hook 负责）。

用法
----
    # 默认：打印最近 7 天到终端（LobeHub 主路径）
    python scripts/weekly-context-builder.py

    # 同时留档一份原始上下文，方便排查
    python scripts/weekly-context-builder.py --write

    # 自定义时间窗口与输出长度
    python scripts/weekly-context-builder.py --days 14 --max-chars 50000

只依赖 Python 标准库与本地 git，无第三方包。
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import subprocess
import sys
from pathlib import Path

# Windows 控制台默认编码可能是 gbk，强制 stdout 为 utf-8，避免中文提交信息
# 被 LobeHub 读取时出现 UnicodeEncodeError / 乱码。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except (AttributeError, ValueError):
    pass  # 老版本 Python 或已被重定向时忽略

# 提交记录分隔符：用不可见控制字符，避免与提交信息中的可见字符冲突。
_COMMIT_MARK = "__COMMIT__"
_FIELD_SEP = "\x1f"  # ASCII Unit Separator


# --------------------------------------------------------------------------- #
# git 调用
# --------------------------------------------------------------------------- #
def run_git(args, cwd):
    """运行一条 git 命令，返回 (stdout_text, rc, stderr_text)。"""
    # 强制 git 以 utf-8 输出，且不转义中文路径。
    cmd = [
        "git",
        "-c", "core.quotepath=false",
        "-c", "i18n.logOutputEncoding=utf-8",
    ] + args
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True)
    out = proc.stdout.decode("utf-8", "replace")
    err = proc.stderr.decode("utf-8", "replace")
    return out, proc.returncode, err


def find_repo_root(start: Path) -> Path | None:
    """从 start 向上定位 git 仓库根目录；找不到返回 None。"""
    out, rc, _ = run_git(["rev-parse", "--show-toplevel"], cwd=start)
    if rc != 0:
        return None
    root = out.strip()
    return Path(root) if root else None


def get_branch(root: Path) -> str:
    out, rc, _ = run_git(["branch", "--show-current"], cwd=root)
    name = out.strip()
    if rc == 0 and name:
        return name
    # 处于 detached HEAD 时给出短 sha。
    out2, _, _ = run_git(["rev-parse", "--short", "HEAD"], cwd=root)
    return f"(detached {out2.strip()})"


# --------------------------------------------------------------------------- #
# 解析 git log
# --------------------------------------------------------------------------- #
def normalize_rename_path(path: str) -> str:
    """把 git 的 rename 路径规整为新路径，覆盖两种记法：

    - 花括号：`{408 => docs/408}/进程与线程.md` -> `docs/408/进程与线程.md`
    - 纯箭头：`a/old.md => b/new.md`          -> `b/new.md`
    非 rename 路径原样返回。
    """
    # 花括号形式：{old => new}
    if "{" in path and "}" in path and "=>" in path:
        pre, rest = path.split("{", 1)
        inner, post = rest.split("}", 1)
        if "=>" in inner:
            path = pre + inner.split("=>", 1)[1].strip() + post
    # 纯箭头形式：old => new（跨目录改名时 git 用这种记法）
    if " => " in path:
        path = path.rsplit(" => ", 1)[1]
    return path


def collect_activity(root: Path, days: int):
    """
    收集最近 days 天的活动。

    返回 dict：
      commits : [(hash, iso_date, subject), ...]   从新到旧
      files   : { path: {added, deleted, ops(set), commits } }
    """
    since = f"{days} days ago"
    fmt = _COMMIT_MARK + "%h" + _FIELD_SEP + "%aI" + _FIELD_SEP + "%s"

    # 一次拿到 提交头 + 每个提交的 numstat（新增/删除行数）
    out, rc, err = run_git(
        ["log", f"--since={since}", "--no-merges", f"--pretty=format:{fmt}", "--numstat"],
        cwd=root,
    )
    if rc != 0:
        print(f"[警告] git log 失败：{err.strip() or '未知错误'}", file=sys.stderr)

    commits: list[tuple[str, str, str]] = []
    files: dict[str, dict] = collections.defaultdict(
        lambda: {"added": 0, "deleted": 0, "ops": set(), "commits": 0}
    )

    current_commit: tuple[str, str, str] | None = None
    for line in out.splitlines():
        if not line:
            continue
        if line.startswith(_COMMIT_MARK):
            rest = line[len(_COMMIT_MARK):]
            parts = rest.split(_FIELD_SEP, 2)
            if len(parts) == 3:
                current_commit = (parts[0], parts[1], parts[2])
                commits.append(current_commit)
            continue
        # numstat 行：<added>\t<deleted>\t[<old>\t]<path>
        cols = line.split("\t")
        if len(cols) < 3:
            continue
        added_s, deleted_s = cols[0], cols[1]
        path = normalize_rename_path(cols[-1])
        try:
            added = int(added_s) if added_s != "-" else 0
            deleted = int(deleted_s) if deleted_s != "-" else 0
        except ValueError:
            continue  # 二进制或异常行，跳过
        f = files[path]
        f["added"] += added
        f["deleted"] += deleted
        f["commits"] += 1

    # 另取 name-status，补全每个文件的操作类型（A/M/D/R/C...）
    ns_out, _, _ = run_git(
        ["log", f"--since={since}", "--no-merges",
         "--pretty=format:", "--name-status"],
        cwd=root,
    )
    for line in ns_out.splitlines():
        if not line:
            continue
        cols = line.split("\t")
        if not cols or not cols[0]:
            continue
        op = cols[0][0].upper()  # A / M / D / R / C ...
        path = normalize_rename_path(cols[-1])
        if path in files:
            files[path]["ops"].add(op)

    return {"commits": commits, "files": files}


# --------------------------------------------------------------------------- #
# 分类与展示
# --------------------------------------------------------------------------- #
def categorize(path: str) -> str:
    """把文件路径归入一个分类，用于分组展示。

    容忍近期的目录重构：既识别 `docs/<目录>/...` 新布局，也识别重构前
    的 `<目录>/...` 旧布局（408 / 数学 / 错题日记 / 模块化整合 等）。
    """
    p = normalize_rename_path(path).replace("\\", "/")
    first = p.split("/", 1)[0]
    if first == "views":
        return "views（视图）"
    if first.startswith("."):
        return "配置与文档"
    if p in ("AGENTS.md", "CLAUDE.md", "GEMINI.md", "README.md", ".gitignore", ".mcp.json"):
        return "配置与文档"
    if first == "docs":
        rest = p[len("docs/"):].split("/", 1)
        return rest[0] if rest and rest[0] else "docs/"
    if "/" in p:
        return first  # 顶层学习目录：408 / 数学 / 错题日记 / 模块化整合 ...
    return "其他"


_OP_LABEL = {
    "A": "新增",
    "M": "修改",
    "D": "删除",
    "R": "重命名",
    "C": "复制",
}


def op_label(ops: set[str]) -> str:
    if not ops:
        return "改动"
    # 固定展示顺序，便于阅读
    ordered = [label for op in ("A", "M", "D", "R", "C") if op in ops for label in [_OP_LABEL[op]]]
    return "/".join(ordered) if ordered else "改动"


def change_label(info: dict) -> str:
    label = op_label(info["ops"])
    if "R" in info["ops"] and has_content_delta(info) and "M" not in info["ops"]:
        return f"{label}/内容改动"
    return label


def is_note(path: str) -> bool:
    return path.lower().endswith(".md")


def is_current_docs_note(root: Path, path: str) -> bool:
    """Return true for current, user-authored notes under docs/."""
    normalized = normalize_rename_path(path).replace("\\", "/")
    if not normalized.startswith("docs/") or not is_note(normalized):
        return False
    return (root / normalized).exists()


def has_content_delta(info: dict) -> bool:
    return bool(info["added"] or info["deleted"])


def split_note_files(root: Path, files: dict[str, dict]) -> tuple[dict[str, dict], dict[str, dict]]:
    notes = {p: v for p, v in files.items() if is_note(p)}
    current_notes = {
        p: v
        for p, v in notes.items()
        if is_current_docs_note(root, p) and has_content_delta(v)
    }
    noisy_notes = {p: v for p, v in notes.items() if p not in current_notes}
    return current_notes, noisy_notes


def fmt_date(iso: str) -> str:
    """把 git 的 %aI（ISO-8601）转成 YYYY-MM-DD。"""
    try:
        return dt.datetime.fromisoformat(iso).strftime("%Y-%m-%d")
    except ValueError:
        return iso


def build_markdown(root: Path, branch: str, days: int, activity: dict) -> str:
    commits = activity["commits"]
    files: dict[str, dict] = activity["files"]

    today = dt.date.today()
    start_date = today - dt.timedelta(days=days)
    n_commits = len(commits)
    note_files, noisy_note_files = split_note_files(root, files)
    n_notes = len(note_files)
    n_files = len(files)
    n_noisy_notes = len(noisy_note_files)

    active_days = len({fmt_date(c[1]) for c in commits})

    # 按当前 docs/ 笔记统计。重命名提交可能没有 M 标记，但有行数变化，
    # 对周报来说仍应视为内容被触碰过。
    n_added = sum(1 for v in note_files.values() if "A" in v["ops"])
    n_deleted = sum(1 for v in note_files.values() if "D" in v["ops"])
    n_content_changed = sum(1 for v in note_files.values() if v["added"] or v["deleted"])

    lines: list[str] = []
    push = lines.append

    push(f"# Vault 周报上下文（{start_date} ~ {today}）")
    push("")
    push("> 本文件由 `scripts/weekly-context-builder.py` 自动生成，供复习周报")
    push(f"> Agent 读取后撰写 `docs/复习周报/{{YYYY-Wxx}}-复习周报.md`。")
    push(f"> 范围：最近 **{days} 天** 的 git 提交活动（不含 merge 提交）。")
    push("")

    # ---- 1. 概览 ----
    push("## 1. 概览")
    push("")
    push(f"- 仓库：`{root}`（分支 `{branch}`）")
    push(f"- 时间范围：{start_date} → {today}（共 {days} 天）")
    push(f"- 提交数：**{n_commits}**")
    push(f"- 改动文件数：{n_files}（当前 `docs/` 笔记：**{n_notes}**）")
    push(f"- 活跃天数：{active_days}")
    push(f"- 当前笔记内容改动：{n_content_changed} 个（新增 {n_added} / 删除 {n_deleted}）")
    if n_noisy_notes:
        push(f"- 结构迁移/非当前笔记改动：{n_noisy_notes} 个文件已被降噪，不计入学习推进主体")
    push("")

    # ---- 2. 提交时间线 ----
    push("## 2. 提交时间线")
    push("")
    if not commits:
        push("_(该时间段内没有提交。)_")
    else:
        for h, iso, subject in commits:
            push(f"- `{h}` {fmt_date(iso)} — {subject}")
    push("")

    # ---- 3. 改动笔记（按目录分组） ----
    push("## 3. 改动笔记（按目录）")
    push("")
    if not note_files:
        push("_(该时间段内没有笔记改动。)_")
    else:
        groups: dict[str, list[str]] = collections.defaultdict(list)
        for path in sorted(note_files.keys()):
            groups[categorize(path)].append(path)
        for cat in sorted(groups.keys()):
            paths = groups[cat]
            push(f"### {cat}（{len(paths)} 个文件）")
            push("")
            for path in paths:
                v = files[path]
                push(f"- `{path}` · +{v['added']} / -{v['deleted']} · {change_label(v)}")
            push("")

    # ---- 4. 改动最频繁的笔记 ----
    push("## 4. 改动最频繁的笔记（Top 10）")
    push("")
    ranked = sorted(
        note_files.items(),
        key=lambda kv: (kv[1]["commits"], kv[1]["added"] + kv[1]["deleted"]),
        reverse=True,
    )[:10]
    if not ranked:
        push("_(无。)_")
    else:
        for i, (path, v) in enumerate(ranked, 1):
            push(f"{i}. `{path}` — {v['commits']} 次提交 · +{v['added']} / -{v['deleted']}")
    push("")

    # ---- 5. 结构迁移/非当前笔记改动 ----
    push("## 5. 结构迁移/非当前笔记改动")
    push("")
    if not noisy_note_files:
        push("_(无。)_")
    else:
        push("这些文件多为历史路径、测试笔记、删除项或仓库结构调整；周报 Agent 只应把它们作为背景，不应当作新的复习推进。")
        push("")
        noise_groups: dict[str, int] = collections.defaultdict(int)
        for path in noisy_note_files:
            noise_groups[categorize(path)] += 1
        for cat in sorted(noise_groups):
            push(f"- {cat}: {noise_groups[cat]} 个文件被降噪")
    push("")

    # ---- 6. 配置与其他改动 ----
    non_notes = sorted(p for p in files if not is_note(p))
    push("## 6. 配置与其他改动")
    push("")
    if not non_notes:
        push("_(无。)_")
    else:
        for path in non_notes:
            v = files[path]
            push(f"- `{path}` · +{v['added']} / -{v['deleted']} · {change_label(v)}")
    push("")

    push("---")
    push("")
    push("生成命令：`python scripts/weekly-context-builder.py"
         + (f" --days {days}" if days != 7 else "")
         + "`")

    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# 入口
# --------------------------------------------------------------------------- #
def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="收集 Vault 最近 N 天的 git 活动，打印为 Markdown 供周报 Agent 读取。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="默认仅打印到终端；加 --write 才同时落盘到 docs/复习周报/_weekly_raw_context.md",
    )
    p.add_argument("--days", type=int, default=7,
                   help="回溯天数（默认 7）")
    p.add_argument("--max-chars", type=int, default=30000,
                   help="输出字符上限，超出尾部截断（默认 30000）")
    p.add_argument("--write", action="store_true",
                   help="同时写入 docs/复习周报/_weekly_raw_context.md（默认不写）")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.days <= 0:
        print("--days 必须为正整数", file=sys.stderr)
        return 2

    # 基于脚本所在目录定位仓库，这样从任意 cwd 调用都能找到 vault。
    repo_root = find_repo_root(Path(__file__).resolve().parent)
    if repo_root is None:
        print("[错误] 未找到 git 仓库。请确认脚本位于 11408-vault 内。", file=sys.stderr)
        return 1

    branch = get_branch(repo_root)
    activity = collect_activity(repo_root, args.days)
    markdown = build_markdown(repo_root, branch, args.days, activity)

    # 截断保护：概览与提交时间线在前，文件列表在后，故截断尾部不影响核心信息。
    total = len(markdown)
    if total > args.max_chars:
        markdown = (
            markdown[:args.max_chars]
            + "\n\n…(已截断：共 {0} 字符，仅显示前 {1}；用 --max-chars 调整)"
            .format(total, args.max_chars)
        )

    # stdout —— LobeHub Agent 读取的主路径
    print(markdown)

    if args.write:
        out_path = repo_root / "docs" / "复习周报" / "_weekly_raw_context.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(markdown + "\n", encoding="utf-8")
        print(f"\n[已留档] {out_path}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
