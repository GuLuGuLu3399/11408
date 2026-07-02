<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

const STORAGE_KEY = '11408-theme';

type Theme = 'light' | 'dark';

const theme = ref<Theme>('light');

const isDark = computed(() => theme.value === 'dark');
const label = computed(() => (isDark.value ? 'Switch to light mode' : 'Switch to dark mode'));

onMounted(() => {
  theme.value = getInitialTheme();
  applyTheme(theme.value);

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
  // 通知 MermaidLoader 等订阅者:主题已变更,按新主题重渲染。
  window.dispatchEvent(new CustomEvent('theme-change', { detail: { theme: next } }));
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
  <!-- 去壳:bg-transparent border-none 让图标完全悬浮在 Header 毛玻璃背景上。
       图标显示走纯 CSS(dark:block / dark:hidden),无 v-if、无闪烁;JS 只负责
       点击 / localStorage / View Transition / theme-change 事件。 -->
  <button
    type="button"
    class="flex min-h-11 min-w-11 cursor-pointer items-center justify-center border-none bg-transparent p-2 text-muted outline-none hover:text-ink motion-safe:transition-[color,opacity,transform] duration-150 ease-out active:scale-95"
    :aria-label="label"
    :title="label"
    @click="toggleTheme"
  >
    <i class="i-lucide-moon size-4 dark:hidden" aria-hidden="true"></i>
    <i class="i-lucide-sun size-4 hidden dark:block" aria-hidden="true"></i>
  </button>
</template>
