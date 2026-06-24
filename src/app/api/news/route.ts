import { NextResponse } from 'next/server'

const YAHOO_BASE = 'https://query1.finance.yahoo.com/v1/finance/search'

// Query separate e specifiche per ogni regione
const QUERIES: Record<string, string[]> = {
  world: [
    'global markets stocks bonds',
    'oil gold commodities prices',
    'inflation interest rates central bank',
    'IMF World Bank economic outlook',
    'currency forex dollar euro yen',
  ],
  americas: [
    'Federal Reserve Powell rates',
    'S&P 500 nasdaq dow jones earnings',
    'US economy jobs GDP inflation',
    'Wall Street stocks buyback dividend',
    'Canada Bank of Canada TSX economy',
    'US treasury bonds yield curve',
    'tech stocks Apple Microsoft Amazon',
  ],
  europe: [
    'ECB Lagarde eurozone interest rates',
    'DAX Frankfurt german economy',
    'FTSE London UK economy Bank of England',
    'CAC Paris french economy',
    'Italy economy Borsa Milano MIB',
    'euro dollar exchange rate',
    'european stocks earnings',
  ],
  asia: [
    'Bank of Japan yen Nikkei economy',
    'China economy yuan Shanghai Shenzhen',
    'Hang Seng Hong Kong markets',
    'ASX Australia RBA interest rates',
    'emerging markets asia pacific',
    'South Korea KOSPI Samsung',
    'India Sensex Nifty economy',
  ],
}

async function fetchYahoo(query: string): Promise<any[]> {
  try {
    const url = `${YAHOO_BASE}?q=${encodeURIComponent(query)}&newsCount=6&quotesCount=0`
    const r = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' },
      signal: AbortSignal.timeout(8000),
      cache: 'no-store',
    })
    if (!r.ok) return []
    const d = await r.json()
    return (d?.news || [])
      .filter((n: any) => n.title && n.title.length > 10)
      .map((n: any) => ({
        title: n.title,
        link: n.link || '#',
        pubDate: n.providerPublishTime
          ? new Date(n.providerPublishTime * 1000).toISOString()
          : new Date().toISOString(),
        source: n.publisher || 'Yahoo Finance',
      }))
  } catch { return [] }
}

export async function GET() {
  const results: Record<string, any[]> = { world: [], americas: [], europe: [], asia: [] }

  await Promise.all(
    Object.entries(QUERIES).map(async ([region, queries]) => {
      const all: any[] = []
      await Promise.all(queries.map(async q => {
        const items = await fetchYahoo(q)
        all.push(...items)
      }))
      // Deduplica per titolo
      const seen = new Set<string>()
      const deduped = all.filter(item => {
        const key = item.title.slice(0, 60).toLowerCase()
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })
      // Ordina per data più recente
      deduped.sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
      results[region] = deduped.slice(0, 30)
    })
  )

  return NextResponse.json(results)
}
