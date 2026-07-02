export function GET(context: { site: URL }) {
  return new Response(
    `User-agent: *
Allow: /

Sitemap: ${new URL('sitemap-index.xml', context.site).href}
`.trim(),
    {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
      },
    },
  );
}
