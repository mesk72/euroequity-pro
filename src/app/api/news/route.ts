import { NextResponse } from 'next/server'

const NEWSAPI_KEY = '401c56a715b445ff89181369faf48b4b'
const BASE = 'https://newsapi.org/v2/everything'

const QUERIES: Record<string, { q: string; domains?: string }> = {
  world: {
    q: 'markets OR economy OR finance OR stocks OR bonds OR inflation OR GDP',
    domains: 'bloomberg.com,reuters.com,ft.com,wsj.com,cnbc.com,marketwatch.com,seekingalpha.com',
  },
  americas: {
    q: 'US economy OR "Federal Reserve" OR "S&P 500" OR nasdaq OR "Wall Street" OR canada OR TSX',
    domains: 'bloomberg.com,reuters.com,wsj.com,cnbc.com,marketwatch.com,ft.com,financialpost.com',
  },
  europe: {
    q: 'ECB OR eurozone OR DAX OR FTSE OR "Bank of England" OR "european markets" OR italy OR germany OR france',
    domains: 'bloomberg.com,reuters.com,ft.com,cnbc.com,ilsole24ore.com,handelsblatt.com,economist.com',
  },
  asia: {
    q: 'nikkei OR "hang seng" OR ASX OR "Bank of Japan" OR china OR japan OR australia OR "hong kong" OR "asia pacific"',
    domains: 'bloomberg.com,reuters.com,ft.com,cnbc.com,scmp.com,japantimes.co.jp,businesstimes.com.sg',
  },
}

async function fetchNewsAPI(region: string): Promise<any[]> {
  try {
    const { q, domains } = QUERIES[region]
    const url = `${BASE}?q=${encodeURIComponent(q)}&domains=${domains}&sortBy=publishedAt&pageSize=30&language=en&apiKey=${NEWSAPI_KEY}`
    const r = await fetch(url, {
      signal: AbortSignal.timeout(10000),
      cache: 'no-store',
    })
    if (!r.ok) {
      console.error(`NewsAPI error ${region}: ${r.status}`)
      return []
    }
    const d = await r.json()
    if (d.status !== 'ok') {
      console.error(`NewsAPI status ${region}: ${d.message}`)
      return []
    }
    return (d.articles || [])
      .filter((a: any) => a.title && a.title !== '[Removed]' && a.url)
      .map((a: any) => ({
        title: a.title,
        link: a.url,
        pubDate: a.publishedAt || new Date().toISOString(),
        source: a.source?.name || 'Unknown',
      }))
  } catch (e) {
    console.error(`NewsAPI fetch error ${region}:`, e)
    return []
  }
}

export async function GET() {
  const results: Record<string, any[]> = { world: [], americas: [], europe: [], asia: [] }

  await Promise.all(
    Object.keys(QUERIES).map(async region => {
      results[region] = await fetchNewsAPI(region)
    })
  )

  return NextResponse.json(results)
}
