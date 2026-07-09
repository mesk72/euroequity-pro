import { MetadataRoute } from 'next'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Tutti i mercati coperti — EU (16), NA (2), APAC (5). GCC escluso finche'
// non e' live con copertura Leeway confermata.
const ALL_EXCHANGES = [
  // Europa
  'MIL','XETRA','PA','LSE','SWX','OM','AS','MC','BR','HE','CPSE','OB','GR','VI','IR','LS',
  // Nord America
  'US','TSX',
  // Asia Pacifico
  'TSE','SEHK','ASX','KRX','SGX',
]

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = 'https://forwardalpha.pro'

  // Pagine statiche
  const staticPages: MetadataRoute.Sitemap = [
    { url: baseUrl,                     lastModified: new Date(), changeFrequency: 'daily',   priority: 1.0 },
    { url: `${baseUrl}/news`,           lastModified: new Date(), changeFrequency: 'hourly',  priority: 0.9 },
    { url: `${baseUrl}/screens`,        lastModified: new Date(), changeFrequency: 'daily',   priority: 0.9 },
    { url: `${baseUrl}/screens/europe`, lastModified: new Date(), changeFrequency: 'daily',   priority: 0.8 },
    { url: `${baseUrl}/screens/us`,     lastModified: new Date(), changeFrequency: 'daily',   priority: 0.8 },
    { url: `${baseUrl}/screens/asia`,   lastModified: new Date(), changeFrequency: 'daily',   priority: 0.8 },
    { url: `${baseUrl}/research`,       lastModified: new Date(), changeFrequency: 'weekly',  priority: 0.8 },
    { url: `${baseUrl}/about`,          lastModified: new Date(), changeFrequency: 'monthly', priority: 0.7 },
    { url: `${baseUrl}/legal`,          lastModified: new Date(), changeFrequency: 'monthly', priority: 0.5 },
  ]

  // Tutti i titoli in universe — tutte le borse
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

  // Top per market cap DAVVERO dal database, per regione separatamente (un
  //'top 60 globale' rischierebbe di sbilanciarsi tutto su una sola area).
  // Non piu' una lista scritta a mano che invecchia e puo' contenere ticker
  // sbagliati o non piu' esistenti — causa piu' probabile dei risultati
  // "senza senso" su Google.
  const REGION_EXCHANGES: Record<string, string[]> = {
    eu:   ['MIL','XETRA','PA','LSE','SWX','OM','AS','MC','BR','HE','CPSE','OB','GR','VI','IR','LS'],
    na:   ['US','TSX'],
    apac: ['TSE','SEHK','ASX','KRX','SGX'],
  }

  let topByMktCap: any[] = []
  for (const exchanges of Object.values(REGION_EXCHANGES)) {
    const { data } = await supabase
      .from('fundamentals')
      .select('ticker,exchange,mkt_cap')
      .in('exchange', exchanges)
      .not('mkt_cap', 'is', null)
      .order('mkt_cap', { ascending: false })
      .limit(20)
    if (data) topByMktCap = topByMktCap.concat(data)
  }

  const topTickerKeys = new Set(
    topByMktCap.map((t: any) => `${t.ticker}-${t.exchange}`)
  )

  const TOP_TICKERS: MetadataRoute.Sitemap = topByMktCap.map((t: any) => ({
    url: `${baseUrl}/stock/${t.ticker}-${t.exchange}`,
    lastModified: new Date(),
    changeFrequency: 'daily' as const,
    priority: 1.0,
  }))

  const stockPages: MetadataRoute.Sitemap = stocks
    .filter((s: any) => !topTickerKeys.has(`${s.ticker}-${s.exchange}`))
    .map((s: any) => ({
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

  return [...staticPages, ...TOP_TICKERS, ...stockPages, ...researchPages]
}
