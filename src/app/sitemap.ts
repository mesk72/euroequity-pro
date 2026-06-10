import { MetadataRoute } from 'next'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

const SLUGS: string[] = ['BNP-PA', 'SHEL-LSE', 'ENR-XETRA', 'ABBN-SWX', 'ASML-AS', 'IFX-XETRA']

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
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

  // Legge tutti i titoli EU e US da Supabase
  const EU_EXCHANGES = ['MIL','XETRA','PA','OM','SWX','LSE','OB','MC','AS','BR','CPSE','HE','GR','VI','IR','LS']
  const US_EXCHANGES = ['US']
  const ALL_EXCHANGES = [...EU_EXCHANGES, ...US_EXCHANGES]

  let stocks: any[] = []
  let from = 0
  const PAGE = 1000
  while (true) {
    const { data, error } = await supabase
      .from('stocks')
      .select('ticker,exchange')
      .in('exchange', ALL_EXCHANGES)
      .range(from, from + PAGE - 1)
    if (error || !data || data.length === 0) break
    stocks = stocks.concat(data)
    if (data.length < PAGE) break
    from += PAGE
  }

  const stockPages = stocks.map((s: any) => ({
    url: `${baseUrl}/stock/${s.ticker}-${s.exchange}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.6,
  }))

  return [...staticPages, ...researchPages, ...stockPages]
}
