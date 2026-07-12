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

const SECTOR_COLORS: Record<string, string> = {
  'Technology': '#3b82f6', 'Financials': '#f59e0b', 'Health Care': '#10b981',
  'Consumer Discretionary': '#f97316', 'Industrials': '#8b5cf6',
  'Communication Services': '#06b6d4', 'Consumer Staples': '#84cc16',
  'Energy': '#ef4444', 'Materials': '#a78bfa', 'Real Estate': '#fb7185', 'Utilities': '#34d399',
}
const getSectorColor = (s: string | null | undefined) => SECTOR_COLORS[s || ''] || '#6b7280'

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

    // Carica ogni titolo singolarmente con ticker+exchange
    // Questo bypassa i filtri top N e funziona per qualsiasi titolo
    const liveMap: Record<string, any> = {}
    await Promise.all(data.map(async (w: any) => {
      try {
        const r = await fetch(`/api/db/stocks?ticker=${encodeURIComponent(w.ticker)}&exchange=${encodeURIComponent(w.exchange)}`)
        if (!r.ok) return
        const d = await r.json()
        const s = (d.stocks || [])[0]
        if (s) liveMap[`${s.ticker}.${s.exchange}`] = s
      } catch {}
    }))

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
      ) : isMobile ? (
        <div className="border border-border rounded overflow-hidden">
          <div className="text-[9px] text-muted px-3 py-1 border-b border-border bg-surface/50">
            Tap a stock to view details
          </div>
          {stocks.map((s) => (
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
                    {s.change1d != null ? fpd(s.change1d / 100) : '-'}
                  </span>
                  <button onClick={(e) => remove(e, s.id)} className="text-muted hover:text-red-400">
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-sub truncate max-w-[180px]">{s.company}</span>
                <span className="text-[9px] font-600" style={{ color: getSectorColor(s.sector) }}>{s.sector || '-'}</span>
              </div>
              <div className="flex gap-2 text-[10px] font-mono">
                <span className="text-muted">PEv: <span style={{color: rankClr(s.rankPeLtm)}}>{fn(s.rankPeLtm)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">PEf: <span style={{color: rankClr(s.rankPeNtm)}}>{fn(s.rankPeNtm)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">EPS: <span style={{color: rankClr(s.rankEpsGr)}}>{fn(s.rankEpsGr)}</span></span>
                <span className="text-[#444]">|</span>
                <span className="text-muted">Rev: <span style={{color: rankClr(s.rankRevGr)}}>{fn(s.rankRevGr)}</span></span>
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
              <th style={{ minWidth: 120 }}>Sector</th>
              <th style={{ width: 70 }}>Price</th>
              <th style={{ width: 65 }}>1D %</th>
              <th style={{ width: 75 }}>MktCap $B</th>
              <th style={{ width: 65 }}>PE LTM Rk</th>
              <th style={{ width: 65 }}>PE NTM Rk</th>
              <th style={{ width: 60 }}>PB Rk</th>
              <th style={{ width: 60 }}>EPS Rk</th>
              <th style={{ width: 60 }}>Rev Rk</th>
              <th style={{ width: 65 }}>1W %</th>
              <th style={{ width: 65 }}>1M %</th>
              <th style={{ width: 65 }}>6M %</th>
              <th style={{ width: 72 }}>12M %</th>
              <th style={{ width: 55 }}>Value</th>
              <th style={{ width: 55 }}>Growth</th>
              <th style={{ width: 55 }}>Best</th>
              <th style={{ width: 60 }}>Move</th>
              <th style={{ width: 36 }}></th>
            </tr></thead>
            <tbody>
              {stocks.map((s) => (
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
                    {s.change1d != null ? fpd(s.change1d / 100) : '-'}
                  </td>
                  <td className="font-mono text-right text-[12px]">{s.mktCap != null ? fv(s.mktCap, 1) : '-'}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: rankClr(s.rankPeLtm)}}>{fn(s.rankPeLtm)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: rankClr(s.rankPeNtm)}}>{fn(s.rankPeNtm)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: rankClr(s.rankPb)}}>{fn(s.rankPb)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: rankClr(s.rankEpsGr)}}>{fn(s.rankEpsGr)}</td>
                  <td className="font-mono text-center text-[12px] font-600" style={{color: rankClr(s.rankRevGr)}}>{fn(s.rankRevGr)}</td>
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
                    {avg('change1d') != null ? fpd((avg('change1d') as number) / 100) : '-'}
                  </td>
                  <td className="font-mono text-right text-[12px] font-700">{avg('mktCap') != null ? fv(avg('mktCap'), 1) : '-'}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: rankClr(avg('rankPeLtm'))}}>{fn(avg('rankPeLtm'))}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: rankClr(avg('rankPeNtm'))}}>{fn(avg('rankPeNtm'))}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: rankClr(avg('rankPb'))}}>{fn(avg('rankPb'))}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: rankClr(avg('rankEpsGr'))}}>{fn(avg('rankEpsGr'))}</td>
                  <td className="font-mono text-center text-[12px] font-700" style={{color: rankClr(avg('rankRevGr'))}}>{fn(avg('rankRevGr'))}</td>
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
    </div>
  )
}
