/**
 * Ranking formula (Andrea Meschini):
 * Rank(x) = (count(xi < x) + 0.5 * count(xi == x)) / N * 100
 * Result: integer 1-100, 1 = worst, 100 = best
 *
 * For inverse metrics (lower = better, e.g. PE ratio):
 * use rank on the inverse (1/x) or negate before ranking
 */

export function computeRank(values: (number | null | undefined)[]): (number | null)[] {
  const n = values.length
  if (n === 0) return []

  // Valid values with original indices
  const valid = values
    .map((v, i) => ({ v: v as number, i }))
    .filter(x => x.v != null && !isNaN(x.v) && isFinite(x.v))

  if (valid.length === 0) return values.map(() => null)

  const result: (number | null)[] = values.map(() => null)

  for (const { v, i } of valid) {
    const lower = valid.filter(x => x.v < v).length
    const equal = valid.filter(x => x.v === v).length
    const rank  = Math.round(((lower + 0.5 * equal) / valid.length) * 100)
    // Clamp to 1-100
    result[i] = Math.max(1, Math.min(100, rank === 0 ? 1 : rank))
  }

  return result
}

export function computeRankInverse(values: (number | null | undefined)[]): (number | null)[] {
  // For metrics where lower = better (PE, PB): rank the inverse
  const inverted = values.map(v =>
    v != null && !isNaN(v as number) && (v as number) > 0 ? 1 / (v as number) : null
  )
  return computeRank(inverted)
}

export function computeCompositeRank(rankArrays: (number | null)[][]): (number | null)[] {
  // Average all non-null ranks per stock, then re-rank
  const n = rankArrays[0]?.length ?? 0
  const averages: (number | null)[] = Array(n).fill(null)

  for (let i = 0; i < n; i++) {
    const vals = rankArrays.map(arr => arr[i]).filter(v => v != null) as number[]
    if (vals.length > 0) {
      averages[i] = vals.reduce((a, b) => a + b, 0) / vals.length
    }
  }

  return computeRank(averages)
}

export interface Stock {
  ticker:       string
  company:      string
  sector:       string | null
  country:      string
  flag:         string
  exchange:     string
  price:        number | null
  change1d:     number | null
  volume:       number | null
  mktCap:       number | null  // billions EUR
  peTrail:      number | null
  peFwd:        number | null
  pb:           number | null
  evEbitda:     number | null
  roe:          number | null
  divYield:     number | null
  beta:         number | null
  epsGrowth:    number | null
  revGrowth:    number | null
  epsMom30d:    number | null
  mom1w:        number | null
  mom1m:        number | null
  mom6m:        number | null
  mom12m:       number | null
  valueScore:   number | null
  growthScore:  number | null
}

export function computeScores(stocks: Stock[]): Stock[] {
  const n = stocks.length
  if (n === 0) return stocks

  // ── VALUE SCORE ──────────────────────────────────────────────
  // Inputs (all ranked: higher rank = better value)
  // Earnings Yield trailing = 1/PE trailing (higher EY = better)
  // Earnings Yield forward  = 1/PE forward
  // 1/PB (lower PB = better value = higher 1/PB rank)
  const r_eyt = computeRankInverse(stocks.map(s => s.peTrail))
  const r_eyf = computeRankInverse(stocks.map(s => s.peFwd))
  const r_pb  = computeRankInverse(stocks.map(s => s.pb))
  const valueComposite = computeCompositeRank([r_eyt, r_eyf, r_pb])

  // ── GROWTH SCORE ─────────────────────────────────────────────
  // EPS Growth %
  const r_epsg = computeRank(stocks.map(s => s.epsGrowth))
  // Revenue Growth %
  const r_revg = computeRank(stocks.map(s => s.revGrowth))
  // EPS Momentum 30d
  const r_epsm = computeRank(stocks.map(s => s.epsMom30d))
  // 12M momentum minus 1M momentum (trend acceleration)
  const mom12_1 = stocks.map(s =>
    s.mom12m != null && s.mom1m != null ? s.mom12m - s.mom1m : null
  )
  // 6M momentum minus 1W momentum
  const mom6_1w = stocks.map(s =>
    s.mom6m != null && s.mom1w != null ? s.mom6m - s.mom1w : null
  )
  const r_m12_1 = computeRank(mom12_1)
  const r_m6_1w = computeRank(mom6_1w)
  const growthComposite = computeCompositeRank([r_epsg, r_revg, r_epsm, r_m12_1, r_m6_1w])

  return stocks.map((s, i) => ({
    ...s,
    valueScore:  valueComposite[i],
    growthScore: growthComposite[i],
  }))
}
