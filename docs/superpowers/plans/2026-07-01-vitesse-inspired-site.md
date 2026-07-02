# Vitesse-Inspired Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework `site/` into a Vitesse-inspired Astro 7 notes site while preserving the Vault/Tolaria data model and the anti-overengineering component rules.

**Architecture:** Keep `11408-vault` as the single repository and leave Tolaria `views/*.yml` untouched. Use `site/` as the Astro display layer, borrowing ideas from `references/astro-theme-vitesse` without copying its Vue-heavy presentation components. Data starts with the existing seed notes and is prepared to switch to `../docs`.

**Tech Stack:** Astro 7, Vue 3 only for future client-state islands, UnoCSS Wind3, Astro Content Collections, pnpm, Vercel Root Directory `site`.

---

## Non-Negotiable Rules

- Do not modify `views/*.yml`; that directory belongs to Talaria saved views.
- Do not copy `references/astro-theme-vitesse/src/components/Header.vue`, `Footer.vue`, `ListPosts.vue`, or `ListProjects.vue` into production. They are pure presentation Vue components and violate this project's component discipline.
- Vue components are allowed only for browser state or native browser APIs, such as `ThemeToggle.vue` or future `SearchModal.vue`.
- Do not create style-only components such as `Container`, `Flex`, `Button`, `Text`, `Card`, or `PostItem`.
- Use native HTML elements with UnoCSS classes directly in pages and macro layout components.
- Keep `references/astro-theme-vitesse` as a reference clone only. Do not make `site/` depend on files inside `references/`.
- Generated directories must remain ignored: `site/node_modules`, `site/.astro`, and `site/dist`.
- The current project has unrelated existing Vault changes. Do not revert them.

## Reference Audit

Reference repo is already cloned at:

```txt
references/astro-theme-vitesse/
```

Useful files to inspect:

```txt
references/astro-theme-vitesse/src/components/BaseHead.astro
references/astro-theme-vitesse/src/layouts/BaseLayout.astro
references/astro-theme-vitesse/src/pages/rss.xml.ts
references/astro-theme-vitesse/src/pages/robots.txt.ts
references/astro-theme-vitesse/src/site-config.ts
references/astro-theme-vitesse/src/styles/global.css
references/astro-theme-vitesse/src/styles/prose.css
references/astro-theme-vitesse/uno.config.ts
references/astro-theme-vitesse/astro.config.ts
references/astro-theme-vitesse/LICENSE
```

Reference facts:

- `astro-theme-vitesse` is MIT licensed.
- It is version `1.3.2`.
- It targets Astro 5-era dependencies, while this project uses Astro 7.
- It uses Vue for `Header`, `Footer`, and list rendering. Treat those as design references only.

## File Structure Target

Create or modify these files:

```txt
site/
  astro.config.mjs
  package.json
  pnpm-lock.yaml
  uno.config.ts
  src/
    site.config.ts
    content.config.ts
    components/
      BaseHead.astro
      Header.astro
      Footer.astro
      FormattedDate.astro
    layouts/
      Layout.astro
    pages/
      index.astro
      notes/[slug].astro
      rss.xml.ts
      robots.txt.ts
```

Delete after route migration:

```txt
site/src/pages/[slug].astro
```

Keep seed notes until the Vault reader is implemented:

```txt
site/src/content/notes/*.md
```

---

### Task 1: Baseline Verification

**Files:**
- Read: `site/package.json`
- Read: `site/src/content.config.ts`
- Read: `site/src/pages/index.astro`
- Read: `site/src/pages/[slug].astro`
- Read: `references/astro-theme-vitesse/LICENSE`

- [ ] **Step 1: Confirm working directory**

Run:

```powershell
Get-Location
```

Expected: the command runs inside `C:\Users\GuLuGuLu\Desktop\11408\11408-vault`.

- [ ] **Step 2: Confirm reference clone exists**

Run:

```powershell
Test-Path -LiteralPath '.\references\astro-theme-vitesse\package.json'
Test-Path -LiteralPath '.\references\astro-theme-vitesse\LICENSE'
```

Expected:

```txt
True
True
```

- [ ] **Step 3: Confirm baseline site checks**

Run:

```powershell
pnpm check
```

from:

```txt
site/
```

Expected:

