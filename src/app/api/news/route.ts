import { NextResponse } from 'next/server'

const FEEDS = {
  world: [
    { name: 'Reuters Top', url: 'https://feeds.feedburner.com/reuters/topNews' },
    { name: 'Reuters World', url: 'https://feeds.feedburner.com/reuters/worldNews' },
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'Investing.com', url: 'https://www.investing.com/rss/news.rss' },
    { name: 'Google Markets', url: 'https://news.google.com/rss/search?q=global+markets+economy&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Commodities', url: 'https://news.google.com/rss/search?q=oil+gold+commodities+prices&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Central Banks', url: 'https://news.google.com/rss/search?q=central+bank+interest+rates+monetary+policy&hl=en&gl=US&ceid=US:en' },
    { name: 'Nasdaq', url: 'https://www.nasdaq.com/feed/rssoutbound?category=Markets' },
    { name: 'MarketWatch', url: 'https://feeds.marketwatch.com/marketwatch/topstories/' },
    { name: 'Seeking Alpha', url: 'https://seekingalpha.com/market_currents.xml' },
  ],
  americas: [
    { name: 'CNBC US', url: 'https://www.cnbc.com/id/10000664/device/rss/rss.html' },
    { name: 'CNBC Markets', url: 'https://www.cnbc.com/id/20910258/device/rss/rss.html' },
    { name: 'MarketWatch', url: 'https://feeds.marketwatch.com/marketwatch/marketpulse/' },
    { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/rss/topstories' },
    { name: 'Motley Fool', url: 'https://www.fool.com/feeds/index.aspx' },
    { name: 'Google US Fed', url: 'https://news.google.com/rss/search?q=Federal+Reserve+interest+rates+economy&hl=en&gl=US&ceid=US:en' },
    { name: 'Google S&P500', url: 'https://news.google.com/rss/search?q=S%26P+500+nasdaq+dow+jones&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Canada', url: 'https://news.google.com/rss/search?q=canada+economy+TSX+markets&hl=en&gl=CA&ceid=CA:en' },
    { name: 'Globe & Mail', url: 'https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/' },
    { name: 'Financial Post', url: 'https://financialpost.com/feed/' },
  ],
  europe: [
    { name: 'CNBC Europe', url: 'https://www.cnbc.com/id/19794221/device/rss/rss.html' },
    { name: 'CNBC Europe Mkts', url: 'https://www.cnbc.com/id/19836768/device/rss/rss.html' },
    { name: 'Il Sole 24 Ore', url: 'https://www.ilsole24ore.com/rss/finanza.xml' },
    { name: 'Handelsblatt', url: 'https://www.handelsblatt.com/contentexport/feed/top-themen' },
    { name: 'Le Monde', url: 'https://www.lemonde.fr/economie/rss_full.xml' },
    { name: 'Expansion', url: 'https://www.expansion.com/rss/mercados.xml' },
    { name: 'NZZ', url: 'https://www.nzz.ch/wirtschaft.rss' },
    { name: 'Google ECB', url: 'https://news.google.com/rss/search?q=ECB+european+central+bank+eurozone&hl=en&gl=US&ceid=US:en' },
    { name: 'Google EU Markets', url: 'https://news.google.com/rss/search?q=DAX+FTSE+CAC40+european+markets&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Italy', url: 'https://news.google.com/rss/search?q=italia+economia+borsa+Milano&hl=it&gl=IT&ceid=IT:it' },
    { name: 'Google Germany', url: 'https://news.google.com/rss/search?q=germany+economy+DAX&hl=en&gl=DE&ceid=DE:de' },
    { name: 'Google UK', url: 'https://news.google.com/rss/search?q=uk+economy+FTSE+Bank+of+England&hl=en&gl=GB&ceid=GB:en' },
  ],
  asia: [
    { name: 'CNBC Asia', url: 'https://www.cnbc.com/id/19832390/device/rss/rss.html' },
    { name: 'SCMP Business', url: 'https://www.scmp.com/rss/92/feed' },
    { name: 'Japan Times', url: 'https://www.japantimes.co.jp/feed/' },
    { name: 'NHK Business', url: 'https://www3.nhk.or.jp/rss/news/cat7.xml' },
    { name: 'Business Times SG', url: 'https://www.businesstimes.com.sg/rss/top-stories' },
    { name: 'Google Nikkei', url: 'https://news.google.com/rss/search?q=nikkei+japan+economy+yen&hl=en&gl=JP&ceid=JP:ja' },
    { name: 'Google China', url: 'https://news.google.com/rss/search?q=china+economy+hang+seng+markets&hl=en&gl=US&ceid=US:en' },
    { name: 'Google Australia', url: 'https://news.google.com/rss/search?q=australia+economy+ASX+RBA&hl=en&gl=AU&ceid=AU:en' },
    { name: 'Google HK', url: 'https://news.google.com/rss/search?q=hong+kong+markets+economy&hl=en&gl=US&ceid=US:en' },
    { name: 'Mint India', url: 'https://www.livemint.com/rss/markets' },
  ],
}

const SKIP_TITLES = [
  'Google News', 'Bloomberg.com', 'MarketWatch.com', 'WSJ.com',
  'FOX Business', 'ABC News', 'Bloomberg Markets', 'Bloomberg Technology',
  'Seeking Alpha', 'Flipboard', 'MSN', 'CNBC.com'
]

function parseRSS(xml: string, source: string): any[] {
  const items: any[] = []
  const itemRegex = /<item>([\s\S]*?)<\/item>/g
  let match
  while ((match = itemRegex.exec(xml)) !== null) {
    const block = match[1]
    const titleMatch = block.match(/<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/)
    const linkMatch  = block.match(/<link>(.*?)<\/link>/) || block.match(/<link[^>]*href="([^"]*)"/)
    const dateMatch  = block.match(/<pubDate>(.*?)<\/pubDate>/) || block.match(/<dc:date>(.*?)<\/dc:date>/)
    const title   = titleMatch?.[1]?.replace(/<!\[CDATA\[|\]\]>/g, '').replace(/<[^>]+>/g, '').trim()
    const link    = linkMatch?.[1]?.trim()
    const pubDate = dateMatch?.[1]?.trim() || new Date().toISOString()
    if (!title || !link || title.length < 10) continue
    if (SKIP_TITLES.some(s => title.includes(s))) continue
    items.push({ title, link, pubDate, source })
  }
  return items.slice(0, 4)
}

export const revalidate = 900

export async function GET() {
  const results: Record<string, any[]> = { world: [], americas: [], europe: [], asia: [] }

  await Promise.all(
    Object.entries(FEEDS).map(async ([region, feeds]) => {
      const allItems: any[] = []
      await Promise.all(
        feeds.map(async (feed) => {
          try {
            const r = await fetch(feed.url, {
              headers: { 'User-Agent': 'Mozilla/5.0 (compatible; ForwardAlpha/1.0; +https://forwardalpha.pro)' },
              signal: AbortSignal.timeout(8000),
              next: { revalidate: 900 },
            })
            if (!r.ok) return
            const xml = await r.text()
            allItems.push(...parseRSS(xml, feed.name))
          } catch {}
        })
      )
      allItems.sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
      results[region] = allItems.slice(0, 25)
    })
  )

  return NextResponse.json(results)
}
