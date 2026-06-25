import { NextResponse } from 'next/server'

const STOP = new Set(['Inc','Ltd','Corp','Group','SA','AG','NV','PLC','SE','Co',
  'The','Holdings','International','Global','Company','Corporation','Limited',
  'de','et','und','of','and'])

function parseXML(xml: string): { title: string; link: string; pubDate: string; source: string }[] {
  const items: any[] = []
  const itemRegex = /<item>([\s\S]*?)<\/item>/g
  let match
  while ((match = itemRegex.exec(xml)) !== null) {
    const block = match[1]
    const title = block.match(/<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/)?.[1]?.replace(/<[^>]+>/g, '').trim()
    const link  = block.match(/<link>(.*?)<\/link>/)?.[1]?.trim() ||
                  block.match(/<guid[^>]*>(.*?)<\/guid>/)?.[1]?.trim()
    const date  = block.match(/<pubDate>(.*?)<\/pubDate>/)?.[1]?.trim()
    const src   = block.match(/<source[^>]*>(.*?)<\/source>/)?.[1]?.trim()
    if (title && link && title.length > 10) {
      items.push({ title, link, pubDate: date || new Date().toISOString(), source: src || 'Yahoo Finance' })
    }
  }
  return items.slice(0, 10)
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const ticker = searchParams.get('ticker')
  const company = searchParams.get('company') || ''
  const exchange = searchParams.get('exchange') || ''
  const yahooTicker = searchParams.get('yahooTicker') || ticker || ''
  const googleUrl = searchParams.get('googleUrl') || ''

  // Modalità Google News diretto - per Global feed
  if (googleUrl && !ticker) {
    try {
      const r = await fetch(googleUrl, {
        headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' },
        signal: AbortSignal.timeout(5000),
        next: { revalidate: 900 },
      })
      if (!r.ok) return NextResponse.json({ items: [] })
      const xml = await r.text()
      const items = parseXML(xml).map(i => ({ ...i, source: i.source || 'Google News' }))
      return NextResponse.json({ items: items.slice(0, 20) })
    } catch {
      return NextResponse.json({ items: [] })
    }
  }

  if (!ticker) return NextResponse.json({ items: [] })

  const UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  const allItems: any[] = []

  // 1. Yahoo Finance RSS
  try {
    const yahooUrl = `https://feeds.finance.yahoo.com/rss/2.0/headline?s=${encodeURIComponent(ticker)}&region=US&lang=en-US`
    const r = await fetch(yahooUrl, {
      headers: { 'User-Agent': UA },
      signal: AbortSignal.timeout(5000),
      next: { revalidate: 1800 },
    })
    if (r.ok) {
      const xml = await r.text()
      const items = parseXML(xml).map(i => ({ ...i, source: i.source || 'Yahoo Finance' }))
      allItems.push(...items)
    }
  } catch {}

  // 2. Google News RSS - stessa logica della stock page
  // US: usa yahooTicker (es. AAPL stock) — più preciso
  // EU/Asia: usa prime 2 parole company name
  if (company || yahooTicker) {
    try {
      const isUS = exchange === 'US' || exchange === 'TSX'
      const query = isUS && yahooTicker
        ? yahooTicker + ' stock'
        : company.split(' ').filter((w: string) => w.length > 2 && !STOP.has(w)).slice(0, 2).join(' ') + ' stock OR earnings'
      const gl = isUS ? 'US' : 'GB'
      const googleUrl = `https://news.google.com/rss/search?q=${encodeURIComponent(query)}&hl=en&gl=${gl}&ceid=${gl}:en`
      const r = await fetch(googleUrl, {
        headers: { 'User-Agent': UA },
        signal: AbortSignal.timeout(5000),
        next: { revalidate: 1800 },
      })
      if (r.ok) {
        const xml = await r.text()
        const items = parseXML(xml).map(i => ({ ...i, source: i.source || 'Google News' }))
        allItems.push(...items)
      }
    } catch {}
  }

  // Deduplica per titolo
  const seen = new Set<string>()
  const deduped = allItems.filter(i => {
    const k = i.title.slice(0, 50).toLowerCase()
    if (seen.has(k)) return false
    seen.add(k)
    return true
  })

  // Filtri finali
  const STOP2 = new Set(['Inc','Ltd','Corp','Group','SA','AG','NV','PLC','SE','Co',
    'The','Holdings','International','Global','Company','Corporation','Limited'])
  const nameWords = company.split(' ')
    .map((w: string) => w.replace(/[^a-zA-Z0-9]/g, '').toLowerCase())
    .filter((w: string) => w.length >= 4 && !STOP2.has(w.charAt(0).toUpperCase() + w.slice(1)))
  const primaryWord = nameWords[0] || ''
  const yahooTickerClean = (yahooTicker || '').split('.')[0].toLowerCase()

  const filtered = deduped.filter(i => {
    const src = (i.source || '').toLowerCase()
    const title = (i.title || '').toLowerCase()
    // Escludi TradingView, Investors Business Daily, Investing.com (troppi falsi positivi)
    if (src.includes('tradingview') || src.includes('investors business') || 
        src.includes('investing.com') || title.includes('tradingview')) return false
    // Verifica che il nome azienda o ticker Yahoo sia nel titolo
    if (primaryWord && primaryWord.length >= 4) {
      const hasName = title.includes(primaryWord)
      const hasTicker = yahooTickerClean.length >= 2 && title.includes(yahooTickerClean)
      if (!hasName && !hasTicker) return false
    }
    return true
  })
  return NextResponse.json({ items: filtered.slice(0, 15) })
}
