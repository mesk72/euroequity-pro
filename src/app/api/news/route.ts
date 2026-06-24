import { NextResponse } from 'next/server'

const YAHOO_QUERIES = {
  world: [
    'global markets economy finance',
    'commodities oil gold prices',
    'central bank interest rates monetary policy',
    'inflation GDP growth recession',
    'Bloomberg Reuters financial news',
  ],
  americas: [
    'US stock market S&P 500 nasdaq dow jones',
    'Federal Reserve interest rates economy',
    'Wall Street earnings quarterly results',
    'canada economy TSX bank of canada',
    'US treasury bonds dollar forex',
  ],
  europe: [
    'european markets DAX FTSE CAC eurostoxx',
    'ECB european central bank eurozone inflation',
    'italy economy borsa milano',
    'germany economy DAX',
    'UK economy FTSE Bank of England pound',
    'france economy CAC paris',
    'switzerland SNB CHF',
  ],
  asia: [
    'japan nikkei economy yen bank of japan',
    'china hang seng economy yuan',
    'australia ASX economy RBA interest rates',
    'hong kong markets economy',
    'india sensex nifty economy',
    'asia pacific markets emerging',
  ],
}

async function fetchYahooNews(query: string): Promise<any[]> {
  try {
    const url = `https://query1.finance.yahoo.com/v1/finance/search?q=${encodeURIComponent(query)}&newsCount=8&quotesCount=0&enableFuzzyQuery=false`
    const r = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' },
      signal: AbortSignal.timeout(8000),
      cache: 'no-store',
    })
    if (!r.ok) return []
    const d = await r.json()
    return (d?.news || []).map((item: any) => ({
      title: item.title || '',
      link: item.link || '#',
      pubDate: item.providerPublishTime
        ? new Date(item.providerPublishTime * 1000).toISOString()
        : new Date().toISOString(),
      source: item.publisher || 'Yahoo Finance',
    })).filter((n: any) => n.title.length > 10)
  } catch { return [] }
}

export async function GET() {
  const results: Record<string, any[]> = { world: [], americas: [], europe: [], asia: [] }

  await Promise.all(
    Object.entries(YAHOO_QUERIES).map(async ([region, queries]) => {
      const allItems: any[] = []
      await Promise.all(queries.map(async q => {
        const items = await fetchYahooNews(q)
        allItems.push(...items)
      }))
      const seen = new Set<string>()
      const deduped = allItems.filter(item => {
        const key = item.title.slice(0, 50).toLowerCase()
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })
      deduped.sort((a: any, b: any) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
      results[region] = deduped.slice(0, 30)
    })
  )

  return NextResponse.json(results)
}
