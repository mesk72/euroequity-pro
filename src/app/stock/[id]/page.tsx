'use client'

import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import WatchlistButton from '@/components/watchlist/WatchlistButton'
import { computeScores } from '@/lib/ranking'
import { RESEARCH_INDEX } from '@/lib/researchIndex'
import { DEMO_STOCKS } from '@/lib/demoData'

const MIC: Record<string, string> = { PA:'XPAR', AS:'XAMS', BR:'XBRU', LS:'XLIS', MIL:'XMIL', IR:'XDUB', OB:'XOSL' }

function getBorseUrl(ticker: string, exchange: string, isin: string | null, primaryExchange?: string): string | null {
  if (exchange === 'MIL' && isin) return `https://www.borsaitaliana.it/borsa/azioni/scheda/${isin}.html`
  if (['PA','AS','BR','LS','IR'].includes(exchange) && isin) return `https://live.euronext.com/en/product/equities/${isin}-${MIC[exchange]}`
  if (exchange === 'OB') return isin ? `https://live.euronext.com/nb/product/equities/${isin}-XOSL` : `https://live.euronext.com/nb/search?q=${ticker}`
  if (exchange === 'XETRA' && isin) return `https://www.boerse-frankfurt.de/equity/${isin}`
  if (exchange === 'MC' && isin) return `https://www.bolsamadrid.es/esp/aspx/Empresas/FichaValor.aspx?ISIN=${isin}`
  if (['LSE','AIM'].includes(exchange)) return `https://www.londonstockexchange.com/stock/${ticker}/company-page`
  if (['OM','HE','CPSE','NGM'].includes(exchange)) return `https://www.nasdaq.com/european-market-activity/shares/${ticker.toLowerCase()}`
  if (exchange === 'VI' && isin) return `https://www.wienerborse.at/aktien-prime-market/${ticker.toLowerCase()}-${isin}/`
  if (exchange === 'SWX') return 'https://www.six-group.com/en/products-services/the-swiss-stock-exchange/market-data/shares/share-explorer.html'
  if (exchange === 'TSX') return `https://www.tsx.com/listings/listing-with-us/listed-company-directory/company-directory-details?ticker=${ticker}`
  // TSE/SEHK/ASX/SGX/KRX: gestiti direttamente nel blocco Official Links
  // sulla pagina (Kabutan/HKEX/ASX/SGX/Naver) come "Official Listing" —
  // qui restano fuori per evitare un secondo link duplicato.
  if (exchange === 'US') {
    const pe = primaryExchange || ''
    if (['NYSE','NYSEAM','ARCA','BATS'].includes(pe)) return `https://www.nyse.com/quote/XNYS:${ticker}`
    if (['NasdaqGS','NasdaqGM','NasdaqCM'].includes(pe)) return `https://www.nasdaq.com/market-activity/stocks/${ticker.toLowerCase()}`
    if (pe === 'OTCPK') return `https://www.otcmarkets.com/stock/${ticker}/overview`
    return null
  }
  return null
}

function fp(v?: number | null, d = 2): string {
  if (v == null || isNaN(v as number)) return '-'
  return `${(v as number) >= 0 ? '+' : ''}${(v as number).toFixed(d)}%`
}
function fv(v?: number | null, d = 2): string {
  if (v == null || isNaN(v as number)) return '-'
  return (v as number).toFixed(d)
}
function fn(v?: number | null): string {
  if (v == null || isNaN(v as number)) return '-'
  return String(Math.round(v as number))
}
function clr(v?: number | null): string {
  if (v == null) return 'var(--text3)'
  return v > 0 ? 'var(--green)' : v < 0 ? 'var(--red)' : 'var(--text3)'
}
function scoreBg(v?: number | null): string {
  if (v == null) return 'transparent'
  if (v >= 70) return 'rgba(34,197,94,0.15)'
  if (v >= 40) return 'rgba(249,115,22,0.12)'
  return 'rgba(239,68,68,0.12)'
}
function scoreClr(v?: number | null): string {
  if (v == null) return 'var(--text3)'
  if (v >= 70) return 'var(--green)'
  if (v >= 40) return 'var(--orange)'
  return 'var(--red)'
}

