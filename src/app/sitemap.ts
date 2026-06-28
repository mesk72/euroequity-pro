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

  // Top titoli per mktcap hardcodati — Google li vede come sitelink principali
  // US: Nvidia, Apple, Microsoft, Alphabet, Amazon, Meta, Tesla, Berkshire, JPM, Visa
  // EU: ASML, LVMH, SAP, Nestle, Novo Nordisk, HSBC, Shell, Roche, AstraZeneca, Siemens
  // APAC: Tencent, Samsung, TSMC, Alibaba, Meituan, Toyota, BHP, Softbank
  const TOP_TICKERS: MetadataRoute.Sitemap = [
    // US — top per mktcap
    { url: `${baseUrl}/stock/NVDA-US`,  lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${baseUrl}/stock/AAPL-US`,  lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${baseUrl}/stock/MSFT-US`,  lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${baseUrl}/stock/GOOGL-US`, lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${baseUrl}/stock/AMZN-US`,  lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${baseUrl}/stock/META-US`,  lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${baseUrl}/stock/TSLA-US`,  lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${baseUrl}/stock/BRK.B-US`, lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
    { url: `${baseUrl}/stock/JPM-US`,   lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
    { url: `${baseUrl}/stock/V-US`,     lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
    // EU — top per mktcap
    { url: `${baseUrl}/stock/ASML-AS`,     lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${baseUrl}/stock/MC-PA`,        lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${baseUrl}/stock/SAP-XETRA`,   lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${baseUrl}/stock/NESN-SWX`,    lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${baseUrl}/stock/NOVO-B-CPSE`, lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${baseUrl}/stock/HSBA-LSE`,    lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
    { url: `${baseUrl}/stock/SHEL-LSE`,    lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
    { url: `${baseUrl}/stock/ROG-SWX`,     lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
    { url: `${baseUrl}/stock/AZN-LSE`,     lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
    { url: `${baseUrl}/stock/SIE-XETRA`,   lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
    // APAC — top per mktcap
    { url: `${baseUrl}/stock/700-SEHK`,    lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${baseUrl}/stock/9984-TSE`,    lastModified: new Date(), changeFrequency: 'daily', priority: 1.0 },
    { url: `${baseUrl}/stock/7203-TSE`,    lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
    { url: `${baseUrl}/stock/BHP-ASX`,     lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
    { url: `${baseUrl}/stock/941-SEHK`,    lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
    // CA — top per mktcap
    { url: `${baseUrl}/stock/RY-TSX`,      lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
    { url: `${baseUrl}/stock/TD-TSX`,      lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
  ]

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

  // Top ticker hardcodati già inclusi — escludi duplicati
  const topUrls = new Set(TOP_TICKERS.map(p => p.url))

  const stockPages: MetadataRoute.Sitemap = stocks
    .map((s: any) => `${baseUrl}/stock/${s.ticker}-${s.exchange}`)
    .filter(url => !topUrls.has(url))
    .map(url => ({
      url,
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
