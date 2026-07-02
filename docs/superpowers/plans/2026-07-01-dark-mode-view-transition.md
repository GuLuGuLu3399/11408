# Dark Mode View Transition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a VitePress/Vercel-like class-based dark mode with a native View Transition circular reveal animation to the Astro Vault site.

**Architecture:** Preserve the current Astro + UnoCSS Wind3 architecture and add dark mode through semantic CSS variables on `html.dark`. Use a real Vue island for browser state (`ThemeToggle.vue`) because theme persistence, system preference detection, and click-origin animation are client-side concerns. Use the View Transition API when available, and fall back to an instant class toggle when unavailable or when reduced motion is requested.

**Tech Stack:** Astro 7, Vue 3 island, UnoCSS Wind3, native `document.startViewTransition()`, localStorage, `matchMedia('(prefers-color-scheme: dark)')`.

---

## Current Project Facts

The site already has:

```txt
site/src/layouts/Layout.astro
site/src/components/Header.astro
site/uno.config.ts
site/package.json
```

The current UnoCSS setup uses:

```ts
presets: [presetWind3(), presetTypography<PresetWind3Theme>()]
```

This plan must preserve `presetWind3()` and must not replace it with `presetUno()`.

The project already has Vue:

```json
"@astrojs/vue": "^7.0.0",
"vue": "^3.5.39"
```

No extra animation library is required.

## Design Decision

Use `html.dark` as the source of truth.

Theme state priority:

```txt
1. localStorage theme = "dark" | "light"
2. system preference via prefers-color-scheme
3. fallback to light
```

Visual direction:

```txt
light: GitHub-light / Instrument Panel
dark: GitHub-dark-inspired, not pure black
```

Do not use:

```txt
presetUno({ dark: 'class' })
transition-all
boxShadow.float
large gradients
decorative glow
card-heavy dark mode
```

Use:

```txt
semantic CSS variables
hairline borders
mono metadata
native View Transition circular reveal
reduced-motion fallback
```

## Non-Negotiable Rules

- Do not replace `presetWind3()` with `presetUno()`.
- Do not add `boxShadow.float`.
- Do not introduce generic `transition-all`.
- Do not create style-only components.
- Do not add an animation library.
- Do not use localStorage in server-rendered Astro frontmatter.
- Do not make dark mode depend on the reference theme under `references/`.
- Do not modify `views/*.yml`.
- Respect `prefers-reduced-motion`.
- ThemeToggle is allowed as a Vue component because it owns real browser state.

---

### Task 1: Baseline Verification

**Files:**
- Read: `site/package.json`
- Read: `site/uno.config.ts`
- Read: `site/src/layouts/Layout.astro`
- Read: `site/src/components/Header.astro`

- [ ] **Step 1: Check working tree**

Run from `11408-vault/`:

```powershell
git status --short
```

Expected: unrelated changes may exist. Do not revert user work.

- [ ] **Step 2: Confirm Vue integration exists**

Run from `11408-vault/site`:

```powershell
pnpm list @astrojs/vue vue --depth 0
```

Expected: both packages are installed.

- [ ] **Step 3: Run baseline check**

Run from `11408-vault/site`:

```powershell
pnpm check
```

Expected: no Astro type errors.

- [ ] **Step 4: Run baseline build**

Run from `11408-vault/site`:

```powershell
pnpm build
```

Expected: build completes.

---

### Task 2: Convert Semantic Colors To CSS Variables

**Files:**
- Modify: `site/uno.config.ts`

- [ ] **Step 1: Preserve Wind3 preset stack**

Ensure this remains true:

```ts
presets: [presetWind3(), presetTypography<PresetWind3Theme>()],
```

Do not introduce:

```ts
presetUno({ dark: 'class' })
```

- [ ] **Step 2: Convert existing semantic tokens to CSS variable colors**

In `theme.colors`, replace fixed hex values with RGB CSS variables:

```ts
colors: {
  ink: 'rgb(var(--c-ink) / <alpha-value>)',
  muted: 'rgb(var(--c-muted) / <alpha-value>)',
  faint: 'rgb(var(--c-faint) / <alpha-value>)',
  line: 'rgb(var(--c-line) / <alpha-value>)',
  canvas: 'rgb(var(--c-canvas) / <alpha-value>)',
  surface: 'rgb(var(--c-surface) / <alpha-value>)',
  accent: 'rgb(var(--c-accent) / <alpha-value>)',
}
```

