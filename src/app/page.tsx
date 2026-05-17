'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  LayoutDashboard, Search, Briefcase, Globe,
  LogIn, LogOut, User, Menu, X, RefreshCw,
  ChevronUp, ChevronDown, TrendingUp, TrendingDown
} from 'lucide-react'
import { supabase, createProfile, ensureDefaultPortfolios } from '@/lib/supabase'
import { EXCHANGES, INDICES } from '@/lib/constants'
import { Stock } from '@/lib/ranking'
import SectorHeatmap from '@/components/dashboard/SectorHeatmap'
import AuthModal from '@/components/auth/AuthModal'
import toast from 'react-hot-toast'
import type { User as SupabaseUser } from '@supabase/supabase-js'
import Portfolio from '@/components/portfolio/PortfolioView'
import { DEMO_STOCKS } from '@/lib/demoData'
import { computeScores } from '@/lib/ranking'

// ── DEMO MODE — set false when Leeway API is active ─────────────
const USE_DEMO = true  // Cambia in false quando Leeway è attivo

// ── HELPERS ───────────────────────────────────────────────────────
const fp = (v: number | null | undefined, d = 1): string => {
  if (v == null || isNaN(v)) return '—'
  return `${v >= 0 ? '+' : ''}${v.toFixed(d)}%`
}
const fv = (v: number | null | undefined, d = 2): string => {
  if (v == null || isNaN(v)) return '—'
  return v.toFixed(d)
}
const fn = (v: number | null | undefined): string => {
  if (v == null || isNaN(v as number)) return '—'
  return String(Math.round(v as number))
}
const clr = (v: number | null | undefined): string => {
  if (v == null) return 'text-sub'
  return v > 0 ? 'text-green' : v < 0 ? 'text-red' : 'text-sub'
}
const fmtVol = (v: number | null | undefined): string => {
  if (!v) return '—'
  if (v >= 1e6) return `${(v/1e6).toFixed(1)}M`
  if (v >= 1e3) return `${(v/1e3).toFixed(0)}k`
  return String(v)
}

type Page = 'dashboard' | 'screener' | 'portfolio' | 'legal'

// ── API CALLS (client-side → Next.js API routes with shared cache) ──
async function apiExchange(code: string): Promise<Stock[]> {
  // Demo mode — mostra dati MSCI EMU hardcoded mentre Leeway non è attivo
  if (USE_DEMO) {
    const scored = computeScores([...DEMO_STOCKS])
    if (code === 'EZ') return scored
    if (code === 'MIL') return scored.filter(s => s.exchange === 'MIL')
    return scored.filter(s => s.exchange === code)
  }
  try {
    const codes = code === 'EZ' ? Object.keys(EXCHANGES) : [code]
    const results = await Promise.all(
      codes.map(c =>
        fetch(`/api/exchange?code=${c}`)
          .then(r => r.ok ? r.json() : { stocks: [] })
          .then(d => (d.stocks || []) as Stock[])
          .catch(() => [] as Stock[])
      )
    )
    const live = results.flat()
    // Fallback a dati demo se Leeway non è attivo
    const hasData = live.some(s => s.price != null && s.price > 0)
    if (!hasData) {
      const scored = computeScores([...DEMO_STOCKS])
      if (code === 'EZ') return scored
      if (code === 'MIL') return scored.filter(s => s.exchange === 'MIL')
      return scored.filter(s => s.exchange === code)
    }
    return live
  } catch {
    const scored = computeScores([...DEMO_STOCKS])
    if (code === 'EZ') return scored
    return scored.filter(s => s.exchange === code)
  }
}

async function apiEnrich(stocks: Stock[]): Promise<Stock[]> {
  const r = await fetch('/api/enrich', {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify({ stocks }),
  })
  if (!r.ok) return stocks
  const d = await r.json()
  return d.stocks || stocks
}

async function apiHistory(ticker: string, exchange: string, days: number) {
  const r = await fetch(`/api/history?ticker=${ticker}&exchange=${exchange}&days=${days}`)
  if (!r.ok) return []
  const d = await r.json()
  return d.history || []
}

async function apiIndices() {
  const r = await fetch('/api/indices')
  if (!r.ok) return []
  const d = await r.json()
  return d.indices || []
}

async function apiSearch(q: string) {
  const r = await fetch(`/api/search?q=${encodeURIComponent(q)}`)
  if (!r.ok) return []
  const d = await r.json()
  return d.results || []
}

// ── INDEX CARD ─────────────────────────────────────────────────────
function IndexCard({ name, close, changeP, loading }: {
  name: string; close: number | null; changeP: number | null; loading: boolean
}) {
  return (
    <div className="index-card">
      <div className="text-[9px] font-700 uppercase tracking-wide text-muted mb-1 truncate">{name}</div>
      {loading ? (
        <div className="shimmer h-4 w-16 mt-1" />
      ) : close ? (
        <>
          <div className={`font-mono font-600 text-sm ${clr(changeP)}`}>{fp(changeP)}</div>
          <div className="font-mono text-[9px] text-sub">{close.toLocaleString('de-DE', { maximumFractionDigits: 1 })}</div>
        </>
      ) : (
        <div className="text-[10px] text-muted">N/A</div>
      )}
    </div>
  )
}

// ── STOCK TABLE ────────────────────────────────────────────────────
type SortKey = keyof Stock

interface ColDef { key: SortKey; label: string; width?: number }

