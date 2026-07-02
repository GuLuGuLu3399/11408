# Typography Blockquote Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove UnoCSS Typography's decorative pseudo-content from inline code and blockquotes, then align Markdown prose with the site's GitHub-like Instrument Panel reading style.

**Architecture:** Keep the existing UnoCSS Wind3 setup and current `prose-blog` shortcut. Use UnoCSS utilities for normal prose styling, and add a tightly scoped `.prose-blog` global CSS patch in `Layout.astro` for pseudo-elements that Typography injects through generated CSS.

**Tech Stack:** Astro 7, UnoCSS Wind3, UnoCSS Typography preset, Astro Markdown content, GitHub-inspired prose styling.

---

## Current Context

The current site already uses:

```ts
presets: [presetWind3(), presetTypography<PresetWind3Theme>()]
```

and has an existing `prose-blog` shortcut in:

```txt
site/uno.config.ts
```

This plan must improve that setup in place. It must not replace Wind3 with `presetUno()`, must not add a new design system, and must not create style-only components.

The issue being fixed:

```css
blockquote p:first-of-type::before {
  content: "\201C";
}
```

UnoCSS Typography may render quote marks or other prose decorations through CSS pseudo-elements. These marks are not real DOM text, cannot be selected, and make technical notes feel like literary quotations. For this Vault, blockquotes should behave like GitHub-style technical memos.

## Non-Negotiable Rules

- Do not replace `presetWind3()` with `presetUno()`.
- Do not replace the whole `theme.colors` object.
- Do not add `boxShadow.float`.
- Do not introduce generic `transition-all`.
- Do not create style-only components such as `Container`, `Card`, `Prose`, or `Blockquote`.
- Do not turn normal blockquotes into rounded cards or colored callouts.
- Keep GitHub Alerts / callouts separate from normal Markdown blockquotes.
- Scope pseudo-element fixes under `.prose-blog`; do not globally affect every future `code` or `blockquote` element in the app.

## Target Files

Modify:

```txt
site/uno.config.ts
site/src/layouts/Layout.astro
```

Optional, only if no existing note can verify the behavior:

```txt
site/src/content/notes/typography-demo.md
```

---

### Task 1: Baseline Verification

**Files:**
- Read: `site/uno.config.ts`
- Read: `site/src/layouts/Layout.astro`
- Verify: `site/`

- [ ] **Step 1: Check current working tree**

Run from `11408-vault/`:

```powershell
git status --short
```

Expected: existing unrelated changes may appear. Do not revert unrelated user work.

- [ ] **Step 2: Run baseline check**

Run from `11408-vault/site`:

```powershell
pnpm check
```

Expected: no Astro type errors.

- [ ] **Step 3: Run baseline build**

Run from `11408-vault/site`:

```powershell
pnpm build
```

Expected: build completes.

- [ ] **Step 4: Inspect current prose setup**

Run from `11408-vault/site`:

```powershell
rg -n "presetWind3|presetUno|presetTypography|prose-blog|t-link|blockquote|code::before|code::after" .\uno.config.ts .\src
```

Expected:

```txt
presetWind3 is present
presetTypography is present
prose-blog is present
```

If `presetUno` is absent, keep it absent.

---

### Task 2: Preserve UnoCSS Preset Architecture

**Files:**
- Modify: `site/uno.config.ts`

- [ ] **Step 1: Confirm preset stack remains Wind3**

Ensure `site/uno.config.ts` still imports and uses:

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
});
```

Do not change this to:

```ts
presetUno()
```

- [ ] **Step 2: Keep existing semantic tokens**

Keep the existing token names:

```ts
colors: {
  ink: '#24292f',
  muted: '#57606a',
  faint: '#8c959f',
  line: '#d0d7de',
  canvas: '#f6f8fa',
  accent: '#0969da',
}
```

Do not replace them with a full Tailwind `gray` palette in this task.

---

### Task 3: Tighten `prose-blog` Markdown Styling

**Files:**
- Modify: `site/uno.config.ts`

- [ ] **Step 1: Update `prose-blog` shortcut**

Replace only the `prose-blog` shortcut value with this structure, while preserving any already-correct local imports and theme config:

```ts
'prose-blog': [
  'prose prose-neutral max-w-none',
  'prose-headings:font-sans prose-headings:text-ink',
  'prose-headings:font-semibold prose-headings:tracking-normal',
  'prose-h2:mt-12 prose-h2:mb-4',
  'prose-h3:mt-10 prose-h3:mb-3',
  'prose-p:my-6 prose-p:text-ink prose-p:leading-[1.8]',
  'prose-li:my-1.5 prose-li:text-ink',
  'prose-a:text-accent prose-a:font-normal prose-a:no-underline',
  'hover:prose-a:underline prose-a:underline-offset-[3px]',
  'prose-strong:text-ink prose-strong:font-semibold',
  'prose-code:before:content-none prose-code:after:content-none',
  'prose-code:font-mono prose-code:text-ink',
  'prose-code:bg-canvas/80 prose-code:border prose-code:border-line/50',
  'prose-code:rounded prose-code:px-1.5 prose-code:py-0.5 prose-code:text-[0.875em]',
  'prose-pre:bg-canvas/80 prose-pre:text-ink',
  'prose-pre:border prose-pre:border-line/60',
  'prose-pre:rounded-md prose-pre:overflow-x-auto',
  'prose-blockquote:not-italic',
  'prose-blockquote:border-l-line',
  'prose-blockquote:text-muted',
  'prose-hr:border-line/70',
].join(' ')
```

Use `tracking-normal` for headings. Do not use negative letter spacing for Chinese reading surfaces.

- [ ] **Step 2: Preserve precise interaction shortcut**

Ensure `t-link` remains precise and does not become `transition-all`:

```ts
't-link': 'motion-safe:transition-[color,background-color,border-color,opacity] duration-150 ease-out',
```

- [ ] **Step 3: Run Uno/Astro check**

Run from `11408-vault/site`:

```powershell
pnpm check
```

Expected: no errors from invalid UnoCSS classes or Astro types.

---

### Task 4: Add Scoped Pseudo-Element Patch

**Files:**
- Modify: `site/src/layouts/Layout.astro`

- [ ] **Step 1: Add `.prose-blog` global CSS overrides**

Inside the existing `<style is:global>` block in `Layout.astro`, add this before the `@media (prefers-reduced-motion: reduce)` block:

```css
  .prose-blog code::before,
  .prose-blog code::after {
    content: none;
  }

  .prose-blog blockquote p:first-of-type::before,
  .prose-blog blockquote p:last-of-type::after {
    content: none;
  }

  .prose-blog blockquote {
    font-style: normal;
  }

  .prose-blog pre code {
    background: transparent;
    border: 0;
    padding: 0;
  }
