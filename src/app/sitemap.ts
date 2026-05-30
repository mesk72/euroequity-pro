import { MetadataRoute } from 'next'

const SLUGS = ['abbn','asml','barc','bnp','enr','eqnr','ifx','inga','mc','mt','pry','rio','rms','shel','ubsg','vow3']

export default function sitemap(): MetadataRoute.Sitemap {
  const baseUrl = 'https://forwardalpha.pro'

  const staticPages = ['', '/research', '/about', '/legal'].map(path => ({
    url: `${baseUrl}${path}`,
    lastModified: new Date(),
    changeFrequency: 'weekly' as const,
    priority: path === '' ? 1.0 : path === '/research' ? 0.9 : 0.7,
  }))

  const researchPages = SLUGS.map(slug => ({
    url: `${baseUrl}/research/${slug}`,
    lastModified: new Date(),
    changeFrequency: 'monthly' as const,
    priority: 0.8,
  }))

  return [...staticPages, ...researchPages]
}
