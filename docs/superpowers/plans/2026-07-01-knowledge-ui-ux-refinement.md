# Knowledge UI/UX Refinement Plan

> **For agentic workers:** Implement task-by-task. Priorities marked P0/P1/P2. Run `pnpm check` + `pnpm build` from `site/` at each verification gate. Work in `11408-vault/`; site lives in `site/`.

> 目标：在保持 Instrument Panel 极简仪表盘质感的前提下，降低首页认知负担，重构 Topics 的两级知识拓扑，并清理 Header 导航冗余。

## 核心判断

当前站点的问题不是视觉不够“漂亮”，而是信息密度没有分层：

- 首页承担了“全量数据库”的职责，导致认知超载。
- Topics 把 subject/topic 扁平并列，缺少档案柜式秩序。
- Header 同时出现 Logo 首页入口与 Notes 导航，RSS 又占据高频导航位，信噪比偏低。

本计划只做 IA 与 UI 密度重构，不引入复杂组件系统。

---

## 设计原则

1. **首页只展示系统心跳，不展示全库**
   - 首页最多展示最新 15 篇。
   - 底部提供 `View all notes ->`。
   - 全量浏览移到 `/notes/`。

2. **Topics 使用两级拓扑**
   - 一级是知识域 (domain)，例如：`408 核心专业课` / `考研数学` / `错题复盘` / `复习节奏` / `心态记录`
   - 二级是 subject，例如：数据结构 / 操作系统 / 计算机组成原理 / 计算机网络 / 高等数学 / 线性代数 / 概率统计

3. **Header 只保留高频导航**
   - Logo 回首页。
   - 删除导航里的 `Notes`。
   - 保留 `Topics`。
   - RSS 移到 Footer（不在 Header 高频区）。

4. **保持 Instrument Panel**
   - hairline 分隔
   - mono metadata
   - editor hover
   - 无卡片、无 chip、无大背景块
   - 原生 HTML + UnoCSS，不新增样式组件

---

## 路由结构目标

```txt
/                         首页：最新 15 篇 + Topics 入口
/notes/                   全量笔记索引（紧凑 archive，暂不 paginate）
/notes/[...slug]/         单篇笔记详情（多段 id，已是 rest 路由）
/topics/                  两级知识拓扑目录
/topics/[topic]/          subject 级详情（保留现有路由，不要打坏链接）
/tags/[tag]/              标签聚合页
/rss.xml                  RSS feed，入口放 Footer
```

> 实现保持轻量：可以不做 `/topics/[domain]/[subject]/`，只做 `/topics/` 两级呈现 + 现有 `/topics/[topic]`。`/topics/[domain]` 属于 P2。

---

## 首页重构

**问题**：长列表让用户一进入就面对全量内容，缺少仪表盘的概览感。

**目标** —— 首页只回答三个问题：最近有什么更新？这个 Vault 大致有哪些知识域？我要看更多内容从哪里进入？

**实现** (`src/pages/index.astro`)：

```ts
const recentPosts = posts.slice(0, 15);
```

页面结构：

```txt
Vault Notes · 2026

最新笔记

[date]  note title
[date]  note title
...

View all notes ->

Knowledge Map
408 核心专业课
考研数学
错题复盘
复习节奏
```

**视觉要求**：最新笔记列表使用 editor hover；`View all notes ->` 使用 mono 小字；不分页首页；不在首页展示 tags（避免二次噪音）。

---

## Notes Archive

新增/完善 `src/pages/notes/index.astro` —— 全量笔记索引。

**策略**：第一阶段不用 Astro paginate，先做紧凑 archive（按 `pubDate / updated_at` 倒序）。如果未来超过 120 篇，再加 pagination（反过度工程）。

**要求**：展示所有 public notes；允许日期；列表密度比首页更高；底部不需要重复 CTA。

---

## Topics 两级拓扑

**问题**：`408 - 数据结构`、`数学 - 高等数学` 等被拍平后，页面像标签云，不像知识库目录。

**目标结构**：

```txt
408 核心专业课
  数据结构
    - 栈与队列
    - 树
    - 图
  操作系统
    - 进程与线程
    - 内存管理

考研数学
  高等数学
  线性代数
  概率统计

错题复盘
  数据结构
  组成原理
  高等数学
```

**数据映射** —— 新增 taxonomy helper（不要在页面里硬写复杂 reduce）：

```ts
type KnowledgeDomain = {
  id: string;
  name: string;
  order: number;
  subjects: KnowledgeSubject[];
};

type KnowledgeSubject = {
  id: string;
  name: string;
  notes: NoteEntry[];
};
```

映射规则（按 `type` → domain）：

```txt
type: 408笔记     -> 408 核心专业课
type: 考研数学    -> 考研数学
type: 错题日记    -> 错题复盘
type: 周报        -> 复习节奏
type: 心态日记    -> 心态记录
type: 综合专题    -> 综合专题
```

`subject` 作为二级分类。Talaria views 仍作为 curated topic 输入，但渲染时归入对应 domain，而不是全部平铺。

---

## Header 导航重构

**问题**：Logo 已是首页入口，再放 `Notes` 是重复信号；RSS 低频，不应占高频触控区。

**推荐 Header**：

```txt
11408 Vault                         Topics
```

（语义清晰，选 `Topics`。）

