# Vault-Aware Topic Routes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a topic-first browsing topology for `11408-vault/site` that reflects the real Vault structure instead of only a chronological post stream.

**Architecture:** Keep the current Vitesse-inspired, minimal UI/UX. Use the Vault itself as the information architecture source: Markdown frontmatter in `docs/`, folder boundaries, public resource rules in `assets/`, and Talaria saved views in `views/*.yml`. Astro routes should derive topics from `type`, `subject`, and Talaria view filters, while preserving plain native HTML and UnoCSS-only styling.

**Tech Stack:** Astro 7 Content Collections, `astro/loaders` glob loader, Zod via `astro/zod`, Node build-time filesystem utilities, `yaml` for Talaria view parsing, TypeScript, UnoCSS.

---

## Skill Search Result

The user explicitly requested skill discovery before the first version of this plan. `npx skills find "astro content collections information architecture"` returned:

- `delineas/astro-framework-agents@astro-framework` — 1.6K installs
- `secondsky/claude-skills@content-collections` — 108 installs
- `lyndonkl/claude@information-architecture` — 97 installs
- several lower-install Astro/content collection skills

Do not install a new skill for this task unless the user explicitly asks. The available local skills plus this plan are sufficient. If a future agent wants to install one, the only result with a stronger install signal is `delineas/astro-framework-agents@astro-framework`.

## Current Vault IA Audit

The real source tree already has a strong knowledge architecture:

```txt
docs/
  408/
  数学/
  错题日记/
  复习周报/
  模块化整合/
  每日心态/
  superpowers/
assets/
  README.md
views/
  408-操作系统.yml
  408-数据结构.yml
  408-组成原理.yml
  408-计算机网络.yml
  数学-高等数学.yml
  数学-线性代数.yml
  数学-概率统计.yml
  错题复习.yml
  待复习.yml
  每日心态.yml
```

Observed Markdown frontmatter patterns:

```yaml
type: 408笔记
subject: 操作系统
status: 待复习
related_to:
  - "[[进程与线程]]"
```

```yaml
type: 考研数学
subject: 高等数学
status: 待复习
```

```yaml
type: 错题日记
subject: 计算机组成原理
status: 待复习
```

Talaria view files are YAML filters. They are not content pages, but they are valuable curated IA definitions. A typical view shape is:

```yaml
name: 408 · 操作系统
sort: "title:asc"
filters:
  all:
    - field: type
      op: equals
      value: 408笔记
    - field: subject
      op: equals
      value: 操作系统
```

`assets/` is a public resource area, not a primary topic taxonomy. It should be treated as supporting material referenced by notes. Current `assets/README.md` defines public paths such as:

```txt
/assets/images/<name>.png
/assets/files/<name>.pdf
```

## IA Decision

Use this priority order for classification:

1. **Talaria views**: if a `views/*.yml` filter matches notes, expose that view as a curated topic group.
2. **Frontmatter type + subject**: derive fallback topic groups from `type` and `subject`.
3. **Folder path**: only use the first `docs/` folder as a fallback when frontmatter is missing.
4. **Manual `category` and `tags`**: support these fields, but do not require them. They are overlays, not the primary truth.

Public topic labels:

```txt
408 · 操作系统
408 · 数据结构
408 · 计算机组成原理
408 · 计算机网络
数学 · 高等数学
数学 · 线性代数
数学 · 概率统计
错题复习
复习周报
综合专题
每日心态
```

Topic routes must hide dates. The home page may keep its current date-oriented recent-notes design.

Tag links must be plain text:

```txt
#操作系统
#高等数学
#待复习
```

No rounded background tags, no chips, no pills.

## Boundaries

- Do not modify `views/*.yml`; Talaria owns those files.
- Do not modify `assets/README.md` unless the user asks for asset policy changes.
- Do not change the current visual direction: restrained typography, black/white/gray, sparse blue accent, direct UnoCSS classes.
- Do not introduce style-only components such as `Container`, `Flex`, `Card`, `TagPill`, `TopicCard`, or `PostItem`.
- Do not copy Vue presentation components from `references/astro-theme-vitesse`.
- Vue is allowed only for browser-state components.

