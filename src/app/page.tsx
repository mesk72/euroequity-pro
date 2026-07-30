'use client'

import { useRouter, useSearchParams, usePathname } from 'next/navigation'
import { useState, useEffect, useCallback, useRef, Suspense } from 'react'
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
import NewsPage from '@/components/news/NewsPage'
import toast from 'react-hot-toast'
import type { User as SupabaseUser } from '@supabase/supabase-js'
import StockDetailPage from '@/components/dashboard/StockDetailPage'
import WatchlistButton from '@/components/watchlist/WatchlistButton'

// Funzione globale (fuori da ogni componente): naviga a una pagina titolo
// salvando la provenienza in sessionStorage, cosi' e' richiamabile da
// qualsiasi sotto-componente senza bisogno di router/pathname nello scope
// locale. Usa window.location.href (ricarica pagina) invece del router
// client-side di Next.js — meno fluido ma elimina alla radice il problema
// di cache del router che ha causato tre tentativi di fix falliti.
function goToStock(ticker: string, exchange: string) {
  // FIX 29/7/2026 (Kimi + Claude): eliminato sessionStorage. Prima l'origine
  // veniva passata sia via sessionStorage sia via ?from nell'URL - due
  // meccanismi paralleli per lo stesso dato, con replaceState() manuale a
  // fare da collante tra i due. Fragile: bastava una race tra i due
  // meccanismi (es. sessionStorage scritto da un secondo titolo mentre lo
  // stato history del primo non era ancora completamente assestato) per
  // mandare il "Back" nel posto sbagliato al secondo titolo aperto dallo
  // stesso screener - bug riportato piu' volte, mai risolto del tutto con
  // fix incrementali sul meccanismo misto. Ora l'origine vive SOLO nell'URL
  // della pagina titolo (?from=...): ogni voce della cronologia del browser
  // porta la propria origine, senza stato globale condiviso tra tab/pagine.
  const origin = window.location.pathname + window.location.search
  window.location.href = `/stock/${ticker}-${exchange}?from=${encodeURIComponent(origin)}`
}

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
// Etichetta + colore per il sistema a quintili — sostituisce i vecchi
// rank esatti quando il dato grezzo non e' disponibile. Riusa la stessa
// palette gia' presente nel sito (verde/arancione/rosso) per coerenza.
const QUINTILE_LABELS: Record<string, { short: string; color: string }> = {
  'Top Quintile':    { short: '1° Quintile',   color: '#22c55e' },
  '2nd Quintile':    { short: '2° Quintile',    color: '#84cc16' },
  'Middle':          { short: '3° Quintile',       color: '#f97316' },
  '4th Quintile':    { short: '4° Quintile',    color: '#f97316' },
  'Bottom Quintile': { short: '5° Quintile',color: '#ef4444' },
}
function quintileDisplay(label: string | null | undefined) {
  if (!label) return { text: '-', color: '#8a9ab8' }
  const q = QUINTILE_LABELS[label]
  return q ? { text: q.short, color: q.color } : { text: '-', color: '#8a9ab8' }
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

  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: 'ForwardAlpha',
    url: 'https://forwardalpha.pro',
    description: 'Institutional-grade quantitative equity research covering 7,000+ global stocks.',
    author: {
      '@type': 'Person',
      name: 'Andrea Meschini',
      jobTitle: 'Portfolio Manager & Founder',
      alumniOf: ['J.P. Morgan Asset Management', 'Zenit SGR'],
    },
    about: {
      '@type': 'Thing',
      name: 'Global Equity Research',
      description: 'Value, Growth and Best Score ranking for stocks in Europe, US, Canada, Japan, Hong Kong and Australia.',
    },
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
      />
      <div>
      <div className="flex justify-between items-center mb-1">
        <span className="text-[9px] text-muted uppercase tracking-wide">{label}</span>
        <span className="text-xs font-700 font-mono" style={{ color }}>{Math.round(value)}</span>
      </div>
      <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div className="h-full rounded-full transition-all" style={{ width: `${value}%`, background: color }} />
      </div>
    </div>
  </>
  )
}

type Page = 'home' | 'dashboard' | 'screener' | 'eurozone' | 'bestideas' | 'bestvalue' | 'bestgrowth' | 'about' | 'sectors' | 'news' | 'bestvalue_us' | 'bestideas_us' | 'bestgrowth_us' | 'sectors_us' | 'portfolio' | 'legal' | 'research' | 'myscreen' | 'northamerica' | 'usscreen' | 'globalscreen' | 'MIL' | 'PA' | 'XETRA' | 'LSE' | 'OM' | 'OB' | 'SWX' | 'MC' | 'AS' | 'HE' | 'BR' | 'GR' | 'CPSE' | 'VI' | 'LS' | 'IR' | 'asiapacific' | 'nascreen' | 'apdashboard' | 'TSE' | 'SEHK' | 'TSX' | 'ASX' | 'KRX' | 'SGX' | 'bestideas_ap' | 'bestvalue_ap' | 'bestgrowth_ap' | 'sectors_ap'