**RSS 处理** —— 移到 Footer：

```txt
© 2026 · 11408 Vault · RSS
```

RSS 可用 14px inline SVG，也可纯文本；若用 icon 必须保留 `aria-label`/sr-only。

---

## UI 细节规范

- **列表 hover**：`border-l-2 border-transparent hover:border-accent hover:bg-canvas/55`。不用 scale / bounce / 大幅 translate。
- **Metadata**：`font-mono text-[13px] tabular-nums tracking-tight text-faint`（hover → text-muted/text-ink）。用于日期 / eyebrow / footer / tags / status / archive count。
- **分隔线**：hairline —— `border-line/50` / `border-line/70`。不用 shadow。
- **Tags**：纯文本 `#动态规划` / `#操作系统`。禁止 `rounded-full` / `bg-*` / `pill` / `chip`。

---

## 执行步骤

### Task 1: Baseline
从 `site/`：`pnpm check` + `pnpm build`，确认当前可构建。

### Task 2: 重构 Header
修改 `site/src/components/Header.astro` + `site/src/site.config.ts`：nav 删除 `Notes`、删除 RSS；nav 保留 `Topics`；Logo 保持首页链接；Header 保留 hairline bottom border。

### Task 3: Footer 增加 RSS
修改 `site/src/components/Footer.astro`：显示版权与 RSS；RSS 权重低（`font-mono text-[13px] text-faint hover:text-ink`）；不新增 footer section。

### Task 4: 首页限制最新 15 篇
修改 `site/src/pages/index.astro`：`posts.slice(0, 15)`；添加 `View all notes ->` → `/notes/`；可加 `Knowledge Map` 一级入口但保持克制；首页不展示全量 tags。

### Task 5: 新增 Notes Archive
新增 `site/src/pages/notes/index.astro`：展示全部 public notes；紧凑列表；按日期倒序；暂不 paginate。

### Task 6: 重构 Topics 数据聚合
修改/新增 `site/src/lib/taxonomy.ts`：从 flat topic groups 升级为 domain → subject → notes；Talaria views 作为 curated source 但归入 domain；保持 fallback 优先级（Talaria → type+subject → folder → 手动 category/tags）。

### Task 7: 重构 Topics 页面
修改 `site/src/pages/topics/index.astro`：一级 domain 用 H2；二级 subject 用 H3 或 mono label；每个 subject 下列 note links；完全隐藏日期；不用 emoji 作结构图标；不用 cards。

### Task 8: 可选 Domain Route
若成本低，新增 `site/src/pages/topics/[domain].astro`；若显著增加复杂度，暂缓，只保留 `/topics/` + 现有 topic detail。

### Task 9: UI Polish 同步
修改 `site/uno.config.ts` + `site/src/components/FormattedDate.astro` + `site/src/pages/notes/[...slug].astro`：metadata 统一 mono；prose 中文节奏优化；单篇加 `cd ..` 返回；文章 header 与正文间加 hairline `<hr>`。

---

## 验收标准

从 `site/`：

```powershell
pnpm check
pnpm build
```

从仓库根目录：

```powershell
git status --short -- views
rg -n "Container|Flex|Button|Card|TagPill|PostItem" .\site\src -S
rg -n "<time|FormattedDate|created_at|updated_at|pubDate" .\site\src\pages\topics
rg -n "rounded-full|pill|chip" .\site\src
```

期望：build 通过；`views/` 无修改；没有新增样式组件；Topics 页面无日期；标签无 chip/pill；Header 不再有 `Notes` + Logo 的重复入口；RSS 不在高频主导航区；首页最多展示 15 篇。

---

## 推荐优先级

- **P0**：Header 去重；RSS 移 Footer；首页 slice 15；`/notes/` archive。
- **P1**：Topics 两级拓扑；metadata 统一；article detail hairline。
- **P2**：`/topics/[domain]`；pagination；search modal。

> 作者建议：首页先 `slice(0, 15)` + `/notes/` archive，**不要先上 paginate**。最符合反过度工程审美，也最容易保持站点气质干净。

---

## 仪表盘美学补丁：字体与阴影

### 1. 阴影设计：Hairline over Shadow（极细线优于阴影）

- **扁平化原则**：剔除文章列表、侧边栏或普通卡片上的 `box-shadow`。通过纯粹的留白（margin）或极淡的 1px 细线（如 `border-line/50`）划分物理边界。
- **阴影唯一合法场景**：元素在 Z 轴真正“浮动”于主内容之上时（全局搜索 Search Modal、悬浮菜单 Dropdown、Tooltip）。
- **质感调优**：抛弃又黑又重的默认阴影，改用具有“弥散感”且透明度极低（4%–8% black）的定制阴影。

### 2. 字体体系：Sans & Mono 的交响

- **正文 Sans**：完全交由系统 UI 字体接管（Mac 苹方 / Windows 微软雅黑），零加载延迟，不引入外部中文字体包。
- **数据 Mono**：日期、分类标签（如 `#408`、`[DRAFT]`）、代码片段，强制使用等宽字体栈（系统 mono），在全中文阅读流中像钉子一样锚定视觉焦点。
- **对比度克制**：不要纯黑（`#000000`）。正文用极深灰（`#24292f` = ink），次要元数据用浅灰（`text-faint`），靠灰度 + 字重（400 vs 600）拉开层次。
