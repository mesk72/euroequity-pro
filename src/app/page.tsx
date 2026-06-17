'use client'

import { useRouter } from 'next/navigation'
import { useState, useEffect, useCallback, useRef } from 'react'
import {
  FileText, LayoutDashboard, Search, Briefcase, Globe, Info,
  LogIn, LogOut, User, Menu, X, RefreshCw,
  ChevronUp, ChevronDown, TrendingUp, TrendingDown, Star
} from 'lucide-react'
import { supabase, createProfile, ensureDefaultPortfolios } from '@/lib/supabase'
import { EXCHANGES, EXCHANGES_EXEMU, ALL_EXCHANGES, INDICES } from '@/lib/constants'
import { Stock } from '@/lib/ranking'
import SectorHeatmap from '@/components/dashboard/SectorHeatmap'
import AuthModal from '@/components/auth/AuthModal'
import ResearchPage from '@/components/research/ResearchPage'
import toast from 'react-hot-toast'
import type { User as SupabaseUser } from '@supabase/supabase-js'
import StockDetailPage from '@/components/dashboard/StockDetailPage'
import WatchlistButton from '@/components/watchlist/WatchlistButton'
import MyScreen from '@/components/watchlist/MyScreen'
import { DEMO_STOCKS } from '@/lib/demoData'
import { computeScores } from '@/lib/ranking'

// - FLAGS -
const USE_DEMO = false  // true = dati demo hardcoded
const USE_DB   = true   // true = legge da Supabase

// - SECTOR COLORS -
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