---

### Task 1: Baseline Verification

**Files:**
- Read: `site/src/content.config.ts`
- Read: `site/src/pages/index.astro`
- Read: `site/src/pages/notes/[slug].astro`
- Read: `views/*.yml`
- Read: `assets/README.md`

- [ ] **Step 1: Check current repo state**

Run from `11408-vault/`:

```powershell
git status --short
```

Expected: existing unrelated changes may appear. Do not revert them.

- [ ] **Step 2: Verify site check**

Run from `site/`:

```powershell
pnpm check
```

Expected:

```txt
0 errors
```

- [ ] **Step 3: Verify site build**

Run from `site/`:

```powershell
pnpm build
```

Expected:

```txt
[build] Complete!
```

- [ ] **Step 4: Confirm Talaria views remain tracked and untouched**

Run from `11408-vault/`:

```powershell
git status --short -- views
```

Expected: no output.

---

### Task 2: Add Build-Time YAML Parser

**Files:**
- Modify: `site/package.json`
- Modify: `site/pnpm-lock.yaml`

- [ ] **Step 1: Add direct YAML dependency**

Run from `site/`:

```powershell
pnpm add yaml@latest
```

Expected: `site/package.json` lists `yaml` under `dependencies`.

- [ ] **Step 2: Verify install**

Run from `site/`:

```powershell
pnpm list yaml --depth 0
```

Expected: one installed `yaml` version is shown.

---

### Task 3: Expand Content Schema For Real Vault Notes

**Files:**
- Modify: `site/src/content.config.ts`

- [ ] **Step 1: Replace schema with Vault-aware schema**

Replace `site/src/content.config.ts` with:

```ts
import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const wikilinkValue = z.union([z.string(), z.array(z.string())]).optional();

const notes = defineCollection({
  loader: glob({
    base: '../docs',
    pattern: '**/*.md',
  }),
  schema: z.object({
    title: z.string().optional(),
    pubDate: z.coerce.date().optional(),
    category: z.string().optional(),
    tags: z.array(z.string()).default([]),
    type: z.string().optional(),
    subject: z.string().optional(),
    status: z.string().optional(),
    related_to: wikilinkValue,
    belongs_to: wikilinkValue,
    has: wikilinkValue,
    uuid: z.string().optional(),
    created_at: z.coerce.date().optional(),
    updated_at: z.coerce.date().optional(),
    _organized: z.boolean().optional(),
  }).passthrough(),
});

export const collections = { notes };
```

- [ ] **Step 2: Verify Content Collections can parse Vault docs**

Run from `site/`:

```powershell
pnpm check
```

Expected: 0 errors. If malformed frontmatter in a specific note fails parsing, record the exact file path and exclude only that file class in Task 4 rather than weakening the entire route design.

---

### Task 4: Add Vault Note Filtering And Title Utilities

**Files:**
- Create: `site/src/lib/vault-notes.ts`

- [ ] **Step 1: Create lib directory**

Run from `11408-vault/`:

```powershell
New-Item -ItemType Directory -Force -Path '.\site\src\lib'
```

- [ ] **Step 2: Create note utilities**

Create `site/src/lib/vault-notes.ts`:

