import { visit } from 'unist-util-visit';

// 将 ```mermaid 围栏代码块转为 <div class="mermaid"> 容器,
// 在 Shiki 高亮之前拦截 —— Shiki 只处理 <pre><code>,不会触碰这个 div,
// 从而避免被当作普通代码高亮(也不会带 astro-code 的默认主题边框)。
// 源码以 data-mermaid-source (encodeURIComponent) 携带,MermaidLoader 客户端解码渲染;
// 转义后的源码同时作为 JS 失败时的可见兜底。
export default function remarkMermaidBlock() {
  return (tree) => {
    visit(tree, 'code', (node, index, parent) => {
      if (node.lang !== 'mermaid' || !parent || typeof index !== 'number') return;
      const source = node.value ?? '';
      parent.children[index] = {
        type: 'html',
        value: `<div class="mermaid" data-mermaid-source="${encodeURIComponent(source)}">${escapeHtml(source)}</div>`,
      };
    });
  };
}

function escapeHtml(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;');
}
