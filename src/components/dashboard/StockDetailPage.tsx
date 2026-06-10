'use client'

import { useState, useEffect } from 'react'
import { X, ArrowLeft } from 'lucide-react'
import { Stock } from '@/lib/ranking'

function fp(v?: number | null, d = 2): string {
  if (v == null || isNaN(v as number)) return '—'
  return `${(v as number) >= 0 ? '+' : ''}${(v as number).toFixed(d)}%`
}
function fpPct(v?: number | null, d = 1): string {
  if (v == null || isNaN(v as number)) return '—'
  const pct = (v as number) * 100
  return `${pct >= 0 ? '+' : ''}${pct.toFixed(d)}%`
}
function fv(v?: number | null, d = 2): string {
  if (v == null || isNaN(v as number)) return '—'
  return (v as number).toFixed(d)
}
function fn(v?: number | null): string {
  if (v == null || isNaN(v as number)) return '—'
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

// Simple SVG price chart
function PriceChart({ history }: { history: any[] }) {
  const prices = history
    .map((d: any) => parseFloat(d.adj_close || d.adjusted_close || d.close || '0'))
    .filter(v => !isNaN(v) && v > 0)

  if (prices.length < 2) return (
    <div style={{ height:200, display:'flex', alignItems:'center', justifyContent:'center', color:'var(--text3)', fontSize:13 }}>
      No chart data available
    </div>
  )

  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const range = max - min || 1
  const W = 800, H = 180, PX = 40, PY = 16

  const pts = prices.map((p, i) => {
    const x = PX + (i / (prices.length - 1)) * (W - 2 * PX)
    const y = PY + ((max - p) / range) * (H - 2 * PY)
    return `${x.toFixed(1)},${y.toFixed(1)}`
  }).join(' ')

  const isUp = prices[prices.length - 1] >= prices[0]
  const c = isUp ? 'var(--green)' : 'var(--red)'
  const perf = ((prices[prices.length - 1] / prices[0] - 1) * 100).toFixed(2)

  const yLabels = [max, (max + min) / 2, min].map((v, i) => ({
    val: v.toFixed(2), y: PY + (i / 2) * (H - 2 * PY)
  }))

  return (
    <div style={{ position:'relative', background:'var(--bg2)', borderRadius:3 }}>
      <div style={{ position:'absolute', top:8, right:12,
        fontFamily:'IBM Plex Mono', fontSize:14, fontWeight:700,
        color: isUp ? 'var(--green)' : 'var(--red)',
        background:'var(--bg2)', padding:'2px 8px', borderRadius:2,
        border:`1px solid ${isUp ? 'rgba(34,197,94,0.3)' : 'rgba(239,68,68,0.3)'}` }}>
        {isUp ? '▲' : '▼'} {isUp ? '+' : ''}{perf}%
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width:'100%', height:200 }}>
        <defs>
          <linearGradient id={`fill-${isUp}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={c} stopOpacity="0.2" />
            <stop offset="100%" stopColor={c} stopOpacity="0.01" />
          </linearGradient>
        </defs>
        {[0, 0.25, 0.5, 0.75, 1].map(r => (
          <line key={r} x1={PX} y1={PY + r*(H-2*PY)} x2={W-PX} y2={PY + r*(H-2*PY)}
            stroke="rgba(30,45,69,0.8)" strokeWidth="1" strokeDasharray="3,3" />
        ))}
        {yLabels.map(({ val, y }) => (
          <text key={val} x={PX-4} y={y+4} textAnchor="end" fill="var(--text4)"
            style={{ fontSize:9, fontFamily:'IBM Plex Mono' }}>{val}</text>
        ))}
        <polygon points={`${PX},${H-PY} ${pts} ${W-PX},${H-PY}`}
          fill={`url(#fill-${isUp})`} />
        <polyline points={pts} fill="none" stroke={c} strokeWidth="1.5"
          strokeLinejoin="round" strokeLinecap="round" />
        {(() => {
          const n = prices.length - 1
          const x = PX + (W - 2*PX)
          const y = PY + ((max - prices[n]) / range) * (H - 2*PY)
          return <circle cx={x} cy={y} r="3.5" fill={c} stroke="var(--bg2)" strokeWidth="1.5" />
        })()}
      </svg>
    </div>
  )
}

interface Props {
  stock: Stock
  onClose: () => void
  onAddPortfolio?: (stock: Stock, qty: number, price: number, pf: string) => void
}

export default function StockDetailPage({ stock, onClose, onAddPortfolio }: Props) {
  const [chartDays, setChartDays] = useState(365)
  const [history,   setHistory]   = useState<any[]>([])
  const [loadingChart, setLoadingChart] = useState(true)
  const [qty,   setQty]   = useState('')
  const [px,    setPx]    = useState(stock.price?.toFixed(2) || '')
  const [pf,    setPf]    = useState('Portfolio 1')
  const [added, setAdded] = useState(false)

  useEffect(() => {
    setLoadingChart(true)
    fetch(`/api/history?ticker=${stock.ticker}&exchange=${stock.exchange}&days=${chartDays}`)
      .then(r => r.ok ? r.json() : { history: [] })
      .then(d => { setHistory(d.history || []); setLoadingChart(false) })
      .catch(() => setLoadingChart(false))
  }, [stock.ticker, stock.exchange, chartDays])

  function handleAdd() {
    if (!qty || !px) return
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
    if (onAddPortfolio) onAddPortfolio(stock, parseFloat(qty), parseFloat(px), pf)
    setAdded(true)
    setTimeout(() => setAdded(false), 2000)
  }

  const chg = stock.change1d || 0

  const leftMetrics: [string, string, string][] = [
    ['Price',   (stock.exchange === 'SWX' ? 'CHF ' : stock.exchange === 'LSE' || stock.exchange === 'AIM' ? 'GBp ' : stock.exchange === 'OM' || stock.exchange === 'NGM' ? 'SEK ' : stock.exchange === 'OB' ? 'NOK ' : stock.exchange === 'CPSE' ? 'DKK ' : stock.exchange === 'US' ? 'USD ' : 'EUR ') + fv(stock.price, 2), ''],
    ['1D Change %',  fp(chg, 2),               chg >= 0 ? 'var(--green)' : 'var(--red)'],
    ['Mkt Cap $B',   fv(stock.mktCap, 2),      ''],
    ['PE LTM Rank',  fn((stock as any).rankPeLtm),  scoreClr((stock as any).rankPeLtm)],
    ['PE NTM Rank',  fn((stock as any).rankPeNtm),  scoreClr((stock as any).rankPeNtm)],
    ['PB Rank',      fn((stock as any).rankPb),      scoreClr((stock as any).rankPb)],
  ]

  const rightMetrics: [string, string, string][] = [
    ['EPS Gr Rank',    fn((stock as any).rankEpsGr),  scoreClr((stock as any).rankEpsGr)],
    ['Rev Gr Rank',    fn((stock as any).rankRevGr),  scoreClr((stock as any).rankRevGr)],
    ['Mom 1 Week %',   fpPct(stock.mom1w),      clr(stock.mom1w)],
    ['Mom 1 Month %',  fpPct(stock.mom1m),      clr(stock.mom1m)],
    ['Mom 6 Months %', fpPct(stock.mom6m),      clr(stock.mom6m)],
    ['Mom 12 Months %',fpPct(stock.mom12m),     clr(stock.mom12m)],
    ['Value Score',    fn(stock.valueScore),    scoreClr(stock.valueScore)],
    ['Growth Score',   fn(stock.growthScore),   scoreClr(stock.growthScore)],
    ['Sector',         stock.sector || '—',     ''],
    ['Country',        stock.country || '—',    ''],
  ]

  return (
    <div style={{
      position:'fixed', inset:0, background:'rgba(0,0,0,0.8)',
      backdropFilter:'blur(4px)', zIndex:100,
      display:'flex', alignItems:'center', justifyContent:'center', padding:16
    }}>
      <div style={{
        background:'var(--surface)', border:'1px solid var(--border2)',
        borderTop:`3px solid var(--orange)`, borderRadius:4,
        width:'100%', maxWidth:1000, maxHeight:'90vh',
        overflow:'auto', animation:'fadeUp 0.2s ease'
      }}>
        {/* Header */}
        <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between',
          padding:'12px 20px', borderBottom:'1px solid var(--border)',
          background:'var(--surface2)', position:'sticky', top:0, zIndex:10 }}>
          <div style={{ display:'flex', alignItems:'baseline', gap:12 }}>
            <span style={{ fontSize:22, fontFamily:'IBM Plex Sans Condensed',
              fontWeight:700, color:'var(--orange)' }}>
              {stock.flag} {stock.ticker}
            </span>
            <span style={{ fontSize:18, fontFamily:'IBM Plex Mono', fontWeight:700, color:'var(--text)' }}>
              {stock.exchange === 'SWX' ? 'CHF' : stock.exchange === 'LSE' || stock.exchange === 'AIM' ? 'GBp' : stock.exchange === 'OM' || stock.exchange === 'NGM' ? 'SEK' : stock.exchange === 'OB' ? 'NOK' : stock.exchange === 'CPSE' ? 'DKK' : stock.exchange === 'US' ? 'USD' : '€'} {fv(stock.price, 2)}
            </span>
            <span style={{ fontSize:16, fontFamily:'IBM Plex Mono', fontWeight:700,
              color: chg >= 0 ? 'var(--green)' : 'var(--red)' }}>
              {fp(chg, 2)}
            </span>
          </div>
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <div style={{ textAlign:'right' }}>
              <div style={{ fontSize:13, color:'var(--text2)' }}>{stock.company}</div>
              <div style={{ fontSize:11, color:'var(--text3)' }}>{stock.exchange} · {stock.sector} · {stock.country}</div>
            </div>
            <button onClick={onClose}
              style={{ color:'var(--text3)', background:'none', border:'none', cursor:'pointer', padding:4 }}>
              <X size={18} />
            </button>
          </div>
        </div>

        <div style={{ padding:20, display:'flex', flexDirection:'column', gap:16 }}>
          {/* Metrics grid */}
          <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
            {/* Left — Valuation */}
            <div style={{ background:'var(--bg2)', border:'1px solid var(--border)', borderRadius:3, padding:12 }}>
              <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--orange)',
                marginBottom:10 }}>Valuation & Key Data</div>
              <table style={{ width:'100%', borderCollapse:'collapse' }}>
                <tbody>
                  {leftMetrics.map(([label, value, color]) => (
                    <tr key={label} style={{ borderBottom:'1px solid rgba(30,45,69,0.4)' }}>
                      <td style={{ padding:'5px 0', fontFamily:'IBM Plex Sans Condensed',
                        fontWeight:600, fontSize:11, color:'var(--text3)' }}>{label}</td>
                      <td style={{ padding:'5px 0', textAlign:'right',
                        fontFamily:'IBM Plex Mono', fontWeight:600, fontSize:12,
                        color: color || 'var(--text)' }}>{value}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Right — Growth & Scores */}
            <div style={{ background:'var(--bg2)', border:'1px solid var(--border)', borderRadius:3, padding:12 }}>
              <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--orange)',
                marginBottom:10 }}>Growth, Momentum & Scores</div>
              <table style={{ width:'100%', borderCollapse:'collapse' }}>
                <tbody>
                  {rightMetrics.map(([label, value, color]) => (
                    <tr key={label} style={{ borderBottom:'1px solid rgba(30,45,69,0.4)' }}>
                      <td style={{ padding:'5px 0', fontFamily:'IBM Plex Sans Condensed',
                        fontWeight:600, fontSize:11, color:'var(--text3)' }}>{label}</td>
                      <td style={{ padding:'5px 0', textAlign:'right' }}>
                        {label.includes('Score') && value !== '—' ? (
                          <span style={{ fontFamily:'IBM Plex Mono', fontWeight:700, fontSize:13,
                            padding:'1px 8px', borderRadius:2,
                            background: scoreBg(label === 'Value Score' ? stock.valueScore : stock.growthScore),
                            color: color || 'var(--text)' }}>{value}</span>
                        ) : (
                          <span style={{ fontFamily:'IBM Plex Mono', fontWeight:600, fontSize:12,
                            color: color || 'var(--text)' }}>{value}</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Chart */}
          <div style={{ background:'var(--bg2)', border:'1px solid var(--border)', borderRadius:3, padding:12 }}>
            <div style={{ display:'flex', alignItems:'center', justifyContent:'space-between', marginBottom:10 }}>
              <div style={{ display:'flex', alignItems:'center', gap:12 }}>
                <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                  letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--orange)' }}>
                  Price Chart (Total Return)
                </div>
                {history.length >= 2 && (() => {
                  const first = parseFloat(history[0]?.adj_close || history[0]?.close || '0')
                  const last = parseFloat(history[history.length-1]?.adj_close || history[history.length-1]?.close || '0')
                  const pct = first > 0 ? ((last/first - 1) * 100) : null
                  return pct != null ? (
                    <span style={{ fontSize:12, fontFamily:'IBM Plex Mono', fontWeight:700,
                      color: pct >= 0 ? 'var(--green)' : 'var(--red)' }}>
                      {pct >= 0 ? '+' : ''}{pct.toFixed(1)}%
                    </span>
                  ) : null
                })()}
              </div>
              <div style={{ display:'flex', gap:4 }}>
                {([['1Y',365],['3Y',1095],['5Y',1825]] as [string,number][]).map(([lbl, d]) => (
                  <button key={lbl} onClick={() => setChartDays(d)}
                    style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                      fontSize:10, padding:'3px 10px', borderRadius:2, cursor:'pointer',
                      border:`1px solid ${chartDays===d ? 'var(--orange)' : 'var(--border)'}`,
                      background: chartDays===d ? 'var(--orange)' : 'transparent',
                      color: chartDays===d ? '#fff' : 'var(--text3)' }}>
                    {lbl}
                  </button>
                ))}
              </div>
            </div>
            <div style={{ fontSize:9, color:'var(--text3)', marginBottom:6, fontFamily:'IBM Plex Sans Condensed' }}>
              Adjusted close price · includes dividends &amp; split adjustments
            </div>
            {loadingChart ? (
              <div style={{ height:200, display:'flex', alignItems:'center', justifyContent:'center', color:'var(--text3)' }}>
                Loading chart…
              </div>
            ) : (
              <PriceChart history={history} />
            )}
          </div>

          {/* Add to portfolio */}
          <div style={{ background:'var(--bg2)', border:'1px solid var(--border)', borderRadius:3, padding:12 }}>
            <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
              letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--orange)', marginBottom:10 }}>
              Add to Portfolio
            </div>
            <div style={{ display:'flex', alignItems:'flex-end', gap:10, flexWrap:'wrap' }}>
              <div>
                <div style={{ fontSize:10, color:'var(--text3)', marginBottom:4,
                  fontFamily:'IBM Plex Sans Condensed', fontWeight:700, textTransform:'uppercase' }}>Portfolio</div>
                <select value={pf} onChange={e => setPf(e.target.value)}
                  className="input-field" style={{ width:140 }}>
                  {['Portfolio 1','Portfolio 2','Portfolio 3'].map(p => <option key={p}>{p}</option>)}
                </select>
              </div>
              <div>
                <div style={{ fontSize:10, color:'var(--text3)', marginBottom:4,
                  fontFamily:'IBM Plex Sans Condensed', fontWeight:700, textTransform:'uppercase' }}>Quantity</div>
                <input type="number" placeholder="100" value={qty}
                  onChange={e => setQty(e.target.value)}
                  className="input-field" style={{ width:90 }} />
              </div>
              <div>
                <div style={{ fontSize:10, color:'var(--text3)', marginBottom:4,
                  fontFamily:'IBM Plex Sans Condensed', fontWeight:700, textTransform:'uppercase' }}>Buy Price</div>
                <input type="number" value={px}
                  onChange={e => setPx(e.target.value)}
                  className="input-field" style={{ width:100 }} />
              </div>
              <button onClick={handleAdd} disabled={!qty || !px || added}
                className="btn-primary">
                {added ? '✅ Added' : '+ Add to Portfolio'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
