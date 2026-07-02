import { readdir, readFile } from 'node:fs/promises';
import { join, relative, resolve, sep } from 'node:path';
import { slugifyPath } from './slugify.mjs';

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

// slug 规则在 ./slugify.mjs（SSOT），与 Astro 内容集合的 generateId 共用同一函数。
async function readEntry(file) {
  const source = await readFile(file, 'utf8');
  const title = readFrontmatterTitle(source);
  const id = relative(DOCS_DIR, file).split(sep).join('/').replace(/\.md$/, '');
  const stem = id.split('/').at(-1) || id;
  const slug = slugifyPath(id);

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
