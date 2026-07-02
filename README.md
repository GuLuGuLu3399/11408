# 11408 Vault

一个围绕 11408 考研复习构建的 Tolaria 笔记库与静态发布站点。

这个仓库的核心目标不是做通用知识库，而是把数学一、408、英语一、政治、错题复盘和每周复盘沉淀成可检索、可发布、可被 Agent 使用的学习系统。

## 内容结构

```text
11408-vault/
├─ docs/                  # Tolaria Markdown 笔记
│  ├─ 408/                # 408 计算机统考笔记
│  ├─ 数学/               # 数学一笔记
│  ├─ 错题日记/           # 错题复盘
│  ├─ 模块化整合/         # 跨章节、跨学科整合
│  ├─ 每日心态/           # 状态记录
│  └─ 复习周报/           # 正式周报
├─ views/                 # Tolaria 保存视图
├─ scripts/               # 本地维护脚本
├─ site/                  # Astro 静态站点
├─ tests/                 # 脚本测试
└─ .claude/               # 本地 Agent prompt / skills（不建议公开依赖）
```

## Tolaria 笔记约定

- 笔记是 Markdown 文件，第一行 H1 作为 Tolaria 标题。
- 用 YAML frontmatter 存储 `type`、`status`、`related_to` 等属性。
- 用 `[[wikilink]]` 建立笔记关系。
- 文件夹用于阅读和维护便利，但不作为唯一语义来源。
- `views/*.yml` 是 Tolaria 保存视图。
- `assets/`、`attachments/` 等资源目录只作为附件来源，不当作笔记本体。

更完整的 Agent 写作约定见 `AGENTS.md`。

## 本地周报

周报上下文由 Git 活动和笔记变更生成，默认只打印到终端：

```powershell
python scripts\weekly-context-builder.py --max-chars 50000
```

常用参数：

```powershell
python scripts\weekly-context-builder.py --days 7 --max-chars 100000
python scripts\weekly-context-builder.py --write
```

说明：

- `_weekly_raw_context.md` 是临时喂料文件，默认不落盘，落盘后也不应作为正式复习资料。
- 正式周报放在 `docs/复习周报/YYYY-Wxx-复习周报.md`。
- 周报判断应以实际笔记内容改动为主，commit message 只作辅助证据。

## RAG 与大资料

本仓库只保存个人笔记、错题、视图、站点和项目级配置。

大资料、Derived 切块、向量库、模型缓存等本地 RAG 资产放在相邻工作区：

```text
../11408-kb/
```

日常复习问答的推荐入口是项目级 `study-rag.study_query`。它负责笔记/错题优先、大资料补充、去重和壳块降噪。不要把大资料 Derived 文件直接当作 Tolaria 笔记扫描。

## Agent 配置

本仓库包含一套本地 Agent 配置，用于 11408 复习工作流：

- 复习助手：面向知识点讲解、刷题、错题复盘、闪卡生成。
- 周报助手：面向每周 Git/笔记变更复盘。
- 督导助手：面向学习节奏、偏科风险和下一步任务拆解。

主要配置位于：

```text
.claude/tolaria-11408-prompt.md
.claude/skills/
```

这些配置是本地工作流的一部分，不应写入全局 Agent 配置。

## 静态站点

站点位于 `site/`，使用 Astro 构建，并从上层 `docs/` 读取笔记内容。

```powershell
cd site
pnpm install
pnpm dev
pnpm build
pnpm preview
```

当前部署目标是 Vercel，生产域名：

```text
https://www.hyh0209.cn
```

站点已接入：

- Vercel Web Analytics
- Vercel Speed Insights
- RSS / Sitemap
- KaTeX 数学公式
- Mermaid 图表
- Wikilink 渲染

## Git 与隐私边界

这个仓库适合提交的内容：

- `docs/` 正式笔记与正式周报
- `views/` Tolaria 视图
- `scripts/` 可复用维护脚本
- `site/` 静态站点源码
- `tests/` 脚本测试

不建议提交或公开依赖的内容：

- `.claude/` 本地 Agent 配置
- `.mcp.json` MCP 本地连接配置
- `.omc/`、`.rag-lancedb/`、`model-cache/`
- `_weekly_raw_context.md`
- 机器相关 IDE / 缓存 / 临时文件

提交前建议检查：

```powershell
git status --short
git diff --stat
```

## 维护原则

- 复习内容优先：笔记和错题是第一资产。
- RAG 辅助但不替代笔记：检索命中用于定位和补充，最终仍应沉淀为可复习的 Markdown。
- 周报只复盘证据：没有笔记或错题变化的科目，不强行编造推进。
- 站点服务阅读：移动端、公式、表格、Mermaid 的可读性优先于装饰性设计。
- 本地配置不污染全局：Agent prompt、skills、MCP 都保持项目级隔离。