function PriceChart({ history, days, momentum }: { history: any[]; days: number; momentum?: any }) {
  const data = history
    .map((d: any) => ({
      date: d.date || d.Date || '',
      close: parseFloat(d.adjusted_close || d.close || '0'),
    }))
    .filter(d => !isNaN(d.close) && d.close > 0)
    .slice(-(days + 1))

  if (data.length < 5) return (
    <div style={{ height:280, display:'flex', alignItems:'center', justifyContent:'center',
      color:'var(--text3)', fontSize:13 }}>
      No chart data available
    </div>
  )

  const closes = data.map(d => d.close)
  const minP = Math.min(...closes)
  const maxP = Math.max(...closes)
  const range = maxP - minP || 1
  const W = 900, H = 260, PX = 52, PY = 20

  function toX(i: number) { return PX + (i / (data.length - 1)) * (W - 2 * PX) }
  function toY(p: number) { return PY + ((maxP - p) / range) * (H - 2 * PY) }

  function ma(n: number): (number | null)[] {
    return closes.map((_, i) => {
      if (i < n - 1) return null
      const slice = closes.slice(i - n + 1, i + 1)
      return slice.reduce((a, b) => a + b, 0) / n
    })
  }

  const ma50 = ma(Math.min(50, data.length))
  const ma200 = ma(Math.min(200, data.length))

  function maPath(values: (number | null)[]): string {
    let path = ''
    values.forEach((v, i) => {
      if (v == null) return
      const x = toX(i), y = toY(v)
      path += path === '' ? `M${x.toFixed(1)},${y.toFixed(1)}` : ` L${x.toFixed(1)},${y.toFixed(1)}`
    })
    return path
  }

  const pricePoints = closes.map((p, i) => `${toX(i).toFixed(1)},${toY(p).toFixed(1)}`).join(' ')
  const isUp = closes[closes.length - 1] >= closes[0]
  const c = isUp ? 'var(--green)' : 'var(--red)'
  const _fb = ((closes[closes.length-1]/closes[0]-1)*100).toFixed(2)
  const _pct = (v: number | null) => v != null ? Number(v).toFixed(2) : null
  const perf = momentum
    ? (days <= 10 ? (_pct(momentum.mom1w) ?? _fb)
    : days <= 40 ? (_pct(momentum.mom1m) ?? _fb)
    : days <= 200 ? (_pct(momentum.mom6m) ?? _fb)
    : days <= 400 ? (_pct(momentum.mom12m) ?? _fb)
    : days <= 1000 ? (_pct(momentum.mom3y) ?? _fb)
    : (_pct(momentum.mom5y) ?? _fb))
    : _fb

  const yLabels = [0, 0.25, 0.5, 0.75, 1].map(r => ({
    val: (maxP - r * range).toFixed(2),
    y: PY + r * (H - 2 * PY)
  }))

  const xLabels = [0, 0.25, 0.5, 0.75, 1].map(r => {
    const idx = Math.min(Math.round(r * (data.length - 1)), data.length - 1)
    return { label: data[idx]?.date?.slice(0, 7) || '', x: toX(idx) }
  })

  const lastMa50 = ma50.filter(v => v != null).pop()
  const lastMa200 = ma200.filter(v => v != null).pop()

  return (
    <div style={{ position:'relative', background:'var(--bg2)', borderRadius:3, padding:'12px 0 4px' }}>
      <div style={{ position:'absolute', top:12, right:16,
        fontFamily:'IBM Plex Mono', fontSize:15, fontWeight:700,
        color: isUp ? 'var(--green)' : 'var(--red)',
        background:'var(--bg2)', padding:'2px 10px', borderRadius:2,
        border:`1px solid ${isUp ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}` }}>
        {isUp ? '▲' : '▼'} {parseFloat(perf) > 0 ? '+' : ''}{perf}%
      </div>
      <div style={{ display:'flex', gap:16, paddingLeft:PX, marginBottom:8 }}>
        <span style={{ fontSize:10, fontFamily:'IBM Plex Sans Condensed', color:'var(--text3)' }}>Price</span>
        {lastMa50 && (
          <span style={{ fontSize:10, fontFamily:'IBM Plex Mono', color:'#f59e0b' }}>
            MA50: {lastMa50.toFixed(2)}
          </span>
        )}
        {lastMa200 && data.length >= 200 && (
          <span style={{ fontSize:10, fontFamily:'IBM Plex Mono', color:'#8b5cf6' }}>
            MA200: {lastMa200.toFixed(2)}
          </span>
        )}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width:'100%', height:280 }}>
        <defs>
          <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={c} stopOpacity="0.18" />
            <stop offset="100%" stopColor={c} stopOpacity="0.01" />
          </linearGradient>
        </defs>
        {yLabels.map(({ y }) => (
          <line key={y} x1={PX} y1={y} x2={W - 4} y2={y}
            stroke="rgba(30,45,69,0.7)" strokeWidth="1" strokeDasharray="3,4" />
        ))}
        {yLabels.map(({ val, y }) => (
          <text key={val} x={PX - 4} y={y + 4} textAnchor="end" fill="var(--text4)"
            style={{ fontSize:9, fontFamily:'IBM Plex Mono' }}>{val}</text>
        ))}
        {xLabels.map(({ label, x }) => (
          <text key={label} x={x} y={H - 4} textAnchor="middle" fill="var(--text4)"
            style={{ fontSize:9, fontFamily:'IBM Plex Mono' }}>{label}</text>
        ))}
        <polygon points={`${PX},${H - PY} ${pricePoints} ${W - PX},${H - PY}`} fill="url(#priceFill)" />
        <polyline points={pricePoints} fill="none" stroke={c} strokeWidth="1.5" strokeLinejoin="round" />
        {lastMa50 && (
          <path d={maPath(ma50)} fill="none" stroke="#f59e0b" strokeWidth="1.2" strokeDasharray="4,2" />
        )}
        {lastMa200 && data.length >= 100 && (
          <path d={maPath(ma200)} fill="none" stroke="#8b5cf6" strokeWidth="1.2" strokeDasharray="6,3" />
        )}
        <circle cx={toX(data.length - 1)} cy={toY(closes[closes.length - 1])}
          r="3.5" fill={c} stroke="var(--bg2)" strokeWidth="1.5" />
      </svg>
    </div>
  )
}

