'use client'

import { useState, useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import { useParams, useRouter } from 'next/navigation'
import { ArrowLeft } from 'lucide-react'
import { computeScores } from '@/lib/ranking'
import { RESEARCH_INDEX } from '@/lib/researchIndex'
import { DEMO_STOCKS } from '@/lib/demoData'

const MIC: Record<string, string> = { PA:'XPAR', AS:'XAMS', BR:'XBRU', LS:'XLIS', MIL:'XMIL', IR:'XDUB', OB:'XOSL' }

function getBorseUrl(ticker: string, exchange: string, isin: string | null, primaryExchange?: string): string | null {
  if (['PA','AS','BR','LS','MIL','IR'].includes(exchange) && isin) return `https://live.euronext.com/en/product/equities/${isin}-${MIC[exchange]}`
  if (exchange === 'OB' && isin) return `https://live.euronext.com/nb/product/equities/${isin}-XOSL`
  if (exchange === 'XETRA' && isin) return `https://www.boerse-frankfurt.de/equity/${isin}`
  if (exchange === 'MC' && isin) return `https://www.bolsamadrid.es/esp/aspx/Empresas/FichaValor.aspx?ISIN=${isin}`
  if (['LSE','AIM'].includes(exchange)) return `https://www.londonstockexchange.com/stock/${ticker}/company-page`
  if (['OM','HE','CPSE','NGM'].includes(exchange)) return `https://www.nasdaq.com/european-market-activity/shares/${ticker.toLowerCase()}`
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

// ── PRICE CHART WITH MOVING AVERAGES ──────────────────────────────
function PriceChart({ history, days, momentum }: { history: any[]; days: number; momentum?: any }) {
  const data = history
    .map((d: any) => ({
      date:  d.date || d.Date || '',
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

  // Moving averages
  function ma(n: number): (number | null)[] {
    return closes.map((_, i) => {
      if (i < n - 1) return null
      const slice = closes.slice(i - n + 1, i + 1)
      return slice.reduce((a, b) => a + b, 0) / n
    })
  }

  const ma50  = ma(Math.min(50,  data.length))
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
  // Performance calcolata sul periodo selezionato (prezzi adjusted close)
  const _fb = ((closes[closes.length-1]/closes[0]-1)*100).toFixed(2)
  const _pct = (v: number | null) => v != null ? Number(v).toFixed(2) : null
  const perf = momentum
    ? (days <= 10  ? (_pct(momentum.mom1w)  ?? _fb)
    : days <= 40   ? (_pct(momentum.mom1m)  ?? _fb)
    : days <= 200  ? (_pct(momentum.mom6m)  ?? _fb)
    : days <= 400  ? (_pct(momentum.mom12m) ?? _fb)
    : days <= 1000 ? (_pct(momentum.mom3y)  ?? _fb)
    :                (_pct(momentum.mom5y)  ?? _fb))
    : _fb

  // Y axis labels
  const yLabels = [0, 0.25, 0.5, 0.75, 1].map(r => ({
    val: (maxP - r * range).toFixed(2),
    y: PY + r * (H - 2 * PY)
  }))

  // X axis labels (dates)
  const xLabels = [0, 0.25, 0.5, 0.75, 1].map(r => {
    const idx = Math.min(Math.round(r * (data.length - 1)), data.length - 1)
    return { label: data[idx]?.date?.slice(0, 7) || '', x: toX(idx) }
  })

  // Last MA values for legend
  const lastMa50  = ma50.filter(v => v != null).pop()
  const lastMa200 = ma200.filter(v => v != null).pop()

  return (
    <div style={{ position:'relative', background:'var(--bg2)', borderRadius:3, padding:'12px 0 4px' }}>
      {/* Performance badge */}
      <div style={{ position:'absolute', top:12, right:16,
        fontFamily:'IBM Plex Mono', fontSize:15, fontWeight:700,
        color: isUp ? 'var(--green)' : 'var(--red)',
        background:'var(--bg2)', padding:'2px 10px', borderRadius:2,
        border:`1px solid ${isUp ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}` }}>
        {isUp ? '▲' : '▼'} {parseFloat(perf) > 0 ? '+' : ''}{perf}%
      </div>

      {/* Legend */}
      <div style={{ display:'flex', gap:16, paddingLeft:PX, marginBottom:8 }}>
        <span style={{ fontSize:10, fontFamily:'IBM Plex Sans Condensed', color:'var(--text3)' }}>
          Price
        </span>
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

        {/* Grid */}
        {yLabels.map(({ y }) => (
          <line key={y} x1={PX} y1={y} x2={W - 4} y2={y}
            stroke="rgba(30,45,69,0.7)" strokeWidth="1" strokeDasharray="3,4" />
        ))}

        {/* Y labels */}
        {yLabels.map(({ val, y }) => (
          <text key={val} x={PX - 4} y={y + 4} textAnchor="end" fill="var(--text4)"
            style={{ fontSize:9, fontFamily:'IBM Plex Mono' }}>{val}</text>
        ))}

        {/* X labels */}
        {xLabels.map(({ label, x }) => (
          <text key={label} x={x} y={H - 4} textAnchor="middle" fill="var(--text4)"
            style={{ fontSize:9, fontFamily:'IBM Plex Mono' }}>{label}</text>
        ))}

        {/* Area fill */}
        <polygon
          points={`${PX},${H - PY} ${pricePoints} ${W - PX},${H - PY}`}
          fill="url(#priceFill)" />

        {/* Price line */}
        <polyline points={pricePoints} fill="none" stroke={c}
          strokeWidth="1.5" strokeLinejoin="round" />

        {/* MA50 */}
        {lastMa50 && (
          <path d={maPath(ma50)} fill="none" stroke="#f59e0b"
            strokeWidth="1.2" strokeDasharray="4,2" />
        )}

        {/* MA200 */}
        {lastMa200 && data.length >= 100 && (
          <path d={maPath(ma200)} fill="none" stroke="#8b5cf6"
            strokeWidth="1.2" strokeDasharray="6,3" />
        )}

        {/* Last price dot */}
        <circle cx={toX(data.length - 1)} cy={toY(closes[closes.length - 1])}
          r="3.5" fill={c} stroke="var(--bg2)" strokeWidth="1.5" />
      </svg>
    </div>
  )
}

// ── MAIN PAGE ─────────────────────────────────────────────────────
export default function StockPage() {
  const params  = useParams()
  const router  = useRouter()
  const id      = (params?.id as string) || ''
  const [ticker, exchangeCode] = id.split('-')

  const [stock, setStock] = useState<any>(null)
  const [loadingStock, setLoadingStock] = useState(true)

  useEffect(() => {
    if (!ticker || !exchangeCode) return
    // Prova prima dal DB
    fetch(`/api/db/stocks?ticker=${ticker}&exchange=${exchangeCode}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        if (d?.stocks?.[0]) {
          setStock(d.stocks[0])
        } else {
          // Fallback a demo
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
  }, [ticker, exchangeCode])

  const [chartDays, setChartDays]   = useState(252)
  const [history,   setHistory]     = useState<any[]>([])
  const [momentum, setMomentum] = useState<any>(null)
  const [loadingChart, setLoading]  = useState(true)
  const [qty,   setQty]   = useState('')
  const [px,    setPx]    = useState(stock?.price?.toFixed(2) || '')
  const [pf,    setPf]    = useState('Portfolio 1')
  const [added, setAdded] = useState(false)
  const [user, setUser] = useState<any>(null)
  useEffect(() => { supabase.auth.getUser().then(({ data }) => setUser(data.user ?? null)) }, [])

  useEffect(() => {
    if (!ticker || !exchangeCode) return
    setLoading(true)
    fetch(`/api/db/history?ticker=${ticker}&exchange=${exchangeCode}&days=${Math.max(chartDays + 50, 1800)}&t=${Date.now()}`, { cache: 'no-store' })
      .then(r => r.ok ? r.json() : { history: [] })
      .then(d => { setHistory(d.history || []); setMomentum(d.momentum || null); setLoading(false) })
      .catch(() => setLoading(false))
  }, [ticker, exchangeCode, chartDays])

  function handleAdd() {
    if (!stock || !qty || !px) return
    const stored = JSON.parse(localStorage.getItem('portfolios') || '{}')
    if (!stored[pf]) stored[pf] = []
    stored[pf].push({
      ticker: stock.ticker, exchange: stock.exchange,
      company: stock.company, flag: stock.flag,
      sector: stock.sector, country: stock.country,
      qty: parseFloat(qty), buy_price: parseFloat(px),
      added_at: new Date().toISOString(),
    })
    localStorage.setItem('portfolios', JSON.stringify(stored))
    setAdded(true)
    setTimeout(() => setAdded(false), 2000)
  }

  if (!stock) {
    return (
      <div style={{ background:'var(--bg)', minHeight:'100vh', color:'var(--text)',
        fontFamily:'IBM Plex Sans, sans-serif', padding:40 }}>
        <style>{`@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap');`}</style>
        <button onClick={() => router.back()}
          style={{ display:'flex', alignItems:'center', gap:8, color:'var(--orange)',
            background:'none', border:'none', cursor:'pointer', fontSize:14, marginBottom:24 }}>
          <ArrowLeft size={16} /> Back
        </button>
        <p style={{ color:'var(--text3)' }}>Stock not found: {ticker}.{exchangeCode}</p>
      </div>
    )
  }

  const s = stock as any
  const metrics = [
    { label:'Price',         val: fv(stock.price, 2),    color: 'var(--text)' },
    { label:'Mkt Cap $B',    val: stock.mktCap ? fv(stock.mktCap, 1) : '—', color: 'var(--text)' },
    { label:'PE LTM Rank',   val: s.rankPeLtm != null ? String(Math.round(s.rankPeLtm)) : '—', color: s.rankPeLtm >= 70 ? 'var(--green)' : s.rankPeLtm <= 30 ? '#e84560' : '#f59e0b' },
    { label:'PE NTM Rank',   val: s.rankPeNtm != null ? String(Math.round(s.rankPeNtm)) : '—', color: s.rankPeNtm >= 70 ? 'var(--green)' : s.rankPeNtm <= 30 ? '#e84560' : '#f59e0b' },
    { label:'PB Rank',       val: s.rankPb    != null ? String(Math.round(s.rankPb))    : '—', color: s.rankPb    >= 70 ? 'var(--green)' : s.rankPb    <= 30 ? '#e84560' : '#f59e0b' },
    { label:'EPS Gr Rank',   val: s.rankEpsGr != null ? String(Math.round(s.rankEpsGr)) : '—', color: s.rankEpsGr >= 70 ? 'var(--green)' : s.rankEpsGr <= 30 ? '#e84560' : '#f59e0b' },
    { label:'Rev Gr Rank',   val: s.rankRevGr != null ? String(Math.round(s.rankRevGr)) : '—', color: s.rankRevGr >= 70 ? 'var(--green)' : s.rankRevGr <= 30 ? '#e84560' : '#f59e0b' },
    { label:'Mom 1 Week',    val: stock.mom1w  != null ? fp(stock.mom1w  * 100, 1) : '—', color: clr(stock.mom1w) },
    { label:'Mom 1 Month',   val: stock.mom1m  != null ? fp(stock.mom1m  * 100, 1) : '—', color: clr(stock.mom1m) },
    { label:'Mom 6 Months',  val: stock.mom6m  != null ? fp(stock.mom6m  * 100, 1) : '—', color: clr(stock.mom6m) },
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

      {/* Top nav */}
      <div style={{ background:'var(--surface)', borderBottom:'2px solid var(--orange)',
        padding:'0 24px', height:44, display:'flex', alignItems:'center', gap:16 }}>
        <button onClick={() => router.back()}
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

        {/* Stock header */}
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
               ['SWX'].includes(stock.exchange) ? 'CHF' :
               ['OM','NGM'].includes(stock.exchange) ? 'kr' :
               ['OB'].includes(stock.exchange) ? 'kr' :
               ['CPSE'].includes(stock.exchange) ? 'kr' :
               stock.exchange === 'US' ? 'USD' : stock.exchange === 'SWX' ? 'CHF' : stock.exchange === 'LSE' ? 'GBp' : '€'}{fv(stock.price, 2)}
              </span>
              <span style={{ fontSize:18, fontFamily:'IBM Plex Mono', fontWeight:600,
                color: (stock.change1d ?? 0) >= 0 ? 'var(--green)' : 'var(--red)' }}>
                {stock.change1d != null ? fp(stock.change1d, 2) : ''}
              </span>

            </div>
            <div style={{ fontSize:14, color:'var(--text3)', marginTop:4 }}>
              {stock.company}
            </div>
            <div style={{ fontSize:12, color:'var(--text4)', marginTop:2 }}>
              {stock.exchange} · {stock.sector} · {stock.country}
            </div>
 {history.length > 0 && (
 <div style={{ fontSize:11, color:'var(--text4)', marginTop:4 }}>
 Last price: {stock.last_price_date || history[history.length - 1]?.date || '-'}
 </div>
 )}
          </div>
          {/* Scores */}
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

        {/* Chart */}
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

        {/* Metrics grid */}
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

        {/* Add to portfolio */}
        <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
          borderRadius:4, padding:16 }}>
          <div style={{ fontSize:10, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
            letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--orange)',
            marginBottom:12 }}>
            Add to Portfolio
          </div>
          <div style={{ display:'flex', alignItems:'flex-end', gap:10, flexWrap:'wrap' }}>
            <div>
              <div style={{ fontSize:10, color:'var(--text4)', marginBottom:4,
                fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                textTransform:'uppercase' }}>Portfolio</div>
              <select value={pf} onChange={e => setPf(e.target.value)}
                className="input-field" style={{ width:140 }}>
                {['Portfolio 1','Portfolio 2','Portfolio 3'].map(p => <option key={p}>{p}</option>)}
              </select>
            </div>
            <div>
              <div style={{ fontSize:10, color:'var(--text4)', marginBottom:4,
                fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                textTransform:'uppercase' }}>Quantity</div>
              <input type="number" placeholder="100" value={qty}
                onChange={e => setQty(e.target.value)}
                className="input-field" style={{ width:90 }} />
            </div>
            <div>
              <div style={{ fontSize:10, color:'var(--text4)', marginBottom:4,
                fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                textTransform:'uppercase' }}>Buy Price</div>
              <input type="number" value={px}
                onChange={e => setPx(e.target.value)}
                className="input-field" style={{ width:100 }} />
            </div>
            <button onClick={handleAdd} disabled={!qty || !px || added}
              className="btn-primary">
              {added ? '✅ Added' : '+ Add to Portfolio'}
            </button>
          </div>
          {added && (
            <div style={{ marginTop:8, fontSize:12, color:'var(--green)' }}>
              ✅ {stock.ticker} added to {pf}
            </div>
          )}
        </div>

        {/* Official links */}
        {(() => {
          const researchSlug = RESEARCH_INDEX[`${ticker}.${exchangeCode}`] || null
          const borseUrl = getBorseUrl(ticker, exchangeCode, (stock as any).isin || null, (stock as any).primary_exchange || undefined)
          const companyUrl = (stock as any).website || null
          if (!borseUrl && !companyUrl && !researchSlug) return null
          return (
            <div style={{ background:'var(--surface)', border:'1px solid var(--border)',
              borderRadius:4, padding:'14px 20px', display:'flex', alignItems:'center',
              justifyContent:'space-between', flexWrap:'wrap', gap:12 }}>
              <div>
                <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                  letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--text4)',
                  marginBottom:6 }}>Official Links</div>
                <div style={{ fontSize:12, color:'var(--text3)', fontFamily:'IBM Plex Mono' }}>
                  ISIN: {(stock as any).isin || "N/A"}
                </div>
              </div>
              <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
                {borseUrl && <a href={borseUrl} target="_blank" rel="noopener noreferrer" style={{ background:'var(--surface2)', color:'var(--text2)', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:12, padding:'7px 14px', borderRadius:3, border:'1px solid var(--border)', textDecoration:'none', display:'inline-flex', alignItems:'center', gap:6 }}>📊 Official Listing ↗</a>}
                {companyUrl && <a href={companyUrl} target="_blank" rel="noopener noreferrer" style={{ background:'var(--orange)', color:'#fff', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:12, padding:'7px 14px', borderRadius:3, textDecoration:'none', display:'inline-flex', alignItems:'center', gap:6 }}>🌐 Company Website ↗</a>}
                {researchSlug && <a href={`/research/${researchSlug}`} style={{ background:'#f97316', color:'#fff', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:12, padding:'7px 14px', borderRadius:3, textDecoration:'none', display:'inline-flex', alignItems:'center', gap:6 }}>📋 Read Analysis ↗</a>}
                <a href={`https://news.google.com/search?q=${encodeURIComponent((stock as any).company || ticker)}+${encodeURIComponent(ticker)}${(stock as any).isin ? '+'+encodeURIComponent((stock as any).isin) : ''}&hl=en&gl=US&ceid=US:en`} target="_blank" rel="noopener noreferrer" style={{ background:'#1a73e8', color:'#fff', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:12, padding:'7px 14px', borderRadius:3, textDecoration:'none', display:'inline-flex', alignItems:'center', gap:6 }}>📰 News ↗</a>
              </div>
            </div>
          )
        })()}

        {/* Disclaimer */}
        <div style={{ marginTop:16, fontSize:10, color:'var(--text4)',
          textAlign:'center', paddingTop:12, borderTop:'1px solid var(--border)' }}>
          ⚠️ Data for informational purposes only · Not investment advice ·
          Andrea Meschini · Verona, Italy · andrea@forwardalpha.pro
        </div>
      </div>
    </div>
  )
}
