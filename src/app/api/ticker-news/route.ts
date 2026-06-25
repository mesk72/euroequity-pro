import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

const GOOGLE_NEWS = 'https://news.google.com/rss/search'

async function fetchGoogleNews(query: string, lang = 'en', geo = 'US'): Promise<any[]> {
  try {
    const url = `${GOOGLE_NEWS}?q=${encodeURIComponent(query)}&hl=${lang}&gl=${geo}&ceid=${geo}:${lang}`
    const r = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0' },
      signal: AbortSignal.timeout(8000),
      next: { revalidate: 900 },
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
        items.push({ title, link, pubDate: date || new Date().toISOString(), source: src || 'Google News' })
      }
    }
    return items.slice(0, 5)
  } catch { return [] }
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const region = searchParams.get('region') || 'americas'

  // Prendi top ticker per regione dal DB
  let exchanges: string[] = []
  let limit = 300
  let lang = 'en'
  let geo = 'US'

  if (region === 'americas') {
    exchanges = ['US', 'TSX']
    limit = 300
  } else if (region === 'europe') {
    exchanges = ['PA', 'XETRA', 'MIL', 'MC', 'AS', 'BR', 'LS', 'OM', 'OB', 'HE', 'SWX', 'IR', 'LSE', 'VI', 'CPSE']
    limit = 200
  } else if (region === 'asia') {
    exchanges = ['TSE', 'SEHK', 'ASX', 'TSX']
    limit = 200
  }

  // Prendi top N titoli per mktCap
  const { data: stocks } = await supabase
    .from('fundamentals')
    .select('ticker, exchange, mkt_cap')
    .in('exchange', exchanges)
    .not('mkt_cap', 'is', null)
    .order('mkt_cap', { ascending: false })
    .limit(limit)

  if (!stocks || stocks.length === 0) {
    return NextResponse.json({ news: [], tickers: [] })
  }

  // Prendi company names
  const tickerList = stocks.map((s: any) => `${s.ticker}.${s.exchange}`)
  const { data: stockInfo } = await supabase
    .from('stocks')
    .select('ticker, exchange, company, yahoo_ticker')
    .in('exchange', exchanges)

  const infoMap: Record<string, any> = {}
  for (const s of (stockInfo || [])) {
    infoMap[`${s.ticker}.${s.exchange}`] = s
  }

  // Costruisci gruppi da 20 ticker per query Google News
  const groups: string[][] = []
  const chunk = 20
  for (let i = 0; i < Math.min(stocks.length, 100); i += chunk) {
    groups.push(stocks.slice(i, i + chunk).map((s: any) => {
      const info = infoMap[`${s.ticker}.${s.exchange}`]
      return info?.yahoo_ticker || info?.company?.split(' ')[0] || s.ticker
    }))
  }

  // Fetch news per ogni gruppo
  const allNews: any[] = []
  await Promise.all(groups.map(async (group) => {
    const query = group.join(' OR ')
    const news = await fetchGoogleNews(query, lang, geo)
    allNews.push(...news)
  }))

  // Deduplica e ordina
  const seen = new Set<string>()
  const deduped = allNews.filter(n => {
    const k = n.title.slice(0, 50).toLowerCase()
    if (seen.has(k)) return false
    seen.add(k)
    return true
  }).sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())

  return NextResponse.json({
    news: deduped.slice(0, 50),
    tickers: stocks.slice(0, 20).map((s: any) => ({
      ticker: s.ticker,
      exchange: s.exchange,
      company: infoMap[`${s.ticker}.${s.exchange}`]?.company || s.ticker,
    }))
  })
}
