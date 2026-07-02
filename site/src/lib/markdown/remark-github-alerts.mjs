import { visit } from 'unist-util-visit';

const ALERTS = new Map([
  ['NOTE', 'Note'],
  ['TIP', 'Tip'],
  ['IMPORTANT', 'Important'],
  ['WARNING', 'Warning'],
  ['CAUTION', 'Caution'],
]);

export default function remarkGithubAlerts() {
  return function transformer(tree) {
    visit(tree, 'blockquote', (node) => {
      const marker = getAlertMarker(node);
      if (!marker) return;

      const title = ALERTS.get(marker);
      const className = `markdown-alert markdown-alert-${marker.toLowerCase()}`;

      removeAlertMarker(node);

      node.data ||= {};
      node.data.hProperties = {
        ...(node.data.hProperties || {}),
        className,
        dataAlert: marker,
      };

      node.children.unshift({
        type: 'paragraph',
        data: {
          hProperties: {
            className: 'markdown-alert-title',
          },
        },
        children: [{ type: 'text', value: title }],
      });
    });
  };
}

function getAlertMarker(node) {
  const first = node.children[0];
  if (!first || first.type !== 'paragraph') return '';

  const firstChild = first.children?.[0];
  if (!firstChild || firstChild.type !== 'text') return '';

  const match = firstChild.value.match(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*/);
  return match?.[1] || '';
}

function removeAlertMarker(node) {
  const first = node.children[0];
  const firstChild = first?.children?.[0];
  if (!first || !firstChild || firstChild.type !== 'text') return;

  firstChild.value = firstChild.value.replace(/^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*/, '');

  if (first.children.length === 1 && firstChild.value.length === 0) {
    node.children.shift();
  }
}
