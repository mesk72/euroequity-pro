'use client'

import { useRouter } from 'next/navigation'
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
import StockDetailPage from '@/components/dashboard/StockDetailPage'
import { DEMO_STOCKS } from '@/lib/demoData'
import { computeScores } from '@/lib/ranking'

// ── FLAGS ────────────────────────────────────────────────────────
const USE_DEMO = false  // true = dati demo hardcoded
const USE_DB   = true   // true = legge da Supabase

// ── SECTOR COLORS ─────────────────────────────────────────────────
const SECTOR_COLORS: Record<string, string> = {
  'Technology':             '#3b82f6',
  'Financials':             '#f59e0b',
  'Health Care':            '#10b981',
  'Consumer Discretionary': '#f97316',
  'Industrials':            '#8b5cf6',
  'Communication Services': '#06b6d4',
  'Consumer Staples':       '#84cc16',
  'Energy':                 '#ef4444',
  'Materials':              '#a78bfa',
  'Real Estate':            '#fb7185',
  'Utilities':              '#34d399',
}
const getSectorColor = (sector: string | null | undefined): string =>
  SECTOR_COLORS[sector || ''] || '#6b7280'

// ── HELPERS ───────────────────────────────────────────────────────
const fp = (v: number | null | undefined, d = 1): string => {
  if (v == null || isNaN(v)) return '-'
  return `${v >= 0 ? '+' : ''}${v.toFixed(d)}%`
}
const fv = (v: number | null | undefined, d = 2): string => {
  if (v == null || isNaN(v)) return '-'
  return v.toFixed(d)
}
const fn = (v: number | null | undefined): string => {
  if (v == null || isNaN(v as number)) return '-'
  return String(Math.round(v as number))
}
const clr = (v: number | null | undefined): string => {
  if (v == null) return 'text-sub'
  return v > 0 ? 'text-green' : v < 0 ? 'text-red' : 'text-sub'
}
const fmtVol = (v: number | null | undefined): string => {
  if (!v) return '-'
  if (v >= 1e6) return `${(v/1e6).toFixed(1)}M`
  if (v >= 1e3) return `${(v/1e3).toFixed(0)}k`
  return String(v)
}

