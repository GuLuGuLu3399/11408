// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import vue from '@astrojs/vue';
import UnoCSS from '@unocss/astro';
import { unified } from '@astrojs/markdown-remark';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import remarkGithubAlerts from './src/lib/markdown/remark-github-alerts.mjs';
import remarkWikilinks from './src/lib/markdown/remark-wikilinks.mjs';
import remarkMermaidBlock from './src/lib/markdown/remark-mermaid-block.mjs';

export default defineConfig({
  site: 'https://11408.vercel.app',
  compressHTML: true,
  prefetch: {
    prefetchAll: true,
    defaultStrategy: 'hover',
  },
  markdown: {
    syntaxHighlight: 'shiki',
    shikiConfig: {
      themes: {
        light: 'github-light',
        dark: 'github-dark',
      },
      defaultColor: false,
      wrap: false,
    },
    processor: unified({
      remarkPlugins: [
        remarkMermaidBlock,
        remarkMath,
        remarkGithubAlerts,
        remarkWikilinks,
      ],
      rehypePlugins: [
        rehypeKatex,
      ],
    }),
  },
  integrations: [
    sitemap(),
    vue(),
    UnoCSS(),
  ],
});