// - HELPERS -
const fp = (v: number | null | undefined, d = 1): string => {
  if (v == null || isNaN(v)) return '-'
  return `${v >= 0 ? '+' : ''}${v.toFixed(d)}%`
}
const fv = (v: number | null | undefined, d = 2): string => {
  if (v == null || isNaN(v)) return '-'
  return v.toFixed(d)
}
const fpd = (v: number | null | undefined, d = 1): string => {
  if (v == null) return '-'
  const pct = v * 100
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(d)}%`
}
const fn = (v: number | null | undefined): string => {
  if (v == null || isNaN(v as number)) return '-'
  return String(Math.round(v as number))
}
const clr = (v: number | null | undefined): string => {
  // Restituisce stringa vuota - usa sempre clrStyle per i colori
  return ''
}
const clrStyle = (v: number | null | undefined): React.CSSProperties => {
  if (v == null) return { color: '#8a9ab8' }
  return { color: v > 0 ? '#22d48a' : v < 0 ? '#e84560' : '#8a9ab8' }
}
const fmtVol = (v: number | null | undefined): string => {
  if (!v) return '-'
  if (v >= 1e6) return `${(v/1e6).toFixed(1)}M`
  if (v >= 1e3) return `${(v/1e3).toFixed(0)}k`
  return String(v)
}

// - SCORE BAR -
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

type Page = 'dashboard' | 'screener' | 'eurozone' | 'bestideas' | 'bestvalue' | 'bestgrowth' | 'about' | 'sectors' | 'portfolio' | 'legal' | 'research' | 'myscreen' | 'northamerica' | 'usscreen' | 'MIL' | 'PA' | 'XETRA' | 'LSE' | 'OM' | 'OB' | 'SWX' | 'MC' | 'AS' | 'HE' | 'BR' | 'GR' | 'CPSE' | 'VI' | 'LS' | 'IR'

// - API CALLS -
async function apiExchange(code: string): Promise<Stock[]> {
  if (USE_DEMO) {
    const scored = computeScores([...DEMO_STOCKS])
    if (code === 'EZ') return scored
    return scored.filter(s => s.exchange === code)
  }
  if (USE_DB) {
    try {
      const EMU_EXCHANGES = 'MIL,XETRA,PA,AS,MC,BR,LS,VI,HE,IR'
      const ALL_EX = 'MIL,XETRA,PA,AS,MC,BR,LS,VI,HE,IR,LSE,SWX,OM,OB,CPSE'
      const url = code === 'EZ' || code === 'ALL'
        ? `/api/db/stocks?exchanges=${ALL_EX}`
        : code === 'EMU'
          ? `/api/db/stocks?exchanges=${EMU_EXCHANGES}`
          : `/api/db/stocks?exchange=${encodeURIComponent(code)}`
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

// - INDEX CARD -
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
            color: (changeP || 0) >= 0 ? '#22d48a' : '#e84560',
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

// - STOCK TABLE -
type SortKey = string

interface ColDef { key: string; label: string; width?: number }

const COLUMNS: ColDef[] = [
  { key: 'ticker',      label: 'Ticker',    width: 80  },
  { key: 'company',     label: 'Company',   width: 180 },
  { key: 'sector',      label: 'Sector',    width: 130 },
  { key: 'price',       label: 'Price',     width: 75  },
  { key: 'change1d',    label: '1D %',      width: 65  },
  { key: 'mktCap',      label: 'MktCap $B', width: 80  },
  { key: 'rankPeLtm',   label: 'PE LTM Rk', width: 70  },
  { key: 'rankPeNtm',   label: 'PE NTM Rk', width: 70  },
  { key: 'rankPb',      label: 'PB Rank',   width: 65  },
  { key: 'rankEpsGr',   label: 'EPS Rk',    width: 60  },
  { key: 'rankRevGr',   label: 'Rev Rk',    width: 60  },
  { key: 'mom1w',       label: '1W %',      width: 65  },
  { key: 'mom1m',       label: '1M %',      width: 65  },
  { key: 'mom6m',       label: '6M %',      width: 65  },
  { key: 'mom12m',      label: '12M %',     width: 72  },
  { key: 'valueScore',  label: 'Value',     width: 55  },
  { key: 'growthScore', label: 'Growth',    width: 60  },
  { key: 'combinedRank',label: 'Best',      width: 55  },
]
// WatchlistButton viene aggiunto nella riga

function cellFmt(s: Stock, key: SortKey): { val: string; cls: string; style?: React.CSSProperties; sectorColor?: string; flag?: string } {
  const v = (s as any)[key] as number | null
  switch (key) {
    case 'ticker':      return { val: s.ticker, cls: 'font-600 text-text', flag: s.flag }
    case 'company':     return { val: s.company || '-',   cls: 'text-sub' }
    case 'country':     return { val: s.country  || '-',   cls: 'text-[10px] text-muted' }
    case 'sector':      return { val: s.sector  || '-',   cls: 'text-[10px]', sectorColor: getSectorColor(s.sector) }
    case 'price':       return { val: v != null ? fv(v, 2)  : '-', cls: v != null ? 'text-text'  : 'text-muted' }
    case 'change1d':    return { val: v != null ? fp(v)     : '-', cls: v != null ? clr(v)        : 'text-muted', style: v != null ? clrStyle(v) : undefined }
    case 'mktCap':      return { val: v != null ? fv(v, 1)  : '-', cls: v != null ? 'text-sub'    : 'text-muted' }
    case 'peTrail':     return { val: v != null ? fv(v, 1)  : '-', cls: v != null ? 'text-sub'    : 'text-muted' }
    case 'peFwd':       return { val: v != null ? fv(v, 1)  : '-', cls: v != null ? 'text-sub'    : 'text-muted' }
    case 'epsGrowth':   return { val: v != null ? fpd(v)    : '-', cls: v != null ? clr(v)        : 'text-muted', style: v != null ? clrStyle(v) : undefined }
    case 'revGrowth':   return { val: v != null ? fpd(v)    : '-', cls: v != null ? clr(v)        : 'text-muted', style: v != null ? clrStyle(v) : undefined }
    case 'mom1w':       return { val: v != null ? fpd(v)    : '-', cls: v != null ? clr(v)        : 'text-muted', style: v != null ? clrStyle(v) : undefined }
    case 'mom1m':       return { val: v != null ? fpd(v)    : '-', cls: v != null ? clr(v)        : 'text-muted', style: v != null ? clrStyle(v) : undefined }
    case 'mom6m':       return { val: v != null ? fpd(v)    : '-', cls: v != null ? clr(v)        : 'text-muted', style: v != null ? clrStyle(v) : undefined }
    case 'mom12m':      return { val: v != null ? fpd(v)    : '-', cls: v != null ? clr(v)        : 'text-muted', style: v != null ? clrStyle(v) : undefined }
    case 'rankPeLtm':   return { val: v != null ? fn(v) : '-', cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-[#e84560]' : 'text-yellow-400') : 'text-muted' }
    case 'rankPeNtm':   return { val: v != null ? fn(v) : '-', cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-[#e84560]' : 'text-yellow-400') : 'text-muted' }
    case 'rankPb':      return { val: v != null ? fn(v) : '-', cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-[#e84560]' : 'text-yellow-400') : 'text-muted' }
    case 'rankEpsGr':   return { val: v != null ? fn(v) : '-', cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-[#e84560]' : 'text-yellow-400') : 'text-muted' }
    case 'rankRevGr':   return { val: v != null ? fn(v) : '-', cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-[#e84560]' : 'text-yellow-400') : 'text-muted' }
    case 'combinedRank': return { val: v != null ? fn(v) : '-', cls: v != null ? (v >= 80 ? 'text-green font-700' : v >= 60 ? 'text-yellow-400' : 'text-muted') : 'text-muted' }
    case 'valueScore':  return { val: v != null ? fn(v)     : '-', cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-[#e84560]' : 'text-yellow-400 font-600') : 'text-muted' }
    case 'growthScore': return { val: v != null ? fn(v)     : '-', cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-[#e84560]' : 'text-yellow-400 font-600') : 'text-muted' }
    default:            return { val: '-', cls: 'text-muted' }
  }
}

function StockTable({ stocks, onSelect, loading, maxRows = 100, userId = null }: {
  stocks: Stock[]
  onSelect: (s: Stock) => void
  loading?: boolean
  maxRows?: number
  userId?: string | null
}) {
  const [sortKey, setSortKey] = useState<SortKey>('mktCap')
  const [sortAsc, setSortAsc] = useState(false)
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  const sorted = [...stocks].sort((a, b) => {
    const av = (a as any)[sortKey]
    const bv = (b as any)[sortKey]
    if (av == null && bv == null) return 0
    if (av == null) return 1
    if (bv == null) return -1
    if (typeof av === 'string') return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av)
    return sortAsc ? av - bv : bv - av
  }).slice(0, maxRows)

  const NO_SORT = new Set(['rankPeLtm','rankPeNtm','rankPb','rankEpsGr','rankRevGr'])
  const LOCKED_GUEST = new Set(['valueScore','growthScore','combinedRank','mom1w','mom1m','mom6m','mom12m'])
  const toggle = (key: SortKey) => {
    if (NO_SORT.has(key)) return
    if (!userId && LOCKED_GUEST.has(key)) {
      alert('Register for free to sort by Value, Growth and Best Score.')
      return
    }
    if (sortKey === key) setSortAsc(a => !a)
    else { setSortKey(key); setSortAsc(false) }
  }

  if (loading) return (
    <div className="p-8 text-center text-muted text-sm space-y-2">
      <RefreshCw size={20} className="animate-spin mx-auto text-gold" />
      <p>Loading market data...</p>
    </div>
  )

  if (stocks.length === 0) return (
    <div className="p-8 text-center text-muted text-sm">No stocks match your filters.</div>
  )

  if (isMobile) return (
    <div>
      <div className="text-[9px] text-muted px-3 py-1 border-b border-border bg-surface/50">
        Prices delayed 15-20 min
      </div>
      {sorted.map((s, i) => {
        const sColor = getSectorColor(s.sector)
        return (
          <div key={i}
            onClick={() => { onSelect(s); window.location.href = `/stock/${s.ticker}-${s.exchange}` }}
            className="cursor-pointer border-b border-border px-3 py-2.5 hover:bg-white/5 active:bg-white/10">
            <div className="flex items-center justify-between mb-1">
              <div className="flex items-center gap-2">
                <span className="font-700 text-sm text-orange">{s.flag} {s.ticker}</span>
                <span className="text-[9px] text-muted">{s.exchange}</span>
                <WatchlistButton stock={s} userId={userId || null} />
              </div>
              <div className="flex items-center gap-2">
                <span className="font-mono font-600 text-sm text-text">
                  {s.price != null ? s.price.toFixed(2) : '-'}
                </span>
                <span className={`font-mono text-xs font-600 ${s.change1d != null ? (s.change1d >= 0 ? 'text-[#22d48a]' : 'text-[#e84560]') : 'text-muted'}`}>
                  {s.change1d != null ? fpd(s.change1d/100) : '-'}
                </span>
              </div>
            </div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-sub truncate max-w-[180px]">{s.company}</span>
              <span className="text-[9px] font-600" style={{ color: sColor }}>{s.sector || '-'}</span>
            </div>
            <div className="flex items-center gap-2 text-[10px] font-mono mt-0.5">
              <span className="text-muted">Cap: <span className="text-sub">{s.mktCap != null ? `$${s.mktCap.toFixed(1)}B` : '-'}</span></span>
              <span className="text-[#444]">|</span>
              <span className="text-muted">PEv: <span style={{color:'#3b82f6'}}>{(s as any).rankPeLtm != null ? Math.round((s as any).rankPeLtm) : '-'}</span></span>
              <span className="text-[#444]">|</span>
              <span className="text-muted">PEf: <span style={{color:'#3b82f6'}}>{(s as any).rankPeNtm != null ? Math.round((s as any).rankPeNtm) : '-'}</span></span>
              <span className="text-[#444]">|</span>
              <span className="text-muted">EPS: <span style={{color:'#22c55e'}}>{(s as any).rankEpsGr != null ? Math.round((s as any).rankEpsGr) : '-'}</span></span>
              <span className="text-[#444]">|</span>
              <span className="text-muted">Rev: <span style={{color:'#22c55e'}}>{(s as any).rankRevGr != null ? Math.round((s as any).rankRevGr) : '-'}</span></span>
            </div>
            <div className="flex items-center gap-2 text-[10px] font-mono mt-0.5">
              <span className="text-muted">Val: <span style={{color:'#3b82f6'}}>{s.valueScore != null ? Math.round(s.valueScore) : '-'}</span></span>
              <span className="text-[#444]">|</span>
              <span className="text-muted">Grw: <span style={{color:'#22c55e'}}>{s.growthScore != null ? Math.round(s.growthScore) : '-'}</span></span>
              <span className="text-[#444]">|</span>
              <span className="text-muted">Best: <span style={{color:'var(--orange)'}}>{s.combinedRank != null ? Math.round(s.combinedRank) : '-'}</span></span>
              <span className="text-[#444]">|</span>
              <span className="text-muted">1M: <span style={{color: s.mom1m != null ? (s.mom1m >= 0 ? '#22d48a' : '#e84560') : '#8a9ab8'}}>{s.mom1m != null ? `${(s.mom1m*100).toFixed(1)}%` : '-'}</span></span>
              <span className="text-[#444]">|</span>
              <span className="text-muted">12M: <span style={{color: s.mom12m != null ? (s.mom12m >= 0 ? '#22d48a' : '#e84560') : '#8a9ab8'}}>{s.mom12m != null ? `${(s.mom12m*100).toFixed(1)}%` : '-'}</span></span>
            </div>
          </div>
        )
      })}
      {stocks.length > maxRows && (
        <div className="text-[10px] text-muted text-center py-2 border-t border-border">
          Showing top {maxRows} of {stocks.length} by market cap
        </div>
      )}
    </div>
  )

  return (
    <div className="overflow-x-auto" style={{ WebkitOverflowScrolling: "touch", overflowX: "auto", touchAction: "pan-x pan-y" }}>
      <div className="text-[9px] text-muted px-3 py-1 border-b border-border bg-surface/50">
        Fundamentals updated daily
      </div>
      <table className="data-table" style={{ minWidth: "900px", width: "max-content" }}>
        <thead>
          <tr>
            {COLUMNS.map((c, ci) => (
              <th
                key={c.key}
                onClick={() => toggle(c.key)}
                style={{
                  minWidth: c.width,
                  userSelect: 'none',
                  cursor: (NO_SORT.has(c.key) || (!userId && LOCKED_GUEST.has(c.key))) ? 'default' : 'pointer',
                  ...(ci === 0 ? {
                    position: 'sticky',
                    left: 0,
                    zIndex: 2,
                    background: '#0d1017',
                    boxShadow: '2px 0 4px rgba(0,0,0,0.3)',
                  } : {})
                }}
              >
                <span className="flex items-center gap-1">
                  {c.label}{!userId && LOCKED_GUEST.has(c.key) ? ' 🔒' : ''}
                  {userId && sortKey === c.key
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
              {COLUMNS.map((c, ci) => {
                const { val, cls, style: cellStyle, sectorColor, flag: cellFlag } = cellFmt(s, c.key)
                return (
                  <td key={c.key} style={{
                    maxWidth: c.width,
                    ...(ci === 0 ? {
                      position: 'sticky',
                      left: 0,
                      zIndex: 1,
                      background: '#0d1017',
                      boxShadow: '2px 0 4px rgba(0,0,0,0.3)',
                    } : {})
                  }}>
                    {c.key === 'sector' && sectorColor ? (
                      <span className="truncate block text-[10px] font-600"
                        style={{ color: sectorColor }}>
                        {val}
                      </span>
                    ) : (!userId && LOCKED_GUEST.has(c.key)) ? (
                      <span className="truncate block text-muted text-center">🔒</span>
                    ) : (
                      <span className={`truncate block ${cls}`} style={cellStyle}>
                        {cellFlag ? <FlagIcon flag={cellFlag} /> : null}{val}
                      </span>
                    )}
                  </td>
                )
              })}
              <td style={{ width: 28 }} onClick={(e) => e.stopPropagation()}>
                <WatchlistButton stock={s} userId={userId} />
              </td>
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
      <div className={`absolute top-2 right-2 text-xs font-700 font-mono ${isUp ? 'text-[#22d48a]' : 'text-[#e84560]'}`}>
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

// - STOCK DETAIL PANEL -
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
    ['EPS Gr %',     fpd(stock.epsGrowth),      clr(stock.epsGrowth)],
    ['Rev Gr %',     fpd(stock.revGrowth),      clr(stock.revGrowth)],
    ['Mom 1W %',     fpd(stock.mom1w),          clr(stock.mom1w)],
    ['Mom 1M %',     fpd(stock.mom1m),          clr(stock.mom1m)],
    ['Mom 6M %',     fpd(stock.mom6m),          clr(stock.mom6m)],
    ['Mom 12M %',    fpd(stock.mom12m),         clr(stock.mom12m)],
    ['Sector',       stock.sector || '-',       ''],
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
        <div className="text-[9px] text-muted mb-1">Prices indicative</div>
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
            + Add
          </button>
        </div>
      </div>
    </div>
  )
}

// - SCREENER -
function Screener({ initExchange = 'MIL', initSector = 'All', initEpsMom = '', onSelectStock, userId = null, initValMin = 0, initGrowMin = 0, initCombinedMin = 0, showAll = false }: {
  initExchange?: string
  initSector?:   string
  initEpsMom?:   string
  onSelectStock?: (s: Stock) => void
  userId?: string | null
  initValMin?: number
  initGrowMin?: number
  initCombinedMin?: number
  showAll?: boolean
}) {
  const [exchange,  setExchange]  = useState(initExchange)
  const [stocks,    setStocks]    = useState<Stock[]>([])
  const [loading,   setLoading]   = useState(false)
  const [selected,  setSelected]  = useState<Stock | null>(null)
  const [portfolioNames, setPortfolioNames] = useState<string[]>(['Portfolio 1', 'Portfolio 2', 'Portfolio 3'])

  // Filters
  const [search,   setSearch]   = useState('')
  const [sector,   setSector]   = useState(initSector)
  const [valMin,      setValMin]      = useState(initValMin)
  const [growMin,     setGrowMin]     = useState(initGrowMin)
  const [combinedMin, setCombinedMin] = useState(initCombinedMin)
  const [showFilters, setShowFilters] = useState(false)
  const [mom6Min,  setMom6Min]  = useState(0)
  const [pbMax,    setPbMax]    = useState(0)
  const [mom12Min, setMom12Min] = useState(0)

  useEffect(() => {
    // Carica nomi portafogli
    if (typeof window === 'undefined') return
    const stored = JSON.parse(localStorage.getItem('portfolios') || '{}')
    const names = Object.keys(stored)
    if (names.length > 0) setPortfolioNames(names)
  }, [])

  useEffect(() => {
    setStocks([]); setSelected(null); setLoading(true)
    const exchToLoad = initEpsMom ? 'EZ' : exchange
    apiExchange(exchToLoad).then(data => {
      // Calcola euroRank su All Europe usando metriche raw
      const ey = (pe: number | null) => (pe && pe !== 0 && Math.abs(pe) <= 200) ? 1/pe : null
      const pctRk = (vals: number[], v: number) => {
        if (!vals.length) return null
        return Math.round(vals.filter(x => x < v).length / vals.length * 100)
      }
      // Distribuzioni europee pre-calcolate
      const eyTVals  = data.map((s:any) => ey(s.peTrail)).filter((v:any) => v != null) as number[]
      const eyFVals  = data.map((s:any) => ey(s.peFwd)).filter((v:any) => v != null) as number[]
      const pbVals   = data.map((s:any) => s.pb).filter((v:any) => v != null && v > 0 && v < 50) as number[]
      const egVals   = data.map((s:any) => s.epsGrowth).filter((v:any) => v != null) as number[]
      const rgVals   = data.map((s:any) => s.revGrowth).filter((v:any) => v != null) as number[]
      const m6AdjVals  = data.map((s:any) => s.mom6m  != null && s.mom1w != null ? s.mom6m  - s.mom1w  : null).filter((v:any) => v != null) as number[]
      const m12AdjVals = data.map((s:any) => s.mom12m != null && s.mom1m != null ? s.mom12m - s.mom1m : null).filter((v:any) => v != null) as number[]

      // Calcola euroVal e euroGrow per ogni titolo
      const NO_RANK_EX = new Set(['VI','LS','IR'])
      const euroScores = data.map((s:any) => {
        if (NO_RANK_EX.has(s.exchange)) return null
        const eyt = ey(s.peTrail); const eyf = ey(s.peFwd)
        const pet = eyt != null ? (s.peTrail > 200 ? 1 : pctRk(eyTVals, eyt)) : null
        const pef = eyf != null ? (s.peFwd   > 200 ? 1 : pctRk(eyFVals, eyf)) : null
        const pb  = s.pb != null && s.pb > 0 && s.pb < 50 ? (100 - pctRk(pbVals, s.pb)!) : null
        const vc  = [pet,pef,pb].filter((v:any) => v != null) as number[]
        const euroVal = vc.length >= 2 ? vc.reduce((a:number,b:number)=>a+b,0)/vc.length : null
        const m6adj  = s.mom6m  != null && s.mom1w != null ? s.mom6m  - s.mom1w  : null
        const m12adj = s.mom12m != null && s.mom1m != null ? s.mom12m - s.mom1m : null
        const eg  = s.epsGrowth != null ? pctRk(egVals,  s.epsGrowth) : null
        const rg  = s.revGrowth != null ? pctRk(rgVals,  s.revGrowth) : null
        const m6r = m6adj  != null ? pctRk(m6AdjVals,  m6adj)  : null
        const m12r= m12adj != null ? pctRk(m12AdjVals, m12adj) : null
        const gc  = [eg,rg,m6r,m12r].filter((v:any) => v != null) as number[]
        const euroGrow = gc.length >= 2 ? gc.reduce((a:number,b:number)=>a+b,0)/gc.length : null
        return euroVal != null && euroGrow != null ? (euroVal + euroGrow) / 2 : null
      })

      // Usa combinedRank dal DB — azzera solo per NO_RANK_EX
      data.forEach((s: any) => {
        if (NO_RANK_EX.has(s.exchange)) { s.combinedRank = null }
      })

      setStocks(data)
      setLoading(false)
    })
  }, [exchange, initEpsMom])

  // Applica conversione USD->EUR alla market cap
  const usdToEur = 0.8615
  const stocksWithEurCap = stocks.map(s => ({
    ...s,
    mktCap: s.mktCap ?? null
  }))

  const filtered = stocksWithEurCap.filter(s => {
    if (search) {
      const q = search.toLowerCase()
      if (!s.ticker.toLowerCase().includes(q) && !(s.company || '').toLowerCase().includes(q)) return false
    }
    if (sector !== 'All' && s.sector !== sector) return false
    if (initEpsMom === 'epsMomPos' && (s.epsMom30d == null || s.epsMom30d <= 0)) return false
    if (initEpsMom === 'epsMomNeg' && (s.epsMom30d == null || s.epsMom30d >= 0)) return false
    if (mom6Min > 0 && (s.mom6m || 0) < mom6Min) return false
    if (pbMax  > 0 && s.pb       != null && s.pb       > pbMax)  return false
    if (mom12Min>0 && (s.mom12m  || 0)                 < mom12Min) return false
    if (valMin > 0 && (s.valueScore  || 0)             < valMin) return false
    if (growMin> 0 && (s.growthScore || 0)             < growMin) return false
    if (combinedMin > 0 && (s.combinedRank || 0)       < combinedMin) return false
    // Escludi mercati senza rank dai Best screens
    if ((valMin > 0 || growMin > 0 || combinedMin > 0) &&
        ['GR','VI','LS','IR','GR'].includes(s.exchange)) return false
    return true
  })

  const sectors = ['All', ...Array.from(
    new Set(stocks.map(s => s.sector).filter(Boolean) as string[])
  ).sort()]

  return (
    <div className="space-y-3 p-3">
      {/* Exchange tabs */}
      <div className="flex gap-1.5 flex-wrap pb-1">
        <button onClick={() => setExchange('EZ')}
          className={`px-3 py-1.5 rounded text-xs font-600 border whitespace-nowrap transition-colors ${exchange === 'EZ' ? 'bg-gold text-bg border-gold' : 'border-border text-muted hover:border-gold hover:text-gold'}`}>
          All Europe
        </button>
        <button onClick={() => setExchange('EMU')}
          className={`px-3 py-1.5 rounded text-xs font-600 border whitespace-nowrap transition-colors ${exchange === 'EMU' ? 'bg-gold text-bg border-gold' : 'border-border text-muted hover:border-gold hover:text-gold'}`}>
          Eurozone
        </button>
        {Object.entries(EXCHANGES).map(([code, meta]) => (
          <button key={code} onClick={() => setExchange(code)}
            className={`px-3 py-1.5 rounded text-xs font-600 border whitespace-nowrap transition-colors ${exchange === code ? 'bg-gold text-bg border-gold' : 'border-border text-muted hover:border-gold hover:text-gold'}`}>
            {(meta as any).flag} {(meta as any).label}
          </button>
        ))}
        {Object.entries(EXCHANGES_EXEMU).map(([code, meta]) => (
          <button key={code} onClick={() => setExchange(code)}
            className={`px-3 py-1.5 rounded text-xs font-600 border whitespace-nowrap transition-colors ${exchange === code ? 'bg-gold text-bg border-gold' : 'border-border text-muted hover:border-gold hover:text-gold'}`}>
            {(meta as any).flag} {(meta as any).label}
          </button>
        ))}
      </div>

      {/* Preset screens */}
      <div className="flex gap-2 flex-wrap">
        <button onClick={() => { setValMin(80); setGrowMin(30); setCombinedMin(0) }}
          className="px-3 py-1 rounded text-xs font-600 border border-border text-gold hover:bg-gold/10">
          ⭐ Best Value V≥80 G≥30
        </button>
        <button onClick={() => { setValMin(0); setGrowMin(80); setCombinedMin(0) }}
          className="px-3 py-1 rounded text-xs font-600 border border-border text-gold hover:bg-gold/10">
          🚀 Best Growth G≥80
        </button>
        <button onClick={() => { setValMin(0); setGrowMin(0); setCombinedMin(80) }}
          className="px-3 py-1 rounded text-xs font-600 border border-border text-orange hover:bg-orange/10">
          🏆 Best Combined ≥80
        </button>
        <button onClick={() => { setValMin(0); setGrowMin(0); setMom6Min(0); setPbMax(0); setMom12Min(0); setCombinedMin(0); setSearch(''); setSector('All') }}
          className="px-3 py-1 rounded text-xs font-600 border border-border text-muted hover:border-gold">
          Reset
        </button>
      </div>

      {/* Filters toggle button */}
      {(() => {
        const activeCount = [mom6Min>0, mom12Min>0, valMin>0, growMin>0, combinedMin>0, search.length>0, sector!=='All'].filter(Boolean).length
        return (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowFilters((f: boolean) => !f)}
              className="flex items-center gap-2 px-3 py-2 rounded text-xs font-600 border transition-colors"
              style={{ borderColor: activeCount > 0 ? 'var(--orange)' : 'var(--border)', color: activeCount > 0 ? 'var(--orange)' : 'var(--text3)' }}>
              <span>⚙ Filters</span>
              {activeCount > 0 && (
                <span style={{ background: 'var(--orange)', color: '#000', borderRadius: 10, padding: '1px 6px', fontSize: 10, fontWeight: 800 }}>
                  {activeCount}
                </span>
              )}
              <span style={{ fontSize: 10 }}>{showFilters ? "▲" : "▼"}</span>
            </button>
            <span className="text-muted text-xs">{filtered.length} results</span>
          </div>
        )
      })()}

      {showFilters && (
        <div className="bg-surface border border-border rounded p-3">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
            <div className="space-y-1.5">
              <div className="text-muted font-700 uppercase tracking-wide text-[10px]">Valuation</div>
              <input type="number" placeholder="Mom 6M % min" value={mom6Min || ''} onChange={e => setMom6Min(+e.target.value || 0)} className="input-field" min={-100} max={1000} />
            </div>
            <div className="space-y-1.5">
              <div className="text-muted font-700 uppercase tracking-wide text-[10px]">Momentum</div>
              <input type="number" placeholder="Mom 12M % min" value={mom12Min || ''} onChange={e => setMom12Min(+e.target.value || 0)} className="input-field" />
            </div>
            <div className="space-y-1.5">
              <div className="text-muted font-700 uppercase tracking-wide text-[10px]">Scores</div>
              {userId ? (
                <>
                  <input type="number" placeholder="Value Score min" value={valMin || ''} onChange={e => setValMin(+e.target.value || 0)} className="input-field" min={0} max={100} />
                  <input type="number" placeholder="Growth Score min" value={growMin || ''} onChange={e => setGrowMin(+e.target.value || 0)} className="input-field" min={0} max={100} />
                  <input type="number" placeholder="Best Rank min" value={combinedMin || ''} onChange={e => setCombinedMin(+e.target.value || 0)} className="input-field" min={0} max={100} />
                </>
              ) : (
                <div onClick={() => alert('Sign up for free to filter by Value, Growth and Best Score.')}
                  style={{ cursor:'pointer', background:'var(--surface2)', border:'1px solid var(--border)',
                    borderRadius:4, padding:'8px 12px', fontSize:12, color:'var(--text3)',
                    display:'flex', alignItems:'center', gap:6 }}>
                  🔒 Value / Growth / Best filters
                  <span style={{ color:'var(--orange)', fontWeight:700, marginLeft:'auto' }}>Sign up free →</span>
                </div>
              )}
            </div>
            <div className="space-y-1.5">
              <div className="text-muted font-700 uppercase tracking-wide text-[10px]">Search</div>
              <input type="text" placeholder="Ticker / name" value={search} onChange={e => setSearch(e.target.value)} className="input-field" />
              <select value={sector} onChange={e => setSector(e.target.value)} className="input-field">
                {sectors.map(s => <option key={s}>{s}</option>)}
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Status */}
      <div className="text-xs text-muted">
        <span className="text-text font-600">{filtered.length}</span> stocks · showing top 100 · <span className="text-[10px]">Prices delayed 15-20 min</span>
      </div>

      {/* Table */}
      <div className="bg-surface border border-border rounded overflow-hidden">
        <StockTable stocks={filtered} onSelect={onSelectStock || (() => {})} loading={loading} maxRows={showAll ? 9999 : 100} userId={userId} />
      </div>
    </div>
  )
}

const FLAG_ISO: Record<string, string> = {
  '🇮🇹': 'it', '🇩🇪': 'de', '🇫🇷': 'fr', '🇳🇱': 'nl',
  '🇪🇸': 'es', '🇧🇪': 'be', '🇵🇹': 'pt', '🇦🇹': 'at',
  '🇫🇮': 'fi', '🇮🇪': 'ie', '🇬🇷': 'gr', '🇬🇧': 'gb',
  '🇨🇭': 'ch', '🇸🇪': 'se', '🇳🇴': 'no', '🇩🇰': 'dk',
  '🇱🇺': 'lu',
}

function FlagIcon({ flag }: { flag: string }) {
  const iso = FLAG_ISO[flag]
  if (!iso) return <span>{flag}</span>
  return (
    <span
      className={`fi fi-${iso}`}
      style={{ fontSize: '14px', marginRight: '4px', display: 'inline-block', verticalAlign: 'middle' }}
    />
  )
}

// - SECTORS -
function SectorScreen({ onSectorClick }: { onSectorClick: (s: string) => void }) {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    apiExchange('EZ').then(data => { setStocks(data); setLoading(false) })
  }, [])

  const stocksEur = stocks.map(s => ({ ...s, mktCap: s.mktCap ?? null }))

  const sectorMap: Record<string, any[]> = {}
  for (const s of stocksEur) {
    const sec = s.sector || 'Other'
    if (!sectorMap[sec]) sectorMap[sec] = []
    sectorMap[sec].push(s)
  }

  const mcw = (list: any[], field: string) => {
    const v = list.filter((s:any) => s[field] != null && s.mktCap != null && s.mktCap > 0)
    const tw = v.reduce((a:number, s:any) => a + (s.mktCap || 0), 0)
    return tw > 0 ? v.reduce((a:number, s:any) => a + (s[field] || 0) * (s.mktCap || 0), 0) / tw : null
  }

  const sectors = Object.entries(sectorMap)
    .map(([name, list]) => ({
      name,
      count: list.length,
      mktCap: list.reduce((a:number, s:any) => a + (s.mktCap || 0), 0),
      change1d: mcw(list, 'change1d'),
      epsGrowth: mcw(list, 'epsGrowth'),
      revGrowth: mcw(list, 'revGrowth'),
      mom12m: mcw(list, 'mom12m'),
      valueScore: mcw(list, 'valueScore'),
      growthScore: mcw(list, 'growthScore'),
      combinedRank: mcw(list, 'combinedRank'),
    }))
    .sort((a, b) => b.mktCap - a.mktCap)

  const fpPct = (v: number | null) => v != null ? (v >= 0 ? '+' : '') + v.toFixed(1) + '%' : '-'
  const fpDec = (v: number | null) => v != null ? (v >= 0 ? '+' : '') + (v * 100).toFixed(1) + '%' : '-'
  const fv = (v: number | null, d = 1) => v != null ? v.toFixed(d) : '-'
  const clr = (v: number | null) => ({ color: v == null ? 'var(--muted)' : v >= 0 ? '#22d48a' : '#e84560' })
  const clrScore = (v: number | null) => ({ color: v == null ? 'var(--muted)' : v >= 70 ? '#22d48a' : v >= 40 ? '#f97316' : '#e84560' })

  return (
    <div className="space-y-4 p-3">
      <div className="section-hdr">Sector Heatmap — All Europe</div>

      {loading ? (
        <div className="text-center py-12 text-muted">
          <RefreshCw size={24} className="animate-spin mx-auto mb-3 text-gold" />
          <p className="text-sm">Loading…</p>
        </div>
      ) : (
        <>
          <div className="bg-surface border border-border rounded-lg p-4">
            <SectorHeatmap stocks={stocksEur} onSectorClick={onSectorClick} />
          </div>

          <div className="bg-surface border border-border rounded-lg overflow-hidden">
            <div className="px-4 py-2 text-[10px] font-700 uppercase tracking-wide border-b border-border text-gold">
              Sector Aggregates - All Europe ({stocksEur.length} stocks)
            </div>
            <div className="overflow-x-auto">
              <table className="data-table w-full">
                <thead><tr>
                  <th>Sector</th>
                  <th>Stocks</th>
                  <th>Mkt Cap $B</th>
                  <th>1D %</th>
                  <th>EPS Gr %</th>
                  <th>Rev Gr %</th>
                  <th>Mom 12M %</th>
                  <th>Value</th>
                  <th>Growth</th>
                  <th>Best</th>
                </tr></thead>
                <tbody>
                  {sectors.map(s => (
                    <tr key={s.name} onClick={() => onSectorClick(s.name)} className="cursor-pointer">
                      <td>
                        <span className="text-[11px] font-600" style={{ color: getSectorColor(s.name) }}>
                          {s.name}
                        </span>
                      </td>
                      <td className="font-mono text-muted">{s.count}</td>
                      <td className="font-mono">{fv(s.mktCap, 0)}</td>
                      <td className="font-mono font-600" style={clr(s.change1d)}>{fpPct(s.change1d)}</td>
                      <td className="font-mono font-600" style={clr(s.epsGrowth)}>{fpDec(s.epsGrowth)}</td>
                      <td className="font-mono font-600" style={clr(s.revGrowth)}>{fpDec(s.revGrowth)}</td>
                      <td className="font-mono font-700" style={clr(s.mom12m)}>{fpDec(s.mom12m)}</td>
                      <td className="font-mono font-600" style={clrScore(s.valueScore)}>{fv(s.valueScore, 0)}</td>
                      <td className="font-mono font-600" style={clrScore(s.growthScore)}>{fv(s.growthScore, 0)}</td>
                      <td className="font-mono font-600" style={clrScore(s.combinedRank)}>{fv(s.combinedRank, 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}


// - DASHBOARD -
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
  const [usdToEur,  setUsdToEur]  = useState(0.8615)
  const searchTimer = useRef<any>(null)

  useEffect(() => {
    // Aggiorna indici ogni 60 secondi
    const loadIndices = () => apiIndices().then(setIndices)
    loadIndices()
    const timer = setInterval(loadIndices, 60000)

    // Carica tasso USD/EUR
    fetch('/api/fx').then(r => r.ok ? r.json() : null)
      .then(d => { if (d?.usdToEur) setUsdToEur(d.usdToEur) })
      .catch(() => {})

    setLoading(true)
    // Carica da tutti gli exchange - EMU + ex-EMU
    apiExchange('ALL').then(stocks => {
      setAllStocks(stocks)
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


  // Top 600 Europe per market cap
  const u200 = allStocks.map((s:any) => ({...s, mktCap: s.mktCap ?? null}))
    .sort((a:any, b:any) => (b.mktCap || 0) - (a.mktCap || 0))
    .slice(0, 600)

  const valid   = u200.filter((s:any) => s.change1d != null)
  const allGainers = [...valid].filter((s:any) => (s.change1d || 0) > 0).sort((a, b) => (b.change1d || 0) - (a.change1d || 0))
  const allLosers  = [...valid].filter((s:any) => (s.change1d || 0) < 0).sort((a, b) => (a.change1d || 0) - (b.change1d || 0))
  const gainers = allGainers.slice(0, 10)
  const losers  = allLosers.slice(0, 10)
  const ewReturn = valid.length > 0
    ? valid.reduce((a, s) => a + (s.change1d || 0), 0) / valid.length
    : null



  // Price Momentum 12M top/bottom 10
  const allWithMom12 = u200.filter(s => s.mom12m != null)
  const topMom12 = [...allWithMom12].sort((a, b) => (b.mom12m || 0) - (a.mom12m || 0)).slice(0, 10)
  const botMom12 = [...allWithMom12].sort((a, b) => (a.mom12m || 0) - (b.mom12m || 0)).slice(0, 10)

  // KPI V+G >= 80 - entrambi i rank >= 70 (titoli con buon value E buon growth)
  // Best Combined: calcolo identico al Best Ideas screen (combinedRank >= 80 su All Europe)
  const ey_d = (pe: number | null) => (pe && pe !== 0 && Math.abs(pe) <= 200) ? 1/pe : null
  const pRk  = (vals: number[], v: number) => vals.length ? Math.round(vals.filter(x => x < v).length / vals.length * 100) : null

  const eyTV  = allStocks.map((s:any) => ey_d(s.peTrail)).filter((v:any) => v != null) as number[]
  const eyFV  = allStocks.map((s:any) => ey_d(s.peFwd)).filter((v:any) => v != null) as number[]
  const pbV   = allStocks.map((s:any) => s.pb).filter((v:any) => v != null && v > 0 && v < 50) as number[]
  const egV   = allStocks.map((s:any) => s.epsGrowth).filter((v:any) => v != null) as number[]
  const rgV   = allStocks.map((s:any) => s.revGrowth).filter((v:any) => v != null) as number[]
  const m6AV  = allStocks.map((s:any) => s.mom6m  != null && s.mom1w != null ? s.mom6m  - s.mom1w  : null).filter((v:any) => v != null) as number[]
  const m12AV = allStocks.map((s:any) => s.mom12m != null && s.mom1m != null ? s.mom12m - s.mom1m  : null).filter((v:any) => v != null) as number[]

  const calcEuroScore = (s: any) => {
    const eyt = ey_d(s.peTrail); const eyf = ey_d(s.peFwd)
    const pet = eyt != null ? (s.peTrail > 200 ? 1 : pRk(eyTV, eyt)) : null
    const pef = eyf != null ? (s.peFwd   > 200 ? 1 : pRk(eyFV, eyf)) : null
    const pb  = s.pb != null && s.pb > 0 && s.pb < 50 ? (100 - pRk(pbV, s.pb)!) : null
    const vc  = [pet,pef,pb].filter((v:any) => v != null) as number[]
    const eV  = vc.length >= 2 ? vc.reduce((a:number,b:number)=>a+b,0)/vc.length : null
    const m6a = s.mom6m  != null && s.mom1w != null ? s.mom6m  - s.mom1w  : null
    const m12a= s.mom12m != null && s.mom1m != null ? s.mom12m - s.mom1m  : null
    const eg  = s.epsGrowth != null ? pRk(egV,  s.epsGrowth) : null
    const rg  = s.revGrowth != null ? pRk(rgV,  s.revGrowth) : null
    const m6r = m6a  != null ? pRk(m6AV,  m6a)  : null
    const m12r= m12a != null ? pRk(m12AV, m12a) : null
    const gc  = [eg,rg,m6r,m12r].filter((v:any) => v != null) as number[]
    const eG  = gc.length >= 2 ? gc.reduce((a:number,b:number)=>a+b,0)/gc.length : null
    return eV != null && eG != null ? (eV + eG) / 2 : null
  }

  const allScores = u200.map(calcEuroScore).filter((v:any) => v != null) as number[]
  const highVG = u200.filter((s:any) => s.combinedRank != null && s.combinedRank >= 80).length

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

      {/* Indices - aggiornati automaticamente ogni 60s */}
      <div>
        {/* Last Update Banner */}
        <div style={{
          background: 'linear-gradient(135deg, #0f1923 0%, #1e3a5f 100%)',
          border: '1px solid rgba(249,115,22,0.3)',
          borderRadius: 8,
          padding: '12px 20px',
          marginBottom: 16,
          textAlign: 'center'
        }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: 'var(--orange)', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: 4 }}>

          </div>
          <div style={{ fontSize: 20, fontWeight: 800, color: '#ffffff', letterSpacing: '0.02em' }}>

          </div>
          <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>
            WORK IN PROGRESS — Prices may be incorrect. New data source coming in a few days.
          </div>
        </div>

        <div className="section-hdr flex items-center gap-2">
          📈 Index Performance
          <span className="text-[9px] text-muted font-normal">· auto-refresh 60s</span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2">
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
          { label: 'Total Stocks',              value: loading ? '…' : '2,111' },
          { label: 'MCW 1D Return (top 600 Europe)', value: loading ? '…' : fp(ewReturn) },
          { label: 'V+G Best Combined (top 600)', value: loading ? '…' : highVG.toString() },
          { label: 'Gainers/Losers (top 600)',  value: loading ? '…' : `${allGainers.length} / ${allLosers.length}` },
        ].map(({ label, value }) => (
          <div key={label} className="metric-card">
            <div className="metric-label">{label}</div>
            <div className="metric-value">{value}</div>
          </div>
        ))}
      </div>

      {/* Gainers / Losers today - top 200 market cap */}
      {!loading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[
            { title: '🟢 Top 10 Gainers Today', list: gainers, color: 'text-[#22d48a]', field: 'change1d' },
            { title: '🔴 Top 10 Losers Today',  list: losers,  color: 'text-[#e84560]',   field: 'change1d' },
          ].map(({ title, list, color, field }) => (
            <div key={title} className="bg-surface border border-border rounded-lg overflow-hidden">
              <div className={`px-4 py-2 text-[10px] font-700 uppercase tracking-wide border-b border-border ${color}`}>
                {title} - Top 600 Europe by Mkt Cap · <span className="font-normal opacity-70"></span>
              </div>
              <table className="data-table">
                <thead><tr>
                  <th style={{width:90}}>Ticker</th><th>Company</th><th style={{width:65}}>1D %</th>
                </tr></thead>
                <tbody>
                  {list.map((s, i) => (
                    <tr key={i}
                      onClick={() => window.location.href = `/stock/${s.ticker}-${s.exchange}`}
                      className="cursor-pointer">
                      <td className="font-700 text-[12px] text-text whitespace-nowrap">{s.flag} {s.ticker}</td>
                      <td className="text-sub text-[11px]" style={{maxWidth:150,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{(s.company||'').length > 22 ? (s.company||'').slice(0,22)+'…' : s.company}</td>
                      <td className="font-mono font-700 text-right whitespace-nowrap" style={clrStyle(s.change1d)}>{fp(s.change1d)}</td>
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
            { title: '🚀 Top 10 Price Mom 12M (Top 600 Europe)', list: topMom12, color: 'var(--green)' },
            { title: '💣 Bottom 10 Price Mom 12M (Top 600 Europe)', list: botMom12, color: 'var(--red)' },
          ].map(({ title, list, color }) => (
            <div key={title} className="bg-surface border border-border rounded-lg overflow-hidden">
              <div className="px-4 py-2 text-[10px] font-700 uppercase tracking-wide border-b border-border"
                style={{ color }}>
                {title}
              </div>
              <table className="data-table w-full">
                <thead><tr>
                  <th style={{width:90}}>Ticker</th><th>Company</th><th style={{width:72}}>12M %</th>
                </tr></thead>
                <tbody>
                  {list.map((s, i) => (
                    <tr key={i}
                      onClick={() => window.location.href = `/stock/${s.ticker}-${s.exchange}`}
                      className="cursor-pointer">
                      <td className="font-700 text-[12px] whitespace-nowrap" style={{ color: 'var(--orange)' }}>{s.flag} {s.ticker}</td>
                      <td className="text-sub text-[11px]" style={{maxWidth:150,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{(s.company||'').length > 22 ? (s.company||'').slice(0,22)+'…' : s.company}</td>
                      <td className="font-mono font-700 text-right whitespace-nowrap"
                        style={{ color: (s.mom12m||0) >= 0 ? '#22d48a' : '#e84560' }}>
                        {s.mom12m != null ? fp(s.mom12m * 100) : '—'}
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
          <div className="text-[10px] text-muted mb-2">Market cap weighted return by sector · Top 600 Europe</div>
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

// - LOGIN GATE -
function LoginGate({ onLogin, title }: { onLogin: () => void, title: string }) {
  return (
    <div className="p-8 space-y-4 fade-in">
      <div className="section-hdr">⭐ {title}</div>
      <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
        borderRadius:6, padding:'32px', textAlign:'center', maxWidth:400, margin:'0 auto' }}>
        <div style={{ fontSize:40, marginBottom:12 }}>🔒</div>
        <div style={{ fontSize:15, fontWeight:700, color:'var(--text)', marginBottom:8 }}>
          Members only
        </div>
        <div style={{ fontSize:12, color:'var(--text3)', marginBottom:20, lineHeight:1.6 }}>
          The <strong style={{ color:'var(--orange)' }}>{title}</strong> screen is reserved
          for registered users. Create a free account to access our best investment ideas.
        </div>
        <button onClick={onLogin} className="btn-primary text-sm px-8 py-2.5">
          Register for Free
        </button>
        <div style={{ fontSize:11, color:'var(--text4)', marginTop:12 }}>
          Free access during Beta · No credit card required
        </div>
      </div>
    </div>
  )
}

// - LEGAL -
function Legal() {
  const [tab, setTab] = useState<'terms'|'privacy'|'cookie'>('terms')

  return (
    <div className="max-w-2xl space-y-5 fade-in">
      <div className="section-hdr">📋 Legal - ForwardAlpha</div>
      <div className="text-xs text-muted">Last updated: 5 June 2026 · 2,111 European equities — Value & Growth Scores updated · 2,000 US stocks added to the research bar. WORK IN PROGRESS — Prices may be incorrect. New data source coming in a few days..</div>

      <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
        {(['terms','privacy','cookie'] as const).map(t => (
          <button key={t} onClick={() => setTab(t)}
            style={{ padding:'6px 16px', borderRadius:4, fontSize:11, fontWeight:600, cursor:'pointer',
              background: tab===t ? 'var(--orange)' : 'var(--surface)',
              color: tab===t ? '#000' : 'var(--text3)',
              border: '1px solid var(--border)' }}>
            {t === 'terms' ? 'Terms of Use' : t === 'privacy' ? 'Privacy Policy' : 'Cookie Policy'}
          </button>
        ))}
      </div>

      {tab === 'terms' && (
        <div className="space-y-4">
          {([
            ['1. Service Ownership',
             'ForwardAlpha is developed and operated by Andrea Meschini, based in Verona, Italy. Contact: andrea@forwardalpha.pro.'],
            ['2. Service Description & Beta Phase',
             'ForwardAlpha is a web-based quantitative financial screening and research tool offering proprietary Value Score and Growth Score models (percentile rankings 1–100). The Platform is currently in Beta. Registration includes a 14-day free trial with no credit card required.'],
            ['3. Legal Disclaimer – No Financial Advice',
             'ForwardAlpha is for informational and educational purposes only. The Owner is not a registered financial advisor and does not provide investment advisory services. No content constitutes a personalised recommendation or offer to buy/sell financial instruments under MiFID II. Investing involves significant risk of capital loss. Past performance is not indicative of future results.'],
            ['4. Data Accuracy & Limitation of Liability',
             'Market prices are delayed approximately 15–20 minutes. Fundamental data is updated end of day. The service is provided "as is" without warranty of accuracy, completeness or uninterrupted availability. The Owner shall not be liable for any direct or indirect losses arising from use of the Platform. Data is sourced from third-party providers; the Owner does not guarantee compliance with their individual licence terms for commercial use.'],
            ['5. Intellectual Property',
             'All content (UI, source code, Value Score and Growth Score algorithms, brand name "ForwardAlpha") is the exclusive property of Andrea Meschini. Strictly prohibited: automated scraping or crawling, reverse engineering of algorithms, redistribution or resale of Platform data to third parties without prior written consent.'],
            ['6. Account, Suspension & Termination',
             'Users are responsible for their login credentials and all account activity. The Owner reserves the right to suspend or terminate any account immediately and without notice in case of breach of these Terms, fraudulent use, or automated data extraction.'],
            ['7. Clausole Vessatorie (Art. 1341–1342 c.c.)',
             'In accordance with Italian civil law, the following clauses are explicitly brought to your attention and require specific acceptance: (a) limitation of liability (clause 4); (b) exclusive jurisdiction of the Court of Verona (clause 8). By creating an account you confirm you have read and specifically accepted these clauses.'],
            ['8. Governing Law & Jurisdiction',
             `These Terms are governed by Italian law. Any disputes shall be subject to the exclusive jurisdiction of the Court of Verona, without prejudice to mandatory consumer protection rights in the user's country of residence. Pursuant to Art. 14 of Regulation (EU) No 524/2013, users may also resolve disputes through the European Commission ODR platform: https://ec.europa.eu/consumers/odr/`],
          ] as [string,string][]).map(([title, body]) => (
            <div key={title} className="bg-surface border border-border rounded-lg p-4">
              <h3 className="font-700 text-text text-sm mb-2">{title}</h3>
              <p className="text-xs text-sub leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      )}

      {tab === 'privacy' && (
        <div className="space-y-4">
          {([
            ['1. Data Controller',
             'Data Controller: Andrea Meschini, Verona (VR), Italy. Contact: andrea@forwardalpha.pro. For GDPR-related requests, contact the Data Controller directly by email.'],
            ['2. Data We Collect',
             'We collect: full name, email address, country of residence, hashed password (via Supabase Auth). We also collect usage data (screens visited, filters applied) solely to improve the service. We do not collect payment data directly — this is handled by Stripe if and when subscriptions are activated.'],
            ['3. Legal Basis for Processing',
             'Personal data is processed on the basis of: (a) contract performance (Art. 6.1.b GDPR) — to provide the service you registered for; (b) legitimate interest (Art. 6.1.f GDPR) — for security and fraud prevention; (c) consent (Art. 6.1.a GDPR) — for optional newsletter communications.'],
            ['4. Data Retention',
             'Account data is retained for as long as your account is active. If you delete your account, personal data is permanently deleted within 30 days. Anonymised usage analytics may be retained indefinitely.'],
            ['5. Your Rights (GDPR)',
             'You have the right to: access your data, rectify inaccurate data, request erasure ("right to be forgotten"), restrict processing, data portability, and object to processing. To exercise these rights, contact andrea@forwardalpha.pro.'],
            ['6. Sub-processors',
             'We use the following third-party sub-processors who act as data processors on our behalf: Supabase Inc. (database and authentication, EU servers — see supabase.com/privacy); Vercel Inc. (hosting and CDN — see vercel.com/legal/privacy-policy). All sub-processors are contractually bound to handle data in accordance with GDPR.'],
            ['7. International Transfers',
             'Data is stored on Supabase EU-based servers. Where any transfer outside the EEA occurs, appropriate safeguards (Standard Contractual Clauses) are in place.'],
            ['8. Newsletter',
             'If you opt in during registration, your email will be used to send product updates and market insights. You may unsubscribe at any time via the link in any email or by contacting us directly.'],
          ] as [string,string][]).map(([title, body]) => (
            <div key={title} className="bg-surface border border-border rounded-lg p-4">
              <h3 className="font-700 text-text text-sm mb-2">{title}</h3>
              <p className="text-xs text-sub leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      )}

      {tab === 'cookie' && (
        <div className="space-y-4">
          {([
            ['1. What are Cookies?',
             'Cookies are small text files stored on your device when you visit a website, retransmitted on subsequent visits.'],
            ['2. Cookies Used by ForwardAlpha',
             'We use only strictly necessary technical cookies: (a) Authentication & Session — to manage login and maintain secure access via Supabase (EU servers); (b) Security — to prevent fraudulent use and protect against attacks; (c) Preferences — to remember choices such as cookie banner acceptance. No advertising, profiling or third-party tracking cookies are used.'],
            ['3. Legal Basis',
             'Processing via technical cookies is based on contract performance (Art. 6.1.b GDPR). Since only strictly necessary cookies are used, prior consent is not required under Art. 122 of the Italian Privacy Code. Should we introduce analytics or advertising cookies in future, a full consent banner will be implemented.'],
            ['4. Managing Cookies',
             'You can control or delete cookies via your browser settings (Chrome, Firefox, Safari, Edge). Disabling technical cookies will prevent login and impair core Platform functionality.'],
            ['5. Contact',
             'For any privacy or cookie queries: andrea@forwardalpha.pro. Andrea Meschini is the data controller under GDPR.'],
          ] as [string,string][]).map(([title, body]) => (
            <div key={title} className="bg-surface border border-border rounded-lg p-4">
              <h3 className="font-700 text-text text-sm mb-2">{title}</h3>
              <p className="text-xs text-sub leading-relaxed">{body}</p>
            </div>
          ))}
        </div>
      )}

      <div className="text-xs text-muted border-t border-border pt-4">
        Andrea Meschini · Verona, Italy ·{' '}
        <a href="mailto:andrea@forwardalpha.pro" className="text-gold underline">andrea@forwardalpha.pro</a>
        {' '}· © 2026 ForwardAlpha
      </div>
    </div>
  )
}

// - COOKIE BANNER -
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

// - ROOT APP -
export default function App() {
  const [page,        setPage]        = useState<Page>('dashboard')
  const [user,        setUser]        = useState<SupabaseUser | null>(null)
  const [showAuth,    setShowAuth]    = useState(false)
  const [sidebarOpen, setSidebar]     = useState(false)
  const [expandedMenus, setExpandedMenus] = useState<Set<string>>(new Set(['dashboard']))
  const toggleMenu = (id: string) => setExpandedMenus(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n })
  const [scrExchange, setScrExchange] = useState('MIL')
  const [scrSector,   setScrSector]   = useState('All')
  const [scrSectorUS, setScrSectorUS] = useState('All')
  const [scrEpsMom,   setScrEpsMom]   = useState<string>('')
  const [detailStock, setDetailStock] = useState<Stock | null>(null)

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setUser(data.user ?? null))
    const { data: sub } = supabase.auth.onAuthStateChange((_, sess) => {
      setUser(sess?.user ?? null)
    })
    return () => sub.subscription.unsubscribe()
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const p = params.get("page")
    const s = params.get("sector")
    if (p) {
      if (p === "northamerica") { setScrSectorUS(s || "All"); setPage("northamerica") }
      else if (p === "screener") { setScrExchange("EZ"); setScrSector(s || "All"); setScrSectorUS("All"); setPage("screener") }
      else { setScrSectorUS("All"); setPage(p as Page) }
    } else {
      setScrSectorUS("All")
    }
  }, [])
  function goSector(sector: string) {
    setScrExchange('EZ'); setScrSector(sector); setScrEpsMom(''); setPage('screener'); setSidebar(false)
  }

  function goScreenerEpsMom(filter: string) {
    setScrExchange('EZ'); setScrSector('All'); setScrEpsMom(filter); setPage('screener'); setSidebar(false)
  }

  const accordionMenus = [
    { id: 'dashboard', label: '📊 Dashboard', items: [
      { id: 'northamerica' as Page, label: '🌎 North America' },
      { id: 'dashboard' as Page, label: '🌍 Europe' },
      { id: null, label: '🌏 Asia Pacific 🔜' },
    ]},
    { id: 'bestideas', label: '⭐ Best Ideas', items: [
      { id: 'bestideas_us' as Page, label: '🌎 North America' },
      { id: 'bestideas' as Page, label: '🌍 Europe' },
      { id: null, label: '🌏 Asia Pacific 🔜' },
    ]},
    { id: 'bestvalue', label: '📈 Best Value', items: [
      { id: 'bestvalue_us' as Page, label: '🌎 North America' },
      { id: 'bestvalue' as Page, label: '🌍 Europe' },
      { id: null, label: '🌏 Asia Pacific 🔜' },
    ]},
    { id: 'bestgrowth', label: '🌱 Best Growth', items: [
      { id: 'bestgrowth_us' as Page, label: '🌎 North America' },
      { id: 'bestgrowth' as Page, label: '🌍 Europe' },
      { id: null, label: '🌏 Asia Pacific 🔜' },
    ]},
    { id: 'sectors', label: '🏭 Sectors', items: [
      { id: 'sectors_us' as Page, label: '🌎 North America' },
      { id: 'sectors' as Page, label: '🌍 Europe' },
      { id: null, label: '🌏 Asia Pacific 🔜' },
    ]},
  ]

  const singleMarkets = [
    { id: 'myscreen' as Page, label: '⭐ My Screen' },
    { id: 'northamerica' as Page, label: '🌎 North America' },
    { id: 'screener' as Page, label: '🌍 All Europe' },
    { id: 'eurozone' as Page, label: '🇪🇺 Eurozone' },
    { id: null, label: '🌏 Asia Pacific 🔜' },
    { id: 'VI' as Page, label: '🇦🇹 Austria' },
    { id: 'BR' as Page, label: '🇧🇪 Belgium' },
    { id: 'CPSE' as Page, label: '🇩🇰 Denmark' },
    { id: 'HE' as Page, label: '🇫🇮 Finland' },
    { id: 'PA' as Page, label: '🇫🇷 France' },
    { id: 'XETRA' as Page, label: '🇩🇪 Germany' },
   
    { id: 'IR' as Page, label: '🇮🇪 Ireland' },
    { id: 'MIL' as Page, label: '🇮🇹 Italy' },
    { id: 'AS' as Page, label: '🇳🇱 Netherlands' },
    { id: 'OB' as Page, label: '🇳🇴 Norway' },
    { id: 'LS' as Page, label: '🇵🇹 Portugal' },
    { id: 'MC' as Page, label: '🇪🇸 Spain' },
    { id: 'SWX' as Page, label: '🇨🇭 Switzerland' },
    { id: 'OM' as Page, label: '🇸🇪 Sweden' },
    { id: 'LSE' as Page, label: '🇬🇧 UK (LSE)' },
    { id: 'usscreen' as Page, label: '🇺🇸 United States' },
  ]

  const externalNav: {href:string,label:string}[] = []

  return (
    <div className="flex h-screen overflow-hidden bg-bg">

      {/* - SIDEBAR - */}
      <aside className={`
        flex-col w-52 bg-surface border-r border-border flex-shrink-0 transition-all
        ${sidebarOpen ? 'flex fixed inset-y-0 left-0 z-40' : 'hidden md:flex'}
      `}>
        {/* Logo */}
        <div className="p-4 border-b border-border">
          <div className="font-700 text-lg leading-tight" style={{ fontFamily: 'IBM Plex Sans Condensed' }}>
            FORWARD<span style={{ color: 'var(--orange)' }}>ALPHA</span>
          </div>
          <div className="text-[9px] text-muted mt-0.5">Global Equity Research</div>
          <div className="flex gap-1 mt-2 flex-wrap">
            <span className="badge badge-beta">🧪 BETA</span>
            <span className="badge badge-live">● LIVE</span>
          </div>
        </div>

        <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
        {/* About + Research */}
        <button onClick={() => { setPage('about'); setSidebar(false) }}
          className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded text-sm font-700 transition-colors ${page === 'about' ? 'bg-gold/15 text-gold' : 'text-orange-400 hover:text-gold'}`}>
          <Info size={16} /> About
        </button>
        <button onClick={() => { window.location.href='/research' }}
          className='w-full flex items-center gap-2.5 px-3 py-2.5 rounded text-sm font-700 text-orange-400 hover:text-gold transition-colors'>
          <FileText size={16} /> 📄 Research
        </button>
        <div style={{ height:1, background:'var(--border)', margin:'4px 4px' }} />
        {accordionMenus.map(menu => (
          <div key={menu.id}>
            <button onClick={() => toggleMenu(menu.id)}
              className='w-full flex items-center justify-between px-3 py-2.5 rounded text-sm font-600 text-orange-400 hover:text-gold transition-colors'>
              <span>{menu.label}</span>
              <ChevronDown size={12} className={`transition-transform ${expandedMenus.has(menu.id) ? 'rotate-180' : ''}`} />
            </button>
            {expandedMenus.has(menu.id) && (
              <div className='ml-2 space-y-0.5'>
                {menu.items.map((item, idx) => item.id ? (
                  <button key={idx} onClick={() => { setPage(item.id as Page); setSidebar(false); toggleMenu(menu.id) }}
                    className={`w-full flex items-center gap-2 px-3 py-2 rounded text-xs transition-colors ${page === item.id ? 'bg-gold/15 text-gold' : 'text-sub hover:text-text'}`}>
                    {item.label}
                  </button>
                ) : (
                  <div key={idx} className='px-3 py-2 text-xs text-muted'>{item.label}</div>
                ))}
              </div>
            )}
          </div>
        ))}
        <div style={{ height:1, background:'var(--border)', margin:'4px 4px' }} />
        {singleMarkets.map((item, idx) => item.id ? (
          <button key={idx} onClick={() => { setScrSectorUS("All"); setScrSector("All"); setPage(item.id as Page); setSidebar(false) }}
            className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded text-sm transition-colors ${page === item.id ? 'bg-gold/15 text-gold' : 'text-text3 hover:text-text hover:bg-surface2'}`}>
          </button>
        ) : (
          <div key={idx} className='px-3 py-2 text-xs text-muted'>{item.label}</div>
        ))}
        <div style={{ height:1, background:'var(--border)', margin:'4px 4px' }} />
        <button onClick={() => { setPage('portfolio'); setSidebar(false) }} className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded text-sm transition-colors ${page === 'portfolio' ? 'bg-gold/10 text-gold' : 'text-text3 hover:text-text hover:bg-surface2'}`}>💼 Portfolio</button>
        <button onClick={() => { setPage('legal'); setSidebar(false) }} className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded text-sm transition-colors ${page === 'legal' ? 'bg-gold/10 text-gold' : 'text-text3 hover:text-text hover:bg-surface2'}`}>📋 Legal</button>
      </nav>

        {/* User */}
        <div className="p-3 border-t border-border space-y-2">
          {user ? (
            <>
              <div className="text-[10px] text-green font-600 truncate">👤 {user?.email}</div>
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
          ⚠️ Prices indicative — new data source coming soon<br />
          ⚠️ Prices indicative — new data source coming soon<br />
          Fundamentals: daily
        </div>
      </aside>

      {sidebarOpen && (
        <div className="fixed inset-0 bg-black/50 z-30 md:hidden" onClick={() => setSidebar(false)} />
      )}

      {/* - MAIN - */}
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
          {(page === 'screener' || page === 'MIL' || page === 'PA' || page === 'XETRA' || page === 'LSE' || page === 'OM' || page === 'OB' || page === 'SWX' || page === 'MC' || page === 'AS' || page === 'HE' || page === 'BR' || page === 'CPSE' || page === 'VI' || page === 'LS' || page === 'IR') && <Screener key={`${page}-${scrSector}`} initExchange={page === 'screener' ? scrExchange : page} initSector={page === 'screener' ? scrSector : 'All'} initEpsMom={scrEpsMom} onSelectStock={setDetailStock} userId={user?.id || null} />}
          {page === 'bestvalue'  && (user
            ? <Screener key="bestvalue"  initExchange="EZ" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} initValMin={80} initGrowMin={30} showAll={true} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Best Value" />
          )}
          {page === 'bestideas'  && (user
            ? <Screener key="bestideas"  initExchange="EZ" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} initValMin={0} initGrowMin={0} initCombinedMin={80} showAll={true} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Best Ideas" />
          )}
          {page === 'bestgrowth' && (user
            ? <Screener key="bestgrowth" initExchange="EZ" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} initValMin={0} initGrowMin={80} showAll={true} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Best Growth" />
          )}
 {page === 'northamerica' && <Screener key="northamerica" initExchange="US" initSector={scrSectorUS} initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} />}
 {page === 'usscreen' && <Screener key="usscreen" initExchange="US" initSector={scrSectorUS} initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} />}
          {page === 'eurozone'  && <Screener key="eurozone"  initExchange="EMU" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} />}
          {page === 'sectors'   && <SectorScreen onSectorClick={goSector} />}
          {page === 'about'     && (
          <div className="flex-1 overflow-y-auto">
            <iframe src="/about" style={{ width:'100%', height:'100%', border:'none', minHeight:'calc(100vh - 60px)' }} />
          </div>
        )}
          {page === 'research' && <ResearchPage />}
        {page === 'myscreen' && (
            user
              ? <MyScreen userId={user!.id} onSelectStock={setDetailStock} />
              : <LoginGate onLogin={() => setShowAuth(true)} title="My Screen" />
          )}
          {page === 'portfolio' && (
            user ? (
              <div className="p-8 space-y-4 fade-in">
                <div className="section-hdr">💼 Portfolio</div>
                <div style={{ background:'rgba(249,115,22,0.08)', border:'1px solid rgba(249,115,22,0.2)',
                  borderRadius:6, padding:'16px', fontSize:12, color:'var(--text3)' }}>
                  <div style={{ fontSize:14, fontWeight:700, color:'var(--orange)', marginBottom:8 }}>
                    🚧 Coming Soon
                  </div>
                  Portfolio tracking with multi-currency support, performance analytics,
                  Value/Growth score overlay and sector breakdown is under development.
                  <div style={{ marginTop:8, fontSize:11, color:'var(--text4)' }}>
                    Logged in as: <span style={{ color:'var(--green)' }}>{user?.email}</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-8 space-y-4 fade-in">
                <div className="section-hdr">💼 Portfolio</div>
                <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
                  borderRadius:6, padding:'24px', textAlign:'center' }}>
                  <div style={{ fontSize:32, marginBottom:12 }}>🔒</div>
                  <div style={{ fontSize:14, fontWeight:700, color:'var(--text)', marginBottom:8 }}>
                    Login required
                  </div>
                  <div style={{ fontSize:12, color:'var(--text3)', marginBottom:16 }}>
                    Create a free account to track your portfolio and access personalised features.
                  </div>
                  <button onClick={() => setShowAuth(true)}
                    className="btn-primary text-sm px-6 py-2">
                    Register / Log In
                  </button>
                </div>
              </div>
            )
          )}
          {page === 'legal'     && <Legal />}
        </div>

        <footer className="border-t border-border px-4 py-2 bg-surface text-[9px] text-muted flex flex-wrap gap-x-4 gap-y-1">
          <span className="font-700 text-sub">ForwardAlpha · Verona, Italy</span>
          <span>⚠️ Not investment advice</span>
          <span>Prices indicative</span>
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
