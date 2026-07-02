import { readdir } from 'node:fs/promises';
import { join } from 'node:path';

export type PublicAsset = {
  kind: 'image' | 'file';
  name: string;
  href: string;
};

// assets/ 相对于 site/ 工作目录。当前仅 assets/README.md 存在,images/files 目录可能缺失 ——
// try/catch 兜底,缺失时返回空数组。此边界不参与主题 IA,仅为未来图片/PDF 引用预留。
const ASSETS_ROOT = '../assets';

export async function readPublicAssets(): Promise<PublicAsset[]> {
  const images = await readAssetDir('images', 'image');
  const files = await readAssetDir('files', 'file');
  return [...images, ...files].sort((a, b) => a.name.localeCompare(b.name, 'zh-CN'));
}

async function readAssetDir(folder: string, kind: PublicAsset['kind']): Promise<PublicAsset[]> {
  const dir = join(ASSETS_ROOT, folder);

  try {
    const entries = await readdir(dir, { withFileTypes: true });
    return entries
      .filter((entry) => entry.isFile())
      .map((entry) => ({
        kind,
        name: entry.name,
        href: `/assets/${folder}/${entry.name}`,
      }));
  } catch {
    return [];
  }
}
