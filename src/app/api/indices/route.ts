import { NextResponse } from 'next/server'

const SYMBOLS = [
  { name: 'DAX',           symbol: '^GDAXI'     },
  { name: 'CAC 40',        symbol: '^FCHI'      },
  { name: 'FTSE MIB',      symbol: 'FTSEMIB.MI' },
  { name: 'FTSE 100',      symbol: '^FTSE'      },
  { name: 'Euro Stoxx 50', symbol: '^STOXX50E'  },
  { name: 'Nikkei 225',    symbol: '^N225'      },
  { name: 'Hang Seng',     symbol: '^HSI'       },
  { name: 'ASX 200',       symbol: '^AXJO'      },
]

function parsePrice(xml: string): { price: number; changePct: number } | null {
  try {
    // Yahoo Finance RSS contiene il prezzo nel tag <title> del feed
    // es: "DAX (^GDAXI) - 18,234.56 - 0.12%"
    const titleMatch = xml.match(/<title>([^<]+)<\/title>/)
    if (!titleMatch) return null
    const title = titleMatch[1]
    const nums = title.match(/([\d,]+\.?\d*)/)
    if (!nums) return null
    const price = parseFloat(nums[1].replace(/,/g, ''))
    const pctMatch = title.match(/([\+\-]\d+\.?\d*)%/)
    const pct = pctMatch ? parseFloat(pctMatch[1]) : 0
    return { price, changePct: pct }
  } catch { return null }
}

export async function GET() {
  const quotes: any[] = []

  await Promise.all(SYMBOLS.map(async ({ name, symbol }) => {
    try {
      const url = 'https://feeds.finance.yahoo.com/rss/2.0/headline?s=' +
        encodeURIComponent(symbol) + '&region=US&lang=en-US'
      const r = await fetch(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
          'Accept': 'application/rss+xml, application/xml, text/xml, */*',
        },
        signal: AbortSignal.timeout(5000),
        cache: 'no-store',
      })
      if (!r.ok) return
      const xml = await r.text()
      // Il feed RSS ha il prezzo nella description del channel
      // Cerca pattern "Price: 18,234.56" o simile
      const priceMatch = xml.match(/regularMarketPrice[^>]*>([\d.]+)/) ||
                         xml.match(/<description>([\d,]+\.?\d+)<\/description>/) ||
                         xml.match(/Last Price[:\s]+([\d,]+\.?\d+)/)
      if (priceMatch) {
        const price = parseFloat(priceMatch[1].replace(/,/g, ''))
        quotes.push({ name, price: price.toLocaleString('en-US', { maximumFractionDigits: 0 }), changePct: 'N/A', up: true })
      }
    } catch {}
  }))

  return NextResponse.json({ quotes })
}