```txt
Result (... files):
- 0 errors
```

- [ ] **Step 4: Confirm baseline site build**

Run:

```powershell
pnpm build
```

from:

```txt
site/
```

Expected:

```txt
[build] Complete!
```

---

### Task 2: Add Site Config

**Files:**
- Create: `site/src/site.config.ts`

- [ ] **Step 1: Create config file**

Create `site/src/site.config.ts`:

```ts
export const siteConfig = {
  title: '11408 Vault',
  subtitle: '静态笔记阅读层',
  description: '从 11408 Vault 发布出来的极简静态笔记站。',
  author: 'GuLuGuLu',
  email: '',
  url: 'https://11408.vercel.app',
  language: 'zh-CN',
  nav: [
    { label: 'Notes', href: '/' },
    { label: 'RSS', href: '/rss.xml' },
  ],
  social: [
    {
      label: 'GitHub',
      href: 'https://github.com/',
    },
  ],
} as const;
```

- [ ] **Step 2: Run type check**

Run:

```powershell
pnpm check
```

from `site/`.

Expected: 0 errors.

---

### Task 3: Add BaseHead

**Files:**
- Create: `site/src/components/BaseHead.astro`
- Modify: `site/astro.config.mjs`

- [ ] **Step 1: Add sitemap dependency**

Run:

```powershell
pnpm add @astrojs/sitemap@latest @astrojs/rss@latest
```

from `site/`.

Expected: `package.json` contains `@astrojs/sitemap` and `@astrojs/rss`.

- [ ] **Step 2: Update Astro config**

Modify `site/astro.config.mjs` to include `site` and sitemap:

```js
// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import vue from '@astrojs/vue';
import UnoCSS from '@unocss/astro';

export default defineConfig({
  site: 'https://11408.vercel.app',
  compressHTML: true,
  markdown: {
    syntaxHighlight: false,
  },
  integrations: [
    sitemap(),
    vue(),
    UnoCSS(),
  ],
});
```

- [ ] **Step 3: Create BaseHead**

Create `site/src/components/BaseHead.astro`:

```astro
---
import { siteConfig } from '../site.config';

interface Props {
  title?: string;
  description?: string;
  type?: 'website' | 'article';
}

const {
  title,
  description = siteConfig.description,
  type = 'website',
} = Astro.props;

const pageTitle = title ? `${title} · ${siteConfig.title}` : siteConfig.title;
const canonical = Astro.site ? new URL(Astro.url.pathname, Astro.site).toString() : Astro.url.pathname;
---

<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta name="description" content={description} />
<meta name="color-scheme" content="light" />
<meta name="generator" content={Astro.generator} />
<link rel="icon" type="image/svg+xml" href="/favicon.svg" />
<link rel="canonical" href={canonical} />
<link rel="sitemap" href="/sitemap-index.xml" />
<link rel="alternate" type="application/rss+xml" href="/rss.xml" title={`${siteConfig.title} RSS`} />
<meta property="og:type" content={type} />
<meta property="og:title" content={pageTitle} />
<meta property="og:description" content={description} />
<meta property="og:url" content={canonical} />
<meta name="twitter:card" content="summary" />
<title>{pageTitle}</title>
```

- [ ] **Step 4: Run check**

Run:

```powershell
pnpm check
```

Expected: 0 errors.

---

### Task 4: Split Macro Layout Components

**Files:**
- Create: `site/src/components/Header.astro`
- Create: `site/src/components/Footer.astro`
- Create: `site/src/components/FormattedDate.astro`
- Replace: `site/src/layouts/Layout.astro`

- [ ] **Step 1: Create Header**

Create `site/src/components/Header.astro`:

```astro
---
import { siteConfig } from '../site.config';
---

<header class="w-full">
  <nav
    aria-label="主导航"
    class="mx-auto flex w-full max-w-2xl items-center justify-between px-6 pb-8 pt-12 sm:px-8"
  >
    <a href="/" class="flex items-baseline gap-1.5 no-underline" aria-label="11408 Vault 首页">
      <span class="text-base font-bold text-ink">11408</span>
      <span class="text-base font-light text-faint">Vault</span>
    </a>
    <ul class="m-0 flex list-none items-center gap-6 p-0">
      {
        siteConfig.nav.map((item) => (
          <li>
            <a
              href={item.href}
              class="text-sm font-normal text-muted no-underline transition-colors hover:text-ink"
            >
              {item.label}
            </a>
          </li>
        ))
      }
    </ul>
  </nav>
</header>
```

