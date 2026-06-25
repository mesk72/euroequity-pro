import { NextResponse } from 'next/server'

const ASIA_INDICES = [
  { name: 'Nikkei 225', symbol: '^N225'  },
  { name: 'Hang Seng',  symbol: '^HSI'   },
  { name: 'ASX 200',    symbol: '^AXJO'  },
]

const EU_INDICES = [
  { name: 'DAX',           symbol: '^GDAXI'    },
  { name: 'CAC 40',        symbol: '^FCHI'     },
  { name: 'FTSE MIB',      symbol: '^FTMIB'    },
  { name: 'FTSE 100',      symbol: '^FTSE'     },
  { name: 'Euro Stoxx 50', symbol: '^STOXX50E' },
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

async function getYahooCrumb(): Promise<{ crumb: string; cookie: string } | null> {
  try {
    const r = await fetch('https://finance.yahoo.com/', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
      },
      signal: AbortSignal.timeout(8000),
      cache: 'no-store',
    })
    const cookie = r.headers.get('set-cookie') || ''
    const html = await r.text()
    const crumbMatch = html.match(/"CrumbStore":\{"crumb":"([^"]+)"\}/) ||
                       html.match(/crumb=([A-Za-z0-9._-]+)/)
    if (!crumbMatch) return { crumb: '', cookie }
    return { crumb: crumbMatch[1], cookie }
  } catch { return null }
}

async function fetchQuotes(symbols: string[]): Promise<any[]> {
  try {
    // Prima ottieni crumb e cookie
    const auth = await getYahooCrumb()
    const syms = symbols.map(s => encodeURIComponent(s)).join(',')
    const crumbParam = auth?.crumb ? `&crumb=${encodeURIComponent(auth.crumb)}` : ''
    const url = `https://query1.finance.yahoo.com/v7/finance/quote?symbols=${syms}&fields=regularMarketPrice,regularMarketChangePercent${crumbParam}`
    
    const fetchHeaders: Record<string, string> = {
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      'Accept': 'application/json',
      'Referer': 'https://finance.yahoo.com/',
    }
    if (auth?.cookie) fetchHeaders['Cookie'] = auth.cookie.split(';')[0]

    const r = await fetch(url, {
      headers: fetchHeaders,
      signal: AbortSignal.timeout(10000),
      cache: 'no-store',
    })
    if (!r.ok) return []
    const d = await r.json()
    return d?.quoteResponse?.result || []
  } catch { return [] }
}

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

  const symbols = toFetch.map(i => i.symbol)
  const results = await fetchQuotes(symbols)

  const quotes = toFetch.map(idx => {
    const q = results.find((d: any) => d.symbol === idx.symbol)
    if (!q) return null
    const price = q.regularMarketPrice || 0
    const pct = q.regularMarketChangePercent || 0
    return {
      name: idx.name,
      price: price.toLocaleString('en-US', { maximumFractionDigits: 0 }),
      changePct: (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%',
      up: pct >= 0,
    }
  }).filter(Boolean)

  return NextResponse.json({
    quotes,
    debug: { asiaOpen, euOpen, utcHour: new Date().getUTCHours(), count: results.length }
  })
}
