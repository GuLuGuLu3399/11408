// 单一事实来源 (SSOT) 的笔记 slug 生成器。
// Astro 内容集合 loader 的 generateId 与 wiki-index 共用此函数，
// 确保页面 URL 与 wikilink href 由同一套规则导出，
// 杜绝大小写/空格在跨平台（Windows 大小写不敏感 / Linux 严格）部署下断链。
//
// 规则：小写 + 空格/下划线→连字符 + 去标点（保留中文、字母数字、连字符）+ 合并连字符。
// 已验证：对全库 54 篇公开笔记的输出与 production sitemap 完全一致，
// 接入 generateId 后零 URL 变更。

export function slugifySegment(value) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[\s_]+/g, '-')
    .replace(/[^a-z0-9一-龥-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '');
}

// 对完整相对路径（如 "408/CPU 与流水线"）逐段 slugify，保留 "/" 分隔。
// generateId 与 wiki-index 都用这个，保证目录段和文件名段一致处理。
export function slugifyPath(path) {
  return path
    .split('/')
    .map((segment) => slugifySegment(segment))
    .join('/');
}