- [ ] **Step 2: Create Footer**

Create `site/src/components/Footer.astro`:

```astro
---
import { siteConfig } from '../site.config';

const year = new Date().getFullYear();
---

<footer class="mt-auto w-full">
  <div class="mx-auto w-full max-w-2xl border-t border-line px-6 py-8 sm:px-8">
    <p class="m-0 font-mono text-sm text-faint">
      © {year} · {siteConfig.title}
    </p>
  </div>
</footer>
```

- [ ] **Step 3: Create FormattedDate**

Create `site/src/components/FormattedDate.astro`:

```astro
---
interface Props {
  date: Date | string;
  class?: string;
}

const { date, class: className = '' } = Astro.props;
const value = date instanceof Date ? date : new Date(date);
const iso = value.toISOString().slice(0, 10);
---

<time datetime={iso} class:list={['font-mono tabular-nums text-faint', className]}>
  {iso}
</time>
```

- [ ] **Step 4: Replace Layout**

Replace `site/src/layouts/Layout.astro`:

```astro
---
import BaseHead from '../components/BaseHead.astro';
import Header from '../components/Header.astro';
import Footer from '../components/Footer.astro';
import { siteConfig } from '../site.config';

interface Props {
  title?: string;
  description?: string;
  type?: 'website' | 'article';
  lang?: string;
}

const {
  title,
  description = siteConfig.description,
  type = 'website',
  lang = siteConfig.language,
} = Astro.props;
---

<!doctype html>
<html lang={lang}>
  <head>
    <BaseHead title={title} description={description} type={type} />
  </head>
  <body class="flex min-h-screen flex-col bg-white font-sans text-ink antialiased selection:bg-accent/15">
    <a
      href="#main"
      class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-md focus:bg-ink focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white"
    >
      跳至正文
    </a>
    <Header />
    <main id="main" class="w-full">
      <div class="mx-auto w-full max-w-2xl px-6 py-12 sm:px-8 sm:py-16">
        <slot />
      </div>
    </main>
    <Footer />
  </body>
</html>

<style is:global>
  :root {
    color-scheme: light;
  }

  html {
    -webkit-text-size-adjust: 100%;
    scroll-behavior: smooth;
    text-rendering: optimizeLegibility;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  :focus-visible {
    outline: 2px solid #0969da;
    outline-offset: 2px;
    border-radius: 2px;
  }

  @media (prefers-reduced-motion: reduce) {
    html {
      scroll-behavior: auto;
    }

    *,
    *::before,
    *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }
  }
</style>
```

- [ ] **Step 5: Verify layout**

Run:

```powershell
pnpm check
pnpm build
```

Expected: both commands exit 0. If chaining causes a Windows/libuv exit assertion, run them separately and record the separate results.

---

### Task 5: Clean UnoCSS Config

**Files:**
- Replace comments in `site/uno.config.ts`

- [ ] **Step 1: Replace `uno.config.ts` with clean comments**

Keep the same behavior, but remove mojibake comments:

```ts
import {
  defineConfig,
  presetWind3,
  presetTypography,
  transformerDirectives,
  transformerVariantGroup,
  type PresetWind3Theme,
} from 'unocss';

export default defineConfig<PresetWind3Theme>({
  presets: [presetWind3(), presetTypography<PresetWind3Theme>()],
  transformers: [transformerDirectives(), transformerVariantGroup()],

  theme: {
    colors: {
      ink: '#24292f',
      muted: '#57606a',
      faint: '#8c959f',
      line: '#d0d7de',
      canvas: '#f6f8fa',
      accent: '#0969da',
    },
    fontFamily: {
      sans:
        'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif',
      mono: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, "Liberation Mono", monospace',
    },
    fontWeight: {
      light: '300',
      normal: '400',
      semibold: '600',
      bold: '700',
    },
  },

  shortcuts: {
    shell: 'mx-auto w-full max-w-[720px] px-6 sm:px-8',
    section: 'py-16 sm:py-24',
    link: 'text-accent font-normal underline-offset-[3px] decoration-accent/40 hover:decoration-accent transition-colors',
    'prose-blog': [
      'prose prose-neutral max-w-none',
      'prose-headings:font-sans prose-headings:text-ink',
      'prose-headings:font-semibold prose-headings:tracking-tight',
      'prose-p:text-ink prose-p:leading-[1.75]',
      'prose-a:text-accent prose-a:font-normal prose-a:no-underline hover:prose-a:underline prose-a:underline-offset-[3px]',
      'prose-strong:text-ink prose-strong:font-semibold',
      'prose-code:before:content-none prose-code:after:content-none prose-code:font-mono',
      'prose-code:text-ink prose-code:bg-canvas prose-code:rounded prose-code:px-1.5 prose-code:py-0.5 prose-code:text-[0.875em]',
      'prose-pre:bg-canvas prose-pre:text-ink prose-pre:rounded-lg',
      'prose-blockquote:border-l-ink prose-blockquote:text-muted',
      'prose-hr:border-line',
    ].join(' '),
  },
});
```