Keep existing token names (`ink`, `muted`, `faint`, `line`, `canvas`, `accent`) so current classes keep working.

Add only `surface` for replacing hardcoded white backgrounds in layout surfaces.

- [ ] **Step 3: Preserve precise interaction shortcut**

Ensure:

```ts
't-link': 'motion-safe:transition-[color,background-color,border-color,opacity] duration-150 ease-out',
```

Do not change it to:

```ts
transition-all
```

- [ ] **Step 4: Run check**

Run from `11408-vault/site`:

```powershell
pnpm check
```

Expected: no errors.

---

### Task 3: Add Theme Variables And Bootstrap Script

**Files:**
- Modify: `site/src/layouts/Layout.astro`

- [ ] **Step 1: Add no-flash theme bootstrap in `<head>`**

Inside `<head>`, before or immediately after `<BaseHead />`, add an inline script:

```astro
<script is:inline>
  (() => {
    const storageKey = '11408-theme';
    const stored = localStorage.getItem(storageKey);
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = stored === 'dark' || stored === 'light'
      ? stored
      : prefersDark
        ? 'dark'
        : 'light';

    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.documentElement.dataset.theme = theme;
  })();
</script>
```

This prevents a flash of the wrong theme before Vue hydrates.

- [ ] **Step 2: Replace body hardcoded white with semantic surface**

Find body class:

```astro
<body class="flex min-h-screen flex-col bg-white font-sans text-ink antialiased selection:bg-accent/15">
```

Replace with:

```astro
<body class="flex min-h-screen flex-col bg-surface font-sans text-ink antialiased selection:bg-accent/15">
```

- [ ] **Step 3: Add CSS variables**

Inside the existing `<style is:global>` block, update `:root` and add `html.dark`:

```css
  :root {
    color-scheme: light;
    --c-ink: 36 41 47;
    --c-muted: 87 96 106;
    --c-faint: 140 149 159;
    --c-line: 208 215 222;
    --c-canvas: 246 248 250;
    --c-surface: 255 255 255;
    --c-accent: 9 105 218;
  }

  html.dark {
    color-scheme: dark;
    --c-ink: 230 237 243;
    --c-muted: 139 148 158;
    --c-faint: 110 118 129;
    --c-line: 48 54 61;
    --c-canvas: 22 27 34;
    --c-surface: 13 17 23;
    --c-accent: 88 166 255;
  }
```

GitHub-inspired dark colors are intentionally muted. Do not use pure black for the surface.

- [ ] **Step 4: Update global theme transition**

Add:

```css
  html {
    background: rgb(var(--c-surface));
  }

  body {
    background: rgb(var(--c-surface));
  }
```

Do not add global transition on all elements. Theme animation will be handled by View Transitions.

- [ ] **Step 5: Run check**

Run from `11408-vault/site`:

```powershell
pnpm check
```

Expected: no errors.

---

### Task 4: Add ThemeToggle Vue Island

**Files:**
- Create: `site/src/components/ThemeToggle.vue`

- [ ] **Step 1: Create `ThemeToggle.vue`**

Create `site/src/components/ThemeToggle.vue`:

