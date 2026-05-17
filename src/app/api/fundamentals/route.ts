import { NextRequest, NextResponse } from 'next/server'
import { getFundamentals, getPriceHistory, parseFundamentals, parseMomentum } from '@/lib/leeway'

export const revalidate = 3600 // 1 hour shared cache

export async function GET(req: NextRequest) {
  const ticker   = req.nextUrl.searchParams.get('ticker') || ''
  const exchange = req.nextUrl.searchParams.get('exchange') || ''

  if (!ticker || !exchange) {
    return NextResponse.json({ error: 'Missing ticker or exchange' }, { status: 400 })
  }

  try {
    const [rawFund, history] = await Promise.all([
      getFundamentals(ticker, exchange),
      getPriceHistory(ticker, exchange, 400),
    ])

    const fund = rawFund ? parseFundamentals(rawFund) : {}
    const mom  = parseMomentum(history)

    return NextResponse.json({ ticker, exchange, ...fund, ...mom })
  } catch {
    return NextResponse.json({ error: 'Failed to load fundamentals' }, { status: 500 })
  }
}