- [ ] **Step 2: Run check**

Run:

```powershell
pnpm check
```

Expected: 0 errors, 0 warnings, 0 hints.

---

### Task 6: Move Note Route Under `/notes`

**Files:**
- Create: `site/src/pages/notes/[slug].astro`
- Modify: `site/src/pages/index.astro`
- Delete: `site/src/pages/[slug].astro`

- [ ] **Step 1: Create note detail route**

Create `site/src/pages/notes/[slug].astro`:

```astro
---
import { getCollection, render } from 'astro:content';
import type { CollectionEntry } from 'astro:content';
import FormattedDate from '../../components/FormattedDate.astro';
import Layout from '../../layouts/Layout.astro';

export async function getStaticPaths() {
  const posts = await getCollection('notes');
  return posts.map((post) => ({
    params: { slug: post.id },
    props: { post },
  }));
}

type Props = {
  post: CollectionEntry<'notes'>;
};

const { post } = Astro.props;
const { title, pubDate } = post.data;
const { Content } = await render(post);
---

<Layout title={title} description={`${title} · 11408 Vault`} type="article">
  <article>
    <header>
      <h1 class="text-3xl font-bold tracking-tight text-ink sm:text-4xl">
        {title}
      </h1>
      <FormattedDate date={pubDate} class="mt-4 block text-sm" />
    </header>
    <div class="prose-blog mt-10">
      <Content />
    </div>
  </article>
</Layout>
```

- [ ] **Step 2: Replace home page**

Replace `site/src/pages/index.astro`:

```astro
---
import { getCollection } from 'astro:content';
import FormattedDate from '../components/FormattedDate.astro';
import Layout from '../layouts/Layout.astro';
import { siteConfig } from '../site.config';

const posts = (await getCollection('notes')).sort(
  (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf(),
);
---

<Layout title="Notes" description={siteConfig.description}>
  <section aria-label="最新笔记">
    <p class="mb-2 font-mono text-xs tracking-wide text-faint">
      Vault Notes · 2026
    </p>
    <h1 class="mb-12 text-2xl font-semibold tracking-tight text-ink sm:mb-16 sm:text-3xl">
      最新笔记
    </h1>
    <ul class="m-0 list-none space-y-8 p-0">
      {
        posts.map((post) => (
          <li>
            <a
              href={`/notes/${post.id}`}
              class="group flex flex-col items-start gap-1 no-underline sm:flex-row sm:items-baseline sm:gap-6"
            >
              <FormattedDate date={post.data.pubDate} class="shrink-0 text-sm sm:w-32" />
              <h2 class="text-lg font-semibold tracking-tight text-ink transition-colors group-hover:text-accent">
                {post.data.title}
              </h2>
            </a>
          </li>
        ))
      }
    </ul>
  </section>
</Layout>
```

- [ ] **Step 3: Delete old root slug route**

Delete:

```txt
site/src/pages/[slug].astro
```

- [ ] **Step 4: Build and inspect routes**

Run:

```powershell
pnpm build
```

Expected generated routes include:

```txt
/notes/reading-hierarchy/index.html
/notes/vault-display-layer/index.html
/index.html
```

---

### Task 7: Add RSS and Robots

**Files:**
- Create: `site/src/pages/rss.xml.ts`
- Create: `site/src/pages/robots.txt.ts`