```ts
import type { CollectionEntry } from 'astro:content';

export type NoteEntry = CollectionEntry<'notes'>;

const EXCLUDED_PREFIXES = [
  'superpowers/',
];

const TYPE_LABELS = new Set([
  '408笔记',
  '考研数学',
  '错题日记',
  '周报',
  '综合专题',
  '心态日记',
  'Note',
]);

export function isPublicNote(note: NoteEntry): boolean {
  if (EXCLUDED_PREFIXES.some((prefix) => note.id.startsWith(prefix))) return false;
  if (note.data.type === 'Type') return false;
  return true;
}

export function getPublicNotes(notes: NoteEntry[]): NoteEntry[] {
  return notes.filter(isPublicNote);
}

export function getNoteTitle(note: NoteEntry): string {
  if (note.data.title?.trim()) return note.data.title.trim();

  const filename = note.id.split('/').at(-1) ?? note.id;
  return filename.replace(/\.md$/, '');
}

export function getNoteKind(note: NoteEntry): string {
  const type = note.data.type?.trim();
  if (type && TYPE_LABELS.has(type)) return type;

  const folder = note.id.split('/')[0];
  return folder || 'Vault';
}

export function getNoteSubject(note: NoteEntry): string {
  const subject = note.data.subject?.trim();
  if (subject) return subject;

  const kind = getNoteKind(note);
  if (kind === '408笔记') return '408';
  if (kind === '考研数学') return '数学';
  return '未分类';
}

export function getNoteSortKey(note: NoteEntry): string {
  return getNoteTitle(note);
}

export function sortNotesByTitle(notes: NoteEntry[]): NoteEntry[] {
  return [...notes].sort((a, b) => getNoteSortKey(a).localeCompare(getNoteSortKey(b), 'zh-CN'));
}

export function getNoteTags(note: NoteEntry): string[] {
  const tags = new Set<string>();

  for (const tag of note.data.tags) {
    const value = tag.trim();
    if (value) tags.add(value);
  }

  const type = note.data.type?.trim();
  const subject = note.data.subject?.trim();
  const status = note.data.status?.trim();

  if (type && type !== 'Type') tags.add(type);
  if (subject) tags.add(subject);
  if (status) tags.add(status);

  return [...tags].sort((a, b) => a.localeCompare(b, 'zh-CN'));
}
```

- [ ] **Step 3: Run check**

Run from `site/`:

```powershell
pnpm check
```

Expected: 0 errors.

---

### Task 5: Add Talaria View Parser

**Files:**
- Create: `site/src/lib/talaria-views.ts`

- [ ] **Step 1: Create Talaria view parser**

Create `site/src/lib/talaria-views.ts`:

```ts
import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';
import YAML from 'yaml';
import type { NoteEntry } from './vault-notes';

export type TalariaFilter = {
  field: string;
  op: string;
  value?: unknown;
};

export type TalariaFilterTree = {
  all?: TalariaFilter[];
  any?: TalariaFilter[];
};

export type TalariaView = {
  id: string;
  name: string;
  sort?: string;
  filters?: TalariaFilterTree;
};

export type ViewGroup = {
  id: string;
  name: string;
  slug: string;
  notes: NoteEntry[];
};

const VIEWS_DIR = '../views';

export async function readTalariaViews(): Promise<TalariaView[]> {
  const entries = await readdir(VIEWS_DIR, { withFileTypes: true });
  const files = entries
    .filter((entry) => entry.isFile() && entry.name.endsWith('.yml'))
    .map((entry) => entry.name)
    .sort((a, b) => a.localeCompare(b, 'zh-CN'));

  const views = await Promise.all(
    files.map(async (file) => {
      const source = await readFile(join(VIEWS_DIR, file), 'utf8');
      const parsed = YAML.parse(source) as Partial<TalariaView>;
      const id = file.replace(/\.yml$/, '');

      return {
        id,
        name: parsed.name || id,
        sort: parsed.sort,
        filters: parsed.filters,
      };
    }),
  );

  return views;
}

export function matchView(note: NoteEntry, view: TalariaView): boolean {
  const filters = view.filters;
  if (!filters) return false;

  if (filters.all) {
    return filters.all.every((filter) => matchFilter(note, filter));
  }

  if (filters.any) {
    return filters.any.some((filter) => matchFilter(note, filter));
  }

  return false;
}

export function matchFilter(note: NoteEntry, filter: TalariaFilter): boolean {
  const value = getFieldValue(note, filter.field);

  if (filter.op === 'equals') return value === filter.value;
  if (filter.op === 'not_equals') return value !== filter.value;
  if (filter.op === 'contains') return String(value ?? '').includes(String(filter.value ?? ''));
  if (filter.op === 'not_contains') return !String(value ?? '').includes(String(filter.value ?? ''));
  if (filter.op === 'is_empty') return value == null || value === '';
  if (filter.op === 'is_not_empty') return value != null && value !== '';

  return false;
}

export function getFieldValue(note: NoteEntry, field: string): unknown {
  if (field === 'title') return note.id;
  if (field === 'body') return '';
  return note.data[field as keyof typeof note.data];
}
```

