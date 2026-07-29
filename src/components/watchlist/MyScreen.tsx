'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { supabase } from '@/lib/supabase'
import { Star, Trash2, RefreshCw } from 'lucide-react'

const fn = (v: number | null | undefined) => {
  if (v == null || isNaN(v as number)) return '-'
  return String(Math.round(v as number))
}
const fv = (v: number | null | undefined, d = 2) => {
  if (v == null || isNaN(v as number)) return '-'
  return (v as number).toFixed(d)
}
const fpd = (v: number | null | undefined) => {
  if (v == null || isNaN(v as number)) return '-'
  const n = (v as number) * 100
  return (n >= 0 ? '+' : '') + n.toFixed(1) + '%'
}
const clrStyle = (v: number | null | undefined) => ({
  color: v == null ? 'var(--text3)' : (v as number) >= 0 ? 'var(--green)' : 'var(--red)'
})
const rankClr = (v: number | null | undefined) => {
  if (v == null) return 'var(--text3)'
  return (v as number) >= 70 ? '#22c55e' : (v as number) <= 30 ? '#e84560' : '#f59e0b'
}
const QLBL: Record<string, { t: string; c: string }> = {
  'Top Quintile':    { t: '1° Quintile',    c: '#22c55e' },
  '2nd Quintile':    { t: '2° Quintile',     c: '#84cc16' },
  'Middle':          { t: '3° Quintile',        c: '#f59e0b' },
  '4th Quintile':    { t: '4° Quintile',     c: '#f59e0b' },
  'Bottom Quintile': { t: '5° Quintile', c: '#e84560' },
}
const qText = (q: string | null | undefined) => q && QLBL[q] ? QLBL[q].t : '-'
const qClr = (q: string | null | undefined) => q && QLBL[q] ? QLBL[q].c : 'var(--text3)'
const quintFromAvg = (r: number | null): string | null => {
  if (r == null) return null
  if (r >= 80) return 'Top Quintile'
  if (r >= 60) return '2nd Quintile'
  if (r >= 40) return 'Middle'
  if (r >= 20) return '4th Quintile'
  return 'Bottom Quintile'
}

const SECTOR_COLORS: Record<string, string> = {
  'Technology': '#3b82f6', 'Financials': '#f59e0b', 'Health Care': '#10b981',
  'Consumer Discretionary': '#f97316', 'Industrials': '#8b5cf6',
  'Communication Services': '#06b6d4', 'Consumer Staples': '#84cc16',
  'Energy': '#ef4444', 'Materials': '#a78bfa', 'Real Estate': '#fb7185', 'Utilities': '#34d399',
}
const getSectorColor = (s: string | null | undefined) => SECTOR_COLORS[s || ''] || '#6b7280'

const COUNTRY_COLORS = [
  '#3b82f6','#f59e0b','#10b981','#f97316','#8b5cf6','#06b6d4',
  '#84cc16','#ef4444','#a78bfa','#fb7185','#34d399','#eab308',
  '#6366f1','#ec4899','#14b8a6','#f43f5e',
]
const countryColorMap = (countries: string[]) => {
  const map: Record<string, string> = {}
  countries.forEach((c, i) => { map[c] = COUNTRY_COLORS[i % COUNTRY_COLORS.length] })
  return map
}

// Grafico a torta SVG puro — nessuna libreria esterna necessaria.
// Pesi equal-weight: ogni titolo del wallet conta 1/N nella sua categoria.
function PieChart({ data, size = 120 }: { data: { label: string; value: number; color: string }[]; size?: number }) {
  const total = data.reduce((sum, d) => sum + d.value, 0)
  if (total === 0) return null
  const r = size / 2
  const cx = r, cy = r
  let angleStart = -90 // parte da ore 12

  const slices = data.map((d) => {
    const fraction = d.value / total
    const angleSweep = fraction * 360
    const angleEnd = angleStart + angleSweep
    const largeArc = angleSweep > 180 ? 1 : 0
    const startRad = (angleStart * Math.PI) / 180
    const endRad = (angleEnd * Math.PI) / 180
    const x1 = cx + r * Math.cos(startRad)
    const y1 = cy + r * Math.sin(startRad)
    const x2 = cx + r * Math.cos(endRad)
    const y2 = cy + r * Math.sin(endRad)
    const path = fraction >= 0.9999
      ? `M ${cx} ${cy - r} A ${r} ${r} 0 1 1 ${cx - 0.01} ${cy - r} Z` // cerchio intero (1 sola categoria)
      : `M ${cx} ${cy} L ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} Z`
    angleStart = angleEnd
    return { path, color: d.color, label: d.label, pct: fraction * 100 }
  })

  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      {slices.map((s, i) => (
        <path key={i} d={s.path} fill={s.color} stroke="var(--bg)" strokeWidth={1}>
          <title>{s.label}: {s.pct.toFixed(1)}%</title>
        </path>
      ))}
    </svg>
  )
}

