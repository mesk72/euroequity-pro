import { NextRequest, NextResponse } from 'next/server'

export const revalidate = 300

const LEEWAY_KEY  = process.env.LEEWAY_KEY || ''
const LEEWAY_BASE = 'https://api.leeway.tech/api/v1/public'

export async function GET(req: NextRequest) {
  const q = req.nextUrl.searchParams.get('q') || ''
  if (!q || q.length < 2) {
    return NextResponse.json({ results: [] })
  }

  try {
    const url = `${LEEWAY_BASE}/search?search=${encodeURIComponent(q)}&apitoken=${LEEWAY_KEY}`
    const r   = await fetch(url, { next: { revalidate: 300 } })
    if (!r.ok) return NextResponse.json({ results: [] })

    const data = await r.json()
    const results = (Array.isArray(data) ? data : [])
      .slice(0, 20)
      .map((item: any) => ({
        ticker:   item.Code || item.code || item.ticker || '',
        company:  item.Name || item.name || '',
        exchange: item.Exchange || item.exchange || '',
        isin:     item.ISIN || item.isin || '',
        type:     item.Type || item.type || '',
      }))
      .filter((r: any) => r.ticker)

    return NextResponse.json({ results })
  } catch {
    return NextResponse.json({ results: [] })
  }
}