```vue
<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

const STORAGE_KEY = '11408-theme';

type Theme = 'light' | 'dark';

const mounted = ref(false);
const theme = ref<Theme>('light');

const isDark = computed(() => theme.value === 'dark');
const label = computed(() => (isDark.value ? 'Switch to light mode' : 'Switch to dark mode'));

onMounted(() => {
  theme.value = getInitialTheme();
  applyTheme(theme.value);
  mounted.value = true;

  window.addEventListener('storage', (event) => {
    if (event.key !== STORAGE_KEY) return;
    theme.value = event.newValue === 'dark' ? 'dark' : 'light';
    applyTheme(theme.value);
  });
});

async function toggleTheme(event: MouseEvent) {
  const next = isDark.value ? 'light' : 'dark';
  const x = event.clientX;
  const y = event.clientY;

  if (shouldReduceMotion() || !document.startViewTransition) {
    setTheme(next);
    return;
  }

  const transition = document.startViewTransition(() => {
    setTheme(next);
  });

  await transition.ready;

  const endRadius = Math.hypot(
    Math.max(x, window.innerWidth - x),
    Math.max(y, window.innerHeight - y),
  );

  document.documentElement.animate(
    {
      clipPath: [
        `circle(0px at ${x}px ${y}px)`,
        `circle(${endRadius}px at ${x}px ${y}px)`,
      ],
    },
    {
      duration: 420,
      easing: 'cubic-bezier(0.22, 1, 0.36, 1)',
      pseudoElement: '::view-transition-new(root)',
    },
  );
}

function setTheme(next: Theme) {
  theme.value = next;
  localStorage.setItem(STORAGE_KEY, next);
  applyTheme(next);
}

function applyTheme(next: Theme) {
  document.documentElement.classList.toggle('dark', next === 'dark');
  document.documentElement.dataset.theme = next;
}

function getInitialTheme(): Theme {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === 'dark' || stored === 'light') return stored;

  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function shouldReduceMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}
</script>

<template>
  <button
    type="button"
    class="t-link inline-flex min-h-9 min-w-9 items-center justify-center text-faint hover:text-ink"
    :aria-label="label"
    :title="label"
    :data-mounted="mounted ? 'true' : 'false'"
    @click="toggleTheme"
  >
    <svg
      v-if="isDark"
      aria-hidden="true"
      class="size-3.5"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-width="1.5"
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2" />
      <path d="M12 20v2" />
      <path d="m4.93 4.93 1.41 1.41" />
      <path d="m17.66 17.66 1.41 1.41" />
      <path d="M2 12h2" />
      <path d="M20 12h2" />
      <path d="m6.34 17.66-1.41 1.41" />
      <path d="m19.07 4.93-1.41 1.41" />
    </svg>

    <svg
      v-else
      aria-hidden="true"
      class="size-3.5"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      stroke-linecap="round"
      stroke-linejoin="round"
      stroke-width="1.5"
    >
      <path d="M12 3a6 6 0 0 0 9 7.5A9 9 0 1 1 12 3Z" />
    </svg>
  </button>
</template>
```

This component uses inline Lucide-style SVG. Do not add an icon package for this.

- [ ] **Step 2: Run check**

Run from `11408-vault/site`:

```powershell
pnpm check
```

Expected: no Vue or TypeScript errors.

---

### Task 5: Mount ThemeToggle In Header

**Files:**
- Modify: `site/src/components/Header.astro`

- [ ] **Step 1: Import component**

Add:

```astro
import ThemeToggle from './ThemeToggle.vue';
```

- [ ] **Step 2: Render in nav**

Add the toggle near the right side of the nav, after existing nav links:

```astro
<ThemeToggle client:load />
```

Keep it inside the header nav controls, not inside a card or separate panel.

- [ ] **Step 3: Preserve touch target**

The button must keep at least:

```txt
min-h-9 min-w-9
```

If mobile QA shows it feels too small, raise to:

```txt
min-h-10 min-w-10
```

- [ ] **Step 4: Run check**

Run from `11408-vault/site`:

```powershell
pnpm check
```

Expected: no errors.

---

### Task 6: Add View Transition CSS Guardrails

**Files:**
- Modify: `site/src/layouts/Layout.astro`

- [ ] **Step 1: Disable default root blend during theme transition**

Inside `<style is:global>`, add:

```css
  ::view-transition-old(root),
  ::view-transition-new(root) {
    animation: none;
    mix-blend-mode: normal;
  }
```

This allows the ThemeToggle component to control the circular reveal with `clipPath`.

- [ ] **Step 2: Preserve reduced-motion behavior**

Ensure the existing reduced-motion block still disables transitions:

```css
  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      animation-duration: 0.01ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.01ms !important;
      scroll-behavior: auto !important;
    }

    ::view-transition-group(*),
    ::view-transition-old(*),
    ::view-transition-new(*) {
      animation: none !important;
    }
  }
```

Do not remove this accessibility guard.

- [ ] **Step 3: Run check**

Run from `11408-vault/site`:

```powershell
pnpm check
```

Expected: no errors.

---

### Task 7: Audit Hardcoded Light Colors

**Files:**
- Modify only files that directly block dark mode.
- Likely files:
  - `site/src/layouts/Layout.astro`
  - `site/src/components/Header.astro`
  - `site/src/components/Footer.astro`
  - `site/src/pages/**/*.astro`
  - `site/src/components/TagLinks.astro`

- [ ] **Step 1: Search hardcoded light surface classes**

Run from `11408-vault/`:

```powershell
rg -n "bg-white|text-white|bg-canvas|#ffffff|#f6f8fa|#24292f|#d0d7de|#8c959f|#0969da" .\site\src .\site\uno.config.ts
```

- [ ] **Step 2: Replace only true blockers**

Examples:

```txt
bg-white -> bg-surface
text-white in skip link may remain if paired with bg-ink
bg-canvas can remain because canvas becomes theme-variable-backed
text-ink can remain
border-line can remain
text-faint can remain
```