// Costruisce i dati aggregati per un grafico a torta a partire dai titoli
// del wallet attivo, raggruppando per il campo indicato (sector o country).
// Pesi equal-weight: ogni titolo vale 1, indipendentemente dal market cap.
function buildPieData(stocks: WatchStock[], field: 'sector' | 'country', colorFn: (key: string) => string) {
  const counts: Record<string, number> = {}
  stocks.forEach(s => {
    const key = (s[field] as string) || 'Unknown'
    counts[key] = (counts[key] || 0) + 1
  })
  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .map(([label, value]) => ({ label, value, color: colorFn(label) }))
}

// Legenda testuale accanto al grafico — mostra categoria, peso %, conteggio
function PieLegend({ data, total }: { data: { label: string; value: number; color: string }[]; total: number }) {
  return (
    <div className="flex flex-col gap-1 text-[10px]">
      {data.map((d, i) => (
        <div key={i} className="flex items-center gap-1.5">
          <span style={{ width: 8, height: 8, borderRadius: 2, background: d.color, flexShrink: 0 }} />
          <span className="text-sub truncate max-w-[90px]">{d.label}</span>
          <span className="text-muted ml-auto font-mono">{((d.value / total) * 100).toFixed(0)}%</span>
        </div>
      ))}
    </div>
  )
}

const WALLET_NAMES = ['My Wallet 1', 'My Wallet 2', 'My Wallet 3']

interface WatchStock {
  id: string
  ticker: string
  exchange: string
  company?: string | null
  added_at: string
  flag?: string
  sector?: string | null
  country?: string | null
  price?: number | null
  change1d?: number | null
  mktCap?: number | null
  mom1w?: number | null
  mom1m?: number | null
  mom6m?: number | null
  mom12m?: number | null
  valueScore?: number | null
  growthScore?: number | null
  combinedRank?: number | null
  rankPeLtm?: number | null
  rankPeNtm?: number | null
  rankPb?: number | null
  rankEpsGr?: number | null
  rankRevGr?: number | null
  wallet?: number | null
}

interface Props {
  userId: string
  onSelectStock?: (s: any) => void
}

