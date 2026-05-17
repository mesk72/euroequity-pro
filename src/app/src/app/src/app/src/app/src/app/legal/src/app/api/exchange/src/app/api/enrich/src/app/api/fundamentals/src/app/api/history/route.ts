import { NextRequest, NextResponse } from 'next/server'
import { getPriceHistory } from '@/lib/leeway'

export const revalidate = 3600

export async function GET(req: NextRequest) {
  const ticker   = req.nextUrl.searchParams.get('ticker') || ''
  const exchange = req.nextUrl.searchParams.get('exchange') || ''
  const days     = parseInt(req.nextUrl.searchParams.get('days') || '365')

  if (!ticker || !exchange) {
    return NextResponse.json({ error: 'Missing params' }, { status: 400 })
  }

  const history = await getPriceHistory(ticker, exchange, days)
  return NextResponse.json({ history })
}