```

Rationale:

- UnoCSS utilities cover normal styling.
- This scoped CSS covers Typography pseudo-elements that may survive utility classes.
- `pre code` prevents fenced code blocks from inheriting inline-code background and padding.

- [ ] **Step 2: Keep the patch scoped**

Do not add global selectors like:

```css
code::before,
code::after,
blockquote p:first-of-type::before {
  content: none;
}
```

All selectors must start with `.prose-blog`.

- [ ] **Step 3: Run check**

Run from `11408-vault/site`:

```powershell
pnpm check
```

Expected: no errors.

---

### Task 5: Optional Fixture For Visual QA

**Files:**
- Optional Create: `site/src/content/notes/typography-demo.md`

- [ ] **Step 1: Prefer existing content**

First search for existing notes with blockquotes and inline code:

```powershell
rg -n "^>|`[^`]+`" ..\docs .\src\content\notes
```

If existing notes are enough, do not create a fixture.

- [ ] **Step 2: Create fixture only when needed**

If no suitable note exists and seed notes are acceptable in this branch, create:

```txt
site/src/content/notes/typography-demo.md
```

with:

````md
---
title: Typography Demo
pubDate: 2026-07-01
---

This is inline `code`.

> 这是一段普通引用，应当像技术备忘录，而不是文学引用。
> 它不应该出现幽灵左双引号，也不应该自动变成斜体。

```ts
const answer = 408
console.log(answer)
```
````

- [ ] **Step 3: Remove fixture if it should not ship**

If this fixture is only for visual verification, delete it before final build.

---

### Task 6: Build And Inspect Output

**Files:**
- Verify: `site/dist`

- [ ] **Step 1: Build**

Run from `11408-vault/site`:

```powershell
pnpm build
```

Expected: build completes.

- [ ] **Step 2: Inspect source and generated output**

Run from `11408-vault/site`:

```powershell
rg -n "prose-blog|blockquote|code::before|code::after|pre code" .\src .\uno.config.ts .\dist
```

Expected:

- `.prose-blog code::before` override exists.
- `.prose-blog blockquote p:first-of-type::before` override exists.
- generated pages contain normal `blockquote` markup, not extra DOM quote characters.

- [ ] **Step 3: Manual visual QA**

Open a note page that contains inline code and blockquotes.

Check:

- inline code has no generated backticks.
- blockquote has no unselectable decorative left double quote.
- blockquote text is not italic.
- blockquote feels like a technical memo: muted text, left border, no card background.
- fenced code blocks do not show inline-code background around every token.
- Chinese paragraph rhythm still feels readable.

---

### Task 7: Guardrails

**Files:**
- Verify: `site/uno.config.ts`
- Verify: `site/src`

- [ ] **Step 1: Ensure no architecture drift**

Run from `11408-vault`:

```powershell
rg -n "presetUno|transition-all|boxShadow|float|Container|Flex|Card|TagPill|PostItem" .\site\src .\site\uno.config.ts
```

Expected:

- no `presetUno`
- no new generic `transition-all`
- no new floating shadow token
- no style-only components

- [ ] **Step 2: Ensure blockquote remains separate from alerts**

Run from `11408-vault/site`:

```powershell
rg -n "markdown-alert|\\[!NOTE\\]|\\[!WARNING\\]" .\src .\uno.config.ts
```

Expected: this plan does not implement alerts. If alert support already exists from another branch, ensure normal `blockquote` styles do not override `.markdown-alert`.

---

## Final Verification

Run from `11408-vault/site`:

```powershell
pnpm check
pnpm build
```

Run from `11408-vault`:

```powershell
git status --short -- views
rg -n "presetUno|transition-all|boxShadow|float" .\site\uno.config.ts
rg -n "Container|Flex|Button|Card|TagPill|PostItem" .\site\src -S
```

Expected:

- `pnpm check` passes.
- `pnpm build` passes.
- `views/` has no changes.
- `presetWind3()` is preserved.
- no generic `transition-all` is introduced.
- no style-only components are introduced.

## Final Report Requirements

The executing agent must report:

- files changed
- whether `presetWind3()` was preserved
- whether inline code pseudo backticks were removed
- whether blockquote ghost quote was removed
- whether blockquote italic styling was removed
- `pnpm check` result
- `pnpm build` result

## Self-Review

- Spec coverage: plan covers inline code pseudo-elements, blockquote pseudo-elements, blockquote italic removal, fenced code isolation, GitHub-like Instrument Panel prose, and architecture guardrails.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: all paths refer to the existing `site/` Astro app and existing `prose-blog` shortcut.
- Scope check: this plan intentionally does not implement GitHub Alerts. Alerts should remain a separate Markdown capability task.
