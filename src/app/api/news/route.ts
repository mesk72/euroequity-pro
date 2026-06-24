import { NextResponse } from 'next/server'

// Yahoo Finance news API - funziona sempre da Vercel
const YAHOO_QUERIES = {
  world: ['global markets', 'economy finance', 'commodities oil gold', 'central bank rates'],
  americas: ['US stock market', 'Federal Reserve', 'S&P 500 nasdaq', 'canada economy TSX'],
  europe: ['european markets DAX FTSE', 'ECB eurozone', 'italy economy', 'germany economy'],
  asia: ['japan nikkei economy', 'china hang seng', 'australia ASX', 'hong kong markets'],
}

async function fetchYahooNews(query: string): Promise<any[]> {
  try {
    const url = `https://query1.finance.yahoo.com/v1/finance/search?q=${encodeURIComponent(query)}&newsCount=8&quotesCount=0&enableFuzzyQuery=false`
    const r = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'application/json',
      },
      signal: AbortSignal.timeout(8000),
      next: { revalidate: 900 },
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

export const revalidate = 900

export async function GET() {
  const results: Record<string, any[]> = { world: [], americas: [], europe: [], asia: [] }

  await Promise.all(
    Object.entries(YAHOO_QUERIES).map(async ([region, queries]) => {
      const allItems: any[] = []
      await Promise.all(queries.map(async q => {
        const items = await fetchYahooNews(q)
        allItems.push(...items)
      }))
      // Deduplica per titolo
      const seen = new Set<string>()
      const deduped = allItems.filter(item => {
        const key = item.title.slice(0, 50).toLowerCase()
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })
      deduped.sort((a: any, b: any) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
      results[region] = deduped.slice(0, 25)
    })
  )

  return NextResponse.json(results)
}