function StockPageInner() {
  const params = useParams()
  const router = useRouter()
  const searchParams = useSearchParams()
  const handleBack = () => {
    let from: string | null = null
    try { from = sessionStorage.getItem('stockBackTo') } catch {}
    if (!from) from = searchParams.get('from')
    if (from) {
      const decoded = from.startsWith('/') ? from : decodeURIComponent(from)
      // Per /news usa history.back() — evita freeze da Router Cache di Next.js
      if (decoded === '/news') {
        window.history.back()
      } else {
        router.push(decoded)
        router.refresh()  // forza il router a non servire una versione in cache
      }
    } else {
      window.history.back()
    }
  }
  const id = (params?.id as string) || ''
  const [ticker, exchangeCode] = id.split('-')

  const [stock, setStock] = useState<any>(null)
  const [restrictedInfo, setRestrictedInfo] = useState<{ ticker: string; company: string } | null>(null)
  const [loadingStock, setLoadingStock] = useState(true)
  const [sectorPopupOpen, setSectorPopupOpen] = useState(false)
  const [sectorAvgData, setSectorAvgData] = useState<any>(null)
  const [sectorAvgLoading, setSectorAvgLoading] = useState(false)

  const getContinent = (ex: string) => {
    if (['US','TSX'].includes(ex)) return 'north_america'
    if (['TSE','SEHK','ASX','KRX','SGX'].includes(ex)) return 'asia_pacific'
    return 'europe'
  }

  const openSectorPopup = async () => {
    setSectorPopupOpen(true)
    if (sectorAvgData || !stock) return
    setSectorAvgLoading(true)
    const continent = getContinent(exchangeCode)
    let authHeader: Record<string, string> = {}
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (session?.access_token) authHeader = { Authorization: `Bearer ${session.access_token}` }
    } catch {}
    fetch(`/api/db/sector-averages?continent=${continent}&sector=${encodeURIComponent(stock.sector || '')}`, { headers: authHeader })
      .then(r => r.ok ? r.json() : null)
      .then(d => { setSectorAvgData(d); setSectorAvgLoading(false) })
      .catch(() => setSectorAvgLoading(false))
  }

  useEffect(() => {
    if (!ticker || !exchangeCode) return
    const load = async () => {
      let authHeader: Record<string, string> = {}
      try {
        const { data: { session } } = await supabase.auth.getSession()
        if (session?.access_token) authHeader = { Authorization: `Bearer ${session.access_token}` }
      } catch {}
      fetch(`/api/db/stocks?ticker=${ticker}&exchange=${exchangeCode}`, { headers: authHeader })
        .then(r => r.ok ? r.json() : null)
        .then(d => {
          if (d?.stocks?.[0]) {
            setStock(d.stocks[0])
            setRestrictedInfo(null)
          } else if (d?.restricted) {
            setRestrictedInfo({ ticker: d.ticker, company: d.company })
            setStock(null)
          } else {
            const allStocks = computeScores([...DEMO_STOCKS])
            const found = allStocks.find(s => s.ticker === ticker && s.exchange === exchangeCode)
            setStock(found || null)
          }
          setLoadingStock(false)
        })
        .catch(() => {
          const allStocks = computeScores([...DEMO_STOCKS])
          const found = allStocks.find(s => s.ticker === ticker && s.exchange === exchangeCode)
          setStock(found || null)
          setLoadingStock(false)
        })
    }
    load()
    // Refresh automatico ogni 5 minuti - stessa logica dello screener,
    // per non mostrare mai dati piu' vecchi di quelli di altre pagine.
    const interval = setInterval(load, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [ticker, exchangeCode])

  const [chartDays, setChartDays] = useState(252)
  const [history, setHistory] = useState<any[]>([])
  const [momentum, setMomentum] = useState<any>(null)
  const [loadingChart, setLoading] = useState(true)
  const [user, setUser] = useState<any>(null)
  useEffect(() => { supabase.auth.getUser().then(({ data }) => setUser(data.user ?? null)) }, [])

  useEffect(() => {
    if (!ticker || !exchangeCode) return
    setLoading(true)
    const load = async () => {
      let authHeader: Record<string, string> = {}
      try {
        const { data: { session } } = await supabase.auth.getSession()
        if (session?.access_token) authHeader = { Authorization: `Bearer ${session.access_token}` }
      } catch {}
      fetch(`/api/db/history?ticker=${ticker}&exchange=${exchangeCode}&days=${Math.max(chartDays + 50, 1800)}&t=${Date.now()}`, { cache: 'no-store', headers: authHeader })
        .then(r => r.ok ? r.json() : { history: [] })
        .then(d => { setHistory(d.history || []); setMomentum(d.momentum || null); setLoading(false) })
        .catch(() => setLoading(false))
    }
    load()
  }, [ticker, exchangeCode, chartDays])



  if (!stock) {
    return (
      <div style={{ background:'var(--bg)', minHeight:'100vh', color:'var(--text)',
        fontFamily:'IBM Plex Sans, sans-serif', padding:40 }}>
        <style>{`@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap');`}</style>
        <button onClick={handleBack}
          style={{ display:'flex', alignItems:'center', gap:8, color:'var(--orange)',
            background:'none', border:'none', cursor:'pointer', fontSize:14, marginBottom:24 }}>
          <ArrowLeft size={16} /> Back
        </button>
        {restrictedInfo ? (
          <div>
            <p style={{ color:'var(--text2)', fontSize:15, marginBottom:8 }}>
              {restrictedInfo.company || restrictedInfo.ticker}
            </p>
            <p style={{ color:'var(--text3)', fontSize:13 }}>
              This stock isn't included in our free top-500 selection.<br />
              Contact <a href="mailto:andrea@forwardalpha.pro" style={{ color:'var(--orange)' }}>andrea@forwardalpha.pro</a> for full access.
            </p>
          </div>
        ) : (
          <p style={{ color:'var(--text3)' }}>Stock not found: {ticker}.{exchangeCode}</p>
        )}
      </div>
    )
  }

  const s = stock as any
  const QLBL: Record<string, { t: string; c: string }> = {
    'Top Quintile':    { t: 'First Quintile',    c: 'var(--green)' },
    '2nd Quintile':    { t: 'Second Quintile',     c: '#84cc16' },
    'Middle':          { t: 'Third Quintile',        c: '#f59e0b' },
    '4th Quintile':    { t: 'Fourth Quintile',     c: '#f59e0b' },
    'Bottom Quintile': { t: 'Fifth Quintile', c: '#e84560' },
  }
  const qText = (q: string | null | undefined) => q && QLBL[q] ? QLBL[q].t : '—'
  const qColor = (q: string | null | undefined) => q && QLBL[q] ? QLBL[q].c : 'var(--text3)'
  const metrics = [
    { label:'Price', val: fv(stock.price, 2), color: 'var(--text)' },
    { label:'Mkt Cap $B', val: stock.mktCap ? fv(stock.mktCap, 1) : '—', color: 'var(--text)' },
    { label:'PE LTM Rank', val: s.rankPeLtm != null ? String(Math.round(s.rankPeLtm)) : qText(s.peTrailingQuintile), color: s.rankPeLtm != null ? (s.rankPeLtm >= 70 ? 'var(--green)' : s.rankPeLtm <= 30 ? '#e84560' : '#f59e0b') : qColor(s.peTrailingQuintile) },
    { label:'PE NTM Rank', val: s.rankPeNtm != null ? String(Math.round(s.rankPeNtm)) : qText(s.peForwardQuintile), color: s.rankPeNtm != null ? (s.rankPeNtm >= 70 ? 'var(--green)' : s.rankPeNtm <= 30 ? '#e84560' : '#f59e0b') : qColor(s.peForwardQuintile) },
    { label:'PB Rank', val: s.rankPb != null ? String(Math.round(s.rankPb)) : qText(s.pbQuintile), color: s.rankPb != null ? (s.rankPb >= 70 ? 'var(--green)' : s.rankPb <= 30 ? '#e84560' : '#f59e0b') : qColor(s.pbQuintile) },
    { label:'EPS Gr Rank', val: s.rankEpsGr != null ? String(Math.round(s.rankEpsGr)) : qText(s.epsGrowthQuintile), color: s.rankEpsGr != null ? (s.rankEpsGr >= 70 ? 'var(--green)' : s.rankEpsGr <= 30 ? '#e84560' : '#f59e0b') : qColor(s.epsGrowthQuintile) },
    { label:'Rev Gr Rank', val: s.rankRevGr != null ? String(Math.round(s.rankRevGr)) : qText(s.revGrowthQuintile), color: s.rankRevGr != null ? (s.rankRevGr >= 70 ? 'var(--green)' : s.rankRevGr <= 30 ? '#e84560' : '#f59e0b') : qColor(s.revGrowthQuintile) },
    { label:'Mom 1 Week', val: stock.mom1w != null ? fp(stock.mom1w * 100, 1) : '—', color: clr(stock.mom1w) },
    { label:'Mom 1 Month', val: stock.mom1m != null ? fp(stock.mom1m * 100, 1) : '—', color: clr(stock.mom1m) },
    { label:'Mom 6 Months', val: stock.mom6m != null ? fp(stock.mom6m * 100, 1) : '—', color: clr(stock.mom6m) },
    { label:'Mom 12 Months', val: stock.mom12m != null ? fp(stock.mom12m * 100, 1) : '—', color: clr(stock.mom12m) },
  ]

  return (
    <div style={{ background:'var(--bg)', minHeight:'100vh', color:'var(--text)',
      fontFamily:'IBM Plex Sans, sans-serif', fontSize:13 }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600;700&display=swap');
        :root {
          --bg:#0a0e1a; --bg2:#0d1221; --surface:#111827; --surface2:#161d2e;
          --border:#1e2d45; --border2:#243550; --orange:#f97316; --green:#22c55e;
          --red:#ef4444; --gold:#eab308; --text:#ffffff; --text2:#e2e8f0;
          --text3:#cbd5e1; --text4:#94a3b8;
        }
        body { background:var(--bg); margin:0; }
        .input-field {
          background:var(--bg2); border:1px solid var(--border); border-radius:3px;
          padding:5px 8px; font-size:13px; color:var(--text);
          font-family:'IBM Plex Sans',sans-serif; outline:none; width:100%;
        }
        .input-field:focus { border-color:var(--orange); }
        .btn-primary {
          background:var(--orange); color:#fff; font-family:'IBM Plex Sans Condensed',sans-serif;
          font-weight:700; font-size:13px; padding:7px 18px; border-radius:3px;
          border:none; cursor:pointer;
        }
        .btn-primary:disabled { opacity:0.5; cursor:not-allowed; }
      `}</style>

      <div style={{ background:'var(--surface)', borderBottom:'2px solid var(--orange)',
        padding:'0 24px', height:44, display:'flex', alignItems:'center', gap:16 }}>
        <button onClick={handleBack}
          style={{ display:'flex', alignItems:'center', gap:6, color:'var(--text4)',
            background:'none', border:'none', cursor:'pointer', fontSize:13 }}>
          <ArrowLeft size={15} /> Back
        </button>
        <div style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
          fontSize:18, color:'var(--orange)' }}>
          FORWARD<span style={{ color:'var(--text3)' }}>ALPHA</span>
        </div>
      </div>

      <div style={{ maxWidth:1100, margin:'0 auto', padding:'24px 16px' }}>
        <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
          borderLeft:'4px solid var(--orange)', borderRadius:4, padding:'16px 20px',
          marginBottom:16, display:'flex', alignItems:'center', justifyContent:'space-between',
          flexWrap:'wrap', gap:12 }}>
          <div>
            <div style={{ display:'flex', alignItems:'baseline', gap:12, flexWrap:'wrap' }}>
              <span style={{ fontSize:28, fontFamily:'IBM Plex Sans Condensed',
                fontWeight:700, color:'var(--orange)' }}>
                {stock.flag} {stock.ticker}
              </span>
              <span style={{ fontSize:24, fontFamily:'IBM Plex Mono',
                fontWeight:700, color:'var(--text)' }}>
                {['LSE','AIM'].includes(stock.exchange) ? 'p' :
                 stock.exchange === 'SWX' ? 'CHF' :
                 ['OM','NGM'].includes(stock.exchange) ? 'kr' :
                 stock.exchange === 'OB' ? 'kr' :
                 stock.exchange === 'CPSE' ? 'kr' :
                 stock.exchange === 'US' ? 'USD' :
                 stock.exchange === 'TSE' ? '¥' :
                 stock.exchange === 'SEHK' ? 'HK$' :
                 stock.exchange === 'TSX' ? 'C$' :
                 stock.exchange === 'ASX' ? 'A$' :
                 '€'}{fv(stock.price, 2)}
              </span>
              <span style={{ fontSize:18, fontFamily:'IBM Plex Mono', fontWeight:600,
                color: (stock.change1d ?? 0) >= 0 ? 'var(--green)' : 'var(--red)' }}>
                {stock.change1d != null ? fp(stock.change1d * 100, 2) : ''}
              </span>
            </div>
            <div style={{ fontSize:14, color:'var(--text3)', marginTop:4 }}>{stock.company}</div>
            <div style={{ fontSize:12, color:'var(--text4)', marginTop:2 }}>
              {stock.exchange} · {stock.sector} · {stock.country}
            </div>
            {history.length > 0 && (
              <div style={{ fontSize:11, color:'var(--text4)', marginTop:4 }}>
                Last price: {stock.last_price_date || history[history.length - 1]?.date || '-'}
              </div>
            )}
          </div>
          <div style={{ display:'flex', gap:12 }}>
            {[
              { label:'Value Score', val: stock.valueScore },
              { label:'Growth Score', val: stock.growthScore },
              { label:'Best', val: stock.combinedRank },
            ].map(({ label, val }) => (
              <div key={label} style={{ textAlign:'center',
                background: scoreBg(val), border:`1px solid ${scoreClr(val)}40`,
                borderRadius:4, padding:'8px 16px' }}>
                <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed',
                  fontWeight:700, letterSpacing:'0.1em', textTransform:'uppercase',
                  color:'var(--text4)', marginBottom:4 }}>{label}</div>
                <div style={{ fontSize:28, fontFamily:'IBM Plex Mono',
                  fontWeight:700, color: scoreClr(val) }}>
                  {user ? fn(val) : '🔒'}
                </div>
                <div style={{ fontSize:9, color:'var(--text4)' }}>/ 100</div>
              </div>
            ))}
          </div>
        </div>

        <button onClick={openSectorPopup} style={{
          background:'transparent', border:'1px solid var(--border)', borderRadius:4,
          color:'var(--text3)', fontSize:11, fontFamily:'IBM Plex Sans Condensed',
          padding:'6px 12px', cursor:'pointer', marginBottom:16 }}>
          📊 Compare vs sector average
        </button>

        {sectorPopupOpen && (
          <div onClick={() => setSectorPopupOpen(false)} style={{
            position:'fixed', top:0, left:0, right:0, bottom:0, background:'rgba(0,0,0,0.6)',
            display:'flex', alignItems:'center', justifyContent:'center', zIndex:1000, padding:16 }}>
            <div onClick={(e) => e.stopPropagation()} style={{
              background:'var(--bg)', border:'1px solid var(--border)', borderRadius:8,
              padding:20, maxWidth:420, width:'100%' }}>
              <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:14 }}>
                <div style={{ fontSize:13, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                  color:'var(--text)' }}>Sector Comparison — {stock?.sector || 'N/A'}</div>
                <button onClick={() => setSectorPopupOpen(false)} style={{
                  background:'none', border:'none', color:'var(--text4)', fontSize:18, cursor:'pointer' }}>✕</button>
              </div>
              {sectorAvgLoading ? (
                <div style={{ fontSize:12, color:'var(--text4)', textAlign:'center', padding:20 }}>Loading...</div>
              ) : sectorAvgData?.averages?.length ? (
                <div>
                  {sectorAvgData.averages.map((g: any, i: number) => (
                    <div key={i}>
                      <div style={{ fontSize:10, color:'var(--text4)', marginBottom:8 }}>
                        Based on {g.universeCount ?? g.stockCount} stocks in this sector, {sectorAvgData.continent.replace('_',' ')}
                      </div>
                      {[
                        { label: 'Value Score', stockVal: stock?.valueScore, avgVal: g.avgValueScore },
                        { label: 'Growth Score', stockVal: stock?.growthScore, avgVal: g.avgGrowthScore },
                        { label: 'Best Score', stockVal: stock?.combinedRank, avgVal: g.avgCombinedRank },
                      ].map(({ label, stockVal, avgVal }) => (
                        <div key={label} style={{ display:'flex', justifyContent:'space-between',
                          alignItems:'center', padding:'8px 0', borderBottom:'1px solid var(--border)' }}>
                          <span style={{ fontSize:11, color:'var(--text3)' }}>{label}</span>
                          <span style={{ fontSize:13, fontFamily:'IBM Plex Mono' }}>
                            <strong style={{ color:'var(--orange)' }}>{fn(stockVal)}</strong>
                            <span style={{ color:'var(--text4)', margin:'0 6px' }}>vs</span>
                            <span style={{ color:'var(--text3)' }}>{avgVal ?? '-'}</span>
                          </span>
                        </div>
                      ))}
                    </div>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize:12, color:'var(--text4)', textAlign:'center', padding:20 }}>
                  No sector data available.
                </div>
              )}
            </div>
          </div>
        )}

        <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
          borderRadius:4, padding:16, marginBottom:16 }}>
          <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between',
            marginBottom:12, flexWrap:'wrap', gap:8 }}>
            <div style={{ fontSize:10, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
              letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--orange)' }}>
              Price Chart · MA50 · MA200
            </div>
            <div style={{ display:'flex', gap:4 }}>
              {([['1W',7],['1M',30],['6M',182],['1Y',252],['3Y',756],['5Y',1260]] as [string,number][]).map(([lbl,d]) => (
                <button key={lbl} onClick={() => setChartDays(d)}
                  style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                    fontSize:11, padding:'4px 12px', borderRadius:2, cursor:'pointer',
                    border:`1px solid ${chartDays===d?'var(--orange)':'var(--border)'}`,
                    background: chartDays===d?'var(--orange)':'transparent',
                    color: chartDays===d?'#fff':'var(--text4)' }}>
                  {lbl}
                </button>
              ))}
            </div>
          </div>
          {loadingChart ? (
            <div style={{ height:280, display:'flex', alignItems:'center',
              justifyContent:'center', color:'var(--text4)', fontSize:13 }}>
              Loading chart…
            </div>
          ) : (
            <PriceChart history={history} days={chartDays} momentum={momentum} />
          )}
          <div style={{ display:'flex', gap:16, marginTop:8, fontSize:10,
            fontFamily:'IBM Plex Mono', color:'var(--text4)' }}>
            <span>―― Price</span>
            <span style={{ color:'#f59e0b' }}>- - MA50</span>
            <span style={{ color:'#8b5cf6' }}>- - - MA200</span>
          </div>
        </div>

        <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:8, marginBottom:16 }}>
          {metrics.map(({ label, val, color }) => (
            <div key={label} style={{ background:'var(--surface)', border:'1px solid var(--border)',
              borderRadius:3, padding:'8px 12px' }}>
              <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                letterSpacing:'0.1em', textTransform:'uppercase', color:'var(--text4)',
                marginBottom:3 }}>{label}</div>
              <div style={{ fontFamily:'IBM Plex Mono', fontWeight:600, fontSize:15, color }}>
                {val}
              </div>
            </div>
          ))}
        </div>

        <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
          borderRadius:4, padding:16 }}>
          <div style={{ fontSize:10, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
            letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--orange)',
            marginBottom:12 }}>
            Add to My Screen
          </div>
          <WatchlistButton stock={stock as any} userId={user?.id ?? null} />
        </div>

        {(() => {
          const researchSlug = RESEARCH_INDEX[`${ticker}.${exchangeCode}`] || null
          const exch = (stock as any).exchange as string
          const tk = (stock as any).ticker as string
          // Un solo link "borsa locale" per tutti i mercati — per i 5 mercati
          // asiatici usa il link specifico (Kabutan/HKEX/ASX/SGX/Naver),
          // altrove usa getBorseUrl come prima. Mai due bottoni per la stessa cosa.
          let asiaListing: string | null = null
          if (exch === 'TSE') {
            asiaListing = `https://kabutan.jp/stock/?code=${tk}`
          } else if (exch === 'SEHK') {
            const noZeros = tk.replace(/^0+/, '')
            asiaListing = `https://www.hkex.com.hk/Market-Data/Securities-Prices/Equities/Equities-Quote?sym=${noZeros}&sc_lang=en`
          } else if (exch === 'ASX') {
            asiaListing = `https://www.asx.com.au/markets/company/${tk}`
          } else if (exch === 'SGX') {
            asiaListing = `https://investors.sgx.com/market/security-details/stocks/${tk}?from=/market/securities`
          } else if (exch === 'KRX') {
            const noA = tk.replace(/^A/, '')
            asiaListing = `https://finance.naver.com/item/main.naver?code=${noA}`
          } else if (exch === 'GCC') {
            const pex = (stock as any).primaryExchange as string
            if (pex === 'DFM') {
              asiaListing = `https://www.dfm.ae/the-exchange/market-information/company/${tk}/trading`
            } else if (pex === 'ADX') {
              asiaListing = `https://www.adx.ae/en/main-market/company-profile/overview?symbols=${tk}&secCode=${tk}`
            } else if (pex === 'DSM') {
              asiaListing = `https://www.qe.com.qa/web/guest/company-profile?InformationCategory=Company&InformationType=News&FromLocalSite=N&MoreNewsTitle=1&CompanyCode=${tk}`
            } else if (pex === 'MSM') {
              asiaListing = `https://www.msx.om/snapshot.aspx?s=${tk}`
            } else if (pex === 'BAX') {
              asiaListing = `https://bahrainbourse.com/en/companyprofile?CompanyNameSymbol=${tk}`
            } else if (pex === 'SASE') {
              // Pattern confermato: il blob prima di "?companySymbol=" e'
              // fisso (stato di navigazione del portale), il ticker e' un
              // parametro pulito alla fine. Il portale WebSphere di Tadawul
              // a volte non risponde bene ai link diretti (comune per
              // questi sistemi) — non e' un problema del pattern in se'.
              asiaListing = `https://www.saudiexchange.sa/wps/portal/saudiexchange/hidden/company-profile-main/!ut/p/z1/04_Sj9CPykssy0xPLMnMz0vMAfIjo8ziTR3NDIw8LAz83d2MXA0C3SydAl1c3Q0NvE30I4EKzBEKDMKcTQzMDPxN3H19LAzdTU31w8syU8v1wwkpK8hOMgUA-oskdg!!/?companySymbol=${tk}`
            } else if (pex === 'KWSE') {
              // Confermato: nessun pattern trovabile — Boursa Kuwait usa un
              // ID interno arbitrario (verificato su due esempi, 635 e 402,
              // senza relazione con il ticker). Resta il link generico.
              // Boursa Kuwait usa un ID numerico interno, non il ticker —
              // non ancora mappato, link alla borsa in generale.
              asiaListing = 'https://www.boursakuwait.com.kw/'
            }
          }
          const borseUrl = asiaListing || getBorseUrl(ticker, exchangeCode, (stock as any).isin || null, (stock as any).primaryExchange || undefined)
          const companyUrl = (stock as any).website || null
          // Niente early-return qui: le News funzionano per qualsiasi titolo
          // (query Google News costruita da ticker/company, nessun dato
          // opzionale richiesto) — la sezione deve comparire sempre, i
          // singoli pulsanti restano condizionati ai propri dati.
          return (
            <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
              borderRadius:4, padding:'14px 20px', display:'flex', alignItems:'center',
              justifyContent:'space-between', flexWrap:'wrap', gap:12 }}>
              <div>
                <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                  letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--text4)',
                  marginBottom:6 }}>Official Links</div>

              </div>
              <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
                {borseUrl && <a href={borseUrl} target="_blank" rel="noopener noreferrer" style={{ background:'var(--surface2)', color:'var(--text2)', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:12, padding:'7px 14px', borderRadius:3, border:'1px solid var(--border)', textDecoration:'none', display:'inline-flex', alignItems:'center', gap:6 }}>📊 Official Listing ↗</a>}
                {companyUrl && <a href={companyUrl} target="_blank" rel="noopener noreferrer" style={{ background:'var(--orange)', color:'#fff', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:12, padding:'7px 14px', borderRadius:3, textDecoration:'none', display:'inline-flex', alignItems:'center', gap:6 }}>🌐 Company Website ↗</a>}
                {researchSlug && <a href={`/research/${researchSlug}`} style={{ background:'#f97316', color:'#fff', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:12, padding:'7px 14px', borderRadius:3, textDecoration:'none', display:'inline-flex', alignItems:'center', gap:6 }}>📋 Read Analysis ↗</a>}
                {(stock as any).sector && <button onClick={() => { window.location.href = `/?page=${['TSE','SEHK','ASX','SGX','KRX'].includes((stock as any).exchange) ? 'asiapacific' : (stock as any).exchange === 'TSX' ? 'nascreen' : (stock as any).exchange === 'US' ? 'nascreen' : 'screener'}&sector=${encodeURIComponent((stock as any).sector)}` }} style={{ background:'var(--surface2)', color:'var(--text3)', fontFamily:'IBM Plex Sans Condensed', fontSize:11, fontWeight:700, padding:'6px 12px', borderRadius:3, border:'1px solid var(--border)', cursor:'pointer' }}>🏭 {(stock as any).sector}</button>}
                <a href={`https://news.google.com/search?q=${(stock as any).exchange === 'US' ? encodeURIComponent(((stock as any).yahooTicker || ticker) + ' ' + (((stock as any).company || '').split(' ').slice(0,2).join(' ')) + ' stock') : encodeURIComponent(((stock as any).company || ticker).split(' ').slice(0,2).join(' '))}&hl=en&gl=${(stock as any).exchange === 'US' ? 'US' : 'GB'}&ceid=${(stock as any).exchange === 'US' ? 'US' : 'GB'}:en`} target="_blank" rel="noopener noreferrer" style={{ background:'#1a73e8', color:'#fff', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:12, padding:'7px 14px', borderRadius:3, textDecoration:'none', display:'inline-flex', alignItems:'center', gap:6 }}>📰 News ↗</a>
                {(stock as any).yahooTicker && <a href={`https://finance.yahoo.com/quote/${(stock as any).yahooTicker}/analysis/?p=${(stock as any).yahooTicker}`} target="_blank" rel="noopener noreferrer" style={{ background:'#6b21a8', color:'#fff', fontFamily:'IBM Plex Sans Condensed', fontSize:11, fontWeight:700, padding:'6px 12px', borderRadius:3, textDecoration:'none' }}>📊 Estimates</a>}
              </div>
            </div>
          )
        })()}

        {(stock as any).yahooTicker && (
          <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
            borderRadius:4, padding:'16px 20px', marginBottom:12 }}>
            <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
              letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--text4)', marginBottom:8 }}>
              About the Company
            </div>
            <div style={{ fontSize:12, color:'var(--text3)', lineHeight:1.6, marginBottom:10 }}>
              Full business description and company profile available on Yahoo Finance.
            </div>
            <a href={`https://finance.yahoo.com/quote/${(stock as any).yahooTicker}/profile?hl=en-US&guccounter=1`}
              target="_blank" rel="noopener noreferrer"
              style={{ background:'#6b21a8', color:'#fff', fontFamily:'IBM Plex Sans Condensed',
                fontWeight:700, fontSize:12, padding:'7px 14px', borderRadius:3,
                textDecoration:'none', display:'inline-flex', alignItems:'center', gap:6 }}>
              📄 View Company Profile on Yahoo Finance ↗
            </a>
          </div>
        )}

        {(stock as any).exchange === 'US' && (stock as any).ke != null && (
          user?.id ? (
            <ReverseDCFSection key={`${(stock as any).ticker}-${(stock as any).exchange}`} stock={stock as any} />
          ) : (
            <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
              borderRadius:4, padding:'24px 20px', marginBottom:12, textAlign:'center' }}>
              <div style={{ fontSize:28, marginBottom:8 }}>🔒</div>
              <div style={{ fontSize:12, fontWeight:700, color:'var(--text2)', marginBottom:4 }}>
                Reverse Earnings Model
              </div>
              <div style={{ fontSize:11, color:'var(--text4)' }}>
                Log in to view implied growth, EPS forward estimates, and the interactive valuation calculator.
              </div>
            </div>
          )
        )}

        <div style={{ marginTop:16, fontSize:10, color:'var(--text4)',
          textAlign:'center', paddingTop:12, borderTop:'1px solid var(--border)' }}>
          ⚠️ Data for informational purposes only · Not investment advice ·
          Andrea Meschini · Verona, Italy · andrea@forwardalpha.pro
        </div>
      </div>
    </div>
  )
}

