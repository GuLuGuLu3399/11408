import type { APIRoute } from 'astro';
import { getCollection } from 'astro:content';
import { getPublicNotes, getNoteTitle, getNoteSubject, getNoteKind, notePath } from '../lib/vault-notes';

// 搜索索引端点:GET /search.json。
// 静态构建期一次性生成,缓存于模块级。每条:{ title, url, breadcrumb }。
interface SearchEntry {
  title: string;
  url: string;
  breadcrumb: string;
}

let cached: SearchEntry[] | null = null;

async function buildIndex(): Promise<SearchEntry[]> {
  if (cached) return cached;
  const notes = getPublicNotes(await getCollection('notes'));
  cached = notes.map((note) => {
    const subject = getNoteSubject(note);
    const kind = getNoteKind(note);
    // breadcrumb = subject + " > " + kind,例如「计算机网络 > 408笔记」。
    const breadcrumb = `${subject} > ${kind}`;
    return {
      title: getNoteTitle(note),
      url: notePath(note.id),
      breadcrumb,
    };
  });
  return cached;
}

export const GET: APIRoute = async () => {
  const body = await buildIndex();
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=3600',
    },
  });
};
