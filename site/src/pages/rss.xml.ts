import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import { siteConfig } from '../site.config';
import { byRecentDesc, getNoteTitle, getPublicNotes, notePath } from '../lib/vault-notes';

export async function GET(context: { site: URL }) {
  const posts = getPublicNotes(await getCollection('notes')).sort(byRecentDesc);

  return rss({
    title: siteConfig.title,
    description: siteConfig.description,
    site: context.site,
    items: posts.map((post) => {
      const date = post.data.updated_at ?? post.data.created_at ?? post.data.pubDate;
      return {
        title: getNoteTitle(post),
        pubDate: date ?? new Date(0),
        link: notePath(post.id),
      };
    }),
  });
}
