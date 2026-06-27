import { MetadataRoute } from 'next'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = 'https://forwardalpha.pro'

  // Pagine statiche
  const staticPages: MetadataRoute.Sitemap = [
    { url: baseUrl,                    lastModified: new Date(), changeFrequency: 'daily',   priority: 1.0 },
    { url: `${baseUrl}/news`,          lastModified: new Date(), changeFrequency: 'hourly',  priority: 0.9 },
    { url: `${baseUrl}/screens`,       lastModified: new Date(), changeFrequency: 'daily',   priority: 0.9 },
    { url: `${baseUrl}/screens/europe`,lastModified: new Date(), changeFrequency: 'daily',   priority: 0.8 },
    { url: `${baseUrl}/screens/us`,    lastModified: new Date(), changeFrequency: 'daily',   priority: 0.8 },
    { url: `${baseUrl}/screens/asia`,  lastModified: new Date(), changeFrequency: 'daily',   priority: 0.8 },
    { url: `${baseUrl}/research`,      lastModified: new Date(), changeFrequency: 'weekly',  priority: 0.8 },
    { url: `${baseUrl}/about`,         lastModified: new Date(), changeFrequency: 'monthly', priority: 0.7 },
    { url: `${baseUrl}/legal`,         lastModified: new Date(), changeFrequency: 'monthly', priority: 0.5 },
  ]

  // Top 50 titoli per mktcap — priority 0.9 (appaiono nei sitelink Google)
  const { data: topStocks } = await supabase
    .from('fundamentals')
    .select('ticker, exchange, mkt_cap')
    .not('mkt_cap', 'is', null)
    .order('mkt_cap', { ascending: false })
    .limit(50)

  const topPages: MetadataRoute.Sitemap = (topStocks || []).map((s: any) => ({
    url: `${baseUrl}/stock/${s.ticker}-${s.exchange}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.9,
  }))

  // Tutti i titoli in universe — tutte le borse
  const ALL_EXCHANGES = [
    'MIL','XETRA','PA','OM','SWX','LSE','OB','MC','AS','BR',
    'CPSE','HE','VI','IR','LS','AIM','NGM','AT',
    'US','TSX',
    'TSE','SEHK','ASX',
  ]

  let stocks: any[] = []
  let from = 0
  const PAGE = 1000
  while (true) {
    const { data, error } = await supabase
      .from('stocks')
      .select('ticker,exchange')
      .in('exchange', ALL_EXCHANGES)
      .eq('in_universe', true)
      .range(from, from + PAGE - 1)
    if (error || !data || data.length === 0) break
    stocks = stocks.concat(data)
    if (data.length < PAGE) break
    from += PAGE
  }

  const stockPages: MetadataRoute.Sitemap = stocks.map((s: any) => ({
    url: `${baseUrl}/stock/${s.ticker}-${s.exchange}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 0.6,
  }))

  // Research slugs
  const { data: research } = await supabase
    .from('research_notes')
    .select('slug')
    .not('slug', 'is', null)
    .limit(200)

  const researchPages: MetadataRoute.Sitemap = (research || []).map((r: any) => ({
    url: `${baseUrl}/research/${r.slug}`,
    lastModified: new Date(),
    changeFrequency: 'monthly' as const,
    priority: 0.8,
  }))

  // Deduplicazione — top titoli con priority 0.9 sovrascrivono i 0.6
  const seen = new Set<string>()
  const topUrls = topPages.map(p => p.url)
  topUrls.forEach(u => seen.add(u))
  const dedupedStocks = stockPages.filter(p => !seen.has(p.url))

  return [...staticPages, ...topPages, ...dedupedStocks, ...researchPages]
}
