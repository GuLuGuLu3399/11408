import type { CollectionEntry } from 'astro:content';

// notes 集合的规范类型:全站唯一来源,取代旧的 utils/notes.ts。
export type NoteEntry = CollectionEntry<'notes'>;

// superpowers/ 下的文档是工作流/计划内部材料,不进入公开浏览面。
const EXCLUDED_PREFIXES = ['superpowers/'];

// 已知「类型定义」笔记的 type 标记 —— 它们是 Tolaria 的模板/分类节点,不是内容笔记。
const TYPE_MARKER = 'Type';

// 已知合法的笔记 type 值,用于推导主题分组。其余 type 回退到首层文件夹名。
const TYPE_LABELS = new Set([
  '408笔记',
  '考研数学',
  '错题日记',
  '周报',
  '综合专题',
  '心态日记',
  'Note',
]);

export function isPublicNote(note: NoteEntry): boolean {
  if (EXCLUDED_PREFIXES.some((prefix) => note.id.startsWith(prefix))) return false;
  if (note.data.type === TYPE_MARKER) return false;
  // 下划线前缀的内部草稿/自动生成文件不公开。
  if (note.id.split('/').at(-1)?.startsWith('_')) return false;
  return true;
}

export function getPublicNotes(notes: NoteEntry[]): NoteEntry[] {
  return notes.filter(isPublicNote);
}

export function getNoteTitle(note: NoteEntry): string {
  const title = note.data.title?.trim();
  if (title) return title;

  const filename = note.id.split('/').at(-1) ?? note.id;
  return filename.replace(/\.md$/, '');
}

export function getNoteKind(note: NoteEntry): string {
  const type = note.data.type?.trim();
  if (type && TYPE_LABELS.has(type)) return type;

  const folder = note.id.split('/')[0];
  return folder || 'Vault';
}

export function getNoteSubject(note: NoteEntry): string {
  const subject = note.data.subject?.trim();
  if (subject) return subject;

  const kind = getNoteKind(note);
  if (kind === '408笔记') return '408';
  if (kind === '考研数学') return '数学';
  return '未分类';
}

export function getNoteSortKey(note: NoteEntry): string {
  return getNoteTitle(note);
}

export function sortNotesByTitle(notes: NoteEntry[]): NoteEntry[] {
  return [...notes].sort((a, b) => getNoteSortKey(a).localeCompare(getNoteSortKey(b), 'zh-CN'));
}

export function getNoteTags(note: NoteEntry): string[] {
  const tags = new Set<string>();

  for (const tag of note.data.tags) {
    const value = tag.trim();
    if (value) tags.add(value);
  }

  const type = note.data.type?.trim();
  const subject = note.data.subject?.trim();
  const status = note.data.status?.trim();

  if (type && type !== TYPE_MARKER) tags.add(type);
  if (subject) tags.add(subject);
  if (status) tags.add(status);

  return [...tags].sort((a, b) => a.localeCompare(b, 'zh-CN'));
}

// 单篇笔记的规范 URL:带尾斜杠,与目录式构建产物 /notes/<id>/index.html 一致。
// 兼容 [...slug] rest 参数:id 中含 "/" 时 Astro 会正确匹配嵌套路由。
export function notePath(id: string): string {
  return `/notes/${id}/`;
}

// 安全的日期比较器:pubDate 现在是可选的,按 updated_at → created_at → pubDate → epoch 回退。
// index 列表与 rss feed 共用,避免两处漂移。
export function byRecentDesc(a: NoteEntry, b: NoteEntry): number {
  const left = a.data.updated_at ?? a.data.created_at ?? a.data.pubDate ?? new Date(0);
  const right = b.data.updated_at ?? b.data.created_at ?? b.data.pubDate ?? new Date(0);
  return right.valueOf() - left.valueOf();
}
