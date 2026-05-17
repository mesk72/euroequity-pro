import { NextRequest, NextResponse } from 'next/server'
import { getFundamentals, getPriceHistory, parseFundamentals, parseMomentum } from '@/lib/leeway'
import { computeScores, Stock } from '@/lib/ranking'

/**
 * POST /api/enrich
 * Body: { stocks: Stock[] }
 * Returns: { stocks: Stock[] } with fundamentals + momentum + scores
 *
 * KEY DESIGN: this runs SERVER-SIDE with Next.js fetch caching.
 * If user A and user B request ASML.MIL in the same minute,
 * Next.js makes ONE call to Leeway and serves both from cache.
 * revalidate=3600 means each ticker is fetched at most once per hour.
 */

export async function POST(req: NextRequest) {
  try {
    const { stocks }: { stocks: Stock[] } = await req.json()
    if (!stocks || !Array.isArray(stocks) || stocks.length === 0) {
      return NextResponse.json({ stocks: [] })
    }

    // Enrich each stock in parallel (Next.js cache deduplicates identical requests)
    const enriched = await Promise.all(
      stocks.map(async (stock) => {
        try {
          const [rawFund, history] = await Promise.all([
            getFundamentals(stock.ticker, stock.exchange),
            getPriceHistory(stock.ticker, stock.exchange, 400),
          ])

          const fund = rawFund ? parseFundamentals(rawFund) : {}
          const mom  = parseMomentum(history)

          return { ...stock, ...fund, ...mom }
        } catch {
          return stock
        }
      })
    )

    // Compute Value Score and Growth Score with correct ranking formula
    const scored = computeScores(enriched as Stock[])

    return NextResponse.json({ stocks: scored })
  } catch (err) {
    return NextResponse.json({ error: 'Enrichment failed' }, { status: 500 })
  }
}