// ── SCORE BAR ─────────────────────────────────────────────────────
function ScoreBar({ value, label }: { value: number | null | undefined; label: string }) {
  if (value == null) return (
    <div>
      <div className="text-[9px] text-muted uppercase tracking-wide mb-1">{label}</div>
      <div className="text-xs text-muted font-mono">-</div>
    </div>
  )
  const color = value >= 70 ? '#22c55e' : value >= 40 ? '#f97316' : '#ef4444'
  return (
    <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-[9px] text-muted uppercase tracking-wide">{label}</span>
        <span className="text-xs font-700 font-mono" style={{ color }}>{Math.round(value)}</span>
      </div>
      <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${value}%`, background: color }} />
      </div>
    </div>
  )
}

type Page = 'dashboard' | 'screener' | 'portfolio' | 'legal'

// ── API CALLS ──────────────────────────────────────────────────────
async function apiExchange(code: string): Promise<Stock[]> {
  if (USE_DEMO) {
    const scored = computeScores([...DEMO_STOCKS])
    if (code === 'EZ') return scored
    return scored.filter(s => s.exchange === code)
  }
  if (USE_DB) {
    try {
      const url = code === 'EZ' ? '/api/db/stocks' : `/api/db/stocks?exchange=${code}`
      const r = await fetch(url)
      if (r.ok) {
        const d = await r.json()
        return d.stocks || []
      }
    } catch {}
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
    const hasData = live.some(s => s.price != null && s.price > 0)
    if (!hasData) {
      const scored = computeScores([...DEMO_STOCKS])
      if (code === 'EZ') return scored
      return scored.filter(s => s.exchange === code)
    }
    return live
  } catch {
    const scored = computeScores([...DEMO_STOCKS])
    if (code === 'EZ') return scored
    return scored.filter(s => s.exchange === code)
  }
}

async function apiHistory(ticker: string, exchange: string, days: number) {
  const endpoint = USE_DB
    ? `/api/db/history?ticker=${ticker}&exchange=${exchange}&days=${days}`
    : `/api/history?ticker=${ticker}&exchange=${exchange}&days=${days}`
  try {
    const r = await fetch(endpoint)
    if (!r.ok) return []
    const d = await r.json()
    return d.history || []
  } catch { return [] }
}

async function apiIndices() {
  const endpoint = USE_DB ? '/api/db/indices' : '/api/indices'
  try {
    const r = await fetch(endpoint)
    if (!r.ok) return []
    const d = await r.json()
    return d.indices || []
  } catch { return [] }
}

// ── INDEX CARD ─────────────────────────────────────────────────────
function IndexCard({ name, close, changeP, loading }: {
  name: string; close: number | null; changeP: number | null; loading: boolean
}) {
  return (
    <div className="index-card">
      <div style={{
        fontSize: 11, fontFamily: 'IBM Plex Sans Condensed, sans-serif',
        fontWeight: 700, color: '#ffffff', letterSpacing: '0.03em',
        marginBottom: 4, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis',
      }}>{name}</div>
      {loading ? (
        <div className="shimmer h-4 w-16 mt-1" />
      ) : close ? (
        <>
          <div style={{
            fontFamily: 'IBM Plex Mono, monospace', fontWeight: 700, fontSize: 14,
            color: (changeP || 0) >= 0 ? 'var(--green)' : 'var(--red)',
          }}>{fp(changeP)}</div>
          <div style={{
            fontFamily: 'IBM Plex Mono, monospace', fontSize: 10,
            color: 'var(--text3)', marginTop: 2,
          }}>{close.toLocaleString('de-DE', { maximumFractionDigits: 1 })}</div>
        </>
      ) : (
        <div style={{ fontSize: 10, color: 'var(--text4)' }}>-</div>
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
  { key: 'price',       label: 'Price',     width: 75  },
  { key: 'change1d',    label: '1D %',      width: 65  },
  { key: 'mktCap',      label: 'MktCap B',  width: 80  },
  { key: 'peTrail',     label: 'P/E Tr.',   width: 65  },
  { key: 'peFwd',       label: 'P/E Fwd',   width: 65  },
  { key: 'pb',          label: 'P/B',       width: 55  },
  { key: 'evEbitda',    label: 'EV/EBITDA', width: 88  },
  { key: 'roe',         label: 'ROE %',     width: 72  },
  { key: 'divYield',    label: 'Div %',     width: 72  },
  { key: 'divPayout',   label: 'Payout %',  width: 72  },
  { key: 'beta',        label: 'Beta',      width: 60  },
  { key: 'epsGrowth',   label: 'EPS Gr%',   width: 72  },
  { key: 'revGrowth',   label: 'Rev Gr%',   width: 72  },
  { key: 'mom1w',       label: '1W %',      width: 65  },
  { key: 'mom1m',       label: '1M %',      width: 65  },
  { key: 'mom6m',       label: '6M %',      width: 65  },
  { key: 'mom12m',      label: '12M %',     width: 72  },
  { key: 'valueScore',  label: 'Value',     width: 55  },
  { key: 'growthScore', label: 'Growth',    width: 60  },
]

function cellFmt(s: Stock, key: SortKey): { val: string; cls: string; sectorColor?: string } {
  const v = s[key] as number | null
  switch (key) {
    case 'ticker':      return { val: `${s.flag || ''} ${s.ticker}`, cls: 'font-600 text-text' }
    case 'company':     return { val: s.company || '-',   cls: 'text-sub' }
    case 'sector':      return { val: s.sector  || '-',   cls: 'text-[10px]', sectorColor: getSectorColor(s.sector) }
    case 'price':       return { val: v != null ? fv(v, 2)  : '-', cls: v != null ? 'text-text'  : 'text-muted' }
    case 'change1d':    return { val: v != null ? fp(v)     : '-', cls: v != null ? clr(v)        : 'text-muted' }
    case 'mktCap':      return { val: v != null ? fv(v, 1)  : '-', cls: v != null ? 'text-sub'    : 'text-muted' }
    case 'peTrail':     return { val: v != null ? fv(v, 1)  : '-', cls: v != null ? 'text-sub'    : 'text-muted' }
    case 'peFwd':       return { val: v != null ? fv(v, 1)  : '-', cls: v != null ? 'text-sub'    : 'text-muted' }
    case 'pb':          return { val: v != null ? fv(v, 2)  : '-', cls: v != null ? 'text-sub'    : 'text-muted' }
    case 'evEbitda':    return { val: v != null ? fv(v, 1)  : '-', cls: v != null ? 'text-sub'    : 'text-muted' }
    case 'roe':         return { val: v != null ? fp(v)     : '-', cls: v != null ? clr(v)        : 'text-muted' }
    case 'divYield':    return { val: v != null ? fp(v)     : '-', cls: v != null ? (v > 0 ? 'text-green' : 'text-sub') : 'text-muted' }
    case 'divPayout':   return { val: v != null ? fp(v)     : '-', cls: v != null ? 'text-sub'    : 'text-muted' }
    case 'beta':        return { val: v != null ? fv(v, 2)  : '-', cls: v != null ? 'text-sub'    : 'text-muted' }
    case 'epsGrowth':   return { val: v != null ? fp(v)     : '-', cls: v != null ? clr(v)        : 'text-muted' }
    case 'revGrowth':   return { val: v != null ? fp(v)     : '-', cls: v != null ? clr(v)        : 'text-muted' }
    case 'mom1w':       return { val: v != null ? fp(v)     : '-', cls: v != null ? clr(v)        : 'text-muted' }
    case 'mom1m':       return { val: v != null ? fp(v)     : '-', cls: v != null ? clr(v)        : 'text-muted' }
    case 'mom6m':       return { val: v != null ? fp(v)     : '-', cls: v != null ? clr(v)        : 'text-muted' }
    case 'mom12m':      return { val: v != null ? fp(v)     : '-', cls: v != null ? clr(v)        : 'text-muted' }
    case 'valueScore':  return { val: v != null ? fn(v)     : '-', cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-red' : 'text-yellow-400 font-600') : 'text-muted' }
    case 'growthScore': return { val: v != null ? fn(v)     : '-', cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-red' : 'text-yellow-400 font-600') : 'text-muted' }
    default:            return { val: '-', cls: 'text-muted' }
  }
}

function StockTable({ stocks, onSelect, loading, maxRows = 100 }: {
  stocks: Stock[]
  onSelect: (s: Stock) => void
  loading?: boolean
  maxRows?: number
}) {
  const [sortKey, setSortKey] = useState<SortKey>('mktCap')
  const [sortAsc, setSortAsc] = useState(false)

  const sorted = [...stocks].sort((a, b) => {
    const av = a[sortKey] as any
    const bv = b[sortKey] as any
    if (av == null && bv == null) return 0
    if (av == null) return 1
    if (bv == null) return -1
    if (typeof av === 'string') return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av)
    return sortAsc ? av - bv : bv - av
  }).slice(0, maxRows)

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
      <div className="text-[9px] text-muted px-3 py-1 border-b border-border bg-surface/50">
        ⚠️ Prices delayed 15-20 min · Fundamentals updated daily
      </div>
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
              onClick={() => { onSelect(s); window.location.href = `/stock/${s.ticker}-${s.exchange}` }}
              className="cursor-pointer"
            >
              {COLUMNS.map(c => {
                const { val, cls, sectorColor } = cellFmt(s, c.key)
                return (
                  <td key={c.key} style={{ maxWidth: c.width }}>
                    {c.key === 'sector' && sectorColor ? (
                      <span className="truncate block text-[10px] font-600"
                        style={{ color: sectorColor }}>
                        {val}
                      </span>
                    ) : (
                      <span className={`truncate block ${cls}`}>{val}</span>
                    )}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
      {stocks.length > maxRows && (
        <div className="text-[10px] text-muted text-center py-2 border-t border-border">
          Showing top {maxRows} of {stocks.length} results by market cap
        </div>
      )}
    </div>
  )
}

// ── PRICE CHART (SVG) ──────────────────────────────────────────────
function PriceChart({ history }: { history: any[] }) {
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
        {[0.25, 0.5, 0.75].map(r => (
          <line key={r} x1={PAD} y1={PAD + r * (H - 2 * PAD)}
            x2={W - PAD} y2={PAD + r * (H - 2 * PAD)}
            stroke="#1e2840" strokeWidth="1" />
        ))}
        <polygon points={`${pts} ${W - PAD},${H - PAD} ${PAD},${H - PAD}`}
          fill={color} fillOpacity="0.08" />
        <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
        {(() => {
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
function StockDetail({ stock, onClose, onAddPortfolio, portfolioNames }: {
  stock: Stock
  onClose: () => void
  onAddPortfolio: (stock: Stock, qty: number, price: number, pf: string) => void
  portfolioNames: string[]
}) {
  const [chartDays, setChartDays] = useState(365)
  const [history,   setHistory]   = useState<any[]>([])
  const [loadingChart, setLoadingChart] = useState(true)
  const [qty,  setQty]  = useState('')
  const [px,   setPx]   = useState(stock.price?.toFixed(2) || '')
  const [pf,   setPf]   = useState(portfolioNames[0] || 'Portfolio 1')

  useEffect(() => {
    setLoadingChart(true)
    apiHistory(stock.ticker, stock.exchange, chartDays).then(h => {
      setHistory(h)
      setLoadingChart(false)
    })
  }, [stock.ticker, stock.exchange, chartDays])

  const metrics: [string, string, string][] = [
    ['Price',        fv(stock.price, 2),       ''],
    ['1D %',         fp(stock.change1d),        clr(stock.change1d)],
    ['Mkt Cap B',    fv(stock.mktCap, 1),       ''],
    ['P/E Trailing', fv(stock.peTrail, 1),      ''],
    ['P/E Fwd',      fv(stock.peFwd, 1),        ''],
    ['P/B',          fv(stock.pb, 2),           ''],
    ['EV/EBITDA',    fv(stock.evEbitda, 1),     ''],
    ['ROE %',        fp(stock.roe),             clr(stock.roe)],
    ['Div Yield %',  fp(stock.divYield),        stock.divYield && stock.divYield > 0 ? 'text-green' : ''],
    ['Beta',         fv(stock.beta, 2),         ''],
    ['EPS Gr %',     fp(stock.epsGrowth),       clr(stock.epsGrowth)],
    ['Rev Gr %',     fp(stock.revGrowth),       clr(stock.revGrowth)],
    ['Mom 1W %',     fp(stock.mom1w),           clr(stock.mom1w)],
    ['Mom 1M %',     fp(stock.mom1m),           clr(stock.mom1m)],
    ['Mom 6M %',     fp(stock.mom6m),           clr(stock.mom6m)],
    ['Mom 12M %',    fp(stock.mom12m),          clr(stock.mom12m)],
    ['Sector',       stock.sector || '-',       ''],
    ['Country',      stock.country || '-',      ''],
  ]

  return (
    <div className="mt-4 bg-surface border border-border rounded-lg overflow-hidden fade-in">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div>
          <div className="font-700 text-base text-text">
            {stock.flag} {stock.ticker}
            <span className={`ml-2 font-mono text-sm ${clr(stock.change1d)}`}>{fp(stock.change1d)}</span>
          </div>
          <div className="text-xs text-muted">{stock.company} · {stock.exchange}</div>
          {stock.sector && (
            <span className="text-[10px] font-600 mt-1 inline-block"
              style={{ color: getSectorColor(stock.sector) }}>
              {stock.sector}
            </span>
          )}
        </div>
        <button onClick={onClose} className="text-muted hover:text-text p-1">
          <X size={16} />
        </button>
      </div>

      {/* Score bars */}
      <div className="px-4 pt-3 pb-2 grid grid-cols-2 gap-4 border-b border-border">
        <ScoreBar value={stock.valueScore}  label="Value Score" />
        <ScoreBar value={stock.growthScore} label="Growth Score" />
      </div>

      <div className="p-4 grid grid-cols-3 md:grid-cols-6 gap-2">
        {metrics.map(([label, value, color]) => (
          <div key={label} className="metric-card">
            <div className="metric-label">{label}</div>
            <div className={`font-mono font-600 text-sm ${color || 'text-gold'}`}>{value}</div>
          </div>
        ))}
      </div>

      <div className="px-4 pb-2">
        <div className="flex gap-2 mb-2">
          {([['1Y', 365], ['3Y', 1095], ['5Y', 1825]] as [string, number][]).map(([lbl, d]) => (
            <button key={lbl} onClick={() => setChartDays(d)}
              className={`px-3 py-1 text-xs rounded border transition-colors ${
                chartDays === d ? 'bg-gold text-bg border-gold' : 'border-border text-muted hover:border-gold'
              }`}>
              {lbl}
            </button>
          ))}
        </div>
        <div className="text-[9px] text-muted mb-1">⚠️ Prices delayed 15-20 min</div>
        <div className="bg-bg border border-border rounded-lg overflow-hidden">
          {loadingChart
            ? <div className="h-48 flex items-center justify-center"><RefreshCw size={16} className="animate-spin text-gold" /></div>
            : <PriceChart history={history} />
          }
        </div>
      </div>

      <div className="px-4 py-3 border-t border-border">
        <div className="text-xs font-700 text-muted uppercase tracking-wide mb-2">Add to Portfolio</div>
        <div className="flex flex-wrap gap-2">
          <select value={pf} onChange={e => setPf(e.target.value)} className="input-field w-40">
            {portfolioNames.map(p => <option key={p}>{p}</option>)}
          </select>
          <input type="number" placeholder="Qty" value={qty} onChange={e => setQty(e.target.value)} className="input-field w-24" />
          <input type="number" placeholder="Buy price" value={px} onChange={e => setPx(e.target.value)} className="input-field w-32" />
          <button
            onClick={() => {
              if (!qty || !px) return
              onAddPortfolio(stock, parseFloat(qty), parseFloat(px), pf)
              toast.success(`${stock.ticker} added to ${pf}`)
            }}
            className="btn-primary">
            ➕ Add
          </button>
        </div>
      </div>
    </div>
  )
}

// ── SCREENER ──────────────────────────────────────────────────────
function Screener({ initExchange = 'MIL', initSector = 'All', initEpsMom = '', onSelectStock }: {
  initExchange?: string
  initSector?:   string
  initEpsMom?:   string
  onSelectStock?: (s: Stock) => void
}) {
  const [exchange,  setExchange]  = useState(initExchange)
  const [stocks,    setStocks]    = useState<Stock[]>([])
  const [loading,   setLoading]   = useState(false)
  const [selected,  setSelected]  = useState<Stock | null>(null)
  const [portfolioNames, setPortfolioNames] = useState<string[]>(['Portfolio 1', 'Portfolio 2', 'Portfolio 3'])

  // Filters
  const [search,   setSearch]   = useState('')
  const [sector,   setSector]   = useState(initSector)
  const [valMin,   setValMin]   = useState(0)
  const [growMin,  setGrowMin]  = useState(0)
  const [peMax,    setPeMax]    = useState(0)
  const [pbMax,    setPbMax]    = useState(0)
  const [divMin,   setDivMin]   = useState(0)
  const [mom12Min, setMom12Min] = useState(0)

  useEffect(() => {
    // Carica nomi portafogli
    const stored = JSON.parse(localStorage.getItem('portfolios') || '{}')
    const names = Object.keys(stored)
    if (names.length > 0) setPortfolioNames(names)
  }, [])

  useEffect(() => {
    setStocks([]); setSelected(null); setLoading(true)
    const exchToLoad = initEpsMom ? 'EZ' : exchange
    apiExchange(exchToLoad).then(data => {
      setStocks(data)
      setLoading(false)
    })
  }, [exchange, initEpsMom])

  const filtered = stocks.filter(s => {
    if (search) {
      const q = search.toLowerCase()
      if (!s.ticker.toLowerCase().includes(q) && !(s.company || '').toLowerCase().includes(q)) return false
    }
    if (sector !== 'All' && s.sector !== sector) return false
    if (initEpsMom === 'epsMomPos' && (s.epsMom30d == null || s.epsMom30d <= 0)) return false
    if (initEpsMom === 'epsMomNeg' && (s.epsMom30d == null || s.epsMom30d >= 0)) return false
    if (peMax  > 0 && s.peFwd    != null && s.peFwd    > peMax)  return false
    if (pbMax  > 0 && s.pb       != null && s.pb       > pbMax)  return false
    if (divMin > 0 && (s.divYield || 0)                < divMin) return false
    if (mom12Min>0 && (s.mom12m  || 0)                 < mom12Min) return false
    if (valMin > 0 && (s.valueScore  || 0)             < valMin) return false
    if (growMin> 0 && (s.growthScore || 0)             < growMin) return false
    return true
  })

  const sectors = ['All', ...Array.from(
    new Set(stocks.map(s => s.sector).filter(Boolean) as string[])
  ).sort()]

  function addToPortfolio(stock: Stock, qty: number, price: number, pf: string) {
    const stored = JSON.parse(localStorage.getItem('portfolios') || '{}')
    if (!stored[pf]) stored[pf] = []
    stored[pf].push({
      ticker: stock.ticker, exchange: stock.exchange,
      company: stock.company, flag: stock.flag,
      qty, buy_price: price, added_at: new Date().toISOString(),
      })
    localStorage.setItem('portfolios', JSON.stringify(stored))
    const names = Object.keys(stored)
    setPortfolioNames(names)
  }

  return (
    <div className="space-y-4 fade-in">
      {/* Exchange tabs */}
      <div className="flex flex-wrap gap-1.5">
        <button onClick={() => setExchange('EZ')}
          className={`px-3 py-1.5 rounded text-xs font-600 border transition-colors ${exchange === 'EZ' ? 'bg-gold text-bg border-gold' : 'border-border text-muted hover:border-gold hover:text-gold'}`}>
          🌍 All Eurozone
        </button>
        {Object.entries(EXCHANGES).map(([code, meta]) => (
          <button key={code} onClick={() => setExchange(code)}
            className={`px-3 py-1.5 rounded text-xs font-600 border transition-colors ${exchange === code ? 'bg-gold text-bg border-gold' : 'border-border text-muted hover:border-gold hover:text-gold'}`}>
            {meta.flag} {meta.label}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="bg-surface border border-border rounded-lg p-4">
        <div className="section-hdr mb-3">Filters</div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="space-y-2">
            <div className="text-[10px] font-700 text-muted uppercase tracking-wide">Valuation</div>
            <input type="number" placeholder="P/E Fwd max" value={peMax || ''} onChange={e => setPeMax(+e.target.value || 0)} className="input-field" />
            <input type="number" placeholder="P/B max" value={pbMax || ''} onChange={e => setPbMax(+e.target.value || 0)} className="input-field" />
            <input type="number" placeholder="Div Yield % min" value={divMin || ''} onChange={e => setDivMin(+e.target.value || 0)} className="input-field" />
          </div>
          <div className="space-y-2">
            <div className="text-[10px] font-700 text-muted uppercase tracking-wide">Momentum</div>
            <input type="number" placeholder="Mom 12M % min" value={mom12Min || ''} onChange={e => setMom12Min(+e.target.value || 0)} className="input-field" />
          </div>
          <div className="space-y-2">
            <div className="text-[10px] font-700 text-muted uppercase tracking-wide">Scores</div>
            <input type="number" placeholder="Value Score min" value={valMin || ''} onChange={e => setValMin(+e.target.value || 0)} className="input-field" />
            <input type="number" placeholder="Growth Score min" value={growMin || ''} onChange={e => setGrowMin(+e.target.value || 0)} className="input-field" />
          </div>
          <div className="space-y-2">
            <div className="text-[10px] font-700 text-muted uppercase tracking-wide">Search & Sector</div>
            <input type="text" placeholder="Search ticker / name" value={search} onChange={e => setSearch(e.target.value)} className="input-field" />
            <select value={sector} onChange={e => setSector(e.target.value)} className="input-field">
              {sectors.map(s => <option key={s}>{s}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="flex items-center gap-3 flex-wrap text-sm text-muted">
        <span><span className="text-text font-600">{filtered.length}</span> stocks · showing top 100 by market cap</span>
        <span className="text-[10px]">⚠️ Prices delayed 15-20 min</span>
      </div>

      {/* Table */}
      <div className="bg-surface border border-border rounded-lg overflow-hidden">
        <StockTable
          stocks={filtered}
          onSelect={(s) => { setSelected(s); if (onSelectStock) onSelectStock(s) }}
          loading={loading}
          maxRows={100}
        />
      </div>

      {selected && (
        <StockDetail
          stock={selected}
          onClose={() => setSelected(null)}
          onAddPortfolio={addToPortfolio}
          portfolioNames={portfolioNames}
        />
      )}
    </div>
  )
}

// ── DASHBOARD ─────────────────────────────────────────────────────
function Dashboard({ onSectorClick, onSelectStock, onGoScreener }: {
  onSectorClick: (s: string) => void
  onSelectStock?: (s: Stock) => void
  onGoScreener?: (filter: string) => void
}) {
  const [indices,   setIndices]   = useState<any[]>([])
  const [allStocks, setAllStocks] = useState<Stock[]>([])
  const [loading,   setLoading]   = useState(true)
  const [search,    setSearch]    = useState('')
  const [searchRes, setSearchRes] = useState<any[]>([])
  const searchTimer = useRef<any>(null)

  useEffect(() => {
    // Aggiorna indici ogni 60 secondi
    const loadIndices = () => apiIndices().then(setIndices)
    loadIndices()
    const timer = setInterval(loadIndices, 60000)

    setLoading(true)
    Promise.all(
      Object.keys(EXCHANGES).map(code =>
        apiExchange(code).then(stocks => stocks.slice(0, 30))
      )
    ).then(arrays => {
      setAllStocks(arrays.flat())
      setLoading(false)
    })

    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    clearTimeout(searchTimer.current)
    if (search.length < 2) { setSearchRes([]); return }
    searchTimer.current = setTimeout(async () => {
      if (USE_DB) {
        try {
          const r = await fetch(`/api/db/stocks?search=${encodeURIComponent(search)}&limit=10`)
          if (r.ok) {
            const d = await r.json()
            setSearchRes(d.stocks || [])
            return
          }
        } catch {}
      }
      const q = search.toLowerCase()
      const results = computeScores([...DEMO_STOCKS])
        .filter((s: any) => s.ticker.toLowerCase().includes(q) || (s.company||'').toLowerCase().includes(q))
        .slice(0, 10)
      setSearchRes(results)
    }, 200)
  }, [search])

  // Top 200 per market cap
  const u200 = allStocks
    .sort((a, b) => (b.mktCap || 0) - (a.mktCap || 0))
    .slice(0, 200)

  const valid   = u200.filter(s => s.change1d != null)
  const gainers = [...valid].sort((a, b) => (b.change1d || 0) - (a.change1d || 0)).slice(0, 10)
  const losers  = [...valid].sort((a, b) => (a.change1d || 0) - (b.change1d || 0)).slice(0, 10)
  const ewReturn = valid.length > 0
    ? valid.reduce((a, s) => a + (s.change1d || 0), 0) / valid.length
    : null

  // EPS Growth top/bottom 10 su tutto l'universo
  const allWithEpsGrowth = allStocks.filter(s => s.epsGrowth != null)
  const topEpsGrowth = [...allWithEpsGrowth].sort((a, b) => (b.epsGrowth || 0) - (a.epsGrowth || 0)).slice(0, 10)
  const botEpsGrowth = [...allWithEpsGrowth].sort((a, b) => (a.epsGrowth || 0) - (b.epsGrowth || 0)).slice(0, 10)

  // Price Momentum 12M top/bottom 10
  const allWithMom12 = allStocks.filter(s => s.mom12m != null)
  const topMom12 = [...allWithMom12].sort((a, b) => (b.mom12m || 0) - (a.mom12m || 0)).slice(0, 10)
  const botMom12 = [...allWithMom12].sort((a, b) => (a.mom12m || 0) - (b.mom12m || 0)).slice(0, 10)

  // KPI V+G >= 80
  const highVG = allStocks.filter(s =>
    s.valueScore != null && s.growthScore != null &&
    (s.valueScore + s.growthScore) >= 80
  ).length

  return (
    <div className="space-y-6 fade-in">

      {/* Search */}
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search ticker or company…"
          className="input-field pl-9 text-sm"
        />
        {searchRes.length > 0 && (
          <div className="absolute top-full left-0 right-0 bg-surface border border-border rounded-lg mt-1 z-30 shadow-xl overflow-hidden">
            {searchRes.map((r: any) => (
              <div key={`${r.ticker}.${r.exchange}`}
                onClick={() => window.location.href = `/stock/${r.ticker}-${r.exchange}`}
                className="px-4 py-2.5 text-sm hover:bg-white/5 cursor-pointer flex items-center gap-3 border-b border-border last:border-0">
                <span style={{ fontSize:15 }}>{r.flag || ''}</span>
                <span className="font-700 text-text w-24 truncate">{r.ticker}</span>
                <span className="text-sub flex-1 truncate">{r.company}</span>
                <span style={{ fontFamily:'IBM Plex Mono', fontSize:11, color:'var(--text3)' }}>{r.price?.toFixed(2)||'-'}</span>
                <span className="badge badge-delay text-[9px]">{r.exchange}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Indices — aggiornati automaticamente ogni 60s */}
      <div>
        <div className="section-hdr flex items-center gap-2">
          📈 Index Performance
          <span className="text-[9px] text-muted font-normal">· auto-refresh 60s · delayed 15-20 min</span>
        </div>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {INDICES.map((idx) => {
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
          { label: 'Total Stocks',              value: loading ? '…' : allStocks.length.toLocaleString() },
          { label: 'EW 1D Return (top 200)',    value: loading ? '…' : fp(ewReturn) },
          { label: 'V+G ≥ 80 (All Markets)',    value: loading ? '…' : highVG.toString() },
          { label: 'Gainers Today (top 200)',   value: loading ? '…' : gainers.length.toString() },
        ].map(({ label, value }) => (
          <div key={label} className="metric-card">
            <div className="metric-label">{label}</div>
            <div className="metric-value">{value}</div>
          </div>
        ))}
      </div>

      {/* Gainers / Losers today — top 200 market cap */}
      {!loading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[
            { title: '🟢 Top 10 Gainers Today', list: gainers, color: 'text-green', field: 'change1d' },
            { title: '🔴 Top 10 Losers Today',  list: losers,  color: 'text-red',   field: 'change1d' },
          ].map(({ title, list, color, field }) => (
            <div key={title} className="bg-surface border border-border rounded-lg overflow-hidden">
              <div className={`px-4 py-2 text-[10px] font-700 uppercase tracking-wide border-b border-border ${color}`}>
                {title} — Top 200 by Market Cap · <span className="font-normal opacity-70">⚠️ 15-20 min delay</span>
              </div>
              <table className="data-table">
                <thead><tr>
                  <th>Ticker</th><th>Company</th><th>Price</th><th>1D %</th>
                </tr></thead>
                <tbody>
                  {list.map((s, i) => (
                    <tr key={i}
                      onClick={() => window.location.href = `/stock/${s.ticker}-${s.exchange}`}
                      className="cursor-pointer">
                      <td className="font-700 text-text">{s.flag} {s.ticker}</td>
                      <td className="text-sub text-[11px]">{s.company}</td>
                      <td className="font-mono">{fv(s.price, 2)}</td>
                      <td className={`font-mono font-600 ${clr(s.change1d)}`}>{fp(s.change1d)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}

      {/* Top 10 EPS Growth */}
      {!loading && topEpsGrowth.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[
            { title: '📈 Top 10 EPS Growth (All Universe)', list: topEpsGrowth, color: 'var(--green)' },
            { title: '📉 Bottom 10 EPS Growth (All Universe)', list: botEpsGrowth, color: 'var(--red)' },
          ].map(({ title, list, color }) => (
            <div key={title} className="bg-surface border border-border rounded-lg overflow-hidden">
              <div className="px-4 py-2 text-[10px] font-700 uppercase tracking-wide border-b border-border"
                style={{ color }}>
                {title}
              </div>
              <table className="data-table">
                <thead><tr>
                  <th>Ticker</th><th>Company</th><th>Sector</th><th>EPS Gr %</th>
                </tr></thead>
                <tbody>
                  {list.map((s, i) => (
                    <tr key={i}
                      onClick={() => window.location.href = `/stock/${s.ticker}-${s.exchange}`}
                      className="cursor-pointer">
                      <td>
                        <span className="font-700" style={{ color: 'var(--orange)' }}>{s.flag} {s.ticker}</span>
                      </td>
                      <td className="text-sub text-[11px]">{s.company}</td>
                      <td>
                        <span className="text-[10px] font-600" style={{ color: getSectorColor(s.sector) }}>
                          {s.sector || '-'}
                        </span>
                      </td>
                      <td>
                        <span className="font-mono font-600" style={{ color: (s.epsGrowth||0) >= 0 ? 'var(--green)' : 'var(--red)' }}>
                          {fp(s.epsGrowth)}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}

      {/* Top 10 Price Momentum 12M */}
      {!loading && topMom12.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[
            { title: '🚀 Top 10 Price Mom 12M (All Universe)', list: topMom12, color: 'var(--green)' },
            { title: '💣 Bottom 10 Price Mom 12M (All Universe)', list: botMom12, color: 'var(--red)' },
          ].map(({ title, list, color }) => (
            <div key={title} className="bg-surface border border-border rounded-lg overflow-hidden">
              <div className="px-4 py-2 text-[10px] font-700 uppercase tracking-wide border-b border-border"
                style={{ color }}>
                {title}
              </div>
              <table className="data-table">
                <thead><tr>
                  <th>Ticker</th><th>Company</th><th>Sector</th><th>Mom 12M %</th>
                </tr></thead>
                <tbody>
                  {list.map((s, i) => (
                    <tr key={i}
                      onClick={() => window.location.href = `/stock/${s.ticker}-${s.exchange}`}
                      className="cursor-pointer">
                      <td>
                        <span className="font-700" style={{ color: 'var(--orange)' }}>{s.flag} {s.ticker}</span>
                      </td>
                      <td className="text-sub text-[11px]">{s.company}</td>
                      <td>
                        <span className="text-[10px] font-600" style={{ color: getSectorColor(s.sector) }}>
                          {s.sector || '-'}
                        </span>
                      </td>
                      <td>
                        <span className="font-mono font-700" style={{ color: (s.mom12m||0) >= 0 ? 'var(--green)' : 'var(--red)' }}>
                          {fp(s.mom12m)}
                        </span>
                      </td>
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
          <p className="text-sm">Loading market data…</p>
        </div>
      )}
    </div>
  )
}

// ── LEGAL ─────────────────────────────────────────────────────────
function Legal() {
  const sections = [
    ['Disclaimer & No Investment Advice',
     'ForwardAlpha is operated by Andrea Meschini (Verona, Italy). All data and tools are for informational purposes only and do not constitute investment advice under MiFID II or any other applicable regulation. Nothing on this platform constitutes a personal recommendation to buy, sell, or hold any financial instrument. All investment decisions are made solely at your own risk.'],
    ['Data Accuracy & Delay',
     'Market prices are delayed by 15–20 minutes from real-time. Fundamental data is updated at end of trading day. Andrea Meschini makes no warranty as to accuracy, completeness, timeliness, or fitness for purpose of any data.'],
    ['Quantitative Models',
     'Value Score and Growth Score are proprietary ranking models. Rankings are calculated as percentile scores from 1 (worst) to 100 (best). These scores do not guarantee future performance.'],
    ['Privacy Policy (GDPR)',
     'Andrea Meschini is the data controller. Contact: andrea@forwardalpha.pro. Data is stored on Supabase (EU servers). We do not sell personal data to third parties.'],
    ['Governing Law',
     'These terms are governed by the laws of Italy. Any disputes shall be subject to the exclusive jurisdiction of the Court of Verona.'],
  ]

  return (
    <div className="max-w-2xl space-y-5 fade-in">
      <div className="section-hdr">📋 Legal — ForwardAlpha</div>
      <div className="text-xs text-muted">Last updated: May 2026</div>
      {sections.map(([title, body]) => (
        <div key={title} className="bg-surface border border-border rounded-lg p-4">
          <h3 className="font-700 text-text text-sm mb-2">{title}</h3>
          <p className="text-xs text-sub leading-relaxed">{body}</p>
        </div>
      ))}
      <div className="text-xs text-muted border-t border-border pt-4">
        Andrea Meschini · Verona, Italy ·{' '}
        <a href="mailto:andrea@forwardalpha.pro" className="text-gold underline">andrea@forwardalpha.pro</a>{' '}
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
    <div className="fixed bottom-0 left-0 right-0 z-50 bg-surface border-t border-border px-4 py-3 flex items-center justify-between gap-4 text-xs text-muted">
      <span>We use strictly necessary cookies.</span>
      <button
        onClick={() => { localStorage.setItem('cookie-ok','1'); setVisible(false) }}
        className="btn-primary py-1.5 px-4 text-xs whitespace-nowrap">
        Accept & Close
      </button>
    </div>
  )
}

// ── ROOT APP ──────────────────────────────────────────────────────
export default function App() {
  const [page,        setPage]        = useState<Page>('dashboard')
  const [user,        setUser]        = useState<SupabaseUser | null>(null)
  const [showAuth,    setShowAuth]    = useState(false)
  const [sidebarOpen, setSidebar]     = useState(false)
  const [scrExchange, setScrExchange] = useState('MIL')
  const [scrSector,   setScrSector]   = useState('All')
  const [scrEpsMom,   setScrEpsMom]   = useState<string>('')
  const [detailStock, setDetailStock] = useState<Stock | null>(null)

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setUser(data.user ?? null))
    const { data: sub } = supabase.auth.onAuthStateChange((_, sess) => {
      setUser(sess?.user ?? null)
    })
    return () => sub.subscription.unsubscribe()
  }, [])

  function goSector(sector: string) {
    setScrExchange('EZ'); setScrSector(sector); setScrEpsMom(''); setPage('screener'); setSidebar(false)
  }

  function goScreenerEpsMom(filter: string) {
    setScrExchange('EZ'); setScrSector('All'); setScrEpsMom(filter); setPage('screener'); setSidebar(false)
  }

  const nav = [
    { id: 'dashboard' as Page, label: 'Dashboard',  icon: <LayoutDashboard size={16} /> },
    { id: 'screener'  as Page, label: 'Screener',   icon: <Search size={16} /> },
    { id: 'portfolio' as Page, label: 'Portfolios', icon: <Briefcase size={16} /> },
    { id: 'legal'     as Page, label: 'Legal',      icon: <Globe size={16} /> },
  ]

  const externalNav = [
    { href: '/value',     label: '⭐ Best Value'  },
    { href: '/sectors',   label: '🏭 Sectors'    },
    { href: '/dividends', label: '💰 Dividends'  },
  ]

  return (
    <div className="flex h-screen overflow-hidden bg-bg">

      {/* ── SIDEBAR ── */}
      <aside className={`
        flex-col w-52 bg-surface border-r border-border flex-shrink-0 transition-all
        ${sidebarOpen ? 'flex fixed inset-y-0 left-0 z-40' : 'hidden md:flex'}
      `}>
        {/* Logo */}
        <div className="p-4 border-b border-border">
          <div className="font-700 text-lg leading-tight" style={{ fontFamily: 'IBM Plex Sans Condensed' }}>
            FORWARD<span style={{ color: 'var(--orange)' }}>ALPHA</span>
          </div>
          <div className="text-[9px] text-muted mt-0.5">European Equity Research</div>
          <div className="flex gap-1 mt-2 flex-wrap">
            <span className="badge badge-beta">🧪 BETA</span>
            <span className="badge badge-live">● LIVE</span>
          </div>
        </div>

        <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
          {nav.map(item => (
            <button key={item.id}
              onClick={() => { setPage(item.id); setSidebar(false) }}
              className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded text-sm font-500 transition-colors text-left ${
                page === item.id ? 'bg-gold/15 text-gold' : 'text-muted hover:text-text hover:bg-white/5'
              }`}>
              {item.icon}{item.label}
            </button>
          ))}
          <div style={{ height:1, background:'var(--border)', margin:'8px 4px' }} />
          {externalNav.map(item => (
            <a key={item.href} href={item.href}
              style={{ display:'flex', alignItems:'center', gap:8, padding:'8px 12px',
                borderRadius:4, color:'var(--text3)', fontSize:13, fontWeight:500,
                textDecoration:'none', transition:'all 0.12s' }}
              onMouseEnter={e => { (e.currentTarget as HTMLElement).style.color='var(--text)'; (e.currentTarget as HTMLElement).style.background='rgba(255,255,255,0.05)' }}
              onMouseLeave={e => { (e.currentTarget as HTMLElement).style.color='var(--text3)'; (e.currentTarget as HTMLElement).style.background='transparent' }}>
              {item.label}
            </a>
          ))}
        </nav>

        {/* User */}
        <div className="p-3 border-t border-border space-y-2">
          {user ? (
            <>
              <div className="text-[10px] text-green font-600 truncate">👤 {user.email}</div>
              <button onClick={async () => { await supabase.auth.signOut(); window.location.reload() }}
                className="flex items-center gap-1.5 text-xs font-600"
                style={{ color: 'var(--red)' }}>
                <LogOut size={12} /> Log Out
              </button>
            </>
          ) : (
            <button onClick={() => setShowAuth(true)}
              className="btn-ghost w-full flex items-center justify-center gap-2 text-xs py-2">
              <LogIn size={14} /> Register / Log In
            </button>
          )}
        </div>

        <div className="px-3 pb-3 text-[9px] text-muted leading-relaxed">
          <span className="text-green font-700">● DATA</span> · TIKR / EODHD<br />
          ⚠️ Prices: 15-20 min delay<br />
          Fundamentals: daily
        </div>
      </aside>

      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-30 md:hidden" onClick={() => setSidebar(false)} />
      )}

      {/* ── MAIN ── */}
      <main className="flex-1 flex flex-col overflow-hidden">

        <div className="md:hidden flex items-center px-4 py-3 border-b border-border bg-surface gap-3">
          <button onClick={() => setSidebar(true)}>
            <Menu size={20} className="text-text" />
          </button>
          <span className="font-700 flex-1" style={{ fontFamily: 'IBM Plex Sans Condensed', color: 'var(--text)' }}>
            FORWARD<span style={{ color: 'var(--orange)' }}>ALPHA</span>
          </span>
          <span className="badge badge-beta">BETA</span>
          {user ? (
            <button onClick={async () => { await supabase.auth.signOut(); window.location.reload() }}>
              <LogOut size={18} className="text-red-400" />
            </button>
          ) : (
            <button onClick={() => setShowAuth(true)}>
              <User size={18} className="text-muted" />
            </button>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-4 md:p-6 pb-20">
          {page === 'dashboard' && <Dashboard onSectorClick={goSector} onSelectStock={setDetailStock} onGoScreener={goScreenerEpsMom} />}
          {page === 'screener'  && <Screener key={`${scrExchange}-${scrSector}-${scrEpsMom}`} initExchange={scrExchange} initSector={scrSector} initEpsMom={scrEpsMom} onSelectStock={setDetailStock} />}
          {page === 'portfolio' && <Portfolio />}
          {page === 'legal'     && <Legal />}
        </div>

        <footer className="border-t border-border px-4 py-2 bg-surface text-[9px] text-muted flex flex-wrap gap-x-4 gap-y-1">
          <span className="font-700 text-sub">ForwardAlpha · Verona, Italy</span>
          <span>⚠️ Not investment advice</span>
          <span>⚠️ Prices delayed 15-20 min</span>
          <button onClick={() => setPage('legal')} className="hover:text-gold underline">Terms & Privacy</button>
          <a href="mailto:andrea@forwardalpha.pro" className="hover:text-gold">Contact</a>
          <span>© 2026 Andrea Meschini</span>
        </footer>
      </main>

      {showAuth && (
        <AuthModal onClose={() => setShowAuth(false)} onSuccess={() => setShowAuth(false)} />
      )}

      <CookieBanner />
    </div>
  )
}
