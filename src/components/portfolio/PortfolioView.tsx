'use client'

import { useState, useEffect } from 'react'
import { Briefcase, Search, X } from 'lucide-react'
import { Stock, computeScores } from '@/lib/ranking'
import { DEMO_STOCKS } from '@/lib/demoData'
import toast from 'react-hot-toast'

function fp(v: number | null | undefined, d = 2): string {
  if (v == null || isNaN(v as number)) return '—'
  return `${(v as number) >= 0 ? '+' : ''}${(v as number).toFixed(d)}%`
}
function fv(v: number | null | undefined, d = 2): string {
  if (v == null || isNaN(v as number)) return '—'
  return (v as number).toFixed(d)
}

function weightedAvg(rows: any[], field: string): number | null {
  const valid = rows.filter((r: any) => r[field] != null && !isNaN(r[field]))
  const sumW = valid.reduce((a: number, r: any) => a + (r.weight || 0), 0)
  if (sumW === 0) return null
  return valid.reduce((a: number, r: any) => a + r[field] * (r.weight || 0), 0) / sumW
}

const PIE_COLORS = ['#f97316','#3b82f6','#22c55e','#eab308','#8b5cf6',
  '#14b8a6','#ef4444','#0ea5e9','#84cc16','#f59e0b','#6366f1','#ec4899']

