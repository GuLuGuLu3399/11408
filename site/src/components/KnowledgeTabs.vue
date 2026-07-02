<script setup lang="ts">
defineProps<{
  categories: {
    name: string;
    count: number;
    items: { title: string; url: string }[];
  }[];
}>();

import { ref } from 'vue';

const activeIndex = ref(0);
const tabRefs = ref<HTMLElement[]>([]);

// 循环切换:ArrowLeft/Right 在 tab 间无缝循环(roving tabindex A11y)。
const handleKeyDown = (e: KeyboardEvent) => {
  const tabs = tabRefs.value;
  const max = tabs.length - 1;
  if (max < 0) return;

  if (e.key === 'ArrowRight') {
    e.preventDefault();
    activeIndex.value = activeIndex.value === max ? 0 : activeIndex.value + 1;
    tabs[activeIndex.value]?.focus();
  } else if (e.key === 'ArrowLeft') {
    e.preventDefault();
    activeIndex.value = activeIndex.value === 0 ? max : activeIndex.value - 1;
    tabs[activeIndex.value]?.focus();
  }
};
</script>

<template>
  <div class="w-full">
    <div
      class="hide-scrollbar flex overflow-x-auto border-b border-line"
      role="tablist"
      aria-orientation="horizontal"
      @keydown="handleKeyDown"
    >
      <button
        v-for="(cat, index) in categories"
        :key="cat.name"
        ref="tabRefs"
        role="tab"
        :aria-selected="activeIndex === index"
        :tabindex="activeIndex === index ? 0 : -1"
        @click="activeIndex = index"
        class="relative mr-5 shrink-0 border-none bg-transparent px-1 py-4 text-sm font-medium tracking-wide outline-none motion-safe:transition-[color,opacity,transform] duration-150 ease-out active:scale-95 sm:mr-8"
        :class="activeIndex === index ? 'text-ink' : 'text-muted hover:text-ink'"
      >
        {{ cat.name }}
        <span class="ml-1.5 font-mono text-xs text-faint">{{ cat.count }}</span>
        <!-- 选中态:2px 主色底线,无滑块动画。 -->
        <div
          v-if="activeIndex === index"
          class="absolute bottom-0 left-0 h-[2px] w-full rounded-t-sm bg-accent"
        ></div>
      </button>
    </div>

    <div class="mt-8">
      <transition name="fade-slide" mode="out-in">
        <div :key="activeIndex" role="tabpanel" class="focus:outline-none" tabindex="0">
          <ul class="m-0 list-none space-y-6 p-0">
            <li v-for="item in categories[activeIndex].items" :key="item.url">
              <a
                :href="item.url"
                class="group flex min-w-0 items-start gap-2 py-1 no-underline outline-none"
              >
                <i class="i-lucide-file-text size-4 shrink-0 text-faint group-hover:text-accent motion-safe:transition-colors duration-150 ease-out" aria-hidden="true"></i>
                <h3
                  class="min-w-0 break-words text-base font-semibold tracking-tight text-ink group-hover:text-accent motion-safe:transition-colors duration-150 ease-out"
                >
                  {{ item.title }}
                </h3>
              </a>
            </li>
          </ul>
        </div>
      </transition>
    </div>
  </div>
</template>

<style scoped>
/* 隐藏原生滚动条,保持视觉纯净。 */
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

/* 内容切换:150ms 褪色 + 4px 纵向浮动;reduced-motion 下由全局 CSS 强制即时。 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.15s ease-out;
}
.fade-slide-enter-from {
  opacity: 0;
  transform: translateY(4px);
}
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
