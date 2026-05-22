import { NextResponse } from 'next/server'

export const revalidate = 3600  // aggiorna ogni ora

export async function GET() {
  try {
    // ExchangeRate-API — piano gratuito, 1500 chiamate/mese
    const r = await fetch(
      'https://open.er-api.com/v6/latest/USD',
      { next: { revalidate: 3600 } }
    )
    if (!r.ok) throw new Error('FX fetch failed')
    const d = await r.json()
    const usdToEur = d.rates?.EUR ?? 0.8615
    return NextResponse.json({ usdToEur, source: 'open.er-api.com' })
  } catch {
    // Fallback tasso fisso
    return NextResponse.json({ usdToEur: 0.8615, source: 'fallback' })
  }
}
