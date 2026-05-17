import { NextRequest, NextResponse } from 'next/server'
import { getSymbols, getLiveQuotes } from '@/lib/leeway'
import { EXCHANGES } from '@/lib/constants'

// Cache condivisa: se 100 utenti chiamano /api/exchange?code=MIL nello stesso minuto,
// Next.js fa UNA sola chiamata a Leeway e serve tutti dalla cache.
export const revalidate = 60 // seconds

export async function GET(req: NextRequest) {
  const code = req.nextUrl.searchParams.get('code') || 'MIL'
  const meta = EXCHANGES[code]
  if (!meta) {
    return NextResponse.json({ error: 'Unknown exchange' }, { status: 400 })
  }

  try {
    const [symbols, quotes] = await Promise.all([
      getSymbols(code, meta.isin),
      getLiveQuotes(code),
    ])

    // Build quotes map
    const quotesMap: Record<string, any> = {}
    for (const q of quotes) {
      const tk = q.ticker || q.Ticker || q.code || q.Code || q.symbol || ''
      if (tk) quotesMap[tk] = q
    }

    const stocks = symbols.map((s: any) => {
      const ticker  = s.Code || s.code || s.Symbol || s.ticker || ''
      const q       = quotesMap[ticker] || {}
      const px      = parseFloat(q.close || q.price || q.last || '0') || null
      const prev    = parseFloat(q.previousClose || q.prev_close || '0') || null
      let change1d: number | null = null
      if (px && prev && prev !== 0) {
        change1d = (px / prev - 1) * 100
      } else {
        const cp = parseFloat(q.changePercent || q.change_p || q.changepercent || '0')
        change1d = isNaN(cp) ? null : cp
      }
      const vol = parseFloat(q.volume || q.Volume || '0') || null

      return {
        ticker,
        company:  s.Name || s.name || ticker,
        isin:     s.ISIN || s.isin || '',
        exchange: code,
        flag:     meta.flag,
        country:  meta.label,
        price:    px,
        change1d,
        volume:   vol,
        // fundamentals loaded separately
        sector:     null,
        mktCap:     null,
        peTrail:    null,
        peFwd:      null,
        pb:         null,
        evEbitda:   null,
        roe:        null,
        divYield:   null,
        beta:       null,
        epsGrowth:  null,
        revGrowth:  null,
        epsMom30d:  null,
        mom1w:      null,
        mom1m:      null,
        mom6m:      null,
        mom12m:     null,
        valueScore: null,
        growthScore:null,
      }
    }).filter(s => s.ticker)
      .sort((a, b) => (b.volume || 0) - (a.volume || 0))

    return NextResponse.json({ stocks, exchange: code, meta })
  } catch (err) {
    return NextResponse.json({ error: 'Failed to load exchange data' }, { status: 500 })
  }
}