- [ ] **Step 2: Verify parser compiles**

Run from `site/`:

```powershell
pnpm check
```

Expected: 0 errors.

---

### Task 6: Add Taxonomy Aggregator

**Files:**
- Create: `site/src/lib/taxonomy.ts`

- [ ] **Step 1: Create taxonomy helper**

Create `site/src/lib/taxonomy.ts`:

```ts
import { matchView, readTalariaViews, type ViewGroup } from './talaria-views';
import {
  getNoteKind,
  getNoteSubject,
  getNoteTags,
  getNoteTitle,
  getPublicNotes,
  sortNotesByTitle,
  type NoteEntry,
} from './vault-notes';

export type TopicGroup = {
  id: string;
  name: string;
  slug: string;
  source: 'talaria-view' | 'derived';
  notes: NoteEntry[];
};

export type TagGroup = {
  tag: string;
  slug: string;
  notes: NoteEntry[];
};

export function slugifyTaxonomy(value: string): string {
  const normalized = value
    .trim()
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-z0-9\u4e00-\u9fff]+/g, '-')
    .replace(/^-+|-+$/g, '');

  return normalized || 'uncategorized';
}

export async function buildTopicGroups(notes: NoteEntry[]): Promise<TopicGroup[]> {
  const publicNotes = getPublicNotes(notes);
  const views = await readTalariaViews();

  const viewGroups = views
    .map<ViewGroup>((view) => ({
      id: view.id,
      name: view.name,
      slug: slugifyTaxonomy(view.id),
      notes: sortNotesByTitle(publicNotes.filter((note) => matchView(note, view))),
    }))
    .filter((group) => group.notes.length > 0)
    .map<TopicGroup>((group) => ({
      ...group,
      source: 'talaria-view',
    }));

  const coveredNoteIds = new Set(viewGroups.flatMap((group) => group.notes.map((note) => note.id)));
  const uncoveredNotes = publicNotes.filter((note) => !coveredNoteIds.has(note.id));
  const derivedGroups = groupNotesByDerivedTopic(uncoveredNotes);

  return [...viewGroups, ...derivedGroups].sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
}

export function groupNotesByDerivedTopic(notes: NoteEntry[]): TopicGroup[] {
  const groups = notes.reduce<Map<string, TopicGroup>>((map, note) => {
    const kind = getNoteKind(note);
    const subject = getNoteSubject(note);
    const name = subject === kind ? kind : `${kind} · ${subject}`;
    const slug = slugifyTaxonomy(name);
    const existing = map.get(slug);

    if (existing) {
      existing.notes.push(note);
      return map;
    }

    map.set(slug, {
      id: slug,
      name,
      slug,
      source: 'derived',
      notes: [note],
    });

    return map;
  }, new Map());

  return [...groups.values()].map((group) => ({
    ...group,
    notes: sortNotesByTitle(group.notes),
  }));
}

export function buildTagGroups(notes: NoteEntry[]): TagGroup[] {
  const publicNotes = getPublicNotes(notes);
  const groups = publicNotes.reduce<Map<string, TagGroup>>((map, note) => {
    for (const tag of getNoteTags(note)) {
      const slug = slugifyTaxonomy(tag);
      const existing = map.get(slug);

      if (existing) {
        existing.notes.push(note);
        continue;
      }

      map.set(slug, {
        tag,
        slug,
        notes: [note],
      });
    }

    return map;
  }, new Map());

  return [...groups.values()]
    .map((group) => ({
      ...group,
      notes: sortNotesByTitle(group.notes),
    }))
    .sort((a, b) => a.tag.localeCompare(b.tag, 'zh-CN'));
}

export { getNoteTags, getNoteTitle, getPublicNotes, sortNotesByTitle };
```

- [ ] **Step 2: Run check**

Run from `site/`:

```powershell
pnpm check
```

Expected: 0 errors.

---

### Task 7: Add Plain Tag Links

**Files:**
- Create or replace: `site/src/components/TagLinks.astro`

- [ ] **Step 1: Create plain text tag links**