const COLUMNS: ColDef[] = [
  { key: 'ticker',      label: 'Ticker',    width: 80  },
  { key: 'company',     label: 'Company',   width: 180 },
  { key: 'sector',      label: 'Sector',    width: 130 },
  { key: 'price',       label: 'Price €',   width: 75  },
  { key: 'change1d',    label: '1D %',      width: 65  },
  { key: 'volume',      label: 'Volume',    width: 75  },
  { key: 'mktCap',      label: 'MktCap €B', width: 80  },
  { key: 'peTrail',     label: 'P/E Tr.',   width: 65  },
  { key: 'peFwd',       label: 'P/E Fwd',   width: 65  },
  { key: 'pb',          label: 'P/B',       width: 55  },
  { key: 'evEbitda',    label: 'EV/EBITDA', width: 75  },
  { key: 'roe',         label: 'ROE %',     width: 65  },
  { key: 'divYield',    label: 'Div %',     width: 60  },
  { key: 'beta',        label: 'Beta',      width: 55  },
  { key: 'epsGrowth',   label: 'EPS Gr%',   width: 70  },
  { key: 'revGrowth',   label: 'Rev Gr%',   width: 70  },
  { key: 'epsMom30d',   label: 'EPSMom30',  width: 75  },
  { key: 'mom1w',       label: '1W %',      width: 60  },
  { key: 'mom1m',       label: '1M %',      width: 60  },
  { key: 'mom6m',       label: '6M %',      width: 60  },
  { key: 'mom12m',      label: '12M %',     width: 65  },
  { key: 'valueScore',  label: 'Value',     width: 55  },
  { key: 'growthScore', label: 'Growth',    width: 60  },
]

function cellFmt(s: Stock, key: SortKey): { val: string; cls: string } {
  const v = s[key] as number | null
  switch (key) {
    case 'ticker':      return { val: `${s.flag || ''} ${s.ticker}`, cls: 'font-600 text-text' }
    case 'company':     return { val: s.company || '—',   cls: 'text-sub' }
    case 'sector':      return { val: s.sector  || '—',   cls: 'text-muted text-[10px]' }
    case 'price':       return { val: fv(v, 2),           cls: 'text-text' }
    case 'change1d':    return { val: fp(v),              cls: clr(v) }
    case 'volume':      return { val: fmtVol(v),          cls: 'text-sub' }
    case 'mktCap':      return { val: fv(v, 1),           cls: 'text-sub' }
    case 'peTrail':     return { val: fv(v, 1),           cls: 'text-sub' }
    case 'peFwd':       return { val: fv(v, 1),           cls: 'text-sub' }
    case 'pb':          return { val: fv(v, 2),           cls: 'text-sub' }
    case 'evEbitda':    return { val: fv(v, 1),           cls: 'text-sub' }
    case 'roe':         return { val: fp(v),              cls: clr(v) }
    case 'divYield':    return { val: fp(v),              cls: v && v > 0 ? 'text-green' : 'text-sub' }
    case 'beta':        return { val: fv(v, 2),           cls: 'text-sub' }
    case 'epsGrowth':   return { val: fp(v),              cls: clr(v) }
    case 'revGrowth':   return { val: fp(v),              cls: clr(v) }
    case 'epsMom30d':   return { val: fp(v),              cls: clr(v) }
    case 'mom1w':       return { val: fp(v),              cls: clr(v) }
    case 'mom1m':       return { val: fp(v),              cls: clr(v) }
    case 'mom6m':       return { val: fp(v),              cls: clr(v) }
    case 'mom12m':      return { val: fp(v),              cls: clr(v) }
    case 'valueScore':  return { val: fn(v), cls: v != null && v >= 70 ? 'text-green font-700' : v != null && v <= 30 ? 'text-red' : 'text-gold font-600' }
    case 'growthScore': return { val: fn(v), cls: v != null && v >= 70 ? 'text-green font-700' : v != null && v <= 30 ? 'text-red' : 'text-gold font-600' }
    default:            return { val: '—', cls: 'text-muted' }
  }
}

