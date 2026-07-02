<script setup lang="ts">
// 搜索命令面板:挂在 Layout 层(client:load),穿越 ClientRouter 导航。
// 触发:Header 派发的 open-search 事件 + 全局 ⌘K / Ctrl+K。
// 数据源:/search.json(首次打开时 fetch 并缓存);本地 title+breadcrumb 子串过滤。
import { computed, nextTick, onMounted, ref, watch } from 'vue';

interface SearchEntry {
  title: string;
  url: string;
  breadcrumb: string;
}

const open = ref(false);
const query = ref('');
const results = ref<SearchEntry[]>([]);
const activeIndex = ref(0);
const inputEl = ref<HTMLInputElement | null>(null);

let cache: SearchEntry[] | null = null;
let prevOverflow = '';

// 读取搜索索引(惰性 + 缓存)。
async function ensureIndex(): Promise<SearchEntry[]> {
  if (cache) return cache;
  try {
    const res = await fetch('/search.json');
    if (!res.ok) throw new Error(`search.json ${res.status}`);
    cache = (await res.json()) as SearchEntry[];
  } catch (err) {
    console.warn('Search index fetch failed', err);
    cache = [];
  }
  return cache;
}

// 本地过滤:title 子串优先于 breadcrumb 子串,大小写不敏感。
function search(entries: SearchEntry[], q: string): SearchEntry[] {
  const needle = q.trim().toLowerCase();
  if (!needle) return [];
  const titleHits: SearchEntry[] = [];
  const crumbHits: SearchEntry[] = [];
  for (const e of entries) {
    const t = e.title.toLowerCase();
    const b = e.breadcrumb.toLowerCase();
    if (t.includes(needle)) titleHits.push(e);
    else if (b.includes(needle)) crumbHits.push(e);
  }
  return [...titleHits, ...crumbHits].slice(0, 40);
}

const hasQuery = computed(() => query.value.trim().length > 0);

watch(query, (q) => {
  if (!cache) return;
  results.value = search(cache, q);
  activeIndex.value = 0;
});

function openModal() {
  if (open.value) return;
  open.value = true;
  prevOverflow = document.body.style.overflow;
  document.body.style.overflow = 'hidden';
  nextTick(() => {
    inputEl.value?.focus();
    if (!cache) void ensureIndex();
  });
}

function closeModal() {
  if (!open.value) return;
  open.value = false;
  query.value = '';
  results.value = [];
  activeIndex.value = 0;
  document.body.style.overflow = prevOverflow;
}

function onBackdropClick(e: MouseEvent) {
  if (e.target === e.currentTarget) closeModal();
}

function moveSelection(delta: number) {
  if (results.value.length === 0) return;
  const n = results.value.length;
  activeIndex.value = (activeIndex.value + delta + n) % n;
  // 让选中行保持在可视区内。
  const el = document.querySelector<HTMLElement>(`[data-search-row="${activeIndex.value}"]`);
  el?.scrollIntoView({ block: 'nearest' });
}

function onKeydown(e: KeyboardEvent) {
  if (!open.value) return;
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    moveSelection(1);
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    moveSelection(-1);
  } else if (e.key === 'Enter') {
    if (results.value[activeIndex.value]) {
      e.preventDefault();
      navigate(results.value[activeIndex.value]);
    }
  } else if (e.key === 'Escape') {
    e.preventDefault();
    closeModal();
  }
}

function navigate(entry: SearchEntry) {
  closeModal();
  // 用 ClientRouter 友好的跳转方式。
  window.location.href = entry.url;
}

// 高亮匹配片段:<mark> 包裹命中子串(yellow 字面量,无 token)。
function highlight(title: string): string {
  const needle = query.value.trim();
  if (!needle) return escapeHtml(title);
  const idx = title.toLowerCase().indexOf(needle.toLowerCase());
  if (idx < 0) return escapeHtml(title);
  const before = escapeHtml(title.slice(0, idx));
  const match = escapeHtml(title.slice(idx, idx + needle.length));
  const after = escapeHtml(title.slice(idx + needle.length));
  return `${before}<mark class="bg-yellow-100 dark:bg-yellow-900 text-inherit rounded-sm">${match}</mark>${after}`;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

onMounted(() => {
  window.addEventListener('open-search', openModal);
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      open.value ? closeModal() : openModal();
    }
  });
  document.addEventListener('keydown', onKeydown);
});
</script>

<template>
  <!-- 遮罩:半透明 + 毛玻璃;面板:无阴影、hairline 边框、surface 背景。 -->
  <div
    v-if="open"
    class="fixed inset-0 z-[100] backdrop-blur-md bg-surface/80 flex justify-center"
    @click="onBackdropClick"
  >
    <div class="max-w-lg w-full mx-4 mt-[20vh] self-start rounded-lg border border-line bg-surface overflow-hidden">
      <!-- 输入行:前置搜索图标 + 透明背景输入框。 -->
      <div class="flex items-center gap-2 px-4 py-3 border-b border-line">
        <i class="i-lucide-search size-4 shrink-0 text-faint" aria-hidden="true"></i>
        <input
          ref="inputEl"
          v-model="query"
          type="text"
          placeholder="搜索笔记…"
          class="w-full bg-transparent outline-none text-ink placeholder:text-faint text-sm"
          autocomplete="off"
          spellcheck="false"
        />
        <kbd class="font-mono text-xs text-faint shrink-0">ESC</kbd>
      </div>
      <!-- 结果列表:最大高度内滚动,无分割线。 -->
      <ul v-if="results.length > 0" class="max-h-80 overflow-y-auto m-0 p-0 list-none">
        <li v-for="(entry, i) in results" :key="entry.url" class="m-0">
          <a
            :href="entry.url"
            :data-search-row="i"
            class="block px-4 py-2 hover:bg-canvas/55"
            :class="i === activeIndex ? 'bg-canvas/55' : ''"
            @click.prevent="navigate(entry)"
          >
            <span class="font-medium text-ink text-sm" v-html="highlight(entry.title)"></span>
            <span class="text-xs text-faint ml-2">{{ entry.breadcrumb }}</span>
          </a>
        </li>
      </ul>
      <!-- 空状态:无查询时静默;查询无命中时一句淡灰提示。 -->
      <div v-else-if="hasQuery" class="px-4 py-6 text-center text-sm text-faint">
        无结果
      </div>
    </div>
  </div>
</template>
