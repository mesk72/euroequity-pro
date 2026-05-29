import { MetadataRoute } from 'next'

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://forwardalpha.pro'

  const staticPages = [
    '',
    '/about',
    '/legal',
  ].map(path => ({
    url: `${baseUrl}${path}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: path === '' ? 1.0 : 0.8,
  }))

  return staticPages
}