function StockTable({ stocks, onSelect, loading }: {
  stocks: Stock[]
  onSelect: (s: Stock) => void
  loading?: boolean
}) {
  const [sortKey, setSortKey] = useState<SortKey>('volume')
  const [sortAsc, setSortAsc] = useState(false)

  const sorted = [...stocks].sort((a, b) => {
    const av = a[sortKey] as any
    const bv = b[sortKey] as any
    if (av == null && bv == null) return 0
    if (av == null) return 1
    if (bv == null) return -1
    if (typeof av === 'string') return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av)
    return sortAsc ? av - bv : bv - av
  })

  const toggle = (key: SortKey) => {
    if (sortKey === key) setSortAsc(a => !a)
    else { setSortKey(key); setSortAsc(false) }
  }

  if (loading) return (
    <div className="p-8 text-center text-muted text-sm space-y-2">
      <RefreshCw size={20} className="animate-spin mx-auto text-gold" />
      <p>Loading market data…</p>
    </div>
  )

  if (stocks.length === 0) return (
    <div className="p-8 text-center text-muted text-sm">No stocks match your filters.</div>
  )

  return (
    <div className="overflow-x-auto">
      <table className="data-table">
        <thead>
          <tr>
            {COLUMNS.map(c => (
              <th
                key={c.key}
                onClick={() => toggle(c.key)}
                style={{ minWidth: c.width, userSelect: 'none' }}
              >
                <span className="flex items-center gap-1">
                  {c.label}
                  {sortKey === c.key
                    ? (sortAsc ? <ChevronUp size={10} className="text-gold" /> : <ChevronDown size={10} className="text-gold" />)
                    : null
                  }
                </span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((s, i) => (
            <tr
              key={`${s.ticker}.${s.exchange}.${i}`}
              onClick={() => onSelect(s)}
              className="cursor-pointer"
            >
              {COLUMNS.map(c => {
                const { val, cls } = cellFmt(s, c.key)
                return (
                  <td key={c.key} style={{ maxWidth: c.width }}>
                    <span className={`truncate block ${cls}`}>{val}</span>
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// ── PRICE CHART (SVG) ──────────────────────────────────────────────
function PriceChart({ history, ticker }: { history: any[]; ticker: string }) {
  const prices = history
    .map((d: any) => parseFloat(d.adjusted_close || d.close || '0'))
    .filter(v => !isNaN(v) && v > 0)

  if (prices.length < 2) return (
    <div className="h-48 flex items-center justify-center text-muted text-sm">
      No chart data available
    </div>
  )

  const min   = Math.min(...prices)
  const max   = Math.max(...prices)
  const range = max - min || 1
  const W = 900, H = 180, PAD = 20

  const pts = prices.map((p, i) => {
    const x = PAD + (i / (prices.length - 1)) * (W - 2 * PAD)
    const y = PAD + ((max - p) / range) * (H - 2 * PAD)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')

  const isUp  = prices[prices.length - 1] >= prices[0]
  const color = isUp ? '#22d48a' : '#e84560'
  const perf  = ((prices[prices.length - 1] / prices[0] - 1) * 100).toFixed(1)

  return (
    <div className="relative">
      <div className={`absolute top-2 right-2 text-xs font-700 font-mono ${isUp ? 'text-green' : 'text-red'}`}>
        {isUp ? '+' : ''}{perf}%
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: 192 }}>
        {/* Grid lines */}
        {[0.25, 0.5, 0.75].map(r => (
          <line
            key={r}
            x1={PAD} y1={PAD + r * (H - 2 * PAD)}
            x2={W - PAD} y2={PAD + r * (H - 2 * PAD)}
            stroke="#1e2840" strokeWidth="1"
          />
        ))}
        {/* Fill area */}
        <polygon
          points={`${pts} ${W - PAD},${H - PAD} ${PAD},${H - PAD}`}
          fill={color}
          fillOpacity="0.08"
        />
        {/* Line */}
        <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
        {/* Last point dot */}
        {prices.length > 0 && (() => {
          const lastIdx = prices.length - 1
          const x = PAD + (lastIdx / (prices.length - 1)) * (W - 2 * PAD)
          const y = PAD + ((max - prices[lastIdx]) / range) * (H - 2 * PAD)
          return <circle cx={x} cy={y} r="3" fill={color} />
        })()}
      </svg>
    </div>
  )
}

// ── STOCK DETAIL PANEL ────────────────────────────────────────────
function StockDetail({ stock, onClose, onAddPortfolio }: {
  stock: Stock
  onClose: () => void
  onAddPortfolio: (stock: Stock, qty: number, price: number, pf: string) => void
}) {
  const [chartDays, setChartDays] = useState(365)
  const [history,   setHistory]   = useState<any[]>([])
  const [loadingChart, setLoadingChart] = useState(true)
  const [qty,  setQty]  = useState('')
  const [px,   setPx]   = useState(stock.price?.toFixed(2) || '')
  const [pf,   setPf]   = useState('Portfolio 1')

  useEffect(() => {
    setLoadingChart(true)
    apiHistory(stock.ticker, stock.exchange, chartDays).then(h => {
      setHistory(h)
      setLoadingChart(false)
    })
  }, [stock.ticker, stock.exchange, chartDays])

  const metrics: [string, string, string][] = [
    ['Price €',      fv(stock.price, 2),        ''],
    ['1D %',         fp(stock.change1d),         clr(stock.change1d)],
    ['Mkt Cap €B',   fv(stock.mktCap, 1),        ''],
    ['P/E Trailing', fv(stock.peTrail, 1),       ''],
    ['P/E Fwd 12M',  fv(stock.peFwd, 1),         ''],
    ['P/B',          fv(stock.pb, 2),            ''],
    ['EV/EBITDA',    fv(stock.evEbitda, 1),      ''],
    ['ROE %',        fp(stock.roe),              clr(stock.roe)],
    ['Div Yield %',  fp(stock.divYield),         stock.divYield && stock.divYield > 0 ? 'text-green' : ''],
    ['Beta',         fv(stock.beta, 2),          ''],
    ['EPS Gr %',     fp(stock.epsGrowth),        clr(stock.epsGrowth)],
    ['Rev Gr %',     fp(stock.revGrowth),        clr(stock.revGrowth)],
    ['EPS Mom 30d',  fp(stock.epsMom30d),        clr(stock.epsMom30d)],
    ['Mom 1W %',     fp(stock.mom1w),            clr(stock.mom1w)],
    ['Mom 1M %',     fp(stock.mom1m),            clr(stock.mom1m)],
    ['Mom 6M %',     fp(stock.mom6m),            clr(stock.mom6m)],
    ['Mom 12M %',    fp(stock.mom12m),           clr(stock.mom12m)],
    ['Value Score',  fn(stock.valueScore),       stock.valueScore && stock.valueScore >= 70 ? 'text-green font-700' : 'text-gold font-600'],
    ['Growth Score', fn(stock.growthScore),      stock.growthScore && stock.growthScore >= 70 ? 'text-green font-700' : 'text-gold font-600'],
    ['Sector',       stock.sector || '—',        ''],
    ['Country',      stock.country || '—',       ''],
  ]

  return (
    <div className="mt-4 bg-surface border border-border rounded-lg overflow-hidden fade-in">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div>
          <div className="font-700 text-base text-text">
            {stock.flag} {stock.ticker}
            <span className={`ml-2 font-mono text-sm ${clr(stock.change1d)}`}>{fp(stock.change1d)}</span>
          </div>
          <div className="text-xs text-muted">{stock.company} · {stock.exchange}</div>
        </div>
        <button onClick={onClose} className="text-muted hover:text-text p-1">
          <X size={16} />
        </button>
      </div>

      {/* Metrics grid */}
      <div className="p-4 grid grid-cols-3 md:grid-cols-7 gap-2">
        {metrics.map(([label, value, color]) => (
          <div key={label} className="metric-card">
            <div className="metric-label">{label}</div>
            <div className={`font-mono font-600 text-sm ${color || 'text-gold'}`}>{value}</div>
          </div>
        ))}
      </div>

      {/* Chart */}
      <div className="px-4 pb-2">
        <div className="flex gap-2 mb-2">
          {([['1Y', 365], ['3Y', 1095], ['5Y', 1825]] as [string, number][]).map(([lbl, d]) => (
            <button
              key={lbl}
              onClick={() => setChartDays(d)}
              className={`px-3 py-1 text-xs rounded border transition-colors ${
                chartDays === d ? 'bg-gold text-bg border-gold' : 'border-border text-muted hover:border-gold'
              }`}
            >
              {lbl}
            </button>
          ))}
        </div>
        <div className="bg-bg border border-border rounded-lg overflow-hidden">
          {loadingChart
            ? <div className="h-48 flex items-center justify-center"><RefreshCw size={16} className="animate-spin text-gold" /></div>
            : <PriceChart history={history} ticker={stock.ticker} />
          }
        </div>
      </div>

      {/* Add to portfolio */}
      <div className="px-4 py-3 border-t border-border">
        <div className="text-xs font-700 text-muted uppercase tracking-wide mb-2">Add to Portfolio</div>
        <div className="flex flex-wrap gap-2">
          <select value={pf} onChange={e => setPf(e.target.value)} className="input-field w-36">
            {['Portfolio 1','Portfolio 2','Portfolio 3'].map(p => (
              <option key={p}>{p}</option>
            ))}
          </select>
          <input type="number" placeholder="Qty" value={qty} onChange={e => setQty(e.target.value)} className="input-field w-24" />
          <input type="number" placeholder="Buy price €" value={px} onChange={e => setPx(e.target.value)} className="input-field w-32" />
          <button
            onClick={() => {
              if (!qty || !px) return
              onAddPortfolio(stock, parseFloat(qty), parseFloat(px), pf)
              toast.success(`${stock.ticker} added to ${pf}`)
            }}
            className="btn-primary"
          >
            ➕ Add
          </button>
        </div>
      </div>
    </div>
  )
}

// ── SCREENER ──────────────────────────────────────────────────────
function Screener({ initExchange = 'MIL', initSector = 'All' }: {
  initExchange?: string
  initSector?:   string
}) {
  const [exchange,    setExchange]   = useState(initExchange)
  const [rawStocks,   setRawStocks]  = useState<Stock[]>([])
  const [stocks,      setStocks]     = useState<Stock[]>([])
  const [loading,     setLoading]    = useState(false)
  const [enriching,   setEnriching]  = useState(false)
  const [enriched,    setEnriched]   = useState(false)
  const [selected,    setSelected]   = useState<Stock | null>(null)
  const [progress,    setProgress]   = useState(0)

  // Filters
  const [search,    setSearch]    = useState('')
  const [sector,    setSector]    = useState(initSector)
  const [priceMin,  setPriceMin]  = useState(0)
  const [priceMax,  setPriceMax]  = useState(0)
  const [volMin,    setVolMin]    = useState(0)
  const [chgMin,    setChgMin]    = useState<number | ''>('')
  const [chgMax,    setChgMax]    = useState<number | ''>('')
  const [peMax,     setPeMax]     = useState(0)
  const [pbMax,     setPbMax]     = useState(0)
  const [divMin,    setDivMin]    = useState(0)
  const [roeMin,    setRoeMin]    = useState(0)
  const [betaMax,   setBetaMax]   = useState(0)
  const [mom12Min,  setMom12Min]  = useState(0)
  const [valMin,    setValMin]    = useState(0)
  const [growMin,   setGrowMin]   = useState(0)

  // Load prices when exchange changes
  useEffect(() => {
    setEnriched(false); setEnriching(false)
    setRawStocks([]); setStocks([])
    setSelected(null); setProgress(0)
    setLoading(true)
    apiExchange(exchange).then(data => {
      setRawStocks(data)
      setLoading(false)
    })
  }, [exchange])

  // Filter
  const filtered = rawStocks.filter(s => {
    if (search) {
      const q = search.toLowerCase()
      if (!s.ticker.toLowerCase().includes(q) && !(s.company || '').toLowerCase().includes(q)) return false
    }
    if (sector !== 'All' && s.sector !== sector) return false
    if (priceMin > 0 && (s.price || 0) < priceMin) return false
    if (priceMax > 0 && (s.price || 0) > priceMax) return false
    if (volMin   > 0 && (s.volume || 0) < volMin * 1000) return false
    if (chgMin !== '' && (s.change1d || 0) < (chgMin as number)) return false
    if (chgMax !== '' && (s.change1d || 0) > (chgMax as number)) return false
    if (enriched) {
      if (peMax  > 0 && s.peFwd    != null && s.peFwd    > peMax)  return false
      if (pbMax  > 0 && s.pb       != null && s.pb       > pbMax)  return false
      if (divMin > 0 && (s.divYield || 0)                < divMin) return false
      if (roeMin > 0 && (s.roe     || 0)                 < roeMin) return false
      if (betaMax> 0 && s.beta     != null && s.beta     > betaMax)return false
      if (mom12Min>0 && (s.mom12m  || 0)                 < mom12Min) return false
      if (valMin > 0 && (s.valueScore  || 0)             < valMin) return false
      if (growMin> 0 && (s.growthScore || 0)             < growMin) return false
      }
    return true
  })

  const candidates = [...filtered]
    .sort((a, b) => (b.volume || 0) - (a.volume || 0))
    .slice(0, 100)

  const sectors = ['All', ...Array.from(
    new Set(rawStocks.map(s => s.sector).filter(Boolean) as string[])
  ).sort()]

  async function runEnrich() {
    setEnriching(true); setProgress(0)
    const BATCH = 10
    let updated = [...rawStocks]
    const idxMap = new Map(candidates.map((s, i) => [`${s.ticker}.${s.exchange}`, i]))

    for (let i = 0; i < candidates.length; i += BATCH) {
      const batch = candidates.slice(i, i + BATCH)
      const enriched = await apiEnrich(batch)
      for (const es of enriched) {
        const ri = updated.findIndex(s => s.ticker === es.ticker && s.exchange === es.exchange)
        if (ri >= 0) updated[ri] = es
      }
      setProgress(Math.round(((i + BATCH) / candidates.length) * 100))
    }
    setRawStocks(updated)
    setEnriched(true)
    setEnriching(false)
    setProgress(100)
    toast.success(`Enriched ${candidates.length} stocks`)
  }

  function addToPortfolio(stock: Stock, qty: number, price: number, pf: string) {
    const stored = JSON.parse(localStorage.getItem('portfolios') || '{}')
    if (!stored[pf]) stored[pf] = []
    stored[pf].push({
      ticker:    stock.ticker,
      exchange:  stock.exchange,
      company:   stock.company,
      flag:      stock.flag,
      qty,
      buy_price: price,
      added_at:  new Date().toISOString(),
    })
    localStorage.setItem('portfolios', JSON.stringify(stored))
  }

  return (
    <div className="space-y-4 fade-in">
      {/* Exchange tabs */}
      <div className="flex flex-wrap gap-1.5">
        <button onClick={() => setExchange('EZ')} className={`px-3 py-1.5 rounded text-xs font-600 border transition-colors ${exchange === 'EZ' ? 'bg-gold text-bg border-gold' : 'border-border text-muted hover:border-gold hover:text-gold'}`}>
          🌍 All Eurozone
        </button>
        {Object.entries(EXCHANGES).map(([code, meta]) => (
          <button key={code} onClick={() => setExchange(code)} className={`px-3 py-1.5 rounded text-xs font-600 border transition-colors ${exchange === code ? 'bg-gold text-bg border-gold' : 'border-border text-muted hover:border-gold hover:text-gold'}`}>
            {meta.flag} {meta.label}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="bg-surface border border-border rounded-lg p-4">
        <div className="section-hdr mb-3">Filters — set then click Load & Apply</div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="space-y-2">
            <div className="text-[10px] font-700 text-muted uppercase tracking-wide">Price & Volume</div>
            <input type="number" placeholder="Price min €" value={priceMin || ''} onChange={e => setPriceMin(+e.target.value || 0)} className="input-field" />
            <input type="number" placeholder="Price max €" value={priceMax || ''} onChange={e => setPriceMax(+e.target.value || 0)} className="input-field" />
            <input type="number" placeholder="Volume min (k)" value={volMin || ''} onChange={e => setVolMin(+e.target.value || 0)} className="input-field" />
          </div>
          <div className="space-y-2">
            <div className="text-[10px] font-700 text-muted uppercase tracking-wide">Performance</div>
            <input type="number" placeholder="1D % min" value={chgMin} onChange={e => setChgMin(e.target.value === '' ? '' : +e.target.value)} className="input-field" />
            <input type="number" placeholder="1D % max" value={chgMax} onChange={e => setChgMax(e.target.value === '' ? '' : +e.target.value)} className="input-field" />
            <input type="number" placeholder="Mom 12M % min" value={mom12Min || ''} onChange={e => setMom12Min(+e.target.value || 0)} className="input-field" />
          </div>
          <div className="space-y-2">
            <div className="text-[10px] font-700 text-muted uppercase tracking-wide">Fundamentals</div>
            <input type="number" placeholder="P/E Fwd max" value={peMax || ''} onChange={e => setPeMax(+e.target.value || 0)} className="input-field" />
            <input type="number" placeholder="P/B max" value={pbMax || ''} onChange={e => setPbMax(+e.target.value || 0)} className="input-field" />
            <input type="number" placeholder="Div Yield % min" value={divMin || ''} onChange={e => setDivMin(+e.target.value || 0)} className="input-field" />
            <input type="number" placeholder="ROE % min" value={roeMin || ''} onChange={e => setRoeMin(+e.target.value || 0)} className="input-field" />
            <input type="number" placeholder="Beta max" value={betaMax || ''} onChange={e => setBetaMax(+e.target.value || 0)} className="input-field" />
          </div>
          <div className="space-y-2">
            <div className="text-[10px] font-700 text-muted uppercase tracking-wide">Scores & Search</div>
            <input type="number" placeholder="Value Score min" value={valMin || ''} onChange={e => setValMin(+e.target.value || 0)} className="input-field" />
            <input type="number" placeholder="Growth Score min" value={growMin || ''} onChange={e => setGrowMin(+e.target.value || 0)} className="input-field" />
            <select value={sector} onChange={e => setSector(e.target.value)} className="input-field">
              {sectors.map(s => <option key={s}>{s}</option>)}
            </select>
            <input type="text" placeholder="Search ticker / name" value={search} onChange={e => setSearch(e.target.value)} className="input-field" />
          </div>
        </div>
      </div>

      {/* Status bar + enrich button */}
      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-sm text-muted">
          <span className="text-text font-600">{filtered.length}</span> stocks ·
          enriching top <span className="text-text font-600">{candidates.length}</span> by volume
        </span>
        <button
          onClick={runEnrich}
          disabled={enriching || loading || candidates.length === 0}
          className="btn-primary flex items-center gap-2"
        >
          {enriching
            ? <><RefreshCw size={14} className="animate-spin" /> {progress}% — Loading fundamentals…</>
            : `⚡ Load & Apply (${candidates.length} stocks)`
          }
        </button>
        {enriched && <span className="text-xs text-green font-600">✅ Fundamentals & scores loaded</span>}
      </div>

      {/* Progress bar */}
      {enriching && (
        <div className="w-full bg-border rounded-full h-1">
          <div className="bg-gold h-1 rounded-full transition-all" style={{ width: `${progress}%` }} />
        </div>
      )}

      {/* Table */}
      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <StockTable
          stocks={enriched ? filtered : candidates}
          onSelect={setSelected}
          loading={loading}
        />
      </div>

      {/* Stock detail */}
      {selected && (
        <StockDetail
          stock={selected}
          onClose={() => setSelected(null)}
          onAddPortfolio={addToPortfolio}
        />
      )}
    </div>
  )
}

// ── DASHBOARD ─────────────────────────────────────────────────────
function Dashboard({ onSectorClick }: { onSectorClick: (s: string) => void }) {
  const [indices,   setIndices]   = useState<any[]>([])
  const [allStocks, setAllStocks] = useState<Stock[]>([])
  const [loading,   setLoading]   = useState(true)
  const [search,    setSearch]    = useState('')
  const [searchRes, setSearchRes] = useState<any[]>([])
  const searchTimer = useRef<any>(null)

  useEffect(() => {
    // Load indices
    apiIndices().then(setIndices)
    // Load prices from all exchanges (top 20 per exchange for speed)
    setLoading(true)
    Promise.all(
      Object.keys(EXCHANGES).map(code =>
        apiExchange(code).then(stocks => stocks.slice(0, 30))
      )
    ).then(arrays => {
      setAllStocks(arrays.flat())
      setLoading(false)
    })
  }, [])

  // Debounced search
  useEffect(() => {
    clearTimeout(searchTimer.current)
    if (search.length < 2) { setSearchRes([]); return }
    searchTimer.current = setTimeout(() => {
      apiSearch(search).then(setSearchRes)
    }, 400)
  }, [search])

  // Top 200 per market cap — gainers/losers su titoli più grandi per capitalizzazione
  const u200 = allStocks
    .sort((a, b) => {
      const am = a.mktCap || 0, bm = b.mktCap || 0
      if (am > 0 && bm > 0) return bm - am
      return (b.volume || 0) - (a.volume || 0)
    })
    .slice(0, 200)

  const valid    = u200.filter(s => s.change1d != null)
  const gainers  = [...valid].sort((a, b) => (b.change1d || 0) - (a.change1d || 0)).slice(0, 10)
  const losers   = [...valid].sort((a, b) => (a.change1d || 0) - (b.change1d || 0)).slice(0, 10)
  const ewReturn = valid.length > 0
    ? valid.reduce((a, s) => a + (s.change1d || 0), 0) / valid.length
    : null

  return (
    <div className="space-y-6 fade-in">

      {/* Search bar */}
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search ticker or company across all Eurozone markets…"
          className="input-field pl-9 text-sm"
        />
        {searchRes.length > 0 && (
          <div className="absolute top-full left-0 right-0 bg-surface border border-border rounded-lg mt-1 z-30 shadow-xl overflow-hidden">
            {searchRes.map((r: any) => (
              <div key={`${r.ticker}.${r.exchange}`}
                className="px-4 py-2.5 text-sm hover:bg-white/5 cursor-pointer flex items-center gap-3 border-b border-border last:border-0">
                <span className="font-700 text-text w-24 truncate">{r.ticker}</span>
                <span className="text-sub flex-1 truncate">{r.company}</span>
                <span className="badge badge-delay text-[9px]">{r.exchange}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Indices */}
      <div>
        <div className="section-hdr">📈 Index Performance</div>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {INDICES.map((idx, i) => {
            const d = indices.find((x: any) => x.ticker === idx.ticker)
            return (
              <IndexCard
                key={idx.ticker}
                name={idx.name}
                close={d?.close ?? null}
                changeP={d?.changeP ?? null}
                loading={indices.length === 0}
              />
            )
          })}
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Stocks — All Markets',   value: loading ? '…' : allStocks.length.toLocaleString() },
          { label: 'EW 1D Return (top 200)',        value: loading ? '…' : fp(ewReturn) },
          { label: 'Gainers Today (top 200)',        value: loading ? '…' : gainers.length.toString() },
          { label: 'Losers Today (top 200)',         value: loading ? '…' : losers.length.toString() },
        ].map(({ label, value }) => (
          <div key={label} className="metric-card">
            <div className="metric-label">{label}</div>
            <div className="metric-value">{value}</div>
          </div>
        ))}
      </div>

      {/* Gainers / Losers */}
      {!loading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[
            { title: '🟢 Top 10 Gainers', list: gainers, color: 'text-green' },
            { title: '🔴 Top 10 Losers',  list: losers,  color: 'text-red'   },
          ].map(({ title, list, color }) => (
            <div key={title} className="bg-surface border border-border rounded-lg overflow-hidden">
              <div className={`px-4 py-2 text-[10px] font-700 uppercase tracking-wide border-b border-border ${color}`}>
                {title} — Top 200 by Volume
              </div>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Company</th>
                    <th>Price €</th>
                    <th>1D %</th>
                    <th>Volume</th>
                  </tr>
                </thead>
                <tbody>
                  {list.map((s, i) => (
                    <tr key={`${s.ticker}.${s.exchange}.${i}`}>
                      <td className="font-700 text-text">{s.flag} {s.ticker}</td>
                      <td className="text-sub text-[11px]">{s.company}</td>
                      <td className="font-mono">{fv(s.price, 2)}</td>
                      <td className={`font-mono font-600 ${clr(s.change1d)}`}>{fp(s.change1d)}</td>
                      <td className="text-sub">{fmtVol(s.volume)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}

      {/* Heatmap settoriale */}
      {!loading && u200.length > 0 && (
        <div className="bg-surface border border-border rounded-lg p-4">
          <SectorHeatmap stocks={u200} onSectorClick={onSectorClick} />
        </div>
      )}

      {loading && (
        <div className="text-center py-12 text-muted">
          <RefreshCw size={24} className="animate-spin mx-auto mb-3 text-gold" />
          <p className="text-sm">Loading Eurozone market data…</p>
        </div>
      )}
    </div>
  )
}

// ── LEGAL ─────────────────────────────────────────────────────────
function Legal() {
  const sections = [
    ['Disclaimer & No Investment Advice',
     'EuroEquity Pro is operated by Andrea Meschini (Verona, Italy). All data and tools are for informational purposes only and do not constitute investment advice under MiFID II or any other applicable regulation. Nothing on this platform constitutes a personal recommendation to buy, sell, or hold any financial instrument. All investment decisions are made solely at your own risk. You should consult a qualified and authorised financial adviser before making any investment decision.'],
    ['Data Accuracy & Delay',
     'Market prices are delayed by 15–20 minutes from real-time and are provided by Leeway (leeway.tech). Fundamental data (P/E, EPS, dividends, etc.) is updated at end of trading day. Andrea Meschini makes no warranty as to accuracy, completeness, timeliness, or fitness for purpose of any data. On earnings reporting dates, forward EPS estimates may roll to the new fiscal year — exercise caution around earnings announcement dates.'],
    ['Quantitative Models',
     'Value Score and Growth Score are proprietary ranking models developed by Andrea Meschini. Rankings are calculated as: Rank(x) = (count(xi < x) + 0.5 × count(xi = x)) / N × 100, yielding integer scores from 1 (worst) to 100 (best). These scores do not guarantee future performance. Past performance is not indicative of future results.'],
    ['Portfolio Tools',
     'Portfolio tracking tools are for personal record-keeping only. Values are indicative and may not reflect actual execution prices. Andrea Meschini is not responsible for any losses arising from reliance on portfolio data. Tools do not account for transaction costs, taxes, currency risk, or market impact.'],
    ['Limitation of Liability',
     'To the maximum extent permitted by applicable law, Andrea Meschini shall not be liable for any direct, indirect, incidental, special, consequential, or punitive damages arising from use of the service, reliance on data, or any investment decisions made based on information from this platform.'],
    ['Privacy Policy (GDPR)',
     'Andrea Meschini is the data controller. We collect: name, email, country, and usage data. Legal basis: contract performance (Art. 6.1.b GDPR), legitimate interest (Art. 6.1.f), consent (Art. 6.1.a). You have the right to access, rectify, erase, restrict, and port your data. Contact: langskltdlondon@gmail.com. We respond within 30 days. Data is stored on Supabase (EU servers, Frankfurt). We do not sell personal data to third parties.'],
    ['Cookie Policy',
     'We use strictly necessary cookies only (session management, security). No advertising or third-party tracking cookies. If analytics are introduced in future, explicit consent will be requested.'],
    ['Intellectual Property',
     'All quantitative models, scoring systems, and software are the intellectual property of Andrea Meschini, protected by copyright. Market data is licensed from Leeway (leeway.tech). Redistribution of data without written permission is prohibited.'],
    ['Regulatory Status',
     'Andrea Meschini is a CFA Level III passed · IMC. Andrea Meschini is not authorised or regulated by the Financial Conduct Authority (FCA) or any other financial regulatory authority to provide investment advice or portfolio management services.'],
    ['Governing Law',
     'These terms are governed by the laws of Italy. Any disputes shall be subject to the exclusive jurisdiction of the Court of Verona (Tribunale di Verona), without prejudice to your rights as a consumer under EU law.'],
  ]

  return (
    <div className="max-w-2xl space-y-5 fade-in">
      <div className="section-hdr">📋 Legal — Andrea Meschini</div>
      <div className="text-xs text-muted">Last updated: May 2026</div>
      {sections.map(([title, body]) => (
        <div key={title} className="bg-surface border border-border rounded-lg p-4">
          <h3 className="font-700 text-text text-sm mb-2">{title}</h3>
          <p className="text-xs text-sub leading-relaxed">{body}</p>
        </div>
      ))}
      <div className="text-xs text-muted border-t border-border pt-4">
        Andrea Meschini · Verona, Italy ·{' '}
        <a href="mailto:langskltdlondon@gmail.com" className="text-gold underline">langskltdlondon@gmail.com</a>{' '}
        · © 2026
      </div>
    </div>
  )
}

// ── COOKIE BANNER ─────────────────────────────────────────────────
function CookieBanner() {
  const [visible, setVisible] = useState(false)
  useEffect(() => {
    if (typeof window !== 'undefined' && !localStorage.getItem('cookie-ok')) {
      setVisible(true)
    }
  }, [])
  if (!visible) return null
  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-surface border-t border-border
                    px-4 py-3 flex items-center justify-between gap-4 text-xs text-muted">
      <span>
        We use strictly necessary cookies.{' '}
        <span className="text-gold underline cursor-pointer">Cookie Policy</span>
      </span>
      <button
        onClick={() => { localStorage.setItem('cookie-ok','1'); setVisible(false) }}
        className="btn-primary py-1.5 px-4 text-xs whitespace-nowrap"
      >
        Accept & Close
      </button>
    </div>
  )
}

// ── ROOT APP ──────────────────────────────────────────────────────
export default function App() {
  const [page,        setPage]       = useState<Page>('dashboard')
  const [user,        setUser]       = useState<SupabaseUser | null>(null)
  const [showAuth,    setShowAuth]   = useState(false)
  const [sidebarOpen, setSidebar]    = useState(false)
  const [scrExchange, setScrExchange]= useState('MIL')
  const [scrSector,   setScrSector]  = useState('All')

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setUser(data.user ?? null))
    const { data: sub } = supabase.auth.onAuthStateChange((_, sess) => {
      setUser(sess?.user ?? null)
    })
    return () => sub.subscription.unsubscribe()
  }, [])

  function goSector(sector: string) {
    setScrExchange('EZ')
    setScrSector(sector)
    setPage('screener')
    setSidebar(false)
  }

  const nav = [
    { id: 'dashboard' as Page, label: 'Dashboard',  icon: <LayoutDashboard size={16} /> },
    { id: 'screener'  as Page, label: 'Screener',   icon: <Search size={16} /> },
    { id: 'portfolio' as Page, label: 'Portfolios', icon: <Briefcase size={16} /> },
    { id: 'legal'     as Page, label: 'Legal',      icon: <Globe size={16} /> },
  ]

  return (
    <div className="flex h-screen overflow-hidden bg-bg">

      {/* ── SIDEBAR ── */}
      <aside className={`
        flex-col w-52 bg-surface border-r border-border flex-shrink-0
        transition-all
        ${sidebarOpen ? 'flex fixed inset-y-0 left-0 z-40' : 'hidden md:flex'}
      `}>
        {/* Logo */}
        <div className="p-4 border-b border-border">
          <div className="text-gold font-700 text-lg italic leading-tight">
            EuroEquity <span className="text-text">Pro</span>
          </div>
          <div className="text-[9px] text-muted mt-0.5">Andrea Meschini · Andrea Meschini</div>
          <div className="flex gap-1 mt-2 flex-wrap">
            <span className="badge badge-beta">🧪 BETA</span>
            <span className="badge badge-live">● LIVE</span>
          </div>
        </div>

        {/* Nav items */}
        <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
          {nav.map(item => (
            <button key={item.id}
              onClick={() => { setPage(item.id); setSidebar(false) }}
              className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded text-sm font-500 transition-colors text-left ${
                page === item.id
                  ? 'bg-gold/15 text-gold'
                  : 'text-muted hover:text-text hover:bg-white/5'
              }`}
            >
              {item.icon}{item.label}
            </button>
          ))}
        </nav>

        {/* User */}
        <div className="p-3 border-t border-border space-y-2">
          {user ? (
            <>
              <div className="text-[10px] text-green font-600 truncate">👤 {user.email}</div>
              <button onClick={() => supabase.auth.signOut()}
                className="flex items-center gap-1.5 text-xs text-muted hover:text-text">
                <LogOut size={12} /> Sign out
              </button>
            </>
          ) : (
            <button onClick={() => setShowAuth(true)}
              className="btn-ghost w-full flex items-center justify-center gap-2 text-xs py-2">
              <LogIn size={14} /> Log in / Register
            </button>
          )}
        </div>

        {/* Data source */}
        <div className="px-3 pb-3 text-[9px] text-muted leading-relaxed">
          <span className="text-green font-700">● DATA</span> · Leeway<br />
          Prices: 15-20 min delay · Cache: 60s<br />
          Fundamentals: daily · Cache: 1h
        </div>
      </aside>

      {/* Overlay for mobile sidebar */}
      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-30 md:hidden" onClick={() => setSidebar(false)} />
      )}

      {/* ── MAIN ── */}
      <main className="flex-1 flex flex-col overflow-hidden">

        {/* Mobile top bar */}
        <div className="md:hidden flex items-center px-4 py-3 border-b border-border bg-surface gap-3">
          <button onClick={() => setSidebar(true)}>
            <Menu size={20} className="text-text" />
          </button>
          <span className="text-gold font-700 italic flex-1">EuroEquity <span className="text-text">Pro</span></span>
          <span className="badge badge-beta">BETA</span>
          <button onClick={() => setShowAuth(true)}>
            <User size={18} className="text-muted" />
          </button>
        </div>

        {/* Page content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 pb-20">
          {page === 'dashboard' && <Dashboard onSectorClick={goSector} />}
          {page === 'screener'  && <Screener key={`${scrExchange}-${scrSector}`} initExchange={scrExchange} initSector={scrSector} />}
          {page === 'portfolio' && <Portfolio />}
          {page === 'legal'     && <Legal />}
        </div>

        {/* Footer */}
        <footer className="border-t border-border px-4 py-2 bg-surface text-[9px] text-muted flex flex-wrap gap-x-4 gap-y-1">
          <span className="font-700 text-sub">Andrea Meschini · Italy</span>
          <span>⚠️ Not investment advice</span>
          <span>Prices delayed 15-20 min</span>
          <span>Data © Leeway</span>
          <button onClick={() => setPage('legal')} className="hover:text-gold underline">Terms</button>
          <button onClick={() => setPage('legal')} className="hover:text-gold underline">Privacy</button>
          <button onClick={() => setPage('legal')} className="hover:text-gold underline">Disclaimer</button>
          <a href="mailto:langskltdlondon@gmail.com" className="hover:text-gold">Contact</a>
          <span>© 2026 Andrea Meschini</span>
        </footer>
      </main>

      {/* Auth modal */}
      {showAuth && (
        <AuthModal onClose={() => setShowAuth(false)} onSuccess={() => setShowAuth(false)} />
      )}

      <CookieBanner />
    </div>
  )
}