Create or replace `site/src/components/TagLinks.astro`:

```astro
---
import { slugifyTaxonomy } from '../lib/taxonomy';

interface Props {
  tags?: string[];
}

const tags = (Astro.props.tags ?? []).map((tag) => tag.trim()).filter(Boolean);
---

{
  tags.length > 0 && (
    <ul class="m-0 flex list-none flex-wrap gap-x-3 gap-y-1 p-0">
      {tags.map((tag) => (
        <li>
          <a
            href={`/tags/${slugifyTaxonomy(tag)}`}
            class="text-sm text-faint no-underline transition-colors hover:text-ink"
          >
            #{tag}
          </a>
        </li>
      ))}
    </ul>
  )
}
```

- [ ] **Step 2: Verify tag UI discipline**

Run from `11408-vault/`:

```powershell
rg -n "rounded|bg-|border|pill|chip" .\site\src\components\TagLinks.astro
```

Expected: no output.

---

### Task 8: Create Topic Index Page

**Files:**
- Create or replace: `site/src/pages/topics/index.astro`
- Modify: `site/src/site.config.ts`

- [ ] **Step 1: Create topics directory**

Run from `11408-vault/`:

```powershell
New-Item -ItemType Directory -Force -Path '.\site\src\pages\topics'
```

- [ ] **Step 2: Create topic index using Talaria-first groups**

Create or replace `site/src/pages/topics/index.astro`:

```astro
---
import { getCollection } from 'astro:content';
import Layout from '../../layouts/Layout.astro';
import TagLinks from '../../components/TagLinks.astro';
import { buildTopicGroups, getNoteTags, getNoteTitle } from '../../lib/taxonomy';

const notes = await getCollection('notes');
const groups = await buildTopicGroups(notes);
---

<Layout title="Topics" description="按知识体系浏览 11408 Vault 笔记。">
  <section aria-label="主题目录">
    <p class="mb-2 font-mono text-xs tracking-wide text-faint">
      Knowledge Map
    </p>
    <h1 class="mb-12 text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
      主题目录
    </h1>

    <div class="columns-1 gap-12 sm:columns-2">
      {
        groups.map((group) => (
          <section class="mb-12 break-inside-avoid" aria-labelledby={`topic-${group.slug}`}>
            <h2 id={`topic-${group.slug}`} class="mb-4 text-xl font-semibold tracking-tight text-ink">
              <a href={`/topics/${group.slug}`} class="text-ink no-underline hover:text-accent">
                {group.name}
              </a>
            </h2>
            <ul class="m-0 list-none space-y-4 p-0">
              {group.notes.map((note) => (
                <li>
                  <a
                    href={`/notes/${note.id}`}
                    class="text-base font-normal text-ink no-underline transition-colors hover:text-accent"
                  >
                    {getNoteTitle(note)}
                  </a>
                  <div class="mt-1">
                    <TagLinks tags={getNoteTags(note)} />
                  </div>
                </li>
              ))}
            </ul>
          </section>
        ))
      }
    </div>
  </section>
</Layout>
```

- [ ] **Step 3: Add Topics nav item**

Modify `site/src/site.config.ts` so the nav includes Topics:

```ts
nav: [
  { label: 'Notes', href: '/' },
  { label: 'Topics', href: '/topics' },
  { label: 'RSS', href: '/rss.xml' },
],
```

- [ ] **Step 4: Build**

Run from `site/`:

```powershell
pnpm build
```

Expected: generated routes include `/topics/index.html`.

---

### Task 9: Create Topic Detail Routes

**Files:**
- Create or replace: `site/src/pages/topics/[topic].astro`

- [ ] **Step 1: Create topic detail route**

Create or replace `site/src/pages/topics/[topic].astro`:

```astro
---
import { getCollection } from 'astro:content';
import Layout from '../../layouts/Layout.astro';
import TagLinks from '../../components/TagLinks.astro';
import {
  buildTopicGroups,
  getNoteTags,
  getNoteTitle,
  type TopicGroup,
} from '../../lib/taxonomy';

export async function getStaticPaths() {
  const notes = await getCollection('notes');
  const groups = await buildTopicGroups(notes);

  return groups.map((group) => ({
    params: { topic: group.slug },
    props: { group },
  }));
}

type Props = {
  group: TopicGroup;
};

const { group } = Astro.props;
---

<Layout title={group.name} description={`按 ${group.name} 浏览 11408 Vault 笔记。`}>
  <section aria-label={`${group.name} 笔记`}>
    <p class="mb-2 font-mono text-xs tracking-wide text-faint">
      Topic
    </p>
    <h1 class="mb-12 text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
      {group.name}
    </h1>

    <ul class="m-0 list-none space-y-6 p-0">
      {
        group.notes.map((note) => (
          <li>
            <a
              href={`/notes/${note.id}`}
              class="text-lg font-semibold tracking-tight text-ink no-underline transition-colors hover:text-accent"
            >
              {getNoteTitle(note)}
            </a>
            <div class="mt-1">
              <TagLinks tags={getNoteTags(note)} />
            </div>
          </li>
        ))
      }
    </ul>
  </section>
</Layout>
```

- [ ] **Step 2: Verify topic detail build**

Run from `site/`:

```powershell
pnpm build
```

Expected: generated routes include topic detail routes derived from `views/*.yml`, such as routes for 408 and math views.

---

### Task 10: Create Tag Routes

**Files:**
- Create or replace: `site/src/pages/tags/[tag].astro`

- [ ] **Step 1: Create tags directory**

Run from `11408-vault/`:

```powershell
New-Item -ItemType Directory -Force -Path '.\site\src\pages\tags'
```

- [ ] **Step 2: Create tag route**

Create or replace `site/src/pages/tags/[tag].astro`:

```astro
---
import { getCollection } from 'astro:content';
import Layout from '../../layouts/Layout.astro';
import { buildTagGroups, getNoteTitle, type TagGroup } from '../../lib/taxonomy';

export async function getStaticPaths() {
  const notes = await getCollection('notes');
  const groups = buildTagGroups(notes);

  return groups.map((group) => ({
    params: { tag: group.slug },
    props: { group },
  }));
}

type Props = {
  group: TagGroup;
};

const { group } = Astro.props;
---

<Layout title={`#${group.tag}`} description={`带有 #${group.tag} 标签的 11408 Vault 笔记。`}>
  <section aria-label={`#${group.tag} 标签`}>
    <p class="mb-2 font-mono text-xs tracking-wide text-faint">
      Tag
    </p>
    <h1 class="mb-12 text-2xl font-semibold tracking-tight text-ink sm:text-3xl">
      #{group.tag}
    </h1>

    <ul class="m-0 list-none space-y-5 p-0">
      {
        group.notes.map((note) => (
          <li>
            <a
              href={`/notes/${note.id}`}
              class="text-base font-normal text-ink no-underline transition-colors hover:text-accent"
            >
              {getNoteTitle(note)}
            </a>
          </li>
        ))
      }
    </ul>
  </section>
</Layout>
```

- [ ] **Step 3: Build**

Run from `site/`:

```powershell
pnpm build
```

Expected: tag routes are generated from `type`, `subject`, `status`, and manual `tags`.

---

### Task 11: Update Notes To Use Vault Titles And Tags

**Files:**
- Modify: `site/src/pages/index.astro`
- Modify: `site/src/pages/notes/[slug].astro`
- Modify: `site/src/pages/rss.xml.ts`

- [ ] **Step 1: Update home page title extraction**

Modify `site/src/pages/index.astro` so it imports:

```astro
import { getNoteTitle, getPublicNotes } from '../lib/taxonomy';
```

Replace the post list source with:

```astro
const posts = getPublicNotes(await getCollection('notes')).sort((a, b) => {
  const left = a.data.updated_at ?? a.data.created_at ?? a.data.pubDate ?? new Date(0);
  const right = b.data.updated_at ?? b.data.created_at ?? b.data.pubDate ?? new Date(0);
  return right.valueOf() - left.valueOf();
});
```

Replace `{post.data.title}` with:

```astro
{getNoteTitle(post)}
```

- [ ] **Step 2: Update note detail page**

Modify `site/src/pages/notes/[slug].astro` imports:

```astro
import TagLinks from '../../components/TagLinks.astro';
import { getNoteTags, getNoteTitle, getPublicNotes } from '../../lib/taxonomy';
```

In `getStaticPaths`, use:

```ts
const posts = getPublicNotes(await getCollection('notes'));
```

Set the title with:

```ts
const title = getNoteTitle(post);
```

Render tags in the article header:

```astro
<div class="mt-3">
  <TagLinks tags={getNoteTags(post)} />