function ReverseDCFSection({ stock }: { stock: any }) {
  const price   = stock.price
  const peFwd   = stock.peFwd
  const ke      = stock.ke
  const impliedG = stock.impliedGrowth10y
  const epsCagr2y = stock.epsCagr2y
  const growth1224 = stock.epsGrowth1224m
  const growth2436 = stock.epsGrowth2436m
  const epsNtm = stock.epsNtmDcf ?? ((price != null && peFwd) ? price / peFwd : null)

  const G_TERMINAL = 0.025
  const YEARS = 10

  // Stesso DCF a due stadi usato lato server (bisection), qui usato in
  // avanti: dato un tasso di crescita, calcola il prezzo implicito.
  function priceForGrowth(g: number): number | null {
    if (epsNtm == null || ke == null || ke <= G_TERMINAL) return null
    let pv = 0
    for (let t = 1; t <= YEARS; t++) {
      pv += epsNtm * Math.pow(1 + g, t) / Math.pow(1 + ke, t)
    }
    const epsTerminal = epsNtm * Math.pow(1 + g, YEARS)
    const tv = epsTerminal * (1 + G_TERMINAL) / (ke - G_TERMINAL)
    pv += tv / Math.pow(1 + ke, YEARS)
    return pv
  }

  const [growthInput, setGrowthInput] = useState(
    impliedG != null ? Math.round(impliedG * 1000) / 10 : 10
  )
  const simulatedPrice = priceForGrowth(growthInput / 100)

  const fmtPct = (v: number | null) => v == null ? '—' : `${(v * 100).toFixed(1)}%`
  const fmtPrice = (v: number | null) => v == null ? '—' : v.toFixed(2)

  return (
    <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
      borderRadius:4, padding:'16px 20px', marginBottom:12 }}>
      <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
        letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--text4)', marginBottom:10 }}>
        Reverse Earnings Model
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:10, marginBottom:14 }}>
        <div>
          <div style={{ fontSize:9, color:'var(--text4)', textTransform:'uppercase' }}>Implied Growth (10y)</div>
          <div style={{ fontSize:16, fontWeight:700, color:'var(--text1)' }}>{fmtPct(impliedG)}</div>
        </div>
        <div>
          <div style={{ fontSize:9, color:'var(--text4)', textTransform:'uppercase' }}>EPS CAGR (12-36m)</div>
          <div style={{ fontSize:16, fontWeight:700, color:'var(--text1)' }}>{fmtPct(epsCagr2y)}</div>
        </div>
        <div>
          <div style={{ fontSize:9, color:'var(--text4)', textTransform:'uppercase' }}>EPS Growth 12-24m</div>
          <div style={{ fontSize:13, color:'var(--text2)' }}>{fmtPct(growth1224)}</div>
        </div>
        <div>
          <div style={{ fontSize:9, color:'var(--text4)', textTransform:'uppercase' }}>EPS Growth 24-36m</div>
          <div style={{ fontSize:13, color:'var(--text2)' }}>{fmtPct(growth2436)}</div>
        </div>
      </div>

      <div style={{ fontSize:11, color:'var(--text3)', lineHeight:1.6, marginBottom:12 }}>
        The model calculates implied growth by comparing the current price, forward EPS,
        and cost of equity (Ke = risk-free rate + Beta × 5%). If implied growth is much
        higher than the EPS growth expected by analysts, the market is pricing in
        expectations above current estimates — and vice versa.
      </div>

      <div style={{ borderTop:'1px solid var(--border)', paddingTop:12 }}>
        <div style={{ fontSize:10, color:'var(--text4)', marginBottom:6 }}>
          Simulate: if 10-year growth were...
        </div>
        <div style={{ display:'flex', alignItems:'center', gap:10, marginBottom:8 }}>
          <input type="range" min={-20} max={40} step={0.5} value={growthInput}
            onChange={e => setGrowthInput(parseFloat(e.target.value))}
            style={{ flex:1 }} />
          <input type="number" value={growthInput} step={0.5}
            onChange={e => setGrowthInput(parseFloat(e.target.value) || 0)}
            style={{ width:64, fontSize:12, padding:'4px 6px', background:'var(--bg)',
              border:'1px solid var(--border)', borderRadius:3, color:'var(--text1)' }} />
          <span style={{ fontSize:12, color:'var(--text3)' }}>%</span>
        </div>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center' }}>
          <span style={{ fontSize:11, color:'var(--text4)' }}>...the fair price would be:</span>
          <span style={{ fontSize:18, fontWeight:700, color:'var(--orange)' }}>
            {stock.exchange === 'US' ? '$' : ''}{fmtPrice(simulatedPrice)}
          </span>
        </div>
        {price != null && simulatedPrice != null && (
          <div style={{ fontSize:11, color:'var(--text4)', marginTop:4, textAlign:'right' }}>
            vs current price {price.toFixed(2)} ({simulatedPrice > price ? '+' : ''}
            {((simulatedPrice / price - 1) * 100).toFixed(1)}%)
          </div>
        )}
      </div>
    </div>
  )
}

// Wrapper con key={id}: forza React a smontare e rimontare da zero l'intero
// componente quando cambia il ticker, cosi' nessuno stato (es. il "from"
// per il tasto Back) puo' restare "incollato" dalla pagina del titolo
// precedente — era questa la causa del bug NA/EU/APAC segnalato.
export default function StockPage() {
  const params = useParams()
  const id = (params?.id as string) || ''
  return <StockPageInner key={id} />
}
