import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// FIX 3/8/2026 (sicurezza): questa route gira SUL SERVER e deve usare la
// chiave di servizio, non quella pubblica. La chiave pubblica e'
// estraibile dal browser: finche' le API la usavano, era necessario
// lasciare le tabelle leggibili a chiunque — cioe' l'intero database di
// prezzi e fondamentali era scaricabile da chiunque senza registrarsi.
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY || process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export const revalidate = 3600 // cache 1 ora — aggiornato dal daily

export async function GET() {
  try {
    const { data, error } = await supabase
      .from('indices')
      .select('ticker, name, price, change1d, date, exchange')
      .order('name')

    if (error || !data) return NextResponse.json({ americas: [], europe: [], asia: [] })

    const fmt = (d: any) => ({
      name:      d.name,
      price:     d.price != null ? Number(d.price).toLocaleString('en-US', { maximumFractionDigits: 2 }) : null,
      changePct: d.change1d != null ? (d.change1d >= 0 ? '+' : '') + Number(d.change1d).toFixed(2) + '%' : null,
      up:        d.change1d != null ? d.change1d >= 0 : null,
      date:      d.date,
    })

    // Mappa exchange → regione
    const REGION: Record<string, string> = {
      'US': 'americas', 'TSX': 'americas',
      'PA': 'europe', 'XETRA': 'europe', 'MIL': 'europe', 'MC': 'europe',
      'LSE': 'europe', 'SWX': 'europe', 'EZ': 'europe',
      'TSE': 'asia', 'SEHK': 'asia', 'ASX': 'asia',
    }

    const americas = data.filter(d => REGION[d.exchange] === 'americas').map(fmt)
    const europe   = data.filter(d => REGION[d.exchange] === 'europe').map(fmt)
    const asia     = data.filter(d => REGION[d.exchange] === 'asia').map(fmt)

    const response = NextResponse.json({ americas, europe, asia })
    response.headers.set('Cache-Control', 'public, s-maxage=3600, stale-while-revalidate=7200')
    return response
  } catch (e: any) {
    return NextResponse.json({ americas: [], europe: [], asia: [], error: e.message })
  }
}
