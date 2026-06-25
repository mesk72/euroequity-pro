import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Domini finanziari affidabili - filtro anti-spam
const FINANCE_DOMAINS = [
  'reuters.com','bloomberg.com','cnbc.com','wsj.com','ft.com','marketwatch.com',
  'seekingalpha.com','fool.com','yahoo.com','barrons.com','investing.com',
  'financialtimes.com','economist.com','businessweek.com','forbes.com',
  'thestreet.com','benzinga.com','zacks.com','morningstar.com','stockanalysis.com',
  'ilsole24ore.com','handelsblatt.com','lesechos.fr','expansion.com','nzz.ch',
  'scmp.com','japantimes.co.jp','nhk.or.jp','businesstimes.com.sg','nikkei.com',
  'globeandmail.com','financialpost.com','bnnbloomberg.ca',
]

function isFinanceNews(link: string): boolean {
  return FINANCE_DOMAINS.some(d => link.includes(d))
}

async function fetchGoogleNewsForTicker(
  ticker: string,
  company: string,
  exchange: string
): Promise<any[]> {
  try {
    // Query: nome azienda + ticker per notizie precise
    const companyShort = company.split(' ').slice(0, 2).join(' ')
    const query = `"${companyShort}" stock OR "${ticker}" stock OR "${company}" earnings`
    const lang = ['TSE','SEHK'].includes(exchange) ? 'en' : 'en'
    const geo = exchange === 'TSX' ? 'CA' :
                ['TSE','SEHK','ASX'].includes(exchange) ? 'US' :
                ['PA','MIL','XETRA','MC','AS','BR','LS','OM','OB','HE','SWX'].includes(exchange) ? 'US' : 'US'

    const url = `https://news.google.com/rss/search?q=${encodeURIComponent(query)}&hl=${lang}&gl=${geo}&ceid=${geo}:${lang}`
    const r = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      signal: AbortSignal.timeout(5000),
      next: { revalidate: 1800 },
    })
    if (!r.ok) return []
    const xml = await r.text()
    const items: any[] = []
    const itemRegex = /<item>([\s\S]*?)<\/item>/g
    let match
    while ((match = itemRegex.exec(xml)) !== null) {
      const block = match[1]
      const title = block.match(/<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/)?.[1]?.replace(/<[^>]+>/g, '').trim()
      const link  = block.match(/<link>(.*?)<\/link>/)?.[1]?.trim()
      const date  = block.match(/<pubDate>(.*?)<\/pubDate>/)?.[1]?.trim()
      const src   = block.match(/<source[^>]*>(.*?)<\/source>/)?.[1]?.trim()
      if (title && link && title.length > 10) {
        items.push({
          title,
          link,
          pubDate: date || new Date().toISOString(),
          source: src || 'Google News',
          ticker,
          exchange,
          company: companyShort,
        })
      }
    }
    // Filtra solo notizie finanziarie
    return items.filter(n => isFinanceNews(n.link)).slice(0, 2)
  } catch { return [] }
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const region = searchParams.get('region') || 'americas'
  const limitParam = parseInt(searchParams.get('limit') || '0')

  let exchanges: string[] = []
  let limit = 500

  if (region === 'americas') {
    exchanges = ['US', 'TSX']
    limit = limitParam || 500
  } else if (region === 'europe') {
    exchanges = ['PA', 'XETRA', 'MIL', 'MC', 'AS', 'BR', 'LS', 'OM', 'OB', 'HE', 'SWX', 'IR', 'LSE', 'VI', 'CPSE']
    limit = limitParam || 600
  } else if (region === 'asia') {
    exchanges = ['TSE', 'SEHK', 'ASX']
    limit = limitParam || 600
  }

  // Top ticker per mktCap con company name
  const { data: stocks } = await supabase
    .from('fundamentals')
    .select('ticker, exchange, mkt_cap')
    .in('exchange', exchanges)
    .not('mkt_cap', 'is', null)
    .order('mkt_cap', { ascending: false })
    .limit(limit)

  if (!stocks || stocks.length === 0) {
    return NextResponse.json({ news: [] })
  }

  const { data: stockInfo } = await supabase
    .from('stocks')
    .select('ticker, exchange, company')
    .in('exchange', exchanges)

  const infoMap: Record<string, string> = {}
  for (const s of (stockInfo || [])) {
    if (s.company) infoMap[`${s.ticker}.${s.exchange}`] = s.company
  }

  // Filtra solo quelli con company name
  const tickersWithName = stocks
    .map((s: any) => ({
      ticker: s.ticker,
      exchange: s.exchange,
      company: infoMap[`${s.ticker}.${s.exchange}`] || '',
    }))
    .filter((s: any) => s.company.length > 0)
    .slice(0, limit)

  // Fetch news in parallelo a batch di 30 alla volta
  const batchSize = 30
  const allNews: any[] = []

  for (let i = 0; i < tickersWithName.length && allNews.length < 60; i += batchSize) {
    const batch = tickersWithName.slice(i, i + batchSize)
    const batchNews = await Promise.all(
      batch.map((s: any) => fetchGoogleNewsForTicker(s.ticker, s.company, s.exchange))
    )
    for (const news of batchNews) allNews.push(...news)
    // Stop se abbiamo abbastanza notizie
    if (allNews.length >= 60) break
  }

  // Deduplica per titolo
  const seen = new Set<string>()
  const deduped = allNews.filter(n => {
    const k = n.title.slice(0, 60).toLowerCase()
    if (seen.has(k)) return false
    seen.add(k)
    return true
  }).sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())

  return NextResponse.json({ news: deduped.slice(0, 50) })
}
