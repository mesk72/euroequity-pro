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
  return items.slice(0, 5)
}

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const ticker = searchParams.get('ticker')
  const company = searchParams.get('company') || ''
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

  // 2. Google News RSS - cerca per nome azienda
  if (company) {
    try {
      const nameWords = company.split(' ')
        .filter((w: string) => w.length > 2 && !STOP.has(w))
        .slice(0, 3).join(' ')
      const query = nameWords + ' stock OR earnings'
      const googleUrl = `https://news.google.com/rss/search?q=${encodeURIComponent(query)}&hl=en&gl=US&ceid=US:en`
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

  return NextResponse.json({ items: deduped.slice(0, 8) })
}
