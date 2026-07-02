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

// views/ 相对于 site/ 工作目录(Astro 在 site/ 下执行 build)。
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
      const parsed = (await YAML.parse(source)) as Partial<TalariaView>;
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
  if (filter.op === 'not_contains')
    return !String(value ?? '').includes(String(filter.value ?? ''));
  if (filter.op === 'is_empty') return value == null || value === '';
  if (filter.op === 'is_not_empty') return value != null && value !== '';

  return false;
}

export function getFieldValue(note: NoteEntry, field: string): unknown {
  // Talaria 的 title 字段对应文件名(无扩展名),不是 frontmatter title。
  if (field === 'title') {
    const filename = note.id.split('/').at(-1) ?? note.id;
    return filename.replace(/\.md$/, '');
  }
  if (field === 'body') return '';
  return note.data[field as keyof typeof note.data];
}