function PieChart(props: { data: Record<string, number>; title: string }) {
  const entries = Object.entries(props.data).sort((a, b) => b[1] - a[1])
  const total = entries.reduce((a, e) => a + e[1], 0)
  let cum = -90
  return (
    <div style={{ background:'var(--surface)', border:'1px solid var(--border)', borderRadius:4, padding:16 }}>
      <div style={{ fontSize:10, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
        letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--text3)', marginBottom:12 }}>
        {props.title}
      </div>
      <div style={{ display:'flex', gap:20, alignItems:'center', flexWrap:'wrap' }}>
        <svg width="140" height="140" viewBox="0 0 140 140" style={{ flexShrink:0 }}>
          {entries.map((e, i) => {
            const angle = (e[1] / total) * 360
            const s = cum * Math.PI / 180
            cum += angle
            const en = cum * Math.PI / 180
            const x1 = 70 + 60 * Math.cos(s), y1 = 70 + 60 * Math.sin(s)
            const x2 = 70 + 60 * Math.cos(en), y2 = 70 + 60 * Math.sin(en)
            return (
              <path key={e[0]}
                d={`M70,70 L${x1.toFixed(1)},${y1.toFixed(1)} A60,60 0 ${angle > 180 ? 1 : 0},1 ${x2.toFixed(1)},${y2.toFixed(1)} Z`}
                fill={PIE_COLORS[i % PIE_COLORS.length]} stroke="var(--bg)" strokeWidth="1.5">
                <title>{e[0]}: {e[1].toFixed(1)}%</title>
              </path>
            )
          })}
          <circle cx="70" cy="70" r="32" fill="var(--surface)" />
        </svg>
        <div style={{ display:'flex', flexDirection:'column', gap:5, flex:1 }}>
          {entries.map((e, i) => (
            <div key={e[0]} style={{ display:'flex', alignItems:'center', gap:7 }}>
              <div style={{ width:10, height:10, borderRadius:2, background:PIE_COLORS[i % PIE_COLORS.length] }} />
              <span style={{ fontSize:11, color:'var(--text2)', flex:1 }}>{e[0]}</span>
              <span style={{ fontSize:11, fontFamily:'IBM Plex Mono', color:'var(--orange)', fontWeight:600 }}>
                {e[1].toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default function Portfolio() {
  const [portfolios,    setPortfolios]    = useState<Record<string, any[]>>({})
  const [active,        setActive]        = useState('Portfolio 1')
  const [newName,       setNewName]       = useState('')
  const [searchQ,       setSearchQ]       = useState('')
  const [searchRes,     setSearchRes]     = useState<Stock[]>([])
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null)
  const [addQty,        setAddQty]        = useState('')
  const [addPrice,      setAddPrice]      = useState('')

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem('portfolios') || '{}')
    setPortfolios({ 'Portfolio 1':[], 'Portfolio 2':[], 'Portfolio 3':[], ...stored })
  }, [])

  useEffect(() => {
    if (searchQ.length < 2) { setSearchRes([]); return }
    const q = searchQ.toLowerCase()
    const results = computeScores([...DEMO_STOCKS])
      .filter(s => s.ticker.toLowerCase().includes(q) || (s.company || '').toLowerCase().includes(q))
      .slice(0, 8)
    setSearchRes(results)
  }, [searchQ])

  function save(pfs: typeof portfolios) {
    setPortfolios(pfs)
    localStorage.setItem('portfolios', JSON.stringify(pfs))
  }

  function createPortfolio() {
    if (!newName.trim() || portfolios[newName]) return
    save({ ...portfolios, [newName]: [] })
    setActive(newName); setNewName('')
  }

  function removePosition(idx: number) {
    save({ ...portfolios, [active]: (portfolios[active] || []).filter((_: any, i: number) => i !== idx) })
  }

  function selectStock(s: Stock) {
    setSelectedStock(s)
    setAddPrice(s.price?.toFixed(2) || '')
    setSearchQ(s.ticker + ' — ' + s.company)
    setSearchRes([])
  }

  function addToPortfolio() {
    if (!selectedStock || !addQty || !addPrice) return
    const pfs = { ...portfolios }
    if (!pfs[active]) pfs[active] = []
    if (pfs[active].length >= 50) { toast.error('Max 50 positions'); return }
    pfs[active].push({
      ticker: selectedStock.ticker, exchange: selectedStock.exchange,
      company: selectedStock.company, flag: selectedStock.flag,
      sector: selectedStock.sector, country: selectedStock.country,
      qty: parseFloat(addQty), buy_price: parseFloat(addPrice),
      added_at: new Date().toISOString(),
    })
    save(pfs)
    toast.success(`${selectedStock.ticker} added to ${active}`)
    setSelectedStock(null); setSearchQ(''); setAddQty(''); setAddPrice('')
  }

  const allScored = computeScores([...DEMO_STOCKS])
  const positions = portfolios[active] || []

  const rows = positions.map((p: any) => {
    const live = allScored.find(s => s.ticker === p.ticker && s.exchange === p.exchange)
    const lastPx   = live?.price ?? p.buy_price
    const chg1d    = live?.change1d ?? null
    const costVal  = p.qty * p.buy_price
    const mktVal   = p.qty * lastPx
    const gainEur  = mktVal - costVal
    const gainPct  = costVal > 0 ? (gainEur / costVal) * 100 : null
    const dailyChg = chg1d != null ? mktVal * chg1d / 100 : null
    return {
      ...p, lastPx, chg1d, costVal, mktVal, gainEur, gainPct, dailyChg,
      peTrail: live?.peTrail, peFwd: live?.peFwd, pb: live?.pb,
      evEbitda: live?.evEbitda, roe: live?.roe, divYield: live?.divYield,
      beta: live?.beta, epsGrowth: live?.epsGrowth, revGrowth: live?.revGrowth,
      epsMom30d: live?.epsMom30d, mom1w: live?.mom1w, mom1m: live?.mom1m,
      mom6m: live?.mom6m, mom12m: live?.mom12m,
      valueScore: live?.valueScore, growthScore: live?.growthScore,
    }
  })

  const totalCost    = rows.reduce((a: number, r: any) => a + r.costVal, 0)
  const totalMkt     = rows.reduce((a: number, r: any) => a + r.mktVal, 0)
  const totalGain    = totalMkt - totalCost
  const totalGainPct = totalCost > 0 ? (totalGain / totalCost) * 100 : null
  const totalDaily   = rows.reduce((a: number, r: any) => a + (r.dailyChg || 0), 0)
  const ewChg1d      = totalMkt > 0
    ? rows.reduce((a: number, r: any) => a + (r.chg1d || 0) * r.mktVal, 0) / totalMkt
    : null

  const rowsW = rows.map((r: any) => ({
    ...r, weight: totalMkt > 0 ? (r.mktVal / totalMkt) * 100 : 0
  }))

  const sectorMap:  Record<string, number> = {}
  const countryMap: Record<string, number> = {}
  rowsW.forEach((r: any) => {
    const sec = r.sector  || 'Other'
    const cty = r.country || 'Other'
    sectorMap[sec]  = (sectorMap[sec]  || 0) + r.weight
    countryMap[cty] = (countryMap[cty] || 0) + r.weight
  })

  const wm: Record<string, number | null> = {}
  ;['peTrail','peFwd','pb','evEbitda','roe','divYield','beta',
    'epsGrowth','revGrowth','epsMom30d','mom1w','mom1m','mom6m','mom12m',
    'valueScore','growthScore'].forEach(f => { wm[f] = weightedAvg(rowsW, f) })

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:16 }}>
      <div className="section-hdr">Portfolio Management</div>

      <div style={{ background:'rgba(249,115,22,0.08)', border:'1px solid rgba(249,115,22,0.2)',
        borderRadius:3, padding:'8px 12px', fontSize:11, color:'var(--text3)' }}>
        Beta: portfolios stored in browser. Cloud sync via Supabase coming in full version.
      </div>

      <div style={{ display:'flex', flexWrap:'wrap', alignItems:'center', gap:8 }}>
        {Object.keys(portfolios).map(name => (
          <button key={name} onClick={() => setActive(name)}
            className={`tab-btn ${active === name ? 'active' : ''}`}>
            {name} ({(portfolios[name] || []).length})
          </button>
        ))}
        <div style={{ display:'flex', gap:6, marginLeft:'auto' }}>
          <input value={newName} onChange={e => setNewName(e.target.value)}
            placeholder="New portfolio name" className="input-field" style={{ width:160 }}
            onKeyDown={e => { if (e.key === 'Enter') createPortfolio() }} />
          <button onClick={createPortfolio} className="btn-ghost">+ Create</button>
        </div>
      </div>

      <div style={{ background:'var(--surface)', border:'1px solid var(--border)', borderRadius:4, padding:16 }}>
        <div style={{ fontSize:11, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
          letterSpacing:'0.1em', textTransform:'uppercase', color:'var(--orange)', marginBottom:12 }}>
          + Add Stock to {active}
        </div>
        <div style={{ position:'relative' }}>
          <Search size={14} style={{ position:'absolute', left:10, top:'50%',
            transform:'translateY(-50%)', color:'var(--text4)', pointerEvents:'none' }} />
          <input value={searchQ} onChange={e => { setSearchQ(e.target.value); setSelectedStock(null) }}
            placeholder="Search ticker or company (ENI, ASML, Intesa...)"
            className="input-field" style={{ paddingLeft:32 }} />
          {searchQ && (
            <button onClick={() => { setSearchQ(''); setSearchRes([]); setSelectedStock(null) }}
              style={{ position:'absolute', right:10, top:'50%', transform:'translateY(-50%)',
                color:'var(--text4)', background:'none', border:'none', cursor:'pointer' }}>
              <X size={14} />
            </button>
          )}
        </div>

        {searchRes.length > 0 && (
          <div style={{ border:'1px solid var(--border2)', borderRadius:3, overflow:'hidden', marginTop:4, marginBottom:8 }}>
            {searchRes.map((s, i) => (
              <div key={i} onClick={() => selectStock(s)}
                style={{ padding:'8px 12px', borderBottom: i < searchRes.length - 1 ? '1px solid var(--border)' : 'none',
                  display:'flex', alignItems:'center', gap:12, cursor:'pointer',
                  background: i % 2 === 0 ? 'var(--surface)' : 'var(--surface2)' }}>
                <span style={{ fontSize:16 }}>{s.flag}</span>
                <span style={{ fontFamily:'IBM Plex Mono', fontWeight:700, color:'var(--orange)', width:60 }}>{s.ticker}</span>
                <span style={{ color:'var(--text2)', fontSize:12, flex:1 }}>{s.company}</span>
                <span style={{ color:'var(--text3)', fontSize:11 }}>{s.exchange}</span>
                <span style={{ fontFamily:'IBM Plex Mono', color:'var(--text)', fontSize:12 }}>€{s.price?.toFixed(2) || '—'}</span>
              </div>
            ))}
          </div>
        )}

        {selectedStock && (
          <div style={{ display:'flex', alignItems:'flex-end', gap:10, flexWrap:'wrap',
            background:'var(--bg2)', border:'1px solid var(--orange)', borderRadius:3, padding:12, marginTop:8 }}>
            <div style={{ display:'flex', alignItems:'center', gap:8, flex:1 }}>
              <span style={{ fontSize:20 }}>{selectedStock.flag}</span>
              <div>
                <div style={{ fontFamily:'IBM Plex Mono', fontWeight:700, color:'var(--orange)', fontSize:15 }}>
                  {selectedStock.ticker}
                </div>
                <div style={{ fontSize:11, color:'var(--text3)' }}>{selectedStock.company}</div>
              </div>
            </div>
            <div>
              <div style={{ fontSize:10, color:'var(--text3)', marginBottom:4,
                fontFamily:'IBM Plex Sans Condensed', fontWeight:700, textTransform:'uppercase' }}>Qty</div>
              <input type="number" placeholder="100" value={addQty}
                onChange={e => setAddQty(e.target.value)} className="input-field" style={{ width:90 }} />
            </div>
            <div>
              <div style={{ fontSize:10, color:'var(--text3)', marginBottom:4,
                fontFamily:'IBM Plex Sans Condensed', fontWeight:700, textTransform:'uppercase' }}>Buy Price €</div>
              <input type="number" value={addPrice}
                onChange={e => setAddPrice(e.target.value)} className="input-field" style={{ width:100 }} />
            </div>
            <button onClick={addToPortfolio} className="btn-primary">+ Add</button>
            <button onClick={() => { setSelectedStock(null); setSearchQ(''); setAddQty(''); setAddPrice('') }}
              style={{ color:'var(--text4)', background:'none', border:'none', cursor:'pointer' }}>
              <X size={16} />
            </button>
          </div>
        )}
      </div>

      <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:8 }}>
        {([
          ['Cost Value', `€${totalCost.toLocaleString('de-DE',{maximumFractionDigits:0})}`, 0],
          ['Market Value', `€${totalMkt.toLocaleString('de-DE',{maximumFractionDigits:0})}`, 0],
          ['Total Gain €', `€${totalGain>=0?'+':''}${totalGain.toLocaleString('de-DE',{maximumFractionDigits:0})}`, totalGain],
          ['Total Gain %', fp(totalGainPct), totalGainPct ?? 0],
          ['Daily Change €', `€${totalDaily>=0?'+':''}${totalDaily.toLocaleString('de-DE',{maximumFractionDigits:0})}`, totalDaily],
          ['Daily Change %', fp(ewChg1d), ewChg1d ?? 0],
        ] as [string,string,number][]).map(([label, value, colorVal], i) => (
          <div key={i} className="metric-card">
            <div className="metric-label">{label}</div>
            <div className="metric-value" style={{
              color: i < 2 ? 'var(--orange)' : colorVal > 0 ? 'var(--green)' : colorVal < 0 ? 'var(--red)' : 'var(--text3)'
            }}>{value}</div>
          </div>
        ))}
      </div>

      {positions.length === 0 ? (
        <div style={{ padding:48, textAlign:'center', color:'var(--text4)',
          border:'1px dashed var(--border)', borderRadius:4 }}>
          <Briefcase size={28} style={{ margin:'0 auto 10px', opacity:0.3 }} />
          <p style={{ fontSize:13 }}>No positions. Search above or add from the Screener.</p>
        </div>
      ) : (
        <div style={{ display:'flex', flexDirection:'column', gap:12 }}>
          <div style={{ background:'var(--surface)', border:'1px solid var(--border)', borderRadius:4, overflow:'hidden' }}>
            <div style={{ overflowX:'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Ticker</th><th>Company</th><th>Sector</th>
                    <th>Qty</th><th>Buy €</th><th>Last €</th><th>1D %</th>
                    <th>Cost €</th><th>Mkt Val €</th><th>Weight %</th>
                    <th>Gain €</th><th>Gain %</th><th>Daily €</th><th></th>
                  </tr>
                </thead>
                <tbody>
                  {rowsW.map((r: any, i: number) => (
                    <tr key={i}>
                      <td>
                        <span style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700, color:'var(--orange)' }}>
                          {r.flag} {r.ticker}
                        </span>
                      </td>
                      <td><span style={{ color:'var(--text2)', fontSize:12 }}>{r.company}</span></td>
                      <td><span style={{ color:'var(--text3)', fontSize:11 }}>{r.sector || '—'}</span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono' }}>{r.qty}</span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono' }}>€{(+r.buy_price).toFixed(2)}</span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono', color:'var(--text)' }}>€{r.lastPx.toFixed(2)}</span></td>
                      <td>
                        <span style={{ fontFamily:'IBM Plex Mono', fontWeight:600,
                          color: r.chg1d != null ? (r.chg1d >= 0 ? 'var(--green)' : 'var(--red)') : 'var(--text3)' }}>
                          {fp(r.chg1d)}
                        </span>
                      </td>
                      <td><span style={{ fontFamily:'IBM Plex Mono' }}>€{r.costVal.toLocaleString('de-DE',{maximumFractionDigits:0})}</span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:600, color:'var(--text)' }}>€{r.mktVal.toLocaleString('de-DE',{maximumFractionDigits:0})}</span></td>
                      <td>
                        <div style={{ display:'flex', alignItems:'center', gap:5 }}>
                          <div style={{ height:4, background:'var(--orange)', borderRadius:2,
                            width:`${Math.min(r.weight,100)}%`, maxWidth:50, minWidth:2 }} />
                          <span style={{ fontFamily:'IBM Plex Mono', fontSize:11 }}>{r.weight.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td>
                        <span style={{ fontFamily:'IBM Plex Mono', fontWeight:600,
                          color: r.gainEur >= 0 ? 'var(--green)' : 'var(--red)' }}>
                          €{r.gainEur >= 0 ? '+' : ''}{r.gainEur.toLocaleString('de-DE',{maximumFractionDigits:0})}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontFamily:'IBM Plex Mono', fontWeight:600,
                          color: r.gainPct != null ? (r.gainPct >= 0 ? 'var(--green)' : 'var(--red)') : 'var(--text3)' }}>
                          {fp(r.gainPct)}
                        </span>
                      </td>
                      <td>
                        <span style={{ fontFamily:'IBM Plex Mono',
                          color: r.dailyChg != null ? (r.dailyChg >= 0 ? 'var(--green)' : 'var(--red)') : 'var(--text3)' }}>
                          {r.dailyChg != null ? `€${r.dailyChg>=0?'+':''}${r.dailyChg.toLocaleString('de-DE',{maximumFractionDigits:0})}` : '—'}
                        </span>
                      </td>
                      <td>
                        <button onClick={() => removePosition(i)}
                          style={{ color:'var(--red)', fontSize:12, cursor:'pointer', background:'none', border:'none' }}>✕</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr style={{ background:'var(--surface2)', borderTop:'2px solid var(--border)' }}>
                    <td colSpan={3} style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                      fontSize:11, color:'var(--orange)', textTransform:'uppercase' }}>
                      TOTAL ({positions.length})
                    </td>
                    <td></td><td></td><td></td>
                    <td>
                      <span style={{ fontFamily:'IBM Plex Mono', fontWeight:700,
                        color: ewChg1d != null ? (ewChg1d >= 0 ? 'var(--green)' : 'var(--red)') : 'var(--text3)' }}>
                        {fp(ewChg1d)}
                      </span>
                    </td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:700 }}>€{totalCost.toLocaleString('de-DE',{maximumFractionDigits:0})}</span></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:700 }}>€{totalMkt.toLocaleString('de-DE',{maximumFractionDigits:0})}</span></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:700, color:'var(--orange)' }}>100%</span></td>
                    <td>
                      <span style={{ fontFamily:'IBM Plex Mono', fontWeight:700,
                        color: totalGain >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        €{totalGain>=0?'+':''}{totalGain.toLocaleString('de-DE',{maximumFractionDigits:0})}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily:'IBM Plex Mono', fontWeight:700,
                        color: totalGainPct != null ? (totalGainPct >= 0 ? 'var(--green)' : 'var(--red)') : 'var(--text3)' }}>
                        {fp(totalGainPct)}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontFamily:'IBM Plex Mono', fontWeight:700,
                        color: totalDaily >= 0 ? 'var(--green)' : 'var(--red)' }}>
                        €{totalDaily>=0?'+':''}{totalDaily.toLocaleString('de-DE',{maximumFractionDigits:0})}
                      </span>
                    </td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <div style={{ background:'var(--surface)', border:'1px solid var(--border)', borderRadius:4, padding:16 }}>
            <div style={{ fontSize:10, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
              letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--text3)',
              marginBottom:12, paddingBottom:8, borderBottom:'1px solid var(--border)' }}>
              Portfolio Weighted Metrics — Market Value Weighted Averages
            </div>
            <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
              letterSpacing:'0.1em', textTransform:'uppercase', color:'var(--orange)', marginBottom:8 }}>
              Valuation
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8, marginBottom:16 }}>
              {(['P/E Trailing|peTrail|fv1','P/E Forward|peFwd|fv1','P/B|pb|fv2',
                'EV/EBITDA|evEbitda|fv1','ROE %|roe|fp1','Div Yield %|divYield|fp2','Beta|beta|fv2'
              ]).map(spec => {
                const [label, field, fmt] = spec.split('|')
                const val = wm[field]
                const display = fmt === 'fp1' ? fp(val,1) : fmt === 'fp2' ? fp(val,2) : fmt === 'fv1' ? fv(val,1) : fv(val,2)
                return (
                  <div key={field} className="metric-card">
                    <div className="metric-label">{label}</div>
                    <div className="metric-value" style={{ fontSize:'0.9rem' }}>{display}</div>
                  </div>
                )
              })}
            </div>
            <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
              letterSpacing:'0.1em', textTransform:'uppercase', color:'var(--orange)', marginBottom:8 }}>
              Growth &amp; Momentum
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8, marginBottom:16 }}>
              {(['EPS Growth %|epsGrowth','Rev Growth %|revGrowth','EPS Mom 30d|epsMom30d',
                'Mom 1W|mom1w','Mom 1M|mom1m','Mom 6M|mom6m','Mom 12M|mom12m'
              ]).map(spec => {
                const [label, field] = spec.split('|')
                return (
                  <div key={field} className="metric-card">
                    <div className="metric-label">{label}</div>
                    <div className="metric-value" style={{ fontSize:'0.9rem',
                      color: wm[field] != null ? (wm[field]! >= 0 ? 'var(--green)' : 'var(--red)') : 'var(--orange)' }}>
                      {fp(wm[field],1)}
                    </div>
                  </div>
                )
              })}
            </div>
            <div style={{ fontSize:9, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
              letterSpacing:'0.1em', textTransform:'uppercase', color:'var(--orange)', marginBottom:8 }}>
              Composite Scores
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8 }}>
              {(['Weighted Value Score|valueScore','Weighted Growth Score|growthScore']).map(spec => {
                const [label, field] = spec.split('|')
                const val = wm[field]
                return (
                  <div key={field} className="metric-card" style={{ display:'flex', alignItems:'center', gap:16 }}>
                    <div style={{ flex:1 }}>
                      <div className="metric-label">{label}</div>
                      <div style={{ fontFamily:'IBM Plex Mono', fontSize:'1.4rem', fontWeight:700,
                        color: val != null ? (val >= 60 ? 'var(--green)' : val >= 40 ? 'var(--orange)' : 'var(--red)') : 'var(--text3)' }}>
                        {val != null ? Math.round(val) : '—'}
                      </div>
                    </div>
                    {val != null && (
                      <div style={{ width:80 }}>
                        <div style={{ height:8, background:'var(--border)', borderRadius:4, overflow:'hidden' }}>
                          <div style={{ height:'100%', borderRadius:4, width:`${Math.min(val,100)}%`,
                            background: val >= 60 ? 'var(--green)' : val >= 40 ? 'var(--orange)' : 'var(--red)' }} />
                        </div>
                        <div style={{ fontSize:9, color:'var(--text3)', textAlign:'right', marginTop:3,
                          fontFamily:'IBM Plex Mono' }}>{Math.round(val)}/100</div>
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </div>

          {Object.keys(sectorMap).length > 0 && (
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
              <PieChart data={sectorMap}  title="Sector Exposure — Market Value Weight %" />
              <PieChart data={countryMap} title="Country Exposure — Market Value Weight %" />
            </div>
          )}
        </div>
      )}
    </div>
  )
}
