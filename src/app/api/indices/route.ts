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

export async function GET() {
  try {
    // Usa Yahoo Finance v11 con crumb - diverso da v7
    const syms = SYMBOLS.map(s => encodeURIComponent(s.symbol)).join('%2C')
    
    // Prima ottieni crumb
    const crumbRes = await fetch('https://query2.finance.yahoo.com/v1/test/csrfToken', {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Referer': 'https://finance.yahoo.com',
      },
      signal: AbortSignal.timeout(5000),
    })
    
    // Prova endpoint alternativo - Yahoo Finance screener API
    const url = `https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?formatted=false&lang=en-US&region=US&scrIds=day_gainers&count=1`
    
    // In realtà usa l'endpoint più semplice con cookie
    const quoteUrl = `https://finance.yahoo.com/quote/${encodeURIComponent('^GDAXI')}/`
    const pageRes = await fetch(quoteUrl, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
      },
      signal: AbortSignal.timeout(8000),
      cache: 'no-store',
    })
    
    if (!pageRes.ok) return NextResponse.json({ quotes: [], error: 'page ' + pageRes.status })
    
    const html = await pageRes.text()
    
    // Estrai dati da financeData JSON embedded nella pagina
    const dataMatch = html.match(/root\.App\.main = (\{.*?\});/s) ||
                      html.match(/"QuoteSummaryStore":\s*(\{[^}]+\})/s) ||
                      html.match(/regularMarketPrice['":\s]+(\d+\.?\d*)/g)
    
    if (dataMatch) {
      console.log('Found data:', dataMatch[0]?.slice(0, 200))
    }
    
    return NextResponse.json({ quotes: [], debug: 'html length: ' + html.length })
  } catch (e: any) {
    return NextResponse.json({ quotes: [], error: e.message })
  }
}
