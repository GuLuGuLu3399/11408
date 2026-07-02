import { readdir, readFile } from 'node:fs/promises';
import { join, relative, resolve, sep } from 'node:path';

const DOCS_DIR = resolve(process.cwd(), '../docs');

let cachedIndex;

export async function getWikiIndex() {
  if (cachedIndex) return cachedIndex;

  const files = await readMarkdownFiles(DOCS_DIR);
  const entries = await Promise.all(files.map(readEntry));
  const byKey = new Map();

  for (const entry of entries) {
    addKey(byKey, entry.title, entry.href);
    addKey(byKey, entry.stem, entry.href);
    addKey(byKey, normalizeKey(entry.title), entry.href);
    addKey(byKey, normalizeKey(entry.stem), entry.href);
  }

  cachedIndex = byKey;
  return cachedIndex;
}

async function readMarkdownFiles(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];

  for (const entry of entries) {
    const fullPath = join(dir, entry.name);

    if (entry.isDirectory()) {
      files.push(...await readMarkdownFiles(fullPath));
      continue;
    }

    if (entry.isFile() && entry.name.endsWith('.md')) {
      files.push(fullPath);
    }
  }

  return files;
}

// 与 Astro 静态路径生成保持一致的 slug 规则。
// 页面实际 URL 是 slugify 后的 id（小写 + 空格→连字符 + 去标点），
// 而 readdir 返回原始文件名（可能含大写/空格）。href 必须同样 slugify，
// 否则在大小写敏感的部署环境（Linux/Vercel）上会 404。
function slugifySegment(value) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[\s_]+/g, '-')
    .replace(/[^\w一-龥-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '');
}

async function readEntry(file) {
  const source = await readFile(file, 'utf8');
  const title = readFrontmatterTitle(source);
  const id = relative(DOCS_DIR, file).split(sep).join('/').replace(/\.md$/, '');
  const stem = id.split('/').at(-1) || id;
  const slug = id.split('/').map(slugifySegment).join('/');

  return {
    title: title || stem,
    stem,
    href: `/notes/${slug}/`,
  };
}

function readFrontmatterTitle(source) {
  const match = source.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (!match) return '';

  const title = match[1].match(/^title:\s*["']?(.+?)["']?\s*$/m);
  return title?.[1]?.trim() || '';
}

function addKey(map, key, href) {
  const value = key?.trim();
  if (!value || map.has(value)) return;
  map.set(value, href);
}

export function normalizeKey(value) {
  return value.trim().toLowerCase();
}
