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
        next: { revalidate: 1800 },
      })
      if (!r.ok) return NextResponse.json({ items: [] })
      const xml = await r.text()
      const items = parseXML(xml).map(i => ({ ...i, source: i.source || 'Google News' }))
      const gr = NextResponse.json({ items: items.slice(0, 20) })
      gr.headers.set('Cache-Control', 'public, max-age=1800, stale-while-revalidate=3600')
      return gr
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
      // Tutti i mercati: usa prime 2 parole significative del nome
      // Per US aggiungi anche yahooTicker nella query per maggiore precisione
      const isUS = exchange === 'US' || exchange === 'TSX'
      const nameQ = company.split(' ').filter((w: string) => w.length > 2 && !STOP.has(w)).slice(0, 2).join(' ')
      const query = isUS && yahooTicker && nameQ
        ? nameQ + ' ' + yahooTicker + ' stock'
        : nameQ ? nameQ + ' stock OR earnings'
        : yahooTicker + ' stock'
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
  // Parole significative del nome (escludi stop words)
  const STOP2 = new Set(['Inc','Ltd','Corp','Group','SA','AG','NV','PLC','SE','Co',
    'The','Holdings','International','Global','Company','Corporation','Limited',
    'de','et','und','of','and','AG','SPA','spa'])
  const nameWords = company.split(' ')
    .map((w: string) => w.replace(/[^a-zA-Z0-9]/g, '').toLowerCase())
    .filter((w: string) => w.length >= 3 && !STOP2.has(w.charAt(0).toUpperCase() + w.slice(1)))
  // Prendi le prime 2 parole significative — es. "Tencent" + "Holdings" (anche se Holdings è stop, ma è usato per disambiguare)
  const allNameWords = company.split(' ')
    .map((w: string) => w.replace(/[^a-zA-Z0-9]/g, '').toLowerCase())
    .filter((w: string) => w.length >= 3)
  const word1 = nameWords[0] || allNameWords[0] || ''
  const word2 = nameWords[1] || allNameWords[1] || ''
  const yahooTickerClean = (yahooTicker || '').split('.')[0].toLowerCase()

  // Parole generiche che da sole non identificano univocamente un titolo
  const GENERIC_WORDS = new Set([
    'semiconductor','manufacturing','international','technology','technologies',
    'energy','financial','services','holdings','systems','solutions','capital',
    'resources','communications','electric','electronics','industrial','industries',
    'pharmaceutical','pharmaceuticals','biotech','biotechnology','healthcare',
    'insurance','investment','investments','management','properties','development',
    'construction','engineering','chemicals','materials','logistics','transport',
  ])

  // Se word1 o word2 sono parole generiche, il ticker Yahoo diventa obbligatorio
  const word1IsGeneric = GENERIC_WORDS.has(word1)
  const word2IsGeneric = GENERIC_WORDS.has(word2)
  const nameIsAmbiguous = word1IsGeneric || word2IsGeneric

  const filtered = deduped.filter(i => {
    const src   = (i.source || '').toLowerCase()
    const title = (i.title || '').toLowerCase()
    // Escludi fonti problematiche
    if (src.includes('tradingview') || src.includes('investors business') ||
        src.includes('investing.com') || title.includes('tradingview')) return false
    if (!word1) return true
    const hasWord1  = title.includes(word1)
    const hasWord2  = !word2 || title.includes(word2)
    const hasTicker = yahooTickerClean.length >= 2 && title.includes(yahooTickerClean)
    // Se il nome è ambiguo (parole generiche), il ticker Yahoo è obbligatorio
    if (nameIsAmbiguous) return hasTicker
    // Altrimenti: (word1 AND word2) OPPURE ticker Yahoo
    if (!(hasWord1 && hasWord2) && !hasTicker) return false
    return true
  })
  const response = NextResponse.json({ items: filtered.slice(0, 15) })
  // Cache 10 minuti su Vercel Edge — riduce chiamate a Yahoo e protegge da scraping
  response.headers.set('Cache-Control', 'public, max-age=1800, stale-while-revalidate=3600')
  return response
}