- [ ] **Step 1: Create RSS route**

Create `site/src/pages/rss.xml.ts`:

```ts
import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import { siteConfig } from '../site.config';

export async function GET(context: { site: URL }) {
  const posts = (await getCollection('notes')).sort(
    (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf(),
  );

  return rss({
    title: siteConfig.title,
    description: siteConfig.description,
    site: context.site,
    items: posts.map((post) => ({
      title: post.data.title,
      pubDate: post.data.pubDate,
      link: `/notes/${post.id}/`,
    })),
  });
}
```

- [ ] **Step 2: Create robots route**

Create `site/src/pages/robots.txt.ts`:

```ts
export function GET(context: { site: URL }) {
  return new Response(
    `User-agent: *
Allow: /

Sitemap: ${new URL('sitemap-index.xml', context.site).href}
`.trim(),
    {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
      },
    },
  );
}
```

- [ ] **Step 3: Build**

Run:

```powershell
pnpm build
```

Expected generated routes include:

```txt
/rss.xml
/robots.txt
```

---

### Task 8: Prepare Vault Reader Boundary

**Files:**
- Modify: `site/src/content.config.ts`

- [ ] **Step 1: Keep seed reader but document production switch**

Replace `site/src/content.config.ts` with:

```ts
import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const notes = defineCollection({
  loader: glob({
    base: './src/content/notes',
    pattern: '**/*.md',
  }),
  schema: z.object({
    title: z.string(),
    pubDate: z.coerce.date(),
  }),
});

export const collections = { notes };
```

Do not switch to `../docs` in this task unless the Vault frontmatter has been normalized to include `title` and `pubDate` for every public note.

- [ ] **Step 2: Add follow-up note in implementation summary**

The executing agent must report:

```txt
Vault reader still uses seed notes. Next step is a frontmatter adapter or normalization pass for ../docs.
```

---

### Task 9: License Attribution

**Files:**
- Create: `site/NOTICE.md`

- [ ] **Step 1: Create NOTICE**

Create `site/NOTICE.md`:

```md
# Notices

This site design was inspired by `astro-theme-vitesse`.

- Project: https://github.com/kieranwv/astro-theme-vitesse
- License: MIT
- Copyright: Copyright (c) 2024 Kieran Wang

No production code imports files from `references/astro-theme-vitesse`.
When copying substantial source code from the reference project, preserve the MIT license notice.
```

- [ ] **Step 2: Verify no runtime imports from references**

Run:

```powershell
rg -n "references/astro-theme-vitesse|astro-theme-vitesse" .\site -g "!node_modules" -g "!dist" -g "!.astro"
```

Expected: only `site/NOTICE.md` mentions it.

---

### Task 10: Final Verification

**Files:**
- Verify all touched site files.

- [ ] **Step 1: Check no Talaria views changed**

Run:

```powershell
git status --short -- views
```

from `11408-vault/`.

Expected: no output.

- [ ] **Step 2: Check component discipline**

Run:

```powershell
rg -n "Container|Flex|Button|Card|ListPosts|ListProjects|Header.vue|Footer.vue" .\site\src -S
```

Expected: no matches for style-only copied components.

- [ ] **Step 3: Check Astro**

Run:

```powershell
pnpm check
```

from `site/`.

Expected:

```txt
0 errors
0 warnings
0 hints
```

- [ ] **Step 4: Build**

Run:

```powershell
pnpm build
```

from `site/`.

Expected:

```txt
[build] Complete!
```

- [ ] **Step 5: Record Vercel settings**

The final response must include:

```txt
Vercel Repository: 11408-vault
Root Directory: site
Build Command: pnpm build
Output Directory: dist
Do not use 11408-vault/views for Astro; it belongs to Talaria saved views.
```

---

## Self-Review

- Spec coverage: plan covers Vitesse reference usage, anti-style-component rules, Astro 7 compatibility, RSS/sitemap/robots, route cleanup, and Vercel settings.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: collection name remains `notes`, route path becomes `/notes/[slug]`, and component imports use relative paths.
- Known risk: `../docs` is not switched on yet because Vault frontmatter may not match the strict `title`/`pubDate` schema. That is intentionally deferred to a separate Vault ingestion plan.
