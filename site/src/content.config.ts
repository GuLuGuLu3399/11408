import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';
import { slugifyPath } from './lib/markdown/slugify.mjs';

// wikilink 字段(related_to / belongs_to / has)在 Vault 里既可能是单字符串也可能是列表,
// 用 union 兜底,避免对历史笔记做强制迁移。
const wikilinkValue = z
  .union([z.string(), z.array(z.string())])
  .nullable()
  .optional();

const notes = defineCollection({
  loader: glob({
    base: '../docs',
    pattern: '**/*.md',
    // SSOT: 页面 id（即 URL slug）与 wiki-index 的 href 共用 slugifyPath，
    // 避免大小写/空格在 Windows(不敏感)↔Linux(严格) 间引发断链。
    generateId: ({ entry }) => slugifyPath(entry.replace(/\.md$/, '')),
  }),
  schema: z
    .object({
      title: z.string().nullable().optional(),
      pubDate: z.coerce.date().nullable().optional(),
      category: z.string().nullable().optional(),
      tags: z.array(z.string()).default([]),
      type: z.string().nullable().optional(),
      subject: z.string().nullable().optional(),
      status: z.string().nullable().optional(),
      related_to: wikilinkValue,
      belongs_to: wikilinkValue,
      has: wikilinkValue,
      uuid: z.string().optional(),
      created_at: z.coerce.date().optional(),
      updated_at: z.coerce.date().optional(),
      _organized: z.boolean().optional(),
    })
    .loose(),
});

export const collections = { notes };
