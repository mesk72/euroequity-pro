import { NextResponse } from 'next/server'

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const ticker = searchParams.get('ticker')
  if (!ticker) return NextResponse.json({ items: [] })

  try {
    const url = `https://feeds.finance.yahoo.com/rss/2.0/headline?s=${encodeURIComponent(ticker)}&region=US&lang=en-US`
    const r = await fetch(url, {
      headers: { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36' },
      signal: AbortSignal.timeout(5000),
      next: { revalidate: 3600 },
    })
    if (!r.ok) return NextResponse.json({ items: [] })
    const xml = await r.text()
    const items: any[] = []
    const itemRegex = /<item>([\s\S]*?)<\/item>/g
    let match
    while ((match = itemRegex.exec(xml)) !== null) {
      const block = match[1]
      const title = block.match(/<title>(?:<!\[CDATA\[)?([\s\S]*?)(?:\]\]>)?<\/title>/)?.[1]?.replace(/<[^>]+>/g, '').trim()
      const link  = block.match(/<link>(.*?)<\/link>/)?.[1]?.trim()
      const date  = block.match(/<pubDate>(.*?)<\/pubDate>/)?.[1]?.trim()
      const src   = block.match(/<source[^>]*>(.*?)<\/source>/)?.[1]?.trim()
      if (title && link && title.length > 10) {
        items.push({ title, link, pubDate: date || new Date().toISOString(), source: src || 'Yahoo Finance' })
      }
    }
    return NextResponse.json({ items: items.slice(0, 5) })
  } catch {
    return NextResponse.json({ items: [] })
  }
}
