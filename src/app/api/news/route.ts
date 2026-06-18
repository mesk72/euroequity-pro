import { NextResponse } from 'next/server'

const FEEDS = {
  americas: [
    { name: 'Bloomberg', url: 'https://feeds.bloomberg.com/markets/news.rss' },
    { name: 'Reuters', url: 'https://feeds.reuters.com/reuters/businessNews' },
    { name: 'WSJ', url: 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml' },
    { name: 'CNBC', url: 'https://search.cnbc.com/rs/search/combinedcgi?id=15839135&format=rss' },
    { name: 'MarketWatch', url: 'https://feeds.marketwatch.com/marketwatch/topstories' },
    { name: 'FT', url: 'https://www.ft.com/rss/home/us' },
    { name: "Barron's", url: 'https://www.barrons.com/xml/rss/3_7510.xml' },
    { name: 'ZeroHedge', url: 'https://feeds.feedburner.com/zerohedge/feed' },
    { name: 'Seeking Alpha', url: 'https://seekingalpha.com/market_currents.xml' },
  ],
  europe: [
    { name: 'Bloomberg', url: 'https://feeds.bloomberg.com/markets/news.rss' },
    { name: 'Reuters', url: 'https://feeds.reuters.com/reuters/businessNews' },
    { name: 'FT', url: 'https://www.ft.com/rss/home/uk' },
    { name: 'WSJ', url: 'https://feeds.a.dj.com/rss/RSSWorldNews.xml' },
    { name: 'CNBC', url: 'https://search.cnbc.com/rs/search/combinedcgi?id=15839135&format=rss' },
    { name: 'MarketWatch', url: 'https://feeds.marketwatch.com/marketwatch/topstories' },
    { name: "Barron's", url: 'https://www.barrons.com/xml/rss/3_7510.xml' },
    { name: 'Handelsblatt', url: 'https://www.handelsblatt.com/rss/finanzen.xml' },
    { name: 'Les Echos', url: 'https://feeds.lesechos.fr/lesechos/finance-marches' },
  ],
  asia: [
    { name: 'Bloomberg', url: 'https://feeds.bloomberg.com/markets/news.rss' },
    { name: 'Reuters', url: 'https://feeds.reuters.com/reuters/asiaPacificNews' },
    { name: 'FT', url: 'https://www.ft.com/rss/home/asia' },
    { name: 'WSJ', url: 'https://feeds.a.dj.com/rss/RSSWorldNews.xml' },
    { name: 'CNBC', url: 'https://search.cnbc.com/rs/search/combinedcgi?id=15839135&format=rss' },
    { name: 'MarketWatch', url: 'https://feeds.marketwatch.com/marketwatch/topstories' },
    { name: "Barron's", url: 'https://www.barrons.com/xml/rss/3_7510.xml' },
    { name: 'Nikkei Asia', url: 'https://asia.nikkei.com/rss/feed/nar' },
    { name: 'SCMP', url: 'https://www.scmp.com/rss/5/feed' },
  ],
}

function parseRSS(xml: string, source: string): any[] {
  const items: any[] = []
  const itemRegex = /<item>([\s\S]*?)<\/item>/g
  let match
  while ((match = itemRegex.exec(xml)) !== null) {
    const item = match[1]
    const title = item.match(/<title><!\[CDATA\[(.*?)\]\]><\/title>|<title>(.*?)<\/title>/)?.[1] || item.match(/<title>(.*?)<\/title>/)?.[1] || ''
    const link = item.match(/<link>(.*?)<\/link>|<link\s[^>]*href="([^"]*)"[^>]*\/>/)?.[1] || ''
    const pubDate = item.match(/<pubDate>(.*?)<\/pubDate>/)?.[1] || ''
    if (title && link) {
      items.push({ title: title.replace(/<!\[CDATA\[|\]\]>/g, '').trim(), link, pubDate, source })
    }
  }
  return items.slice(0, 5)
}

export const revalidate = 900 // 15 minuti

export async function GET() {
  const results: Record<string, any[]> = { americas: [], europe: [], asia: [] }

  for (const [region, feeds] of Object.entries(FEEDS)) {
    const allItems: any[] = []
    await Promise.all(
      feeds.map(async (feed) => {
        try {
          const r = await fetch(feed.url, {
            headers: { 'User-Agent': 'Mozilla/5.0' },
            signal: AbortSignal.timeout(5000),
          })
          if (!r.ok) return
          const xml = await r.text()
          const items = parseRSS(xml, feed.name)
          allItems.push(...items)
        } catch {}
      })
    )
    // Ordina per data e prendi le prime 15
    allItems.sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
    results[region] = allItems.slice(0, 15)
  }

  return NextResponse.json(results)
}
