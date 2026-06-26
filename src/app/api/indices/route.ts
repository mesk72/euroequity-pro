import { NextResponse } from 'next/server'

const ASIA_INDICES = [
  { name: 'Nikkei 225', symbol: '%5EN225'  },
  { name: 'Hang Seng',  symbol: '%5EHSI'   },
  { name: 'ASX 200',    symbol: '%5EAXJO'  },
]

const EU_INDICES = [
  { name: 'DAX',           symbol: '%5EGDAXI'    },
  { name: 'CAC 40',        symbol: '%5EFCHI'     },
  { name: 'FTSE 100',      symbol: '%5EFTSE'     },
  { name: 'Euro Stoxx 50', symbol: '%5ESTOXX50E' },
]

function isWeekday(): boolean {
  return new Date().getUTCDay() >= 1 && new Date().getUTCDay() <= 5
}
function isAsiaOpen(): boolean {
  if (!isWeekday()) return false
  const t = new Date().getUTCHours() * 60 + new Date().getUTCMinutes()
  return t >= 0 && t <= 480
}
function isEUOpen(): boolean {
  if (!isWeekday()) return false
  const t = new Date().getUTCHours() * 60 + new Date().getUTCMinutes()
  return t >= 420 && t <= 930
}

async function fetchIndexRSS(symbol: string, name: string): Promise<{ name: string; price: string; changePct: string; up: boolean } | null> {
  try {
    // Stesso approccio di /api/yahoo-news che funziona
    const url = `https://feeds.finance.yahoo.com/rss/2.0/headline?s=${symbol}&region=US&lang=en-US`
    const r = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        'Referer': 'https://finance.yahoo.com/',
      },
      signal: AbortSignal.timeout(6000),
      cache: 'no-store',
    })
    if (!r.ok) return null
    const xml = await r.text()
    
    // Il feed RSS di Yahoo Finance ha il prezzo e variazione nel tag <title> del channel
    // Formato tipico: "DAX (^GDAXI) 23,456.78 +1.23% : Index Data"
    // Oppure nelle description degli item
    const channelTitle = xml.match(/<channel>[\s\S]*?<title>([^<]+)<\/title>/)?.[1] || ''
    const firstItem = xml.match(/<item>[\s\S]*?<title>([^<]+)<\/title>/)?.[1] || ''
    
    // Cerca numeri nel formato prezzo (es. 23,456.78 o 18234.56)
    const combined = channelTitle + ' ' + firstItem
    const priceMatch = combined.match(/([\d,]+\.\d{2})/)
    const pctMatch = combined.match(/([+-]?\d+\.\d+)%/)
    
    if (!priceMatch) return null
    const price = parseFloat(priceMatch[1].replace(/,/g, ''))
    const pct = pctMatch ? parseFloat(pctMatch[1]) : 0
    
    return {
      name,
      price: price.toLocaleString('en-US', { maximumFractionDigits: 0 }),
      changePct: (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%',
      up: pct >= 0,
    }
  } catch { return null }
}

export const revalidate = 900

export async function GET() {
  const asiaOpen = isAsiaOpen()
  const euOpen = isEUOpen()
  const toFetch = [
    ...(asiaOpen ? ASIA_INDICES : []),
    ...(euOpen ? EU_INDICES : []),
  ]

  if (toFetch.length === 0) {
    return NextResponse.json({ quotes: [], debug: 'markets closed', utcHour: new Date().getUTCHours() })
  }

  const results = await Promise.all(
    toFetch.map(idx => fetchIndexRSS(idx.symbol, idx.name))
  )

  const quotes = results.filter(Boolean)

  return NextResponse.json({
    quotes,
    debug: { asiaOpen, euOpen, utcHour: new Date().getUTCHours(), count: quotes.length }
  })
}
