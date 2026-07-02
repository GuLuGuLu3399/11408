import { visit } from 'unist-util-visit';
import { getWikiIndex, normalizeKey } from './wiki-index.mjs';

const WIKILINK_RE = /!?\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g;

export default function remarkWikilinks() {
  return async function transformer(tree) {
    const index = await getWikiIndex();

    visit(tree, 'text', (node, indexInParent, parent) => {
      if (!parent || typeof indexInParent !== 'number') return;
      if (!node.value.includes('[[')) return;

      const children = splitWikilinks(node.value, index);
      if (children.length === 1 && children[0].type === 'text') return;

      parent.children.splice(indexInParent, 1, ...children);
    });
  };
}

function splitWikilinks(value, index) {
  const nodes = [];
  let lastIndex = 0;

  for (const match of value.matchAll(WIKILINK_RE)) {
    const [raw, target, alias] = match;
    const start = match.index ?? 0;

    if (start > lastIndex) {
      nodes.push({ type: 'text', value: value.slice(lastIndex, start) });
    }

    if (raw.startsWith('!')) {
      nodes.push({ type: 'text', value: raw });
    } else {
      nodes.push(createWikiNode(target.trim(), alias?.trim(), index));
    }

    lastIndex = start + raw.length;
  }

  if (lastIndex < value.length) {
    nodes.push({ type: 'text', value: value.slice(lastIndex) });
  }

  return nodes;
}

function createWikiNode(target, alias, index) {
  const href = index.get(target) || index.get(normalizeKey(target));
  const label = alias || target;

  if (href) {
    return {
      type: 'link',
      url: href,
      title: null,
      data: {
        hProperties: {
          className: ['internal-link'],
        },
      },
      children: [{ type: 'text', value: label }],
    };
  }

  return {
    type: 'html',
    value: `<span class="wiki-link-missing">[[${escapeHtml(label)}]]</span>`,
  };
}

function escapeHtml(value) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}