Do not churn files just to remove every old string. Make targeted changes.

- [ ] **Step 3: Fix global Markdown hardcoded colors**

If the Markdown rendering pipeline plan already added hardcoded values in `Layout.astro`, convert these to CSS variables:

```css
color: rgb(var(--c-ink));
color: rgb(var(--c-faint));
border-color: rgb(var(--c-line));
background: rgb(var(--c-canvas));
```

Keep semantic alert border colors as fixed GitHub-like colors unless contrast is poor in dark mode.

- [ ] **Step 4: Run check**

Run from `11408-vault/site`:

```powershell
pnpm check
```

Expected: no errors.

---

### Task 8: Update Markdown And Code Highlight Dark Behavior

**Files:**
- Modify: `site/astro.config.mjs`
- Modify: `site/src/layouts/Layout.astro`

- [ ] **Step 1: Keep Shiki simple unless current config already supports dual themes**

If current `astro.config.mjs` uses:

```js
shikiConfig: {
  theme: 'github-light',
}
```

Keep it for this task. Do not introduce a Shiki dual-theme refactor unless the current pipeline already has a known working dual-theme setup.

Reason: theme toggle must be shipped safely first; Shiki dual-theme can be a follow-up.

- [ ] **Step 2: Ensure prose container colors come from semantic tokens**

In `.prose-blog` global CSS, prefer:

```css
color: rgb(var(--c-ink));
border-color: rgb(var(--c-line));
background: rgb(var(--c-canvas));
```

- [ ] **Step 3: Run build**

Run from `11408-vault/site`:

```powershell
pnpm build
```

Expected: build completes.

---

### Task 9: Manual Browser Verification

**Files:**
- Verify running site.

- [ ] **Step 1: Start dev server**

Run from `11408-vault/site`:

```powershell
pnpm dev
```

- [ ] **Step 2: Verify initial theme**

Manual checks:

- If `localStorage["11408-theme"]` is absent, site follows system preference.
- If `localStorage["11408-theme"] = "dark"`, page opens dark without flashing light.
- If `localStorage["11408-theme"] = "light"`, page opens light without flashing dark.

- [ ] **Step 3: Verify toggle**

Manual checks:

- Clicking toggle switches `html.dark`.
- `html[data-theme]` becomes `dark` or `light`.
- Preference persists after reload.
- The icon changes.
- Button has accessible label.

- [ ] **Step 4: Verify animation**

Manual checks in a browser that supports View Transitions:

- Theme expands from click point with circular reveal.
- There is no page layout jump.
- No large glow or decorative animation.

Manual checks when reduced motion is enabled:

- Theme changes without circular animation.

- [ ] **Step 5: Verify navigation**

Because the site uses Astro `<ClientRouter />`, navigate between pages and confirm:

- theme persists
- toggle still works
- no hydration error appears in the console

---

### Task 10: Final Verification

**Files:**
- Verify all changed site files.

- [ ] **Step 1: Type check**

Run from `11408-vault/site`:

```powershell
pnpm check
```

Expected: no errors.

- [ ] **Step 2: Production build**

Run from `11408-vault/site`:

```powershell
pnpm build
```

Expected: build completes.

- [ ] **Step 3: Guardrail search**

Run from `11408-vault/`:

```powershell
git status --short -- views
rg -n "presetUno|transition-all|boxShadow|float" .\site\uno.config.ts .\site\src
rg -n "Container|Flex|Button|Card|TagPill|PostItem" .\site\src -S
```

Expected:

- no changes under `views/`
- no `presetUno`
- no new `transition-all`
- no floating shadow token
- no style-only components

---

## Final Report Requirements

The executing agent must report:

- files changed
- whether `presetWind3()` was preserved
- whether `ThemeToggle.vue` was added
- whether theme state persists in localStorage
- whether no-flash bootstrap was added
- whether View Transition circular reveal works
- whether reduced-motion fallback works
- whether `pnpm check` passed
- whether `pnpm build` passed

## Self-Review

- Spec coverage: plan covers class-based dark mode, theme persistence, system preference fallback, no-flash bootstrap, View Transition circular reveal, reduced-motion fallback, and UnoCSS guardrails.
- Placeholder scan: no TBD/TODO placeholders remain.
- Type consistency: all paths refer to the current `site/` Astro app and current Vue integration.
- Scope check: this plan does not change Markdown parser behavior and does not alter Talaria views.