</div>
```

- [ ] **Step 3: Update RSS titles**

Modify `site/src/pages/rss.xml.ts` so RSS item titles use `getNoteTitle(post)` and notes are filtered with `getPublicNotes`.

- [ ] **Step 4: Check**

Run from `site/`:

```powershell
pnpm check
```

Expected: 0 errors.

---

### Task 12: Assets Classification Boundary

**Files:**
- Create: `site/src/lib/assets.ts`

- [ ] **Step 1: Create asset inventory helper**

Create `site/src/lib/assets.ts`:

```ts
import { readdir } from 'node:fs/promises';
import { join } from 'node:path';

export type PublicAsset = {
  kind: 'image' | 'file';
  name: string;
  href: string;
};

const ASSETS_ROOT = '../assets';

export async function readPublicAssets(): Promise<PublicAsset[]> {
  const images = await readAssetDir('images', 'image');
  const files = await readAssetDir('files', 'file');
  return [...images, ...files].sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
}

async function readAssetDir(folder: string, kind: PublicAsset['kind']): Promise<PublicAsset[]> {
  const dir = join(ASSETS_ROOT, folder);

  try {
    const entries = await readdir(dir, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isFile())
      .map((entry) => ({
        kind,
        name: entry.name,
        href: `/assets/${folder}/${entry.name}`,
      }));
  } catch {
    return [];
  }
}
```

- [ ] **Step 2: Do not add an assets page yet**

No route is created in this task. Current `assets/` has only policy text. The asset helper is a boundary for later image/PDF references and does not affect topic IA.

- [ ] **Step 3: Check**

Run from `site/`:

```powershell
pnpm check
```

Expected: 0 errors.

---

### Task 13: Final Verification

**Files:**
- Verify all changed files under `site/src`.

- [ ] **Step 1: Verify Talaria views untouched**

Run from `11408-vault/`:

```powershell
git status --short -- views
```

Expected: no output.

- [ ] **Step 2: Verify tag UI has no chips**

Run from `11408-vault/`:

```powershell
rg -n "rounded|bg-|border|pill|chip" .\site\src\components\TagLinks.astro .\site\src\pages\topics .\site\src\pages\tags
```

Expected: no output.

- [ ] **Step 3: Verify topic pages hide dates**

Run from `11408-vault/`:

```powershell
rg -n "<time|FormattedDate|created_at|updated_at|pubDate" .\site\src\pages\topics
```

Expected: no output.

- [ ] **Step 4: Type check**

Run from `site/`:

```powershell
pnpm check
```

Expected:

```txt
0 errors
```

- [ ] **Step 5: Production build**

Run from `site/`:

```powershell
pnpm build
```

Expected:

```txt
[build] Complete!
```

- [ ] **Step 6: Verify core routes exist**

Run from `11408-vault/`:

```powershell
Test-Path -LiteralPath '.\site\dist\topics\index.html'
Test-Path -LiteralPath '.\site\dist\notes'
Test-Path -LiteralPath '.\site\dist\tags'
```

Expected:

```txt
True
True
True
```

---

## Self-Review

- Spec coverage: this plan now covers real `docs/`, `assets/`, and Talaria `views/` rather than only seed-note metadata.
- UI/UX coverage: all topic/tag routes preserve the current sparse typography and plain text link style.
- Data consistency: classification priority is Talaria view, frontmatter `type + subject`, folder fallback, manual `category/tags` overlay.
- Safety: `views/*.yml` and `assets/README.md` are read-only inputs.
- Scope boundary: this plan does not normalize mojibake or rewrite Vault notes. It adapts the site to existing metadata without bulk editing the Vault.
