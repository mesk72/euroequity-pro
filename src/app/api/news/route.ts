import { NextResponse } from 'next/server'

// Usa rss2json.com come proxy - gratuito, bypass CORS
const RSS2JSON = 'https://api.rss2json.com/v1/api.json?rss_url='

const FEEDS = {
  world: [
    { name: 'Reuters', url: 'https://feeds.feedburner.com/reuters/topNews' },
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'MarketWatch', url: 'https://feeds.marketwatch.com/marketwatch/topstories/' },
    { name: 'Google Markets', url: 'https://news.google.com/rss/search?q=global+markets+economy&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Commodities', url: 'https://news.google.com/rss/search?q=oil+gold+commodities&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Central Banks', url: 'https://news.google.com/rss/search?q=central+bank+interest+rates&hl=en&gl=US&ceid=US:en' },
  ],
  americas: [
    { name: 'CNBC US', url: 'https://www.cnbc.com/id/10000664/device/rss/rss.html' },
    { name: 'CNBC Markets', url: 'https://www.cnbc.com/id/20910258/device/rss/rss.html' },
    { name: 'MarketWatch Pulse', url: 'https://feeds.marketwatch.com/marketwatch/marketpulse/' },
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'Google Fed', url: 'https://news.google.com/rss/search?q=Federal+Reserve+rates&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Canada', url: 'https://news.google.com/rss/search?q=canada+economy+TSX&hl=en&gl=CA&ceid=CA:en' },
  ],
  europe: [
    { name: 'CNBC Europe', url: 'https://www.cnbc.com/id/19794221/device/rss/rss.html' },
    { name: 'Il Sole 24 Ore', url: 'https://www.ilsole24ore.com/rss/finanza.xml' },
    { name: 'Handelsblatt', url: 'https://www.handelsblatt.com/contentexport/feed/top-themen' },
    { name: 'Google ECB', url: 'https://news.google.com/rss/search?q=ECB+eurozone+economy&hl=en&gl=US&ceid=US:en' },
    { name: 'Google EU Markets', url: 'https://news.google.com/rss/search?q=DAX+FTSE+CAC40+markets&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Italy', url: 'https://news.google.com/rss/search?q=italia+economia+borsa&hl=it&gl=IT&ceid=IT:it' },
  ],
  asia: [
    { name: 'CNBC Asia', url: 'https://www.cnbc.com/id/19832390/device/rss/rss.html' },
    { name: 'NHK Business', url: 'https://www3.nhk.or.jp/rss/news/cat7.xml' },
    { name: 'Google Nikkei', url: 'https://news.google.com/rss/search?q=nikkei+japan+economy&hl=en&gl=US&ceid=US:en' },
    { name: 'Google China', url: 'https://news.google.com/rss/search?q=china+hang+seng+markets&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Australia', url: 'https://news.google.com/rss/search?q=australia+ASX+economy&hl=en&gl=AU&ceid=AU:en' },
    { name: 'Google HK', url: 'https://news.google.com/rss/search?q=hong+kong+markets&hl=en&gl=US&ceid=US:en' },
  ],
}

const SKIP = ['Google News','Bloomberg.com','MarketWatch.com','WSJ.com','Flipboard','MSN']

export const revalidate = 900

export async function GET() {
  const results: Record<string, any[]> = { world: [], americas: [], europe: [], asia: [] }

  await Promise.all(
    Object.entries(FEEDS).map(async ([region, feeds]) => {
      const allItems: any[] = []
      await Promise.all(
        feeds.map(async ({ name, url }) => {
          try {
            const apiUrl = `${RSS2JSON}${encodeURIComponent(url)}&count=5`
            const r = await fetch(apiUrl, {
              signal: AbortSignal.timeout(6000),
              next: { revalidate: 900 },
            })
            if (!r.ok) return
            const d = await r.json()
            if (d.status !== 'ok' || !d.items) return
            for (const item of d.items) {
              const title = item.title?.replace(/<[^>]+>/g, '').trim()
              if (!title || title.length < 10) continue
              if (SKIP.some(s => title.includes(s))) continue
              allItems.push({
                title,
                link: item.link || item.url || '#',
                pubDate: item.pubDate || item.published || new Date().toISOString(),
                source: name,
              })
            }
          } catch {}
        })
      )
      allItems.sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
      // Deduplicazione per titolo simile
      const seen = new Set<string>()
      const deduped = allItems.filter(item => {
        const key = item.title.slice(0, 40).toLowerCase()
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })
      results[region] = deduped.slice(0, 25)
    })
  )

  return NextResponse.json(results)
}
