import { NextResponse } from 'next/server'

const FEEDS = {
 world: [
 { name: 'Bloomberg', url: 'https://feeds.bloomberg.com/markets/news.rss' },
 { name: 'Bloomberg Economy', url: 'https://feeds.bloomberg.com/economics/news.rss' },
 { name: 'Bloomberg Business', url: 'https://feeds.bloomberg.com/business/news.rss' },
 { name: 'Bloomberg Industries', url: 'https://feeds.bloomberg.com/industries/news.rss' },
 { name: 'Reuters World', url: 'https://feeds.feedburner.com/reuters/worldNews' },
 { name: 'Reuters Top', url: 'https://feeds.feedburner.com/reuters/topNews' },
 { name: 'Reuters Tech', url: 'https://feeds.feedburner.com/reuters/technologyNews' },
 { name: 'WSJ World', url: 'https://feeds.a.dj.com/rss/RSSWorldNews.xml' },
 { name: 'CNN International', url: 'http://rss.cnn.com/rss/money_news_international.rss' },
 { name: 'The Economist', url: 'https://www.economist.com/finance-and-economics/rss.xml' },
 { name: 'FT World', url: 'https://www.ft.com/rss/world' },
 { name: 'CBS News', url: 'https://www.cbsnews.com/latest/rss/main' },
 { name: 'ABC News', url: 'https://abcnews.go.com/abcnews/topstories' },
 { name: 'Google World', url: 'https://news.google.com/rss/search?q=global+economy+world+markets&hl=en&gl=US&ceid=US:en' },
 { name: 'Google Commodities', url: 'https://news.google.com/rss/search?q=oil+gold+commodities+prices&hl=en&gl=US&ceid=US:en' },
 { name: 'Google Central Banks', url: 'https://news.google.com/rss/search?q=central+bank+monetary+policy&hl=en&gl=US&ceid=US:en' },
 { name: 'Google Crypto', url: 'https://news.google.com/rss/search?q=bitcoin+crypto+markets&hl=en&gl=US&ceid=US:en' },
 ],
 americas: [
 { name: 'CNBC US', url: 'https://www.cnbc.com/id/10000664/device/rss/rss.html' },
 { name: 'CNBC Business', url: 'https://www.cnbc.com/id/10001147/device/rss/rss.html' },
 { name: 'WSJ Markets', url: 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml' },
 { name: 'WSJ Business', url: 'https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml' },
 { name: 'MarketWatch', url: 'https://feeds.marketwatch.com/marketwatch/topstories/' },
 { name: 'MarketWatch Pulse', url: 'https://feeds.marketwatch.com/marketwatch/marketpulse/' },
 { name: 'Reuters Business', url: 'https://feeds.feedburner.com/reuters/businessNews' },
 { name: 'Yahoo Finance', url: 'https://finance.yahoo.com/rss/topstories' },
 { name: 'CNN Money', url: 'http://rss.cnn.com/rss/money_latest.rss' },
 { name: 'CNN Markets', url: 'http://rss.cnn.com/rss/money_markets.rss' },
 { name: 'CNN Economy', url: 'http://rss.cnn.com/rss/money_news_economy.rss' },
 { name: 'Fox Business', url: 'https://feeds.foxbusiness.com/foxbusiness/latest' },
 { name: 'CBS MoneyWatch', url: 'https://www.cbsnews.com/latest/rss/moneywatch' },
 { name: 'ABC Business', url: 'https://abcnews.go.com/abcnews/businessheadlines' },
 { name: 'Seeking Alpha', url: 'https://seekingalpha.com/market_currents.xml' },
 { name: 'ZeroHedge', url: 'https://feeds.feedburner.com/zerohedge/feed' },
 { name: 'Globe & Mail', url: 'https://www.theglobeandmail.com/arc/outboundfeeds/rss/category/business/' },
 { name: 'Financial Post', url: 'https://financialpost.com/feed/' },
 { name: 'Google US Economy', url: 'https://news.google.com/rss/search?q=US+economy+federal+reserve&hl=en&gl=US&ceid=US:en' },
 { name: 'Google US Fed', url: 'https://news.google.com/rss/search?q=Federal+Reserve+interest+rates&hl=en&gl=US&ceid=US:en' },
 { name: 'Google Canada', url: 'https://news.google.com/rss/search?q=canada+economy+markets&hl=en&gl=CA&ceid=CA:en' },
 ],
 europe: [
 { name: 'CNBC Europe', url: 'https://www.cnbc.com/id/19794221/device/rss/rss.html' },
 { name: 'CNBC Europe Mkts', url: 'https://www.cnbc.com/id/19836768/device/rss/rss.html' },
 { name: 'FT UK', url: 'https://www.ft.com/rss/home/uk' },
 { name: 'FT Markets', url: 'https://www.ft.com/rss/markets' },
 { name: 'Il Sole 24 Ore', url: 'https://www.ilsole24ore.com/rss/finanza.xml' },
 { name: 'Le Monde', url: 'https://www.lemonde.fr/economie/rss_full.xml' },
 { name: 'Handelsblatt', url: 'https://www.handelsblatt.com/contentexport/feed/top-themen' },
 { name: 'Expansion', url: 'https://www.expansion.com/rss/mercados.xml' },
 { name: 'NZZ', url: 'https://www.nzz.ch/wirtschaft.rss' },
 { name: 'Dagens Industri', url: 'https://www.di.se/rss' },
 { name: 'Borsen DK', url: 'https://borsen.dk/rss' },
 { name: 'Google EU Markets', url: 'https://news.google.com/rss/search?q=european+markets&hl=en&gl=US&ceid=US:en' },
 { name: 'Google EU ECB', url: 'https://news.google.com/rss/search?q=ECB+european+economy&hl=en&gl=US&ceid=US:en' },
 { name: 'Google Italy', url: 'https://news.google.com/rss/search?q=italia+economia+mercati&hl=it&gl=IT&ceid=IT:it' },
 { name: 'Google France', url: 'https://news.google.com/rss/search?q=france+economie+marches&hl=fr&gl=FR&ceid=FR:fr' },
 { name: 'Google Germany', url: 'https://news.google.com/rss/search?q=germany+economy+dax&hl=en&gl=US&ceid=US:en' },
 { name: 'Google UK', url: 'https://news.google.com/rss/search?q=uk+economy+ftse&hl=en&gl=GB&ceid=GB:en' },
 { name: 'Google Spain', url: 'https://news.google.com/rss/search?q=spain+economy+ibex&hl=en&gl=US&ceid=US:en' },
 ],
 asia: [
 { name: 'CNBC Asia', url: 'https://www.cnbc.com/id/19832390/device/rss/rss.html' },
 { name: 'SCMP Business', url: 'https://www.scmp.com/rss/92/feed' },
 { name: 'SCMP Finance', url: 'https://www.scmp.com/rss/5/feed' },
 { name: 'Japan Times', url: 'https://www.japantimes.co.jp/feed/' },
 { name: 'NHK Business', url: 'https://www3.nhk.or.jp/rss/news/cat7.xml' },
 { name: 'Economic Times', url: 'https://economictimes.indiatimes.com/rssfeedstopstories.cms' },
 { name: 'Mint', url: 'https://www.livemint.com/rss/markets' },
 { name: 'Business Times SG', url: 'https://www.businesstimes.com.sg/rss/top-stories' },
 { name: 'Google China', url: 'https://news.google.com/rss/search?q=china+markets+economy&hl=en&gl=US&ceid=US:en' },
 { name: 'Google Japan', url: 'https://news.google.com/rss/search?q=japan+nikkei+economy+yen&hl=en&gl=US&ceid=US:en' },
 { name: 'Google India', url: 'https://news.google.com/rss/search?q=india+sensex+nifty+economy&hl=en&gl=US&ceid=US:en' },
 { name: 'Google Australia', url: 'https://news.google.com/rss/search?q=australia+economy+asx&hl=en&gl=AU&ceid=AU:en' },
 { name: 'Google Korea', url: 'https://news.google.com/rss/search?q=korea+kospi+economy&hl=en&gl=US&ceid=US:en' },
 { name: 'Google HK SG', url: 'https://news.google.com/rss/search?q=hong+kong+singapore+markets&hl=en&gl=US&ceid=US:en' },
 ],
}

function parseRSS(xml: string, source: string): any[] {
 const items: any[] = []
 const itemRegex = /<item>([\s\S]*?)<\/item>/g
 let match
 while ((match = itemRegex.exec(xml)) !== null) {
 const block = match[1]
 const titleMatch = block.match(/<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/)
 const linkMatch = block.match(/<link>(.*?)<\/link>/) || block.match(/<link[^>]*href="([^"]*)"/) 
 const dateMatch = block.match(/<pubDate>(.*?)<\/pubDate>/) || block.match(/<dc:date>(.*?)<\/dc:date>/)
 const title = titleMatch?.[1]?.replace(/<!\[CDATA\[|\]\]>/g, '').replace(/<[^>]+>/g, '').trim()
 const link = linkMatch?.[1]?.trim()
 const pubDate = dateMatch?.[1]?.trim() || new Date().toISOString()
 if (title && link && title.length > 10 &&
 !title.includes('Google News') && !title.includes('Google Actual') &&
 !title.includes('Bloomberg.com') && !title.includes('Flipso') &&
 !title.includes('MarketWatch.com') && !title.includes('WSJ.com') &&
 !title.includes('FOX Business') && !title.includes('ABC News') &&
 !title.includes('Bloomberg Markets') && !title.includes('Bloomberg Technology')) {
 items.push({ title, link, pubDate, source })
 }
 }
 return items.slice(0, 3)
}

export const revalidate = 900

export async function GET() {
 const results: Record<string, any[]> = { world: [], americas: [], europe: [], asia: [] }

 for (const [region, feeds] of Object.entries(FEEDS)) {
 const allItems: any[] = []
 await Promise.all(
 feeds.map(async (feed) => {
 try {
 const r = await fetch(feed.url, {
 headers: { 'User-Agent': 'Mozilla/5.0 (compatible; ForwardAlpha/1.0)' },
 next: { revalidate: 900 },
 })
 if (!r.ok) return
 const xml = await r.text()
 const items = parseRSS(xml, feed.name)
 allItems.push(...items)
 } catch {}
 })
 )
 allItems.sort((a, b) => new Date(b.pubDate).getTime() - new Date(a.pubDate).getTime())
 results[region] = allItems.slice(0, 20)
 }

 return NextResponse.json(results)
}