// - API CALLS -
async function apiExchange(code: string, thresholds?: { minValue?: number; minGrowth?: number; minCombined?: number; capRows?: number }): Promise<Stock[]> {
  if (USE_DEMO) {
    const scored = computeScores([...DEMO_STOCKS])
    if (code === 'EZ') return scored
    return scored.filter(s => s.exchange === code)
  }
  if (USE_DB) {
    try {
      const EMU_EXCHANGES = 'MIL,XETRA,PA,AS,MC,BR,LS,VI,HE,IR,GR'
      const ALL_EX = 'MIL,XETRA,PA,AS,MC,BR,LS,VI,HE,IR,GR,LSE,SWX,OM,OB,CPSE'
      // Gestisce exchange multipli separati da virgola (es. "US,TSX" o "TSE,SEHK,ASX,KRX,SGX")
      const isMulti = code.includes(',')
      let url = code === 'EZ' || code === 'ALL'
        ? `/api/db/stocks?exchanges=${ALL_EX}`
        : code === 'EMU'
          ? `/api/db/stocks?exchanges=${EMU_EXCHANGES}`
          : isMulti
            ? `/api/db/stocks?exchanges=${encodeURIComponent(code)}`
            : `/api/db/stocks?exchange=${encodeURIComponent(code)}`
      // Soglie di punteggio (Best Value/Growth/Ideas): filtra lato server,
      // cosi' il browser non riceve mai l'intero universo del continente
      // per poi filtrarlo localmente — solo i titoli che gia' qualificano.
      if (thresholds?.minValue) url += `&minValue=${thresholds.minValue}`
      if (thresholds?.minGrowth) url += `&minGrowth=${thresholds.minGrowth}`
      if (thresholds?.minCombined) url += `&minCombined=${thresholds.minCombined}`
      if (thresholds?.capRows) url += `&capRows=${thresholds.capRows}`
      // Rate limiting per utente, non solo per IP — recuperato qui
      // internamente cosi' TUTTE le chiamate esistenti a apiExchange lo
      // includono automaticamente, senza dover modificare ogni chiamante.
      // Include anche il vero token di sessione (non solo l'id) come
      // header Authorization, cosi' il server puo' VERIFICARE davvero
      // che l'utente sia autenticato, non solo fidarsi di un id scritto
      // nell'URL — necessario perche' i punteggi reali vengono inviati
      // solo a chi supera questa verifica.
      let authHeader: Record<string, string> = {}
      try {
        const { data: { session: currentSession } } = await supabase.auth.getSession()
        if (currentSession?.user?.id) url += `&uid=${encodeURIComponent(currentSession.user.id)}`
        if (currentSession?.access_token) authHeader = { Authorization: `Bearer ${currentSession.access_token}` }
      } catch {}
      const r = await fetch(url, { cache: 'no-store', headers: authHeader })
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
        fetch(`/api/exchange?code=${c}`, { cache: 'no-store' })
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
    case 'change1d':    return { val: v != null ? fp(v*100)     : '-', cls: v != null ? clr(v)        : 'text-muted', style: v != null ? clrStyle(v) : undefined }
    case 'mktCap':      return { val: v != null ? fv(v, 1)  : '-', cls: v != null ? 'text-sub'    : 'text-muted' }
    case 'peTrail':     return { val: v != null ? fv(v, 1)  : '-', cls: v != null ? 'text-sub'    : 'text-muted' }
    case 'peFwd':       return { val: v != null ? fv(v, 1)  : '-', cls: v != null ? 'text-sub'    : 'text-muted' }
    case 'epsGrowth':   return { val: v != null ? fpd(v)    : '-', cls: v != null ? clr(v)        : 'text-muted', style: v != null ? clrStyle(v) : undefined }
    case 'revGrowth':   return { val: v != null ? fpd(v)    : '-', cls: v != null ? clr(v)        : 'text-muted', style: v != null ? clrStyle(v) : undefined }
    case 'mom1w':       return { val: v != null ? fpd(v)    : '-', cls: v != null ? clr(v)        : 'text-muted', style: v != null ? clrStyle(v) : undefined }
    case 'mom1m':       return { val: v != null ? fpd(v)    : '-', cls: v != null ? clr(v)        : 'text-muted', style: v != null ? clrStyle(v) : undefined }
    case 'mom6m':       return { val: v != null ? fpd(v)    : '-', cls: v != null ? clr(v)        : 'text-muted', style: v != null ? clrStyle(v) : undefined }
    case 'mom12m':      return { val: v != null ? fpd(v)    : '-', cls: v != null ? clr(v)        : 'text-muted', style: v != null ? clrStyle(v) : undefined }
    case 'rankPeLtm':   return { val: v != null ? fn(v) : quintileDisplay((s as any).peTrailingQuintile).text, cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-[#e84560]' : 'text-yellow-400') : '', style: v == null ? { color: quintileDisplay((s as any).peTrailingQuintile).color } : undefined }
    case 'rankPeNtm':   return { val: v != null ? fn(v) : quintileDisplay((s as any).peForwardQuintile).text, cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-[#e84560]' : 'text-yellow-400') : '', style: v == null ? { color: quintileDisplay((s as any).peForwardQuintile).color } : undefined }
    case 'rankPb':      return { val: v != null ? fn(v) : quintileDisplay((s as any).pbQuintile).text, cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-[#e84560]' : 'text-yellow-400') : '', style: v == null ? { color: quintileDisplay((s as any).pbQuintile).color } : undefined }
    case 'rankEpsGr':   return { val: v != null ? fn(v) : quintileDisplay((s as any).epsGrowthQuintile).text, cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-[#e84560]' : 'text-yellow-400') : '', style: v == null ? { color: quintileDisplay((s as any).epsGrowthQuintile).color } : undefined }
    case 'rankRevGr':   return { val: v != null ? fn(v) : quintileDisplay((s as any).revGrowthQuintile).text, cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-[#e84560]' : 'text-yellow-400') : '', style: v == null ? { color: quintileDisplay((s as any).revGrowthQuintile).color } : undefined }
    case 'combinedRank': return { val: v != null ? fn(v) : '-', cls: v != null ? (v >= 80 ? 'text-green font-700' : v >= 60 ? 'text-yellow-400' : 'text-muted') : 'text-muted' }
    case 'valueScore':  return { val: v != null ? fn(v)     : '-', cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-[#e84560]' : 'text-yellow-400 font-600') : 'text-muted' }
    case 'growthScore': return { val: v != null ? fn(v)     : '-', cls: v != null ? (v >= 70 ? 'text-green font-700' : v <= 30 ? 'text-[#e84560]' : 'text-yellow-400 font-600') : 'text-muted' }
    default:            return { val: '-', cls: 'text-muted' }
  }
}

function StockTable({ stocks, onSelect, loading, maxRows = 100, userId = null, fromPage = "", restrictScoreSort = false }: {
  stocks: Stock[]
  onSelect: (s: Stock) => void
  loading?: boolean
  maxRows?: number
  userId?: string | null
  fromPage?: string
  restrictScoreSort?: boolean
}) {
  const router = useRouter()
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
  // Nelle viste Best Ideas/Value/Growth, ordinare per Value/Growth/Best
  // Score e' riservato al solo proprietario — anche per chi e' loggato
  // o institutional viewer (23/7/2026, richiesta esplicita).
  const SCORE_KEYS = new Set(['valueScore','growthScore','combinedRank'])
  const toggle = (key: SortKey) => {
    if (NO_SORT.has(key)) return
    if (restrictScoreSort && SCORE_KEYS.has(key)) return
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
 {sorted.map((s, i) => {
 const sColor = getSectorColor(s.sector)
 return (
 <div key={`${s.ticker}.${s.exchange}`}
 onClick={() => goToStock(s.ticker, s.exchange)}
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
 {s.change1d != null ? fpd(s.change1d) : '-'}
 </span>
 </div>
 </div>
 <div className="flex items-center justify-between mb-1">
 <span className="text-xs text-sub truncate max-w-[180px]">{s.company}</span>
 <span className="text-[9px] font-600" style={{ color: sColor }}>{s.sector || '-'}</span>
 </div>
 <div className="flex items-center gap-2 text-[10px] font-mono mt-0.5">
 <span className="text-muted">Cap: <span className="text-sub">{s.mktCap != null ? ('$'+s.mktCap.toFixed(1)+'B') : '-'}</span></span>
 <span className="text-[#444]">|</span>
 <span className="text-muted">PEv: <span style={{color: (s as any).rankPeLtm != null ? '#3b82f6' : quintileDisplay((s as any).peTrailingQuintile).color}}>{(s as any).rankPeLtm != null ? Math.round((s as any).rankPeLtm) : quintileDisplay((s as any).peTrailingQuintile).text}</span></span>
 <span className="text-[#444]">|</span>
 <span className="text-muted">PEf: <span style={{color: (s as any).rankPeNtm != null ? '#3b82f6' : quintileDisplay((s as any).peForwardQuintile).color}}>{(s as any).rankPeNtm != null ? Math.round((s as any).rankPeNtm) : quintileDisplay((s as any).peForwardQuintile).text}</span></span>
 <span className="text-[#444]">|</span>
 <span className="text-muted">EPS: <span style={{color: (s as any).rankEpsGr != null ? '#22c55e' : quintileDisplay((s as any).epsGrowthQuintile).color}}>{(s as any).rankEpsGr != null ? Math.round((s as any).rankEpsGr) : quintileDisplay((s as any).epsGrowthQuintile).text}</span></span>
 <span className="text-[#444]">|</span>
 <span className="text-muted">Rev: <span style={{color: (s as any).rankRevGr != null ? '#22c55e' : quintileDisplay((s as any).revGrowthQuintile).color}}>{(s as any).rankRevGr != null ? Math.round((s as any).rankRevGr) : quintileDisplay((s as any).revGrowthQuintile).text}</span></span>
 </div>
 <div className="flex items-center gap-2 text-[10px] font-mono mt-0.5">
 <span className="text-muted">Val: <span style={{color:'#3b82f6'}}>{userId ? (s.valueScore != null ? Math.round(s.valueScore) : '-') : '🔒'}</span></span>
 <span className="text-[#444]">|</span>
 <span className="text-muted">Grw: <span style={{color:'#22c55e'}}>{userId ? (s.growthScore != null ? Math.round(s.growthScore) : '-') : '🔒'}</span></span>
 <span className="text-[#444]">|</span>
 <span className="text-muted">Best: <span style={{color:'var(--orange)'}}>{userId ? (s.combinedRank != null ? Math.round(s.combinedRank) : '-') : '🔒'}</span></span>
 <span className="text-[#444]">|</span>
 <span className="text-muted">1M: <span style={{color: s.mom1m != null ? (s.mom1m >= 0 ? '#22d48a' : '#e84560') : '#8a9ab8'}}>{userId ? (s.mom1m != null ? ((s.mom1m*100).toFixed(1)+'%') : '-') : '🔒'}</span></span>
 <span className="text-[#444]">|</span>
 <span className="text-muted">12M: <span style={{color: s.mom12m != null ? (s.mom12m >= 0 ? '#22d48a' : '#e84560') : '#8a9ab8'}}>{userId ? (s.mom12m != null ? ((s.mom12m*100).toFixed(1)+'%') : '-') : '🔒'}</span></span>
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
                  cursor: (NO_SORT.has(c.key) || (!userId && LOCKED_GUEST.has(c.key)) || (restrictScoreSort && SCORE_KEYS.has(c.key))) ? 'default' : 'pointer',
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
              onClick={() => goToStock(s.ticker, s.exchange)}
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
    ['1D %',         fp(stock.change1d != null ? stock.change1d*100 : null),        clr(stock.change1d)],
    ['Mkt Cap B',    fv(stock.mktCap, 1),       ''],
    ['P/E Trailing', stock.peTrail != null ? fv(stock.peTrail, 1) : quintileDisplay(stock.peTrailingQuintile).text,      stock.peTrail != null ? '' : `text-[${quintileDisplay(stock.peTrailingQuintile).color}]`],
    ['P/E Fwd',      stock.peFwd != null ? fv(stock.peFwd, 1) : quintileDisplay(stock.peForwardQuintile).text,        stock.peFwd != null ? '' : `text-[${quintileDisplay(stock.peForwardQuintile).color}]`],
    ['P/B',          stock.pb != null ? fv(stock.pb, 2) : quintileDisplay(stock.pbQuintile).text,           stock.pb != null ? '' : `text-[${quintileDisplay(stock.pbQuintile).color}]`],
    ['EPS Gr %',     stock.epsGrowth != null ? fpd(stock.epsGrowth) : quintileDisplay(stock.epsGrowthQuintile).text,      stock.epsGrowth != null ? '' : `text-[${quintileDisplay(stock.epsGrowthQuintile).color}]`],
    ['Rev Gr %',     stock.revGrowth != null ? fpd(stock.revGrowth) : quintileDisplay(stock.revGrowthQuintile).text,      stock.revGrowth != null ? '' : `text-[${quintileDisplay(stock.revGrowthQuintile).color}]`],
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
            <span className={`ml-2 font-mono text-sm ${clr(stock.change1d)}`}>{fp(stock.change1d != null ? stock.change1d*100 : null)}</span>
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
function Screener({ initExchange = 'MIL', initSector = 'All', initEpsMom = '', onSelectStock, userId = null, initValMin = 0, initGrowMin = 0, initCombinedMin = 0, showAll = false, maxRows: maxRowsProp, restrictScoreSort = false }: {
  initExchange?: string
  initSector?:   string
  initEpsMom?:   string
  onSelectStock?: (s: Stock) => void
  userId?: string | null
  initValMin?: number
  initGrowMin?: number
  initCombinedMin?: number
  showAll?: boolean
  maxRows?: number
  restrictScoreSort?: boolean
}) {
  const scrRouter = useRouter()
  const scrPathname = usePathname()
  const scrSearchParams = useSearchParams()
  // La selezione del mercato dentro lo Screener (Italia, All Europe, ecc.)
  // era SOLO stato interno React, mai riflessa nell'URL — quando si
  // tornava indietro da un titolo, l'URL salvato non sapeva quale mercato
  // fosse stato scelto, mostrando il default invece della vera selezione
  // (23/7/2026, "All Europe" -> ASML -> indietro mostrava un mix casuale).
  const urlExchange = scrSearchParams.get('scr_ex')
  const [exchange,  setExchange]  = useState(urlExchange || initExchange)
  const [stocks,    setStocks]    = useState<Stock[]>([])
  const [loading,   setLoading]   = useState(false)
  const [selected,  setSelected]  = useState<Stock | null>(null)
  const [portfolioNames, setPortfolioNames] = useState<string[]>(['Portfolio 1', 'Portfolio 2', 'Portfolio 3'])

  // Filters
  const [search,   setSearch]   = useState('')
  const [gSearch,    setGSearch]    = useState('')
  const [gSearchRes, setGSearchRes] = useState<any[]>([])
  const gSearchTimer = useRef<any>(null)
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

  const loadRequestId = useRef(0)

  // Sincronizza la selezione con l'URL. FIX (diagnosi con Kimi, 25/7/2026):
  // router.replace() da solo e' ASINCRONO — se l'utente clicca su un
  // titolo subito dopo aver cambiato mercato, window.location.search
  // potrebbe non essere ancora aggiornato quando goToStock lo legge,
  // salvando l'indirizzo VECCHIO. history.replaceState() aggiorna
  // l'URL del browser SUBITO (sincrono), eliminando la race condition;
  // router.replace() resta solo per notificare Next.js.
  useEffect(() => {
    const params = new URLSearchParams(scrSearchParams.toString())
    if (exchange && exchange !== initExchange) {
      params.set('scr_ex', exchange)
    } else {
      params.delete('scr_ex')
    }
    const qs = params.toString()
    const newUrl = qs ? `${scrPathname}?${qs}` : scrPathname
    if (typeof window !== 'undefined' && window.location.pathname + window.location.search !== newUrl) {
      window.history.replaceState(window.history.state, '', newUrl)
    }
    scrRouter.replace(newUrl, { scroll: false })
  }, [exchange])
  useEffect(() => {
    const myRequestId = ++loadRequestId.current
    const load = () => {
    setStocks([]); setSelected(null); setLoading(true)
    const ALL_GLOBAL_EXCHANGES = 'US,TSX,MIL,XETRA,PA,LSE,SWX,OM,AS,MC,BR,HE,CPSE,OB,GR,VI,IR,LS,TSE,SEHK,ASX,KRX,SGX'
    const exchToLoad = initEpsMom ? 'EZ' : (exchange === 'GLOBAL' ? ALL_GLOBAL_EXCHANGES : exchange)
    apiExchange(exchToLoad, {
      minValue: initValMin > 0 ? initValMin : undefined,
      minGrowth: initGrowMin > 0 ? initGrowMin : undefined,
      minCombined: initCombinedMin > 0 ? initCombinedMin : undefined,
    }).then(data => {
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

      // Scarta risposte obsolete — se nel frattempo l'utente ha cambiato
      // mercato, una richiesta precedente piu' lenta (es. US, grande
      // mercato) potrebbe rispondere DOPO quella piu' recente (es. Italia,
      // piccola e veloce), sovrascrivendo la selezione corretta con dati
      // sbagliati. Solo la richiesta piu' recente puo' aggiornare lo stato.
      if (myRequestId !== loadRequestId.current) return

      setStocks(data)
      setLoading(false)
    })
    }
    load()
    // Refresh automatico ogni 5 minuti - stesso meccanismo delle altre pagine.
    const interval = setInterval(load, 5 * 60 * 1000)
    return () => clearInterval(interval)
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
    if (sector !== 'All') {
      if (sector === 'Other') {
        if (s.sector && s.sector !== 'Other') return false
      } else {
        if (s.sector !== sector) return false
      }
    }
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
        ['VI','LS','IR'].includes(s.exchange)) return false
    return true
  })

  const sectors = ['All', ...Array.from(
    new Set(stocks.map(s => s.sector).filter(Boolean) as string[])
  ).sort()]

  useEffect(() => {
    clearTimeout(gSearchTimer.current)
    if (gSearch.length < 2) { setGSearchRes([]); return }
    gSearchTimer.current = setTimeout(async () => {
      try {
        const r = await fetch(`/api/db/stocks?search=${encodeURIComponent(gSearch)}&limit=10`)
        if (r.ok) {
          const d = await r.json()
          setGSearchRes(d.stocks || [])
        }
      } catch {}
    }, 200)
  }, [gSearch])

  return (
    <div className="space-y-3 p-3">

      {/* Ricerca globale — qualsiasi titolo, qualsiasi mercato */}
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
        <input
          value={gSearch}
          onChange={e => setGSearch(e.target.value)}
          placeholder="Search any ticker or company, any market…"
          className="input-field pl-9 text-sm"
        />
        {gSearchRes.length > 0 && (
          <div className="absolute top-full left-0 right-0 bg-surface border border-border rounded-lg mt-1 z-30 shadow-xl overflow-hidden">
            {gSearchRes.map((r: any) => (
              <div key={`${r.ticker}.${r.exchange}`}
                onClick={() => { setGSearch(''); setGSearchRes([]); goToStock(r.ticker, r.exchange) }}
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

      {/* Exchange tabs */}
      <div className="flex gap-1.5 flex-wrap pb-1">
        {[
          { code: 'GLOBAL',        label: '🌐 Global' },
          { code: 'US,TSX',        label: '🌎 North America' },
          { code: 'EZ',            label: '🌍 All Europe' },
          { code: 'EMU',           label: '🇪🇺 Eurozone' },
          { code: 'TSE,SEHK,ASX,KRX,SGX', label: '🌏 Asia Pacific' },
          { code: 'MIL',           label: '🇮🇹 Italy' },
          { code: 'XETRA',         label: '🇩🇪 Germany' },
          { code: 'PA',            label: '🇫🇷 France' },
          { code: 'AS',            label: '🇳🇱 Netherlands' },
          { code: 'MC',            label: '🇪🇸 Spain' },
          { code: 'BR',            label: '🇧🇪 Belgium' },
          { code: 'LS',            label: '🇵🇹 Portugal' },
          { code: 'VI',            label: '🇦🇹 Austria' },
          { code: 'HE',            label: '🇫🇮 Finland' },
          { code: 'IR',            label: '🇮🇪 Ireland' },
          { code: 'GR',            label: '🇬🇷 Greece' },
          { code: 'LSE',           label: '🇬🇧 UK (LSE)' },
          { code: 'SWX',           label: '🇨🇭 Switzerland' },
          { code: 'OM',            label: '🇸🇪 Sweden' },
          { code: 'OB',            label: '🇳🇴 Norway' },
          { code: 'CPSE',          label: '🇩🇰 Denmark' },
          { code: 'US',            label: '🇺🇸 United States' },
          { code: 'TSX',           label: '🇨🇦 Canada' },
          { code: 'TSE',           label: '🇯🇵 Japan' },
          { code: 'SEHK',          label: '🇭🇰 Hong Kong' },
          { code: 'ASX',           label: '🇦🇺 Australia' },
          { code: 'KRX',           label: '🇰🇷 South Korea' },
          { code: 'SGX',           label: '🇸🇬 Singapore' },
        ].map(({ code, label }) => (
          <button key={code} onClick={() => setExchange(code)}
            className={`px-3 py-1.5 rounded text-xs font-600 border whitespace-nowrap transition-colors ${exchange === code ? 'bg-gold text-bg border-gold' : 'border-border text-muted hover:border-gold hover:text-gold'}`}>
            {label}
          </button>
        ))}
      </div>

      {/* Preset screens */}
      <div className="flex gap-2 flex-wrap">
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
                initValMin > 0 || initGrowMin > 0 || initCombinedMin > 0 ? (
                  <div style={{ fontSize:11, color:'var(--text4)', padding:'8px 0' }}>
                    Curated selection — criteria not shown
                  </div>
                ) : (
                <>
                  <input type="number" placeholder="Value Score min" value={valMin || ''} onChange={e => setValMin(+e.target.value || 0)} className="input-field" min={0} max={100} />
                  <input type="number" placeholder="Growth Score min" value={growMin || ''} onChange={e => setGrowMin(+e.target.value || 0)} className="input-field" min={0} max={100} />
                  <input type="number" placeholder="Best Rank min" value={combinedMin || ''} onChange={e => setCombinedMin(+e.target.value || 0)} className="input-field" min={0} max={100} />
                </>
                )
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
        <span className="text-text font-600">{filtered.length}</span> stocks · showing top 100
      </div>

      {/* Table */}
      <div className="bg-surface border border-border rounded overflow-hidden">
        <StockTable stocks={filtered} fromPage={initExchange === "US" ? "northamerica" : "screener"} onSelect={onSelectStock || (() => {})} loading={loading} maxRows={showAll ? 9999 : (maxRowsProp || 100)} userId={userId} restrictScoreSort={restrictScoreSort} />
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
    const load = () => { setLoading(true); apiExchange('EZ').then(data => { setStocks(data); setLoading(false) }) }
    load()
    const interval = setInterval(load, 5 * 60 * 1000)
    return () => clearInterval(interval)
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
  // Per i rendimenti di prezzo (change1d, mom12m ecc.) pesa per la market
  // cap di PARTENZA stimata, non quella attuale — altrimenti i titoli che
  // sono saliti di piu' pesano di piu' proprio perche' saliti, gonfiando
  // la media a loro favore (bias circolare, piu' forte su periodi lunghi).
  const mcwReturn = (list: any[], field: string) => {
    const v = list.filter((s:any) => s[field] != null && s.mktCap != null && s.mktCap > 0)
    let ws = 0, tw = 0
    for (const s of v) {
      const ret = s[field] || 0
      const ratio = 1 + ret
      const clampedRatio = Math.max(0.1, Math.min(10, ratio))
      const startCap = (s.mktCap || 0) / clampedRatio
      ws += ret * startCap
      tw += startCap
    }
    return tw > 0 ? ws / tw : null
  }

  const sectors = Object.entries(sectorMap)
    .map(([name, list]) => ({
      name,
      count: list.length,
      mktCap: list.reduce((a:number, s:any) => a + (s.mktCap || 0), 0),
      change1d: mcwReturn(list, 'change1d'),
      epsGrowth: mcw(list, 'epsGrowth'),
      revGrowth: mcw(list, 'revGrowth'),
      mom12m: mcwReturn(list, 'mom12m'),
      valueScore: mcw(list, 'valueScore'),
      growthScore: mcw(list, 'growthScore'),
      combinedRank: mcw(list, 'combinedRank'),
      epsGrowthQuintile: (list[0] as any)?.sectorEpsGrowthQuintile ?? null,
      revGrowthQuintile: (list[0] as any)?.sectorRevGrowthQuintile ?? null,
    }))
    .sort((a, b) => b.mktCap - a.mktCap)

  const totalRow = {
    count: stocksEur.length,
    mktCap: stocksEur.reduce((a:number, s:any) => a + (s.mktCap || 0), 0),
    change1d: mcwReturn(stocksEur, 'change1d'),
    epsGrowth: mcw(stocksEur, 'epsGrowth'),
    revGrowth: mcw(stocksEur, 'revGrowth'),
    mom12m: mcwReturn(stocksEur, 'mom12m'),
    valueScore: mcw(stocksEur, 'valueScore'),
    growthScore: mcw(stocksEur, 'growthScore'),
    combinedRank: mcw(stocksEur, 'combinedRank'),
    epsGrowthQuintile: (stocksEur[0] as any)?.continentEpsGrowthQuintile ?? null,
    revGrowthQuintile: (stocksEur[0] as any)?.continentRevGrowthQuintile ?? null,
  }

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
                      <td className="font-mono font-600" style={clr(s.change1d)}>{fpPct(s.change1d != null ? s.change1d*100 : null)}</td>
                      <td className="font-mono font-600" style={s.epsGrowth != null ? {} : { color: quintileDisplay(s.epsGrowthQuintile).color }}>{s.epsGrowth != null ? fpDec(s.epsGrowth) : quintileDisplay(s.epsGrowthQuintile).text}</td>
                      <td className="font-mono font-600" style={s.revGrowth != null ? {} : { color: quintileDisplay(s.revGrowthQuintile).color }}>{s.revGrowth != null ? fpDec(s.revGrowth) : quintileDisplay(s.revGrowthQuintile).text}</td>
                      <td className="font-mono font-700" style={clr(s.mom12m)}>{fpDec(s.mom12m)}</td>
                      <td className="font-mono font-600" style={clrScore(s.valueScore)}>{fv(s.valueScore, 0)}</td>
                      <td className="font-mono font-600" style={clrScore(s.growthScore)}>{fv(s.growthScore, 0)}</td>
                      <td className="font-mono font-600" style={clrScore(s.combinedRank)}>{fv(s.combinedRank, 0)}</td>
                    </tr>
                  ))}
                  <tr style={{ borderTop: '2px solid var(--gold)', background: 'rgba(249,115,22,0.08)' }}>
                    <td className="font-800" style={{ color: 'var(--gold)' }}>TOTAL — All Europe</td>
                    <td className="font-mono font-700">{totalRow.count}</td>
                    <td className="font-mono font-700">{fv(totalRow.mktCap, 0)}</td>
                    <td className="font-mono font-700" style={clr(totalRow.change1d)}>{fpPct(totalRow.change1d != null ? totalRow.change1d*100 : null)}</td>
                    <td className="font-mono font-700" style={totalRow.epsGrowth != null ? {} : { color: quintileDisplay((totalRow as any).epsGrowthQuintile).color }}>{totalRow.epsGrowth != null ? fpDec(totalRow.epsGrowth) : quintileDisplay((totalRow as any).epsGrowthQuintile).text}</td>
                    <td className="font-mono font-700" style={totalRow.revGrowth != null ? {} : { color: quintileDisplay((totalRow as any).revGrowthQuintile).color }}>{totalRow.revGrowth != null ? fpDec(totalRow.revGrowth) : quintileDisplay((totalRow as any).revGrowthQuintile).text}</td>
                    <td className="font-mono font-800" style={clr(totalRow.mom12m)}>{fpDec(totalRow.mom12m)}</td>
                    <td className="font-mono font-700" style={clrScore(totalRow.valueScore)}>{fv(totalRow.valueScore, 0)}</td>
                    <td className="font-mono font-700" style={clrScore(totalRow.growthScore)}>{fv(totalRow.growthScore, 0)}</td>
                    <td className="font-mono font-700" style={clrScore(totalRow.combinedRank)}>{fv(totalRow.combinedRank, 0)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}


function SectorScreenUS({ onSectorClick }: { onSectorClick: (s: string) => void }) {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = () => { setLoading(true); apiExchange('US,TSX').then(data => { setStocks(data); setLoading(false) }) }
    load()
    const interval = setInterval(load, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const stocksUS = stocks.map(s => ({ ...s, mktCap: s.mktCap ?? null }))

  const sectorMap: Record<string, any[]> = {}
  for (const s of stocksUS) {
    const sec = s.sector || 'Other'
    if (!sectorMap[sec]) sectorMap[sec] = []
    sectorMap[sec].push(s)
  }

  const mcw = (list: any[], field: string) => {
    const v = list.filter((s:any) => s[field] != null && s.mktCap != null && s.mktCap > 0)
    const tw = v.reduce((a:number, s:any) => a + (s.mktCap || 0), 0)
    return tw > 0 ? v.reduce((a:number, s:any) => a + (s[field] || 0) * (s.mktCap || 0), 0) / tw : null
  }
  // Per i rendimenti di prezzo (change1d, mom12m ecc.) pesa per la market
  // cap di PARTENZA stimata, non quella attuale — altrimenti i titoli che
  // sono saliti di piu' pesano di piu' proprio perche' saliti, gonfiando
  // la media a loro favore (bias circolare, piu' forte su periodi lunghi).
  const mcwReturn = (list: any[], field: string) => {
    const v = list.filter((s:any) => s[field] != null && s.mktCap != null && s.mktCap > 0)
    let ws = 0, tw = 0
    for (const s of v) {
      const ret = s[field] || 0
      const ratio = 1 + ret
      const clampedRatio = Math.max(0.1, Math.min(10, ratio))
      const startCap = (s.mktCap || 0) / clampedRatio
      ws += ret * startCap
      tw += startCap
    }
    return tw > 0 ? ws / tw : null
  }

  const sectors = Object.entries(sectorMap)
    .map(([name, list]) => ({
      name,
      count: list.length,
      mktCap: list.reduce((a:number, s:any) => a + (s.mktCap || 0), 0),
      change1d: mcwReturn(list, 'change1d'),
      epsGrowth: mcw(list, 'epsGrowth'),
      revGrowth: mcw(list, 'revGrowth'),
      mom12m: mcwReturn(list, 'mom12m'),
      valueScore: mcw(list, 'valueScore'),
      growthScore: mcw(list, 'growthScore'),
      combinedRank: mcw(list, 'combinedRank'),
      epsGrowthQuintile: (list[0] as any)?.sectorEpsGrowthQuintile ?? null,
      revGrowthQuintile: (list[0] as any)?.sectorRevGrowthQuintile ?? null,
    }))
    .sort((a, b) => b.mktCap - a.mktCap)

  const totalRow = {
    count: stocksUS.length,
    mktCap: stocksUS.reduce((a:number, s:any) => a + (s.mktCap || 0), 0),
    change1d: mcwReturn(stocksUS, 'change1d'),
    epsGrowth: mcw(stocksUS, 'epsGrowth'),
    revGrowth: mcw(stocksUS, 'revGrowth'),
    mom12m: mcwReturn(stocksUS, 'mom12m'),
    valueScore: mcw(stocksUS, 'valueScore'),
    growthScore: mcw(stocksUS, 'growthScore'),
    combinedRank: mcw(stocksUS, 'combinedRank'),
    epsGrowthQuintile: (stocksUS[0] as any)?.continentEpsGrowthQuintile ?? null,
    revGrowthQuintile: (stocksUS[0] as any)?.continentRevGrowthQuintile ?? null,
  }

  const fpPct = (v: number | null) => v != null ? (v >= 0 ? '+' : '') + v.toFixed(1) + '%' : '-'
  const fpDec = (v: number | null) => v != null ? (v >= 0 ? '+' : '') + (v * 100).toFixed(1) + '%' : '-'
  const fv = (v: number | null, d = 1) => v != null ? v.toFixed(d) : '-'
  const clr = (v: number | null) => ({ color: v == null ? 'var(--muted)' : v >= 0 ? '#22d48a' : '#e84560' })
  const clrScore = (v: number | null) => ({ color: v == null ? 'var(--muted)' : v >= 70 ? '#22d48a' : v >= 40 ? '#f97316' : '#e84560' })

  return (
    <div className="space-y-4 p-3">
      <div className="section-hdr">Sector Heatmap — North America</div>

      {loading ? (
        <div className="text-center py-12 text-muted">
          <RefreshCw size={24} className="animate-spin mx-auto mb-3 text-gold" />
          <p className="text-sm">Loading…</p>
        </div>
      ) : (
        <>
          <div className="bg-surface border border-border rounded-lg overflow-hidden">
          <div className="bg-surface border border-border rounded-lg p-4">
            <SectorHeatmap stocks={stocksUS} onSectorClick={onSectorClick} />
          </div>

            <div className="px-4 py-2 text-[10px] font-700 uppercase tracking-wide border-b border-border text-gold">
              Sector Aggregates - North America ({stocksUS.length} stocks)
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
                      <td className="font-mono font-600" style={clr(s.change1d)}>{fpPct(s.change1d != null ? s.change1d*100 : null)}</td>
                      <td className="font-mono font-600" style={s.epsGrowth != null ? {} : { color: quintileDisplay(s.epsGrowthQuintile).color }}>{s.epsGrowth != null ? fpDec(s.epsGrowth) : quintileDisplay(s.epsGrowthQuintile).text}</td>
                      <td className="font-mono font-600" style={s.revGrowth != null ? {} : { color: quintileDisplay(s.revGrowthQuintile).color }}>{s.revGrowth != null ? fpDec(s.revGrowth) : quintileDisplay(s.revGrowthQuintile).text}</td>
                      <td className="font-mono font-700" style={clr(s.mom12m)}>{fpDec(s.mom12m)}</td>
                      <td className="font-mono font-600" style={clrScore(s.valueScore)}>{fv(s.valueScore, 0)}</td>
                      <td className="font-mono font-600" style={clrScore(s.growthScore)}>{fv(s.growthScore, 0)}</td>
                      <td className="font-mono font-600" style={clrScore(s.combinedRank)}>{fv(s.combinedRank, 0)}</td>
                    </tr>
                  ))}
                  <tr style={{ borderTop: '2px solid var(--gold)', background: 'rgba(249,115,22,0.08)' }}>
                    <td className="font-800" style={{ color: 'var(--gold)' }}>TOTAL — North America</td>
                    <td className="font-mono font-700">{totalRow.count}</td>
                    <td className="font-mono font-700">{fv(totalRow.mktCap, 0)}</td>
                    <td className="font-mono font-700" style={clr(totalRow.change1d)}>{fpPct(totalRow.change1d != null ? totalRow.change1d*100 : null)}</td>
                    <td className="font-mono font-700" style={totalRow.epsGrowth != null ? {} : { color: quintileDisplay((totalRow as any).epsGrowthQuintile).color }}>{totalRow.epsGrowth != null ? fpDec(totalRow.epsGrowth) : quintileDisplay((totalRow as any).epsGrowthQuintile).text}</td>
                    <td className="font-mono font-700" style={totalRow.revGrowth != null ? {} : { color: quintileDisplay((totalRow as any).revGrowthQuintile).color }}>{totalRow.revGrowth != null ? fpDec(totalRow.revGrowth) : quintileDisplay((totalRow as any).revGrowthQuintile).text}</td>
                    <td className="font-mono font-800" style={clr(totalRow.mom12m)}>{fpDec(totalRow.mom12m)}</td>
                    <td className="font-mono font-700" style={clrScore(totalRow.valueScore)}>{fv(totalRow.valueScore, 0)}</td>
                    <td className="font-mono font-700" style={clrScore(totalRow.growthScore)}>{fv(totalRow.growthScore, 0)}</td>
                    <td className="font-mono font-700" style={clrScore(totalRow.combinedRank)}>{fv(totalRow.combinedRank, 0)}</td>
                  </tr>
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
  const router = useRouter()
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
    apiExchange('ALL', { capRows: 600 }).then(stocks => {
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


  // Top 100 Europe per market cap
  const u200 = allStocks.map((s:any) => ({...s, mktCap: s.mktCap ?? null}))
    .sort((a:any, b:any) => (b.mktCap || 0) - (a.mktCap || 0))
    .slice(0, 100)

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
  const pbV = allStocks.map((s:any) => s.pb).filter((v:any) => v != null && v > 0) as number[]
  const egV   = allStocks.map((s:any) => s.epsGrowth).filter((v:any) => v != null) as number[]
  const rgV   = allStocks.map((s:any) => s.revGrowth).filter((v:any) => v != null) as number[]
  const m6AV  = allStocks.map((s:any) => s.mom6m  != null && s.mom1w != null ? s.mom6m  - s.mom1w  : null).filter((v:any) => v != null) as number[]
  const m12AV = allStocks.map((s:any) => s.mom12m != null && s.mom1m != null ? s.mom12m - s.mom1m  : null).filter((v:any) => v != null) as number[]

  const calcEuroScore = (s: any) => {
    const eyt = ey_d(s.peTrail); const eyf = ey_d(s.peFwd)
    const pet = eyt != null ? (s.peTrail > 200 ? 1 : pRk(eyTV, eyt)) : null
    const pef = eyf != null ? (s.peFwd   > 200 ? 1 : pRk(eyFV, eyf)) : null
    const pb = s.pb != null && s.pb > 0 ? (100 - pRk(pbV, s.pb)!) : null
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
                onClick={() => goToStock(r.ticker, r.exchange)}
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
        <div style={{
          background: 'rgba(249,115,22,0.08)', border: '1px solid rgba(249,115,22,0.3)',
          borderRadius: 6, padding: '10px 16px', marginBottom: 12,
          fontSize: 11, color: 'var(--orange)', fontWeight: 600,
          fontFamily: 'IBM Plex Sans Condensed'
        }}>
          ⚠️ WORK IN PROGRESS — Prices may be incorrect. New data source coming soon.
        </div>

        <div className="section-hdr flex items-center gap-2">
          📈 Index Performance
          <span className="text-[9px] text-muted font-normal"></span>
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
          { label: 'MCW 1D Return (top 600 Europe)', value: loading ? '…' : fp(ewReturn != null ? ewReturn*100 : null) },
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
                {title} - Top 100 Europe by Mkt Cap · <span className="font-normal opacity-70"></span>
              </div>
              <table className="data-table">
                <thead><tr>
                  <th style={{width:90}}>Ticker</th><th>Company</th><th style={{width:65}}>1D %</th>
                </tr></thead>
                <tbody>
                  {list.map((s, i) => (
                    <tr key={i}
                      onClick={() => goToStock(s.ticker, s.exchange)}
                      className="cursor-pointer">
                      <td className="font-700 text-[12px] text-text whitespace-nowrap">{s.flag} {s.ticker}</td>
                      <td className="text-sub text-[11px]" style={{maxWidth:150,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{(s.company||'').length > 22 ? (s.company||'').slice(0,22)+'…' : s.company}</td>
                      <td className="font-mono font-700 text-right whitespace-nowrap" style={clrStyle(s.change1d)}>{fp(s.change1d != null ? s.change1d*100 : null)}</td>
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
            { title: '🚀 Top 10 Price Mom 12M (Top 100 Europe)', list: topMom12, color: 'var(--green)' },
            { title: '💣 Bottom 10 Price Mom 12M (Top 100 Europe)', list: botMom12, color: 'var(--red)' },
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
                      onClick={() => goToStock(s.ticker, s.exchange)}
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
          <div className="text-[10px] text-muted mb-2">Market cap weighted return by sector · Top 100 Europe</div>
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



const INDICES_US = [
  { ticker: '^DJI', name: 'Dow Jones' },
  { ticker: '^IXIC', name: 'Nasdaq' },
  { ticker: '^GSPC', name: 'S&P 500' },
  { ticker: '^GSPTSE', name: 'TSX' },
]


function DashboardUS({ onSectorClick, onSelectStock, onGoScreener }: {
  onSectorClick: (s: string) => void
  onSelectStock?: (s: Stock) => void
  onGoScreener?: (filter: string) => void
}) {
  const router = useRouter()
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
    // North America = US + Canada (TSX), coerente con la definizione usata ovunque nel sito
    apiExchange('US,TSX', { capRows: 600 }).then(stocks => {
      const seen = new Set()
      const deduped = stocks.filter((s: any) => {
        const key = `${s.ticker}.${s.exchange}`
        if (seen.has(key)) return false
        seen.add(key)
        return true
      })
      setAllStocks(deduped)
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


  // Top 100 North America per market cap
  const u200 = allStocks.map((s:any) => ({...s, mktCap: s.mktCap ?? null}))
    .sort((a:any, b:any) => (b.mktCap || 0) - (a.mktCap || 0))
    .slice(0, 100)

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
  const pbV = allStocks.map((s:any) => s.pb).filter((v:any) => v != null && v > 0) as number[]
  const egV   = allStocks.map((s:any) => s.epsGrowth).filter((v:any) => v != null) as number[]
  const rgV   = allStocks.map((s:any) => s.revGrowth).filter((v:any) => v != null) as number[]
  const m6AV  = allStocks.map((s:any) => s.mom6m  != null && s.mom1w != null ? s.mom6m  - s.mom1w  : null).filter((v:any) => v != null) as number[]
  const m12AV = allStocks.map((s:any) => s.mom12m != null && s.mom1m != null ? s.mom12m - s.mom1m  : null).filter((v:any) => v != null) as number[]

  const calcEuroScore = (s: any) => {
    const eyt = ey_d(s.peTrail); const eyf = ey_d(s.peFwd)
    const pet = eyt != null ? (s.peTrail > 200 ? 1 : pRk(eyTV, eyt)) : null
    const pef = eyf != null ? (s.peFwd   > 200 ? 1 : pRk(eyFV, eyf)) : null
    const pb = s.pb != null && s.pb > 0 ? (100 - pRk(pbV, s.pb)!) : null
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
                onClick={() => goToStock(r.ticker, r.exchange)}
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
        <div style={{
          background: 'rgba(249,115,22,0.08)', border: '1px solid rgba(249,115,22,0.3)',
          borderRadius: 6, padding: '10px 16px', marginBottom: 12,
          fontSize: 11, color: 'var(--orange)', fontWeight: 600,
          fontFamily: 'IBM Plex Sans Condensed'
        }}>
          ⚠️ WORK IN PROGRESS — Prices may be incorrect. New data source coming soon.
        </div>

        <div className="section-hdr flex items-center gap-2">
          📈 Index Performance — North America
          <span className="text-[9px] text-muted font-normal"></span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-2">
          {INDICES_US.map((idx) => {
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
          { label: 'Total Stocks',              value: loading ? '…' : '1,972' },
          { label: 'MCW 1D Return (top 100 North America)', value: loading ? '…' : fp(ewReturn != null ? ewReturn*100 : null) },
          { label: 'V+G Best Combined (top 100)', value: loading ? '…' : highVG.toString() },
          { label: 'Gainers/Losers (top 100)',  value: loading ? '…' : `${allGainers.length} / ${allLosers.length}` },
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
                {title} - Top 100 North America by Mkt Cap · <span className="font-normal opacity-70"></span>
              </div>
              <table className="data-table">
                <thead><tr>
                  <th style={{width:90}}>Ticker</th><th>Company</th><th style={{width:65}}>1D %</th>
                </tr></thead>
                <tbody>
                  {list.map((s, i) => (
                    <tr key={i}
                      onClick={() => goToStock(s.ticker, s.exchange)}
                      className="cursor-pointer">
                      <td className="font-700 text-[12px] text-text whitespace-nowrap">{s.flag} {s.ticker}</td>
                      <td className="text-sub text-[11px]" style={{maxWidth:150,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{(s.company||'').length > 22 ? (s.company||'').slice(0,22)+'…' : s.company}</td>
                      <td className="font-mono font-700 text-right whitespace-nowrap" style={clrStyle(s.change1d)}>{fp(s.change1d != null ? s.change1d*100 : null)}</td>
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
            { title: '🚀 Top 10 Price Mom 12M (Top 100 North America)', list: topMom12, color: 'var(--green)' },
            { title: '💣 Bottom 10 Price Mom 12M (Top 100 North America)', list: botMom12, color: 'var(--red)' },
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
                      onClick={() => goToStock(s.ticker, s.exchange)}
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
          <div className="text-[10px] text-muted mb-2">Market cap weighted return by sector · Top 100 North America</div>
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
const INDICES_AP = [
  { ticker: '^N225',  name: 'Nikkei 225' },
  { ticker: '^TOPX',  name: 'TOPIX' },
  { ticker: '^HSI',   name: 'Hang Seng' },
  { ticker: '^AXJO',  name: 'ASX 200' },
]

function DashboardAP({ onSectorClick, onSelectStock }: {
  onSectorClick: (s: string) => void
  onSelectStock?: (s: Stock) => void
}) {
  const router = useRouter()
  const [indices,   setIndices]   = useState<any[]>([])
  const [allStocks, setAllStocks] = useState<Stock[]>([])
  const [loading,   setLoading]   = useState(true)
  const [search,    setSearch]    = useState('')
  const [searchRes, setSearchRes] = useState<any[]>([])
  const searchTimer = useRef<any>(null)

  useEffect(() => {
    const loadIndices = () => apiIndices().then(setIndices)
    loadIndices()
    const timer = setInterval(loadIndices, 60000)
    setLoading(true)
    apiExchange('TSE,SEHK,ASX,KRX,SGX', { capRows: 600 }).then(stocks => { setAllStocks(stocks); setLoading(false) })
    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    clearTimeout(searchTimer.current)
    if (search.length < 2) { setSearchRes([]); return }
    searchTimer.current = setTimeout(async () => {
      if (USE_DB) {
        try {
          const r = await fetch(`/api/db/stocks?search=${encodeURIComponent(search)}&limit=10`)
          if (r.ok) { const d = await r.json(); setSearchRes(d.stocks || []); return }
        } catch {}
      }
    }, 200)
  }, [search])

  const u600 = allStocks.map((s:any) => ({...s, mktCap: s.mktCap ?? null}))
    .sort((a:any, b:any) => (b.mktCap || 0) - (a.mktCap || 0)).slice(0, 100)
  const valid = u600.filter((s:any) => s.change1d != null)
  const allGainers = [...valid].filter((s:any) => (s.change1d || 0) > 0).sort((a, b) => (b.change1d || 0) - (a.change1d || 0))
  const allLosers  = [...valid].filter((s:any) => (s.change1d || 0) < 0).sort((a, b) => (a.change1d || 0) - (b.change1d || 0))
  const gainers  = allGainers.slice(0, 10)
  const losers   = allLosers.slice(0, 10)
  const ewReturn = valid.length > 0 ? valid.reduce((a, s) => a + (s.change1d || 0), 0) / valid.length : null
  const allWithMom12 = u600.filter(s => s.mom12m != null)
  const topMom12 = [...allWithMom12].sort((a, b) => (b.mom12m || 0) - (a.mom12m || 0)).slice(0, 10)
  const botMom12 = [...allWithMom12].sort((a, b) => (a.mom12m || 0) - (b.mom12m || 0)).slice(0, 10)
  const highVG   = u600.filter((s:any) => s.combinedRank != null && s.combinedRank >= 80).length

  return (
    <div className="space-y-6 fade-in">
      <div className="relative">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted pointer-events-none" />
        <input value={search} onChange={e => setSearch(e.target.value)}
          placeholder="Search ticker or company…" className="input-field pl-9 text-sm" />
        {searchRes.length > 0 && (
          <div className="absolute top-full left-0 right-0 bg-surface border border-border rounded-lg mt-1 z-30 shadow-xl overflow-hidden">
            {searchRes.map((r: any) => (
              <div key={`${r.ticker}.${r.exchange}`}
                onClick={() => goToStock(r.ticker, r.exchange)}
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
      <div>
        <div className="section-hdr flex items-center gap-2">📈 Index Performance — Asia Pacific</div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-2">
          {INDICES_AP.map((idx) => {
            const d = indices.find((x: any) => x.ticker === idx.ticker)
            return <IndexCard key={idx.ticker} name={idx.name} close={d?.close ?? null} changeP={d?.changeP ?? null} loading={indices.length === 0} />
          })}
        </div>
      </div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total Stocks', value: loading ? '…' : allStocks.length.toString() },
          { label: 'MCW 1D Return (top 600 Asia Pacific)', value: loading ? '…' : fp(ewReturn != null ? ewReturn*100 : null) },
          { label: 'V+G Best Combined ≥80 (top 600)', value: loading ? '…' : highVG.toString() },
          { label: 'Gainers/Losers (top 600)', value: loading ? '…' : `${allGainers.length} / ${allLosers.length}` },
        ].map(({ label, value }) => (
          <div key={label} className="metric-card">
            <div className="metric-label">{label}</div>
            <div className="metric-value">{value}</div>
          </div>
        ))}
      </div>
      {!loading && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[
            { title: '🟢 Top 10 Gainers Today', list: gainers, color: 'text-[#22d48a]' },
            { title: '🔴 Top 10 Losers Today',  list: losers,  color: 'text-[#e84560]' },
          ].map(({ title, list, color }) => (
            <div key={title} className="bg-surface border border-border rounded-lg overflow-hidden">
              <div className={`px-4 py-2 text-[10px] font-700 uppercase tracking-wide border-b border-border ${color}`}>
                {title} — Top 100 Asia Pacific by Mkt Cap
              </div>
              <table className="data-table">
                <thead><tr>
                  <th style={{width:90}}>Ticker</th><th>Company</th><th style={{width:65}}>1D %</th>
                </tr></thead>
                <tbody>
                  {list.map((s, i) => (
                    <tr key={i} onClick={() => goToStock(s.ticker, s.exchange)} className="cursor-pointer">
                      <td className="font-700 text-[12px] text-text whitespace-nowrap">{s.flag} {s.ticker}</td>
                      <td className="text-sub text-[11px]" style={{maxWidth:150,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{(s.company||'').length > 22 ? (s.company||'').slice(0,22)+'…' : s.company}</td>
                      <td className="font-mono font-700 text-right whitespace-nowrap" style={clrStyle(s.change1d)}>{fp(s.change1d != null ? s.change1d*100 : null)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      )}
      {!loading && topMom12.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {[
            { title: '🚀 Top 10 Price Mom 12M', list: topMom12, color: 'var(--green)' },
            { title: '💣 Bottom 10 Price Mom 12M', list: botMom12, color: 'var(--red)' },
          ].map(({ title, list, color }) => (
            <div key={title} className="bg-surface border border-border rounded-lg overflow-hidden">
              <div className="px-4 py-2 text-[10px] font-700 uppercase tracking-wide border-b border-border" style={{ color }}>
                {title} — Top 100 Asia Pacific by Mkt Cap
              </div>
              <table className="data-table w-full">
                <thead><tr>
                  <th style={{width:90}}>Ticker</th><th>Company</th><th style={{width:72}}>12M %</th>
                </tr></thead>
                <tbody>
                  {list.map((s, i) => (
                    <tr key={i} onClick={() => goToStock(s.ticker, s.exchange)} className="cursor-pointer">
                      <td className="font-700 text-[12px] whitespace-nowrap" style={{ color: 'var(--orange)' }}>{s.flag} {s.ticker}</td>
                      <td className="text-sub text-[11px]" style={{maxWidth:150,overflow:'hidden',textOverflow:'ellipsis',whiteSpace:'nowrap'}}>{(s.company||'').length > 22 ? (s.company||'').slice(0,22)+'…' : s.company}</td>
                      <td className="font-mono font-700 text-right whitespace-nowrap" style={{ color: (s.mom12m||0) >= 0 ? '#22d48a' : '#e84560' }}>
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
      {!loading && u600.length > 0 && (
        <div className="bg-surface border border-border rounded-lg p-4">
          <div className="text-[10px] text-muted mb-2">Market cap weighted return by sector · Top 100 Asia Pacific</div>
          <SectorHeatmap stocks={u600} onSectorClick={onSectorClick} />
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

function SectorScreenAP({ onSectorClick }: { onSectorClick: (s: string) => void }) {
  const [stocks, setStocks] = useState<Stock[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = () => { setLoading(true); apiExchange('TSE,SEHK,ASX,KRX,SGX').then(data => { setStocks(data); setLoading(false) }) }
    load()
    const interval = setInterval(load, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const stocksAP = stocks.map(s => ({ ...s, mktCap: s.mktCap ?? null }))
  const sectorMap: Record<string, any[]> = {}
  for (const s of stocksAP) {
    const sec = s.sector || 'Other'
    if (!sectorMap[sec]) sectorMap[sec] = []
    sectorMap[sec].push(s)
  }
  const mcw = (list: any[], field: string) => {
    const v = list.filter((s:any) => s[field] != null && s.mktCap != null && s.mktCap > 0)
    const tw = v.reduce((a:number, s:any) => a + (s.mktCap || 0), 0)
    return tw > 0 ? v.reduce((a:number, s:any) => a + (s[field] || 0) * (s.mktCap || 0), 0) / tw : null
  }
  // Per i rendimenti di prezzo (change1d, mom12m ecc.) pesa per la market
  // cap di PARTENZA stimata, non quella attuale — altrimenti i titoli che
  // sono saliti di piu' pesano di piu' proprio perche' saliti, gonfiando
  // la media a loro favore (bias circolare, piu' forte su periodi lunghi).
  const mcwReturn = (list: any[], field: string) => {
    const v = list.filter((s:any) => s[field] != null && s.mktCap != null && s.mktCap > 0)
    let ws = 0, tw = 0
    for (const s of v) {
      const ret = s[field] || 0
      const ratio = 1 + ret
      const clampedRatio = Math.max(0.1, Math.min(10, ratio))
      const startCap = (s.mktCap || 0) / clampedRatio
      ws += ret * startCap
      tw += startCap
    }
    return tw > 0 ? ws / tw : null
  }
  const sectors = Object.entries(sectorMap)
    .map(([name, list]) => ({
      name, count: list.length,
      mktCap: list.reduce((a:number, s:any) => a + (s.mktCap || 0), 0),
      change1d: mcwReturn(list, 'change1d'), epsGrowth: mcw(list, 'epsGrowth'),
      revGrowth: mcw(list, 'revGrowth'), mom12m: mcwReturn(list, 'mom12m'),
      valueScore: mcw(list, 'valueScore'), growthScore: mcw(list, 'growthScore'),
      combinedRank: mcw(list, 'combinedRank'),
      epsGrowthQuintile: (list[0] as any)?.sectorEpsGrowthQuintile ?? null,
      revGrowthQuintile: (list[0] as any)?.sectorRevGrowthQuintile ?? null,
    }))
    .sort((a, b) => b.mktCap - a.mktCap)

  const totalRow = {
    count: stocksAP.length,
    mktCap: stocksAP.reduce((a:number, s:any) => a + (s.mktCap || 0), 0),
    change1d: mcwReturn(stocksAP, 'change1d'),
    epsGrowth: mcw(stocksAP, 'epsGrowth'),
    revGrowth: mcw(stocksAP, 'revGrowth'),
    mom12m: mcwReturn(stocksAP, 'mom12m'),
    valueScore: mcw(stocksAP, 'valueScore'),
    growthScore: mcw(stocksAP, 'growthScore'),
    combinedRank: mcw(stocksAP, 'combinedRank'),
    epsGrowthQuintile: (stocksAP[0] as any)?.continentEpsGrowthQuintile ?? null,
    revGrowthQuintile: (stocksAP[0] as any)?.continentRevGrowthQuintile ?? null,
  }

  const fpPct = (v: number | null) => v != null ? (v >= 0 ? '+' : '') + v.toFixed(1) + '%' : '-'
  const fpDec = (v: number | null) => v != null ? (v >= 0 ? '+' : '') + (v * 100).toFixed(1) + '%' : '-'
  const fvs = (v: number | null, d = 1) => v != null ? v.toFixed(d) : '-'
  const clrS = (v: number | null) => ({ color: v == null ? 'var(--muted)' : v >= 0 ? '#22d48a' : '#e84560' })
  const clrScore = (v: number | null) => ({ color: v == null ? 'var(--muted)' : v >= 70 ? '#22d48a' : v >= 40 ? '#f97316' : '#e84560' })

  return (
    <div className="space-y-4 p-3">
      <div className="section-hdr">Sector Heatmap — Asia Pacific</div>
      {loading ? (
        <div className="text-center py-12 text-muted">
          <RefreshCw size={24} className="animate-spin mx-auto mb-3 text-gold" />
          <p className="text-sm">Loading…</p>
        </div>
      ) : (
        <>
          <div className="bg-surface border border-border rounded-lg p-4">
            <SectorHeatmap stocks={stocksAP} onSectorClick={onSectorClick} />
          </div>
          <div className="bg-surface border border-border rounded-lg overflow-hidden">
            <div className="px-4 py-2 text-[10px] font-700 uppercase tracking-wide border-b border-border text-gold">
              Sector Aggregates - Asia Pacific ({stocksAP.length} stocks)
            </div>
            <div className="overflow-x-auto">
              <table className="data-table w-full">
                <thead><tr>
                  <th>Sector</th><th>Stocks</th><th>Mkt Cap $B</th>
                  <th>1D %</th><th>EPS Gr %</th><th>Rev Gr %</th>
                  <th>Mom 12M %</th><th>Value</th><th>Growth</th><th>Best</th>
                </tr></thead>
                <tbody>
                  {sectors.map(s => (
                    <tr key={s.name} onClick={() => onSectorClick(s.name)} className="cursor-pointer">
                      <td><span className="text-[11px] font-600" style={{ color: getSectorColor(s.name) }}>{s.name}</span></td>
                      <td className="font-mono text-muted">{s.count}</td>
                      <td className="font-mono">{fvs(s.mktCap, 0)}</td>
                      <td className="font-mono font-600" style={clrS(s.change1d)}>{fpPct(s.change1d != null ? s.change1d*100 : null)}</td>
                      <td className="font-mono font-600" style={s.epsGrowth != null ? clrS(s.epsGrowth) : { color: quintileDisplay(s.epsGrowthQuintile).color }}>{s.epsGrowth != null ? fpDec(s.epsGrowth) : quintileDisplay(s.epsGrowthQuintile).text}</td>
                      <td className="font-mono font-600" style={s.revGrowth != null ? clrS(s.revGrowth) : { color: quintileDisplay(s.revGrowthQuintile).color }}>{s.revGrowth != null ? fpDec(s.revGrowth) : quintileDisplay(s.revGrowthQuintile).text}</td>
                      <td className="font-mono font-700" style={clrS(s.mom12m)}>{fpDec(s.mom12m)}</td>
                      <td className="font-mono font-600" style={clrScore(s.valueScore)}>{fvs(s.valueScore, 0)}</td>
                      <td className="font-mono font-600" style={clrScore(s.growthScore)}>{fvs(s.growthScore, 0)}</td>
                      <td className="font-mono font-600" style={clrScore(s.combinedRank)}>{fvs(s.combinedRank, 0)}</td>
                    </tr>
                  ))}
                  <tr style={{ borderTop: '2px solid var(--gold)', background: 'rgba(249,115,22,0.08)' }}>
                    <td className="font-800" style={{ color: 'var(--gold)' }}>TOTAL — Asia Pacific</td>
                    <td className="font-mono font-700">{totalRow.count}</td>
                    <td className="font-mono font-700">{fvs(totalRow.mktCap, 0)}</td>
                    <td className="font-mono font-700" style={clrS(totalRow.change1d)}>{fpPct(totalRow.change1d != null ? totalRow.change1d*100 : null)}</td>
                    <td className="font-mono font-700" style={totalRow.epsGrowth != null ? clrS(totalRow.epsGrowth) : { color: quintileDisplay((totalRow as any).epsGrowthQuintile).color }}>{totalRow.epsGrowth != null ? fpDec(totalRow.epsGrowth) : quintileDisplay((totalRow as any).epsGrowthQuintile).text}</td>
                    <td className="font-mono font-700" style={totalRow.revGrowth != null ? clrS(totalRow.revGrowth) : { color: quintileDisplay((totalRow as any).revGrowthQuintile).color }}>{totalRow.revGrowth != null ? fpDec(totalRow.revGrowth) : quintileDisplay((totalRow as any).revGrowthQuintile).text}</td>
                    <td className="font-mono font-800" style={clrS(totalRow.mom12m)}>{fpDec(totalRow.mom12m)}</td>
                    <td className="font-mono font-700" style={clrScore(totalRow.valueScore)}>{fvs(totalRow.valueScore, 0)}</td>
                    <td className="font-mono font-700" style={clrScore(totalRow.growthScore)}>{fvs(totalRow.growthScore, 0)}</td>
                    <td className="font-mono font-700" style={clrScore(totalRow.combinedRank)}>{fvs(totalRow.combinedRank, 0)}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

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
             'ForwardAlpha is a web-based quantitative financial screening and research tool offering proprietary Value Score and Growth Score models (percentile rankings 1–100). The Platform is currently in Beta and free to use.'],
            ['3. Legal Disclaimer – No Financial Advice',
             'ForwardAlpha is for informational and educational purposes only. The Owner is not a registered financial advisor and does not provide investment advisory services. No content constitutes a personalised recommendation or offer to buy/sell financial instruments under MiFID II. Investing involves significant risk of capital loss. Past performance is not indicative of future results.'],
            ['4. Data Accuracy & Limitation of Liability',
             'Prices tend to be updated daily (we are currently experiencing some technical issues affecting update reliability). Fundamental data is updated weekly. The service is provided "as is" without warranty of accuracy, completeness or uninterrupted availability. The Owner shall not be liable for any direct or indirect losses arising from use of the Platform. Data is sourced from third-party providers; the Owner does not guarantee compliance with their individual licence terms for commercial use.'],
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
        Accept &amp; Close
      </button>
    </div>
  )
}

// - ROOT APP -
function AppContent() {
  const searchParams = useSearchParams()
  const pathname = usePathname()
  const appRouter = useRouter()
  // Deriva page direttamente dall'URL — unica sorgente di verità
  const page = (searchParams.get('page') as Page) ?? 'home'

  // Cambia schermata aggiornando solo l'URL
  // FIX 29/7/2026: stesso pattern gia' applicato al sotto-filtro "exchange"
  // dello Screener (diagnosi Kimi, 25/7/2026) — router.replace() di Next.js
  // e' ASINCRONO, quindi se l'utente clicca su un titolo subito dopo aver
  // cambiato tab/mercato (es. passa a Giappone/TSE e clicca SoftBank),
  // window.location.search letto da goToStock() puo' ancora riflettere la
  // pagina PRECEDENTE (es. Nord America), salvando l'indirizzo sbagliato
  // per il tasto "Back". history.replaceState() aggiorna l'URL del browser
  // SUBITO (sincrono), eliminando la race condition per OGNI screener/tab
  // — prima il fix copriva solo il sotto-filtro interno allo Screener, non
  // il cambio di pagina principale che governa TUTTI gli screener.
  const navigateTo = (newPage: Page) => {
    const newUrl = newPage === 'home' ? '/' : `/?page=${newPage}`
    if (typeof window !== 'undefined' && window.location.pathname + window.location.search !== newUrl) {
      window.history.replaceState(window.history.state, '', newUrl)
    }
    appRouter.replace(newUrl, { scroll: false })
  }
  const [user,        setUser]        = useState<SupabaseUser | null>(null)
  const isOwner = user?.email === 'andreameschini19@gmail.com'
  const [showAuth,    setShowAuth]    = useState(false)
  const [authMode,    setAuthMode]    = useState<'login'|'register'>('login')
  useEffect(() => {
    if (searchParams.get('auth') === 'signup') {
      setAuthMode('register')
      setShowAuth(true)
    }
  }, [])
  const [sidebarOpen, setSidebar]     = useState(false)
  const [expandedMenus, setExpandedMenus] = useState<Set<string>>(new Set(['dashboard']))
  const toggleMenu = (id: string) => setExpandedMenus(prev => { const n = new Set(prev); n.has(id) ? n.delete(id) : n.add(id); return n })
  const [scrExchange, setScrExchange] = useState('EZ')
  const [scrSector,   setScrSector]   = useState('All')
  const [scrSectorUS, setScrSectorUS] = useState('All')
  const [scrSectorAP, setScrSectorAP] = useState('All')
  const [scrEpsMom,   setScrEpsMom]   = useState<string>('')
  const [detailStock, setDetailStock] = useState<Stock | null>(null)

  const [showAccessPopup, setShowAccessPopup] = useState(false)

  useEffect(() => {
    supabase.auth.getUser().then(({ data }) => setUser(data.user ?? null))
    const { data: sub } = supabase.auth.onAuthStateChange((event, sess) => {
      setUser(sess?.user ?? null)
      if (event === 'SIGNED_IN' && sess?.user?.email !== 'andreameschini19@gmail.com') {
        setShowAccessPopup(true)
      }
    })
    return () => sub.subscription.unsubscribe()
  }, [])

  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    const p = params.get("page")
    const s = params.get("sector")
    if (p) {
      if (p === "northamerica") { setScrSectorUS(s || "All"); setScrSectorAP("All"); navigateTo("northamerica") }
      else if (p === "nascreen") { setScrSectorUS(s || "All"); setScrSectorAP("All"); navigateTo("nascreen") }
      else if (p === "screener") { setScrExchange("EZ"); setScrSector(s || "All"); setScrSectorUS("All"); setScrSectorAP("All"); navigateTo("screener") }
      else if (p === "asiapacific") { setScrSectorAP(s || "All"); setScrSectorUS("All"); setScrSector("All"); navigateTo("asiapacific") }
      else { setScrSectorUS("All"); setScrSectorAP("All"); setScrSector("All"); navigateTo(p as Page) }
    } else {
      setScrSectorUS("All"); setScrSectorAP("All")
    }
  }, [])
  function goSector(sector: string) {
    setScrExchange('EZ'); setScrSector(sector); setScrSectorUS('All'); setScrEpsMom(''); navigateTo('screener'); setSidebar(false)
  }

  function goScreenerEpsMom(filter: string) {
    setScrExchange('EZ'); setScrSector('All'); setScrEpsMom(filter); navigateTo('screener'); setSidebar(false)
  }

  const accordionMenus = [
    { id: 'bestideas', label: '⭐ Best Ideas', items: [
      { id: 'bestideas_us' as Page, label: '🌎 North America' },
      { id: 'bestideas' as Page, label: '🌍 Europe' },
      { id: 'bestideas_ap' as Page, label: '🌏 Asia Pacific' },
    ]},
    { id: 'bestvalue', label: '📈 Best Value', items: [
      { id: 'bestvalue_us' as Page, label: '🌎 North America' },
      { id: 'bestvalue' as Page, label: '🌍 Europe' },
      { id: 'bestvalue_ap' as Page, label: '🌏 Asia Pacific' },
    ]},
    { id: 'bestgrowth', label: '🌱 Best Growth', items: [
      { id: 'bestgrowth_us' as Page, label: '🌎 North America' },
      { id: 'bestgrowth' as Page, label: '🌍 Europe' },
      { id: 'bestgrowth_ap' as Page, label: '🌏 Asia Pacific' },
    ]},
    { id: 'sectors', label: '🏭 Sectors', items: [
      { id: 'sectors_us' as Page, label: '🌎 North America' },
      { id: 'sectors' as Page, label: '🌍 Europe' },
      { id: 'sectors_ap' as Page, label: '🌏 Asia Pacific' },
    ]},
  ]

  const singleMarkets = [
    { id: 'myscreen' as Page, label: '⭐ My Screen' },
    { id: 'globalscreen' as Page, label: '🌐 Global' },
    { id: 'nascreen' as Page, label: '🌎 North America' },
    { id: 'screener' as Page, label: '🌍 All Europe' },
    { id: 'eurozone' as Page, label: '🇪🇺 Eurozone' },
    { id: 'asiapacific' as Page, label: '🌏 Asia Pacific' },
    { id: 'ASX' as Page, label: '🇦🇺 Australia' },
    { id: 'VI' as Page, label: '🇦🇹 Austria' },
    { id: 'BR' as Page, label: '🇧🇪 Belgium' },
    { id: 'TSX' as Page, label: '🇨🇦 Canada' },
    { id: 'CPSE' as Page, label: '🇩🇰 Denmark' },
    { id: 'HE' as Page, label: '🇫🇮 Finland' },
    { id: 'PA' as Page, label: '🇫🇷 France' },
    { id: 'XETRA' as Page, label: '🇩🇪 Germany' },
    { id: 'GR' as Page, label: '🇬🇷 Greece' },
    { id: 'SEHK' as Page, label: '🇭🇰 Hong Kong' },
    { id: 'IR' as Page, label: '🇮🇪 Ireland' },
    { id: 'MIL' as Page, label: '🇮🇹 Italy' },
    { id: 'TSE' as Page, label: '🇯🇵 Japan' },
    { id: 'AS' as Page, label: '🇳🇱 Netherlands' },
    { id: 'OB' as Page, label: '🇳🇴 Norway' },
    { id: 'LS' as Page, label: '🇵🇹 Portugal' },
    { id: 'SGX' as Page, label: '🇸🇬 Singapore' },
    { id: 'KRX' as Page, label: '🇰🇷 South Korea' },
    { id: 'MC' as Page, label: '🇪🇸 Spain' },
    { id: 'OM' as Page, label: '🇸🇪 Sweden' },
    { id: 'SWX' as Page, label: '🇨🇭 Switzerland' },
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
        {/* About + News + Research */}
        <button onClick={() => { navigateTo('about'); setSidebar(false) }}
          className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded text-sm font-700 transition-colors ${page === 'about' ? 'bg-gold/15 text-gold' : 'text-sub hover:text-text hover:bg-white/5'}`}>
          <Info size={16} /> About
        </button>
        <button onClick={() => { navigateTo('news'); setSidebar(false) }}
          className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded text-sm font-700 transition-colors ${page === 'news' ? 'bg-gold/15 text-gold' : 'text-sub hover:text-text hover:bg-white/5'}`}>
          <span>📰 News</span>
        </button>
        <button onClick={() => { window.location.href='/research' }}
          className='w-full flex items-center gap-2.5 px-3 py-2.5 rounded text-sm font-700 text-orange-400 hover:text-gold transition-colors'>
          <FileText size={16} /> 📄 Research
        </button>
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
                  <button key={idx} onClick={() => { navigateTo(item.id as Page); setSidebar(false); toggleMenu(menu.id) }}
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
          <button key={idx} onClick={() => { setScrSectorUS("All"); setScrSector("All"); setScrSectorAP("All"); navigateTo(item.id as Page); setSidebar(false) }}
            className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded text-sm transition-colors ${page === item.id ? 'bg-gold/15 text-gold' : 'text-text3 hover:text-text hover:bg-surface2'}`}>
            {item.label}
          </button>
        ) : (
          <div key={idx} className='px-3 py-2 text-xs text-muted'>{item.label}</div>
        ))}
        <div style={{ height:1, background:'var(--border)', margin:'4px 4px' }} />
        <button onClick={() => { navigateTo('portfolio'); setSidebar(false) }} className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded text-sm transition-colors ${page === 'portfolio' ? 'bg-gold/10 text-gold' : 'text-text3 hover:text-text hover:bg-surface2'}`}>💼 Portfolio</button>
        <button onClick={() => { navigateTo('legal'); setSidebar(false) }} className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded text-sm transition-colors ${page === 'legal' ? 'bg-gold/10 text-gold' : 'text-text3 hover:text-text hover:bg-surface2'}`}>📋 Legal</button>
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
          {page === 'home' && (
            <div style={{ maxWidth: 980, margin: '0 auto' }}>
              <div style={{ textAlign: 'center', padding: '48px 12px 40px' }}>
                <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 10,
                  letterSpacing: '0.16em', textTransform: 'uppercase', color: 'var(--orange)', marginBottom: 18 }}>
                  Institutional-grade equity research, built for one
                </div>
                <h1 style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 'clamp(30px, 5.5vw, 52px)',
                  lineHeight: 1.08, letterSpacing: '-0.02em', margin: '0 0 20px', color: 'var(--text)' }}>
                  Value and growth,<br />
                  <span style={{ color: 'var(--orange)' }}>ranked across three continents.</span>
                </h1>
                <p style={{ fontSize: 15, color: 'var(--text3)', maxWidth: 540, margin: '0 auto 30px', lineHeight: 1.6 }}>
                  ForwardAlpha percentile-ranks approximately 8,000 stocks across North America, Europe
                  and Asia Pacific on valuation and growth — the same methodology used by institutional
                  portfolio managers, rebuilt as a transparent, always-on screener.
                </p>
                <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
                  <button onClick={() => { setAuthMode('register'); setShowAuth(true) }}
                    style={{ background: 'var(--orange)', color: '#07101f', fontFamily: 'IBM Plex Sans Condensed',
                    fontWeight: 700, fontSize: 13, padding: '13px 26px', borderRadius: 4, border: 'none', cursor: 'pointer' }}>
                    Create free account →
                  </button>
                  <button onClick={() => navigateTo('about')}
                    style={{ border: '1px solid var(--border2)', color: 'var(--text2)', background: 'transparent',
                    fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 13, padding: '13px 26px',
                    borderRadius: 4, cursor: 'pointer' }}>
                    How the scoring works
                  </button>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text4)', marginTop: 14 }}>
                  Free during Beta · No card required
                </div>
              </div>

              <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 10,
                letterSpacing: '0.14em', textTransform: 'uppercase', color: 'var(--text4)',
                textAlign: 'center', marginBottom: 18 }}>
                Three markets, one framework
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, marginBottom: 40 }}>
                {[
                  { code: 'NA', name: 'North America', detail: 'US + Canada', count: '~3,400 stocks', go: 'nascreen' as Page },
                  { code: 'EU', name: 'Europe', detail: '16 exchanges', count: '~2,100 stocks', go: 'screener' as Page },
                  { code: 'AP', name: 'Asia Pacific', detail: 'Japan · Hong Kong · Australia · Korea · Singapore', count: '~2,350 stocks', go: 'asiapacific' as Page },
                ].map(r => (
                  <button key={r.code} onClick={() => navigateTo(r.go)} style={{ textAlign: 'left', background: 'var(--surface)',
                    border: '1px solid var(--border)', borderRadius: 6, padding: '20px 18px', cursor: 'pointer' }}>
                    <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 11,
                      color: 'var(--orange)', letterSpacing: '0.08em', marginBottom: 8 }}>{r.code}</div>
                    <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 16,
                      color: 'var(--text)', marginBottom: 5 }}>{r.name}</div>
                    <div style={{ fontSize: 11.5, color: 'var(--text3)', lineHeight: 1.5, marginBottom: 10 }}>{r.detail}</div>
                    <div style={{ fontSize: 11, color: 'var(--text4)', fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700 }}>{r.count}</div>
                  </button>
                ))}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 14, marginBottom: 24 }}>
                {[
                  { t: 'Value Score', d: 'Three value parameters, ranked against comparable peers.' },
                  { t: 'Growth Score', d: 'Four growth parameters, combined.' },
                  { t: 'Best Score', d: 'A combination of Value and Growth — the shortlist of what deserves a closer look.' },
                ].map(x => (
                  <div key={x.t} style={{ borderLeft: '2px solid var(--orange)', paddingLeft: 14 }}>
                    <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 13, color: 'var(--text)', marginBottom: 5 }}>{x.t}</div>
                    <div style={{ fontSize: 12, color: 'var(--text3)', lineHeight: 1.55 }}>{x.d}</div>
                  </div>
                ))}
              </div>

              <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6,
                borderLeft: '2px solid var(--orange)', padding: '20px 24px', marginBottom: 24 }}>
                <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 14,
                  color: 'var(--text)', marginBottom: 8 }}>
                  Reverse Earnings Model — US stocks only, for now
                </div>
                <div style={{ fontSize: 12.5, color: 'var(--text3)', lineHeight: 1.6 }}>
                  Starting from the current price and the next-twelve-month EPS estimate, and holding
                  a 2.5% terminal growth rate constant, the model solves backward for the earnings
                  growth rate the market would need over the next ten years to justify today's price.
                  You can then compare that implied rate against faster or slower growth assumptions
                  and see how the resulting price would change. It's a way to read what growth the
                  market is currently pricing in — not a price target, a projection, or a
                  recommendation to buy or sell.
                </div>
              </div>

              <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 6,
                padding: '22px 24px', marginBottom: 24, display: 'flex', alignItems: 'center',
                justifyContent: 'space-between', flexWrap: 'wrap', gap: 16 }}>
                <div>
                  <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 15,
                    color: 'var(--text)', marginBottom: 6 }}>
                    📰 News — last 24 hours only
                  </div>
                  <div style={{ fontSize: 12.5, color: 'var(--text3)', lineHeight: 1.55, maxWidth: 520 }}>
                    Scan run on demand — all ~8,000 stocks across North America,
                    Europe and Asia Pacific, not just the largest names — and keep only what was
                    published in the last 24 hours. No stale headlines, no gaps in coverage.
                  </div>
                </div>
                <button onClick={() => navigateTo('news')}
                  style={{ background: 'var(--orange)', color: '#07101f', fontFamily: 'IBM Plex Sans Condensed',
                  fontWeight: 700, fontSize: 12.5, padding: '11px 22px', borderRadius: 4, border: 'none',
                  cursor: 'pointer', whiteSpace: 'nowrap' }}>
                  View latest news →
                </button>
              </div>
            </div>
          )}
          {page === 'dashboard' && (
            <div style={{ padding: '48px 24px', textAlign: 'center', maxWidth: 480, margin: '0 auto' }}>
              <div style={{ fontSize: 40, marginBottom: 16 }}>🛠️</div>
              <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Dashboard temporarily unavailable</div>
              <p style={{ color: 'var(--text3)', fontSize: 14 }}>We're upgrading our data pipeline. This section will be back online shortly. In the meantime, the Screener and Research sections remain fully available.</p>
            </div>
          )}
          {(page === 'screener' || page === 'MIL' || page === 'PA' || page === 'XETRA' || page === 'LSE' || page === 'OM' || page === 'OB' || page === 'SWX' || page === 'MC' || page === 'AS' || page === 'HE' || page === 'BR' || page === 'GR' || page === 'CPSE' || page === 'VI' || page === 'LS' || page === 'IR') && <Screener key={`${page}-${scrSector}`} initExchange={page === 'screener' ? scrExchange : page} initSector={page === 'screener' ? scrSector : 'All'} initEpsMom={scrEpsMom} onSelectStock={setDetailStock} userId={user?.id || null} />}
          {page === 'bestvalue'  && (user
            ? <Screener key="bestvalue"  initExchange="EZ" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} initValMin={80} initGrowMin={30} showAll={true} restrictScoreSort={!isOwner} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Best Value" />
          )}
          {page === 'bestideas'  && (user
            ? <Screener key="bestideas"  initExchange="EZ" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} initValMin={0} initGrowMin={0} initCombinedMin={80} showAll={true} restrictScoreSort={!isOwner} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Best Ideas" />
          )}
          {page === 'bestgrowth' && (user
            ? <Screener key="bestgrowth" initExchange="EZ" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} initValMin={0} initGrowMin={80} showAll={true} restrictScoreSort={!isOwner} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Best Growth" />
          )}
          {page === 'bestvalue_us' && (user
            ? <Screener key="bestvalue_us" initExchange="US,TSX" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} initValMin={80} initGrowMin={30} initCombinedMin={0} restrictScoreSort={!isOwner} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Best Value US" />
          )}
          {page === 'bestideas_us' && (user
            ? <Screener key="bestideas_us" initExchange="US,TSX" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} initValMin={0} initGrowMin={0} initCombinedMin={80} restrictScoreSort={!isOwner} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Best Ideas US" />
          )}
          {page === 'bestgrowth_us' && (user
            ? <Screener key="bestgrowth_us" initExchange="US,TSX" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} initValMin={0} initGrowMin={80} initCombinedMin={0} restrictScoreSort={!isOwner} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Best Growth US" />
          )}
          {page === 'northamerica' && (
            <div style={{ padding: '48px 24px', textAlign: 'center', maxWidth: 480, margin: '0 auto' }}>
              <div style={{ fontSize: 40, marginBottom: 16 }}>🛠️</div>
              <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Dashboard temporarily unavailable</div>
              <p style={{ color: 'var(--text3)', fontSize: 14 }}>We're upgrading our data pipeline. This section will be back online shortly. In the meantime, the Screener and Research sections remain fully available.</p>
            </div>
          )}
          {page === 'globalscreen' && <Screener key="globalscreen" initExchange="US,TSX,MIL,XETRA,PA,LSE,SWX,OM,AS,MC,BR,HE,CPSE,OB,GR,VI,IR,LS,TSE,SEHK,ASX,KRX,SGX" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} maxRows={1000} />}
          {page === 'nascreen' && <Screener key={`nascreen-${scrSectorUS}`} initExchange="US,TSX" initSector={scrSectorUS} initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} maxRows={500} />}
          {page === 'apdashboard' && (
            <div style={{ padding: '48px 24px', textAlign: 'center', maxWidth: 480, margin: '0 auto' }}>
              <div style={{ fontSize: 40, marginBottom: 16 }}>🛠️</div>
              <div style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>Dashboard temporarily unavailable</div>
              <p style={{ color: 'var(--text3)', fontSize: 14 }}>We're upgrading our data pipeline. This section will be back online shortly. In the meantime, the Screener and Research sections remain fully available.</p>
            </div>
          )}
          {page === 'asiapacific' && <Screener key={`asiapacific-${scrSectorAP}`} initExchange="TSE,SEHK,ASX,KRX,SGX" initSector={scrSectorAP} initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} maxRows={350} />}
          {page === 'TSE' && <Screener key="TSE" initExchange="TSE" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} maxRows={300} />}
          {page === 'SEHK' && <Screener key="SEHK" initExchange="SEHK" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} maxRows={250} />}
          {page === 'TSX' && <Screener key="TSX" initExchange="TSX" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} maxRows={200} />}
          {page === 'ASX' && <Screener key="ASX" initExchange="ASX" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} maxRows={150} />}
          {page === 'KRX' && <Screener key="KRX" initExchange="KRX" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} maxRows={400} />}
          {page === 'SGX' && <Screener key="SGX" initExchange="SGX" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} maxRows={100} />}
          {page === 'bestvalue_ap' && (user
            ? <Screener key="bestvalue_ap" initExchange="TSE,SEHK,ASX,KRX,SGX" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} initValMin={80} initGrowMin={30} showAll={true} restrictScoreSort={!isOwner} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Best Value Asia Pacific" />
          )}
          {page === 'bestideas_ap' && (user
            ? <Screener key="bestideas_ap" initExchange="TSE,SEHK,ASX,KRX,SGX" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} initValMin={0} initGrowMin={0} initCombinedMin={80} showAll={true} restrictScoreSort={!isOwner} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Best Ideas Asia Pacific" />
          )}
          {page === 'bestgrowth_ap' && (user
            ? <Screener key="bestgrowth_ap" initExchange="TSE,SEHK,ASX,KRX,SGX" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} initValMin={0} initGrowMin={80} showAll={true} restrictScoreSort={!isOwner} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Best Growth Asia Pacific" />
          )}
          {page === 'usscreen' && <Screener key={'usscreen-'+scrSectorUS} initExchange='US,TSX' initSector={scrSectorUS} initEpsMom='' onSelectStock={setDetailStock} userId={user?.id || null} />}
          {page === 'eurozone'  && <Screener key="eurozone"  initExchange="EMU" initSector="All" initEpsMom="" onSelectStock={setDetailStock} userId={user?.id || null} />}
          {page === 'sectors'   && (user
            ? <SectorScreen onSectorClick={goSector} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Sector Heatmap — All Europe" />
          )}
          {page === 'sectors_us' && (user
            ? <SectorScreenUS onSectorClick={(s) => { setScrSectorUS(s); navigateTo('usscreen') }} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Sector Heatmap — North America" />
          )}
          {page === 'sectors_ap' && (user
            ? <SectorScreenAP onSectorClick={(s) => { setScrSectorAP(s); navigateTo('asiapacific') }} />
            : <LoginGate onLogin={() => setShowAuth(true)} title="Sector Heatmap — Asia Pacific" />
          )}
          {page === 'about' && (
            <div className="flex-1 overflow-y-auto">
              <iframe src="/about" style={{ width:'100%', height:'100%', border:'none', minHeight:'calc(100vh - 60px)' }} />
            </div>
          )}
          {page === 'news' && (
            user
              ? <NewsPage />
              : <LoginGate onLogin={() => setShowAuth(true)} title="News" />
          )}
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
          <button onClick={() => navigateTo('legal')} className="hover:text-gold underline">Terms &amp; Privacy</button>
          <a href="mailto:andrea@forwardalpha.pro" className="hover:text-gold">Contact</a>
          <span>© 2026 Andrea Meschini</span>
        </footer>
      </main>

      {showAuth && (
        <AuthModal onClose={() => setShowAuth(false)} onSuccess={() => setShowAuth(false)} initialMode={authMode} />
      )}

      {showAccessPopup && (
        <div onClick={() => setShowAccessPopup(false)} style={{
          position:'fixed', top:0, left:0, right:0, bottom:0, background:'rgba(0,0,0,0.6)',
          display:'flex', alignItems:'center', justifyContent:'center', zIndex:2000, padding:16 }}>
          <div onClick={(e) => e.stopPropagation()} style={{
            background:'var(--bg)', border:'1px solid var(--border)', borderRadius:8,
            padding:24, maxWidth:440, width:'100%' }}>
            <div style={{ fontSize:14, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
              color:'var(--orange)', marginBottom:12 }}>ForwardAlpha — Free Access</div>
            <div style={{ fontSize:13, color:'var(--text2)', lineHeight:1.6, marginBottom:16 }}>
              You're viewing our top 500 companies by global market capitalization — a curated
              selection covering the world's largest and most liquid names across all markets we track.
              <br /><br />
              For full access to our complete global universe of 8,000+ stocks, institutional-grade
              coverage, and professional features, contact us at{' '}
              <a href="mailto:andrea@forwardalpha.pro" style={{ color:'var(--orange)' }}>andrea@forwardalpha.pro</a>.
            </div>
            <button onClick={() => setShowAccessPopup(false)} style={{
              background:'var(--orange)', border:'none', borderRadius:4, color:'#000',
              fontSize:12, fontWeight:700, padding:'8px 16px', cursor:'pointer' }}>Got it</button>
          </div>
        </div>
      )}

      <CookieBanner />
    </div>
  )
}

export default function App() {
  return (
    <Suspense fallback={null}>
      <AppContent />
    </Suspense>
  )
}