export default function MyScreen({ userId, onSelectStock }: Props) {
  const router = useRouter()
  const [allStocks, setAllStocks] = useState<WatchStock[]>([])
  const [loading, setLoading] = useState(true)
  // Ripristina il wallet attivo da sessionStorage — senza questo, tornare
  // indietro da una pagina titolo faceva ripartire sempre dal Wallet 1
  // invece di restare sul wallet da cui si era partiti.
  const [activeWallet, setActiveWalletState] = useState(() => {
    if (typeof window === 'undefined') return 0
    const saved = sessionStorage.getItem('myScreenActiveWallet')
    return saved != null ? parseInt(saved, 10) : 0
  })
  const setActiveWallet = (idx: number) => {
    setActiveWalletState(idx)
    if (typeof window !== 'undefined') sessionStorage.setItem('myScreenActiveWallet', String(idx))
  }
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768)
    check()
    window.addEventListener('resize', check)
    return () => window.removeEventListener('resize', check)
  }, [])

  const load = async () => {
    setLoading(true)
    const { data } = await supabase
      .from('watchlist')
      .select('*')
      .eq('user_id', userId)
      .order('added_at', { ascending: false })

    if (!data || data.length === 0) { setAllStocks([]); setLoading(false); return }

    // FIX 29/7/2026: prima caricava ogni titolo della watchlist con una
    // chiamata HTTP SEPARATA (in parallelo tra loro, ma ognuna rifaceva
    // la verifica utente sul token — chiamata di rete a Supabase Auth
    // ripetuta una volta per titolo). Con molti titoli in watchlist
    // diventava lento. Ora una sola chiamata batch (endpoint tickers=),
    // una sola verifica utente, stessi identici dati per ogni titolo.
    let authHeader: Record<string, string> = {}
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (session?.access_token) authHeader = { Authorization: `Bearer ${session.access_token}` }
    } catch {}
    const liveMap: Record<string, any> = {}
    try {
      const tickersParam = data.map((w: any) => `${w.ticker}.${w.exchange}`).join(',')
      const r = await fetch(`/api/db/stocks?tickers=${encodeURIComponent(tickersParam)}`, { headers: authHeader })
      if (r.ok) {
        const d = await r.json()
        for (const s of (d.stocks || [])) {
          if (s) liveMap[`${s.ticker}.${s.exchange}`] = s
        }
      }
    } catch {}
    // Titoli restanti (non restituiti dal batch, es. fuori dai 500
    // pubblici per un utente non istituzionale) — segnati come "restricted"
    // cosi' la UI puo' mostrarli comunque come limitati anziche' vuoti.
    for (const w of data) {
      const key = `${w.ticker}.${w.exchange}`
      if (!liveMap[key]) liveMap[key] = { ticker: w.ticker, exchange: w.exchange, company: w.ticker, restricted: true }
    }

    const merged = data.map((w: any) => {
      const live = liveMap[`${w.ticker}.${w.exchange}`] || {}
      return { ...w, ...live, id: w.id, added_at: w.added_at, wallet: w.wallet ?? 0 }
    })

    setAllStocks(merged)
    setLoading(false)
  }

  useEffect(() => { load() }, [userId])

  const remove = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    await supabase.from('watchlist').delete().eq('id', id)
    setAllStocks(prev => prev.filter(s => s.id !== id))
  }

  const moveToWallet = async (e: React.MouseEvent, id: string, wallet: number) => {
    e.stopPropagation()
    await supabase.from('watchlist').update({ wallet }).eq('id', id)
    setAllStocks(prev => prev.map(s => s.id === id ? { ...s, wallet } : s))
  }

  const stocks = allStocks.filter(s => (s.wallet ?? 0) === activeWallet)

  // Notizie delle ultime 24 ore per i titoli del wallet attivo — riusa
  // la stessa cache news_cache gia' popolata per la pagina News, filtrata
  // solo sui ticker presenti in questo specifico wallet.
  const [walletNews, setWalletNews] = useState<any[]>([])
  const [newsLoading, setNewsLoading] = useState(false)
  useEffect(() => {
    if (stocks.length === 0) { setWalletNews([]); return }
    const tickersParam = stocks.map(s => `${s.ticker}.${s.exchange}`).join(',')
    setNewsLoading(true)
    fetch(`/api/news-cache?tickers=${encodeURIComponent(tickersParam)}&limit=50`, { cache: 'no-store' })
      .then(r => r.ok ? r.json() : { items: [] })
      .then(d => { setWalletNews(d.items || []); setNewsLoading(false) })
      .catch(() => setNewsLoading(false))
  }, [activeWallet, stocks.length])

  // Ordinamento per colonna — clic sull'intestazione per Settore, Market
  // Cap, 1D/1W/1M/6M/12M, Value/Growth/Best
  const [sortField, setSortField] = useState<keyof WatchStock | null>(null)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const toggleSort = (field: keyof WatchStock) => {
    if (sortField === field) setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    else { setSortField(field); setSortDir('desc') }
  }
  const sortedStocks = sortField ? [...stocks].sort((a, b) => {
    const av = a[sortField], bv = b[sortField]
    if (av == null && bv == null) return 0
    if (av == null) return 1
    if (bv == null) return -1
    if (typeof av === 'string' || typeof bv === 'string') {
      return sortDir === 'asc'
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av))
    }
    return sortDir === 'asc' ? (av as number) - (bv as number) : (bv as number) - (av as number)
  }) : stocks
  const sortArrow = (field: keyof WatchStock) => sortField === field ? (sortDir === 'desc' ? ' ▼' : ' ▲') : ''

  const avg = (field: keyof WatchStock) => {
    const vals = stocks.map(s => s[field] as number | null).filter(v => v != null && !isNaN(v as number)) as number[]
    if (vals.length === 0) return null
    return vals.reduce((a, b) => a + b, 0) / vals.length
  }

  if (loading) return (
    <div className="p-8 text-center text-muted text-sm space-y-2">
      <RefreshCw size={20} className="animate-spin mx-auto text-gold" />
      <p>Loading My Screen...</p>
    </div>
  )

  return (
    <div className="space-y-4 fade-in">
      {/* Header */}
      <div className="section-hdr flex items-center gap-2">
        <Star size={16} className="text-orange-400" />
        My Screen
        <button onClick={load} className="ml-auto text-muted hover:text-text transition-colors">
          <RefreshCw size={13} />
        </button>
      </div>

      {/* Wallet tabs */}
      <div className="flex gap-2 flex-wrap">
        {WALLET_NAMES.map((name, idx) => {
          const count = allStocks.filter(s => (s.wallet ?? 0) === idx).length
          return (
            <button key={idx} onClick={() => setActiveWallet(idx)}
              className={`px-4 py-2 rounded text-xs font-600 border transition-colors`}
              style={{
                background: activeWallet === idx ? 'var(--orange)' : 'var(--surface)',
                color: activeWallet === idx ? '#000' : 'var(--text3)',
                borderColor: activeWallet === idx ? 'var(--orange)' : 'var(--border)'
              }}>
              {name}
              <span className="ml-2 opacity-70">{count}/100</span>
            </button>
          )
        })}
      </div>

      {stocks.length === 0 ? (
        <div className="p-8 text-center text-muted text-sm">
          <Star size={32} className="mx-auto mb-3 opacity-30" />
          <p>{WALLET_NAMES[activeWallet]} is empty.</p>
          <p className="text-xs mt-1 opacity-70">Add stocks using the <strong>+</strong> button, then move them here.</p>
        </div>
      ) : (
      <>
      {/* Sector & Country allocation — equal weight, un titolo = un voto */}
      <div className={isMobile ? "flex flex-col gap-3" : "flex gap-4"}>
        {(() => {
          const sectorData = buildPieData(stocks, 'sector', getSectorColor)
          const cMap = countryColorMap(Array.from(new Set(stocks.map(s => s.country || 'Unknown'))))
          const countryData = buildPieData(stocks, 'country', (k) => cMap[k] || '#6b7280')
          return (
            <>
              <div className="border border-border rounded p-3 flex items-center gap-3 flex-1">
                <PieChart data={sectorData} size={isMobile ? 90 : 100} />
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] text-muted mb-1.5 font-600">Sector Exposure</div>
                  <PieLegend data={sectorData} total={stocks.length} />
                </div>
              </div>
              <div className="border border-border rounded p-3 flex items-center gap-3 flex-1">
                <PieChart data={countryData} size={isMobile ? 90 : 100} />
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] text-muted mb-1.5 font-600">Country Exposure</div>
                  <PieLegend data={countryData} total={stocks.length} />
                </div>
              </div>
            </>
          )
        })()}
      </div>
      </>
      )}

      {stocks.length === 0 ? null :
       isMobile ? (
        <div className="border border-border rounded overflow-hidden">
          <div className="flex items-center gap-2 px-3 py-1.5 border-b border-border bg-surface/50">
            <span className="text-[9px] text-muted">Sort:</span>
            <select
              value={sortField || ''}
              onChange={(e) => { const f = e.target.value as keyof WatchStock | ''; if (f) toggleSort(f); else setSortField(null) }}
              className="text-[10px] bg-transparent border border-border rounded px-1.5 py-0.5 text-text flex-1"
            >
              <option value="">Default (added order)</option>
              <option value="sector">Sector</option>
              <option value="mktCap">Market Cap</option>
              <option value="change1d">1D %</option>
              <option value="mom1w">1W %</option>
              <option value="mom1m">1M %</option>
              <option value="mom6m">6M %</option>
              <option value="mom12m">12M %</option>
              <option value="valueScore">Value Score</option>
              <option value="growthScore">Growth Score</option>
              <option value="combinedRank">Best Score</option>
            </select>
            {sortField && (
              <button onClick={() => setSortDir(d => d === 'desc' ? 'asc' : 'desc')} className="text-[10px] text-gold px-1">
                {sortDir === 'desc' ? '▼' : '▲'}
              </button>
            )}
          </div>
          {sortedStocks.map((s) => (
            <a key={s.id}
              href={`/stock/${s.ticker}-${s.exchange}?from=${encodeURIComponent(typeof window !== 'undefined' ? window.location.pathname + window.location.search : '/')}`}
              style={{ display:'block', textDecoration:'none', color:'inherit' }}
              className="cursor-pointer border-b border-border px-3 py-2.5 hover:bg-white/5">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <span className="font-700 text-sm text-orange-400">{s.flag} {s.ticker}</span>
                  <span className="text-[9px] text-muted">{s.exchange}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-mono font-600 text-sm">{fv(s.price)}</span>
                  <span className="font-mono text-xs" style={clrStyle(s.change1d)}>
                    {s.change1d != null ? fpd(s.change1d) : '-'}
                  </span>
                  <button onClick={(e) => remove(e, s.id)} className="text-muted hover:text-red-400">
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-sub truncate max-w-[180px]">{s.company}</span>
                {(s as any).restricted && (
                  <span style={{ fontSize:9, color:'var(--text4)', border:'1px solid var(--border)', borderRadius:3, padding:'1px 4px', marginLeft:6 }}>
                    Not in free selection
                  </span>
                )}
                <span className="text-[9px] font-600" style={{ color: getSectorColor(s.sector) }}>{s.sector || '-'}</span>
              </div>
              <div className="flex gap-2 text-[10px] font-mono">
                <span className="text-muted">PEv: <span style={{color: s.rankPeLtm != null ? rankClr(s.rankPeLtm) : qClr((s as any).peTrailingQuintile)}}>{s.rankPeLtm != null ? fn(s.rankPeLtm) : qText((s as any).peTrailingQuintile)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">PEf: <span style={{color: s.rankPeNtm != null ? rankClr(s.rankPeNtm) : qClr((s as any).peForwardQuintile)}}>{s.rankPeNtm != null ? fn(s.rankPeNtm) : qText((s as any).peForwardQuintile)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">EPS: <span style={{color: s.rankEpsGr != null ? rankClr(s.rankEpsGr) : qClr((s as any).epsGrowthQuintile)}}>{s.rankEpsGr != null ? fn(s.rankEpsGr) : qText((s as any).epsGrowthQuintile)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">Rev: <span style={{color: s.rankRevGr != null ? rankClr(s.rankRevGr) : qClr((s as any).revGrowthQuintile)}}>{s.rankRevGr != null ? fn(s.rankRevGr) : qText((s as any).revGrowthQuintile)}</span></span>
              </div>
              <div className="flex gap-2 text-[10px] font-mono mt-0.5">
                <span className="text-muted">Val: <span style={{color:'#3b82f6'}}>{fn(s.valueScore)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">Grw: <span style={{color:'#22c55e'}}>{fn(s.growthScore)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">Best: <span style={{color:'var(--orange)'}}>{fn(s.combinedRank)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">1M: <span style={clrStyle(s.mom1m)}>{fpd(s.mom1m)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">12M: <span style={clrStyle(s.mom12m)}>{fpd(s.mom12m)}</span></span>
              </div>
              {/* Move to wallet buttons */}
              <div className="flex gap-1 mt-1.5">
                {WALLET_NAMES.map((name, idx) => idx !== activeWallet && (
                  <button key={idx}
                    onClick={(e) => moveToWallet(e, s.id, idx)}
                    className="text-[9px] px-2 py-0.5 rounded border border-border text-muted hover:text-orange-400 hover:border-orange-400">
                    → W{idx+1}
                  </button>
                ))}
              </div>
            </a>
          ))}
          {stocks.length > 1 && (
            <div className="px-3 py-2.5 bg-orange-500/5 border-t-2 border-orange-500/30">
              <div className="flex items-center justify-between mb-1">
                <span className="font-700 text-xs text-orange-400">∅ Wallet Average</span>
                <span className="text-[9px] text-muted">{stocks.length} stocks</span>
              </div>
              <div className="flex gap-2 text-[10px] font-mono flex-wrap">
                <span className="text-muted">1D: <span style={clrStyle(avg('change1d'))}>{avg('change1d') != null ? fpd(avg('change1d') as number) : '-'}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">PEv: <span style={{color: qClr(quintFromAvg(avg('rankPeLtm')))}}>{qText(quintFromAvg(avg('rankPeLtm')))}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">PEf: <span style={{color: qClr(quintFromAvg(avg('rankPeNtm')))}}>{qText(quintFromAvg(avg('rankPeNtm')))}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">EPS: <span style={{color: qClr(quintFromAvg(avg('rankEpsGr')))}}>{qText(quintFromAvg(avg('rankEpsGr')))}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">Rev: <span style={{color: qClr(quintFromAvg(avg('rankRevGr')))}}>{qText(quintFromAvg(avg('rankRevGr')))}</span></span>
              </div>
              <div className="flex gap-2 text-[10px] font-mono mt-0.5 flex-wrap">
                <span className="text-muted">Val: <span style={{color:'#3b82f6'}}>{fn(avg('valueScore'))}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">Grw: <span style={{color:'#22c55e'}}>{fn(avg('growthScore'))}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">Best: <span style={{color:'var(--orange)'}}>{fn(avg('combinedRank'))}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">1M: <span style={clrStyle(avg('mom1m'))}>{fpd(avg('mom1m'))}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">12M: <span style={clrStyle(avg('mom12m'))}>{fpd(avg('mom12m'))}</span></span>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="overflow-x-auto rounded border border-border" style={{ WebkitOverflowScrolling: 'touch' }}>
          <div className="text-[9px] text-muted px-3 py-1 border-b border-border bg-surface/50">
            Ranks calculated vs country universe
          </div>
          <table className="data-table" style={{ minWidth: 1100, width: 'max-content' }}>
            <thead><tr>
              <th style={{ position: 'sticky', left: 0, background: '#0d1017', zIndex: 2, minWidth: 90 }}>Ticker</th>
              <th style={{ minWidth: 130 }}>Company</th>
              <th style={{ minWidth: 120, cursor: 'pointer' }} onClick={() => toggleSort('sector')}>Sector{sortArrow('sector')}</th>
              <th style={{ width: 70 }}>Price</th>
              <th style={{ width: 65, cursor: 'pointer' }} onClick={() => toggleSort('change1d')}>1D %{sortArrow('change1d')}</th>
              <th style={{ width: 75, cursor: 'pointer' }} onClick={() => toggleSort('mktCap')}>MktCap $B{sortArrow('mktCap')}</th>
              <th style={{ width: 65 }}>PE LTM Rk</th>
              <th style={{ width: 65 }}>PE NTM Rk</th>
              <th style={{ width: 60 }}>PB Rk</th>
              <th style={{ width: 60 }}>EPS Rk</th>
              <th style={{ width: 60 }}>Rev Rk</th>
              <th style={{ width: 65, cursor: 'pointer' }} onClick={() => toggleSort('mom1w')}>1W %{sortArrow('mom1w')}</th>
              <th style={{ width: 65, cursor: 'pointer' }} onClick={() => toggleSort('mom1m')}>1M %{sortArrow('mom1m')}</th>
              <th style={{ width: 65, cursor: 'pointer' }} onClick={() => toggleSort('mom6m')}>6M %{sortArrow('mom6m')}</th>
              <th style={{ width: 72, cursor: 'pointer' }} onClick={() => toggleSort('mom12m')}>12M %{sortArrow('mom12m')}</th>
              <th style={{ width: 55, cursor: 'pointer' }} onClick={() => toggleSort('valueScore')}>Value{sortArrow('valueScore')}</th>
              <th style={{ width: 55, cursor: 'pointer' }} onClick={() => toggleSort('growthScore')}>Growth{sortArrow('growthScore')}</th>
              <th style={{ width: 55, cursor: 'pointer' }} onClick={() => toggleSort('combinedRank')}>Best{sortArrow('combinedRank')}</th>
              <th style={{ width: 60 }}>Move</th>
              <th style={{ width: 36 }}></th>
            </tr></thead>
            <tbody>
              {sortedStocks.map((s) => (
                <tr key={s.id}
                  onClick={() => router.push(`/stock/${s.ticker}-${s.exchange}?from=${encodeURIComponent(window.location.pathname + window.location.search)}`)}
                  className="cursor-pointer">
                  <td style={{ position: 'sticky', left: 0, background: '#0d1017', zIndex: 1, boxShadow: '2px 0 4px rgba(0,0,0,0.3)' }}>
                    <span className="font-700 text-[12px] text-orange-400 whitespace-nowrap">{s.flag} {s.ticker}</span>
                    <span className="text-[9px] text-muted ml-1">{s.exchange}</span>
                  </td>
                  <td className="text-sub text-[11px]" style={{ maxWidth: 130, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {(s.company || '').slice(0, 20)}
                  </td>
                  <td>
                    <span className="text-[10px] font-600" style={{ color: getSectorColor(s.sector) }}>
                      {s.sector || '-'}
                    </span>
                  </td>
                  <td className="font-mono text-right text-[12px]">{fv(s.price)}</td>
                  <td className="font-mono text-right text-[12px]" style={clrStyle(s.change1d)}>
                    {s.change1d != null ? fpd(s.change1d) : '-'}
                  </td>
                  <td className="font-mono text-right text-[12px]">{s.mktCap != null ? fv(s.mktCap, 1) : '-'}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: s.rankPeLtm != null ? rankClr(s.rankPeLtm) : qClr((s as any).peTrailingQuintile)}}>{s.rankPeLtm != null ? fn(s.rankPeLtm) : qText((s as any).peTrailingQuintile)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: s.rankPeNtm != null ? rankClr(s.rankPeNtm) : qClr((s as any).peForwardQuintile)}}>{s.rankPeNtm != null ? fn(s.rankPeNtm) : qText((s as any).peForwardQuintile)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: s.rankPb != null ? rankClr(s.rankPb) : qClr((s as any).pbQuintile)}}>{s.rankPb != null ? fn(s.rankPb) : qText((s as any).pbQuintile)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: s.rankEpsGr != null ? rankClr(s.rankEpsGr) : qClr((s as any).epsGrowthQuintile)}}>{s.rankEpsGr != null ? fn(s.rankEpsGr) : qText((s as any).epsGrowthQuintile)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: s.rankRevGr != null ? rankClr(s.rankRevGr) : qClr((s as any).revGrowthQuintile)}}>{s.rankRevGr != null ? fn(s.rankRevGr) : qText((s as any).revGrowthQuintile)}</td>
                  <td className="font-mono text-right text-[12px]" style={clrStyle(s.mom1w)}>{fpd(s.mom1w)}</td>
                  <td className="font-mono text-right text-[12px]" style={clrStyle(s.mom1m)}>{fpd(s.mom1m)}</td>
                  <td className="font-mono text-right text-[12px]" style={clrStyle(s.mom6m)}>{fpd(s.mom6m)}</td>
                  <td className="font-mono text-right font-700 text-[12px]" style={clrStyle(s.mom12m)}>{fpd(s.mom12m)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color:'#3b82f6'}}>{fn(s.valueScore)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color:'#22c55e'}}>{fn(s.growthScore)}</td>
                  <td className="font-mono text-center font-700 text-[12px]" style={{color:'var(--orange)'}}>{fn(s.combinedRank)}</td>
                  <td onClick={(e) => e.stopPropagation()} className="text-center">
                    <div className="flex gap-0.5 justify-center">
                      {WALLET_NAMES.map((_, idx) => idx !== activeWallet && (
                        <button key={idx}
                          onClick={(e) => moveToWallet(e, s.id, idx)}
                          className="text-[9px] px-1.5 py-0.5 rounded border border-border text-muted hover:text-orange-400 hover:border-orange-400">
                          W{idx+1}
                        </button>
                      ))}
                    </div>
                  </td>
                  <td onClick={(e) => remove(e, s.id)} className="cursor-pointer text-muted hover:text-red-400 transition-colors text-center">
                    <Trash2 size={13} />
                  </td>
                </tr>
              ))}
              {stocks.length > 1 && (
                <tr style={{ borderTop: '2px solid rgba(249,115,22,0.3)', background: 'rgba(249,115,22,0.04)' }}>
                  <td style={{ position: 'sticky', left: 0, background: '#120f0a', zIndex: 1, boxShadow: '2px 0 4px rgba(0,0,0,0.3)' }}>
                    <span className="font-700 text-[11px] text-orange-400">∅ Average</span>
                    <span className="text-[9px] text-muted ml-1">{stocks.length} stocks</span>
                  </td>
                  <td></td><td></td>
                  <td></td>
                  <td className="font-mono text-right text-[12px] font-700" style={clrStyle(avg('change1d'))}>
                    {avg('change1d') != null ? fpd(avg('change1d') as number) : '-'}
                  </td>
                  <td className="font-mono text-right text-[12px] font-700">{avg('mktCap') != null ? fv(avg('mktCap'), 1) : '-'}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: qClr(quintFromAvg(avg('rankPeLtm')))}}>{qText(quintFromAvg(avg('rankPeLtm')))}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: qClr(quintFromAvg(avg('rankPeNtm')))}}>{qText(quintFromAvg(avg('rankPeNtm')))}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: qClr(quintFromAvg(avg('rankPb')))}}>{qText(quintFromAvg(avg('rankPb')))}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: qClr(quintFromAvg(avg('rankEpsGr')))}}>{qText(quintFromAvg(avg('rankEpsGr')))}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: qClr(quintFromAvg(avg('rankRevGr')))}}>{qText(quintFromAvg(avg('rankRevGr')))}</td>
                  <td className="font-mono text-right text-[12px] font-700" style={clrStyle(avg('mom1w'))}>{fpd(avg('mom1w'))}</td>
                  <td className="font-mono text-right text-[12px] font-700" style={clrStyle(avg('mom1m'))}>{fpd(avg('mom1m'))}</td>
                  <td className="font-mono text-right text-[12px] font-700" style={clrStyle(avg('mom6m'))}>{fpd(avg('mom6m'))}</td>
                  <td className="font-mono text-right font-700 text-[12px]" style={clrStyle(avg('mom12m'))}>{fpd(avg('mom12m'))}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color:'#3b82f6'}}>{fn(avg('valueScore'))}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color:'#22c55e'}}>{fn(avg('growthScore'))}</td>
                  <td className="font-mono text-center font-700 text-[12px]" style={{color:'var(--orange)'}}>{fn(avg('combinedRank'))}</td>
                  <td></td><td></td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
      <div className="text-xs text-muted text-right">{100 - stocks.length} slots remaining in {WALLET_NAMES[activeWallet]}</div>

      <div style={{ marginTop:20 }}>
        <div style={{ fontSize:11, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
          letterSpacing:'0.08em', textTransform:'uppercase', color:'var(--orange)', marginBottom:8 }}>
          📰 News — last 24h for {WALLET_NAMES[activeWallet]}
        </div>
        {newsLoading ? (
          <div style={{ fontSize:12, color:'var(--text4)' }}>Loading news...</div>
        ) : walletNews.length === 0 ? (
          <div style={{ fontSize:12, color:'var(--text4)' }}>No news in the last 24 hours for these tickers.</div>
        ) : (
          <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
            {walletNews.map((n: any, i: number) => (
              <a key={i} href={n.link} target="_blank" rel="noopener noreferrer" style={{
                display:'block', padding:'8px 10px', border:'1px solid var(--border)',
                borderRadius:4, textDecoration:'none', color:'inherit' }}>
                <div style={{ fontSize:12, color:'var(--text)', marginBottom:2 }}>
                  <span style={{ color:'var(--orange)', fontWeight:700 }}>[{n.ticker}]</span> {n.title}
                </div>
                <div style={{ fontSize:10, color:'var(--text4)' }}>{n.source}</div>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
