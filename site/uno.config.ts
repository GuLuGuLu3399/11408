import {
  defineConfig,
  presetWind3,
  presetTypography,
  presetIcons,
  transformerDirectives,
  transformerVariantGroup,
  type PresetWind3Theme,
} from 'unocss';

export default defineConfig<PresetWind3Theme>({
  presets: [
    presetWind3({ dark: 'class' }),
    presetTypography<PresetWind3Theme>(),
    // pnpm 隔离下,presetIcons 的自动 loader 找不到 @iconify-json/lucide;
    // 显式注入 collection 绕过自动解析。
    presetIcons({
      scale: 1.2,
      warn: true,
      collections: {
        lucide: () => import('@iconify-json/lucide/icons.json').then((m) => m.default),
      },
    }),
  ],
  transformers: [transformerDirectives(), transformerVariantGroup()],

  theme: {
    colors: {
      ink: 'rgb(var(--c-ink) / <alpha-value>)',
      muted: 'rgb(var(--c-muted) / <alpha-value>)',
      faint: 'rgb(var(--c-faint) / <alpha-value>)',
      line: 'rgb(var(--c-line) / <alpha-value>)',
      canvas: 'rgb(var(--c-canvas) / <alpha-value>)',
      surface: 'rgb(var(--c-surface) / <alpha-value>)',
      accent: 'rgb(var(--c-accent) / <alpha-value>)',
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
    // 中心内容容器:Header / Main / Footer 共用,锁定 max-w-2xl + 移动端安全内边距。
    'container-page': 'mx-auto w-full max-w-2xl px-4',
    // 交互元素过渡底线:仅过渡颜色相关属性,禁用全局 transition-all(motion-safe 守护 a11y)。
    't-link': 'motion-safe:transition-[color,background-color,border-color,opacity] duration-150 ease-out',
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
      'prose-pre:rounded-md prose-pre:overflow-x-auto prose-pre:shadow-[0_1px_2px_0_rgb(0_0_0/0.04)]',
      'prose-blockquote:not-italic',
      'prose-blockquote:border-l-line',
      'prose-blockquote:text-muted',
      'prose-hr:border-line/70',
    ].join(' '),
  },
});
