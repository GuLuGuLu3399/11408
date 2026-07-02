import { matchView, readTalariaViews, type ViewGroup } from './talaria-views';
import {
  getNoteKind,
  getNoteSubject,
  getNoteTags,
  getNoteTitle,
  getPublicNotes,
  sortNotesByTitle,
  type NoteEntry,
} from './vault-notes';

export type TopicGroup = {
  id: string;
  name: string;
  slug: string;
  source: 'talaria-view' | 'derived';
  notes: NoteEntry[];
};

export type TagGroup = {
  tag: string;
  slug: string;
  notes: NoteEntry[];
};

// ===== 两级知识拓扑:domain → subject → notes =====

export type KnowledgeSubject = {
  id: string;
  name: string;
  slug: string;
  notes: NoteEntry[];
};

export type KnowledgeDomain = {
  id: string;
  name: string;
  order: number;
  subjects: KnowledgeSubject[];
  count: number;
};

// 紧凑型:首页 Knowledge Map 入口只需要 domain 名与计数。
export type DomainSummary = {
  id: string;
  name: string;
  order: number;
  count: number;
};

// type → domain 映射(顺序即陈列顺序)。
const DOMAIN_ORDER: Array<{ type: string; domain: string }> = [
  { type: '408笔记', domain: '408 核心专业课' },
  { type: '考研数学', domain: '考研数学' },
  { type: '错题日记', domain: '错题复盘' },
  { type: '周报', domain: '复习节奏' },
  { type: '心态日记', domain: '心态记录' },
  { type: '综合专题', domain: '综合专题' },
];

const TYPE_TO_DOMAIN = new Map(DOMAIN_ORDER.map((entry) => [entry.type, entry.domain]));
const DOMAIN_RANK = new Map(DOMAIN_ORDER.map((entry, index) => [entry.domain, index]));
const UNCATEGIZED_DOMAIN = '未分类';

function domainOf(note: NoteEntry): string {
  const type = note.data.type?.trim();
  if (type && TYPE_TO_DOMAIN.has(type)) return TYPE_TO_DOMAIN.get(type)!;
  // Note 类型与未知 type 归到未分类,仍可浏览。
  return UNCATEGIZED_DOMAIN;
}

// 标签/主题的 URL slug:保留中文与字母数字,折叠标点到连字符。
export function slugifyTaxonomy(value: string): string {
  const normalized = value
    .trim()
    .toLowerCase()
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .replace(/[^a-z0-9一-鿿]+/g, '-')
    .replace(/^-+|-+$/g, '');

  return normalized || 'uncategorized';
}

// 主题分组优先级:Talaria views(策展) → frontmatter type+subject 推导(兜底)。
export async function buildTopicGroups(notes: NoteEntry[]): Promise<TopicGroup[]> {
  const publicNotes = getPublicNotes(notes);
  const views = await readTalariaViews();

  const viewGroups = views
    .map<ViewGroup>((view) => ({
      id: view.id,
      name: view.name,
      slug: slugifyTaxonomy(view.id),
      notes: sortNotesByTitle(publicNotes.filter((note) => matchView(note, view))),
    }))
    .filter((group) => group.notes.length > 0)
    .map<TopicGroup>((group) => ({
      ...group,
      source: 'talaria-view',
    }));

  // 已被任何 view 命中的笔记不再进入推导分组,避免重复陈列。
  const coveredNoteIds = new Set(viewGroups.flatMap((group) => group.notes.map((note) => note.id)));
  const uncoveredNotes = publicNotes.filter((note) => !coveredNoteIds.has(note.id));
  const derivedGroups = groupNotesByDerivedTopic(uncoveredNotes);

  return [...viewGroups, ...derivedGroups].sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
}

// subject 二级分类:优先 frontmatter subject,其次按 type 推导默认值。
function subjectOf(note: NoteEntry): string {
  const subject = note.data.subject?.trim();
  if (subject) return subject;
  return getNoteSubject(note);
}

// 完整两级拓扑:domain → subject → notes,Talaria views 折叠进对应 domain。
export function buildDomainTopology(notes: NoteEntry[]): KnowledgeDomain[] {
  const publicNotes = getPublicNotes(notes);

  // 先按 domain → subject 把每篇笔记归类。
  const tree = new Map<string, Map<string, NoteEntry[]>>();

  for (const note of publicNotes) {
    const domainName = domainOf(note);
    const subjectName = subjectOf(note);
    if (!tree.has(domainName)) tree.set(domainName, new Map());
    const subjects = tree.get(domainName)!;
    if (!subjects.has(subjectName)) subjects.set(subjectName, []);
    subjects.get(subjectName)!.push(note);
  }

  const domains: KnowledgeDomain[] = [...tree.entries()].map(([domainName, subjectsMap]) => {
    const subjects: KnowledgeSubject[] = [...subjectsMap.entries()]
      .map(([subjectName, subjectNotes]) => ({
        id: slugifyTaxonomy(subjectName),
        name: subjectName,
        slug: slugifyTaxonomy(subjectName),
        notes: sortNotesByTitle(subjectNotes),
      }))
      .sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));

    return {
      id: slugifyTaxonomy(domainName),
      name: domainName,
      order: DOMAIN_RANK.get(domainName) ?? DOMAIN_ORDER.length,
      subjects,
      count: subjects.reduce((sum, subject) => sum + subject.notes.length, 0),
    };
  });

  return domains.sort((a, b) => a.order - b.order);
}

// 首页 Knowledge Map 入口:每个 domain 一行 + 总计数。
export function buildKnowledgeMap(notes: NoteEntry[]): DomainSummary[] {
  return buildDomainTopology(notes).map(({ id, name, order, count }) => ({
    id,
    name,
    order,
    count,
  }));
}

export function groupNotesByDerivedTopic(notes: NoteEntry[]): TopicGroup[] {
  const groups = notes.reduce<Map<string, TopicGroup>>((map, note) => {
    const kind = getNoteKind(note);
    const subject = getNoteSubject(note);
    const name = subject === kind ? kind : `${kind} · ${subject}`;
    const slug = slugifyTaxonomy(name);
    const existing = map.get(slug);

    if (existing) {
      existing.notes.push(note);
      return map;
    }

    map.set(slug, {
      id: slug,
      name,
      slug,
      source: 'derived',
      notes: [note],
    });

    return map;
  }, new Map());

  return [...groups.values()].map((group) => ({
    ...group,
    notes: sortNotesByTitle(group.notes),
  }));
}

// 标签来源:手动 tags + type + subject + status(去重后按拼音排序)。
export function buildTagGroups(notes: NoteEntry[]): TagGroup[] {
  const publicNotes = getPublicNotes(notes);
  const groups = publicNotes.reduce<Map<string, TagGroup>>((map, note) => {
    for (const tag of getNoteTags(note)) {
      const slug = slugifyTaxonomy(tag);
      const existing = map.get(slug);

      if (existing) {
        existing.notes.push(note);
        continue;
      }

      map.set(slug, {
        tag,
        slug,
        notes: [note],
      });
    }

    return map;
  }, new Map());

  return [...groups.values()]
    .map((group) => ({
      ...group,
      notes: sortNotesByTitle(group.notes),
    }))
    .sort((a, b) => a.tag.localeCompare(b.tag, 'zh-CN'));
}

export { getNoteTags, getNoteTitle, getPublicNotes, sortNotesByTitle };
