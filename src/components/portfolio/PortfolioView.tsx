'use client'
import { useState, useEffect } from 'react'
import { Briefcase, Search, X } from 'lucide-react'
import { Stock } from '@/lib/ranking'
import toast from 'react-hot-toast'


const CURRENCY_MAP: Record<string, string> = {
  MIL:'EUR', PA:'EUR', XETRA:'EUR', AS:'EUR', MC:'EUR', BR:'EUR',
  HE:'EUR', AT:'EUR', LS:'EUR', IR:'EUR', VI:'EUR',
  LSE:'GBp', AIM:'GBp', SWX:'CHF', OM:'SEK', NGM:'SEK',
  OB:'NOK', CPSE:'DKK'
}
const DISPLAY_CURRENCIES = ['EUR','GBp','CHF','SEK','NOK','DKK','USD','GBP']
// Tassi approssimati vs EUR
const FX_TO_EUR: Record<string,number> = {
  EUR:1, GBp:0.01173, GBP:1.173, CHF:1.067, SEK:0.0872,
  NOK:0.0864, DKK:0.134, USD:0.896
}

const fp = (v?: number | null, d = 2): string => {
  if (v == null || isNaN(v)) return '—'
  return `${v >= 0 ? '+' : ''}${v.toFixed(d)}%`
}
const fv = (v?: number | null, d = 2): string => {
  if (v == null || isNaN(v)) return '—'
  return v.toFixed(d)
}

// ── PIE CHART COMPONENT ─────────────────────────────────────────
const PIE_COLORS = ['#f97316','#3b82f6','#22c55e','#eab308','#8b5cf6',
  '#14b8a6','#ef4444','#0ea5e9','#84cc16','#f59e0b','#6366f1','#ec4899']

function PieChart({ data, title }: { data: Record<string,number>; title: string }) {
  const entries = Object.entries(data).sort((a,b) => b[1]-a[1])
  const total   = entries.reduce((a,[,v])=>a+v,0)
  let cumAngle  = -90 // start from top

  return (
    <div style={{ background:'var(--surface)', border:'1px solid var(--border)', borderRadius:4, padding:16 }}>
      <div style={{ fontSize:10, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
        letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--text3)', marginBottom:12 }}>
        {title}
      </div>
      <div style={{ display:'flex', gap:20, alignItems:'center', flexWrap:'wrap' }}>
        {/* SVG Pie */}
        <svg width="140" height="140" viewBox="0 0 140 140" style={{ flexShrink:0 }}>
          {entries.map(([label, val], i) => {
            const pct   = val / total
            const angle = pct * 360
            const start = cumAngle * Math.PI / 180
            cumAngle   += angle
            const end   = cumAngle * Math.PI / 180
            const r     = 60, cx = 70, cy = 70
            const x1 = cx + r * Math.cos(start)
            const y1 = cy + r * Math.sin(start)
            const x2 = cx + r * Math.cos(end)
            const y2 = cy + r * Math.sin(end)
            const large = angle > 180 ? 1 : 0
            const color = PIE_COLORS[i % PIE_COLORS.length]
            return (
              <path key={label}
                d={`M${cx},${cy} L${x1.toFixed(1)},${y1.toFixed(1)} A${r},${r} 0 ${large},1 ${x2.toFixed(1)},${y2.toFixed(1)} Z`}
                fill={color} stroke="var(--bg)" strokeWidth="1.5">
                <title>{label}: {val.toFixed(1)}%</title>
              </path>
            )
          })}
          {/* Center hole */}
          <circle cx="70" cy="70" r="32" fill="var(--surface)" />
          <text x="70" y="73" textAnchor="middle" fill="var(--text)"
            style={{ fontSize:11, fontFamily:'IBM Plex Mono', fontWeight:600 }}>
            {entries.length}
          </text>
          <text x="70" y="84" textAnchor="middle" fill="var(--text3)"
            style={{ fontSize:8, fontFamily:'IBM Plex Sans Condensed' }}>
            {entries.length === 1 ? 'sector' : 'sectors'}
          </text>
        </svg>
        {/* Legend */}
        <div style={{ display:'flex', flexDirection:'column', gap:5, flex:1, minWidth:120 }}>
          {entries.map(([label, val], i) => (
            <div key={label} style={{ display:'flex', alignItems:'center', gap:7 }}>
              <div style={{ width:10, height:10, borderRadius:2, flexShrink:0,
                background: PIE_COLORS[i % PIE_COLORS.length] }} />
              <span style={{ fontSize:11, color:'var(--text2)', flex:1, fontFamily:'IBM Plex Sans' }}>
                {label}
              </span>
              <span style={{ fontSize:11, fontFamily:'IBM Plex Mono', color:'var(--orange)', fontWeight:600 }}>
                {val.toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Weighted average utility
function wAvg(rows: any[], metric: (r: any) => number | null | undefined): number | null {
  const valid = rows.filter(r => { const v = metric(r); return v != null && !isNaN(v as number) })
  const sumW = valid.reduce((a: number, r: any) => a + r.weight, 0)
  if (sumW === 0) return null
  return valid.reduce((a: number, r: any) => a + (metric(r) as number) * r.weight, 0) / sumW
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
  const [displayCcy,    setDisplayCcy]    = useState('EUR')

  useEffect(() => {
    const stored = JSON.parse(localStorage.getItem('portfolios') || '{}')
    setPortfolios({ 'Portfolio 1':[], 'Portfolio 2':[], 'Portfolio 3':[], ...stored })
  }, [])

  useEffect(() => {
    if (searchQ.length < 2) { setSearchRes([]); return }
    const q = searchQ.toLowerCase()
    fetch(`/api/db/search?q=${encodeURIComponent(q)}&limit=8`)
      .then(r => r.json())
      .then(data => setSearchRes(data || []))
      .catch(() => setSearchRes([]))
  }, [searchQ])

  const save = (pfs: typeof portfolios) => {
    setPortfolios(pfs)
    localStorage.setItem('portfolios', JSON.stringify(pfs))
  }

  function createPortfolio() {
    if (!newName.trim() || portfolios[newName]) return
    save({ ...portfolios, [newName]: [] })
    setActive(newName); setNewName('')
  }

  function removePosition(idx: number) {
    save({ ...portfolios, [active]: (portfolios[active]||[]).filter((_:any,i:number)=>i!==idx) })
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
    if (pfs[active].length >= 50) { toast.error('Max 50 positions per portfolio'); return }
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

  // ── CALCULATIONS ──────────────────────────────────────────────
  const positions = portfolios[active] || []
  const allScored: any[] = []  // Stocks loaded from Supabase via parent

  // Conversione valuta
  const toCcy = (amount: number, fromCcy: string, toCcy2: string): number => {
    const toEur = FX_TO_EUR[fromCcy] || 1
    const fromEur = FX_TO_EUR[toCcy2] || 1
    return amount * toEur / fromEur
  }
  const getCcy = (exchange: string) => CURRENCY_MAP[exchange] || 'EUR'
  const sym = displayCcy === 'GBp' ? 'p' : displayCcy === 'EUR' ? '€' :
              displayCcy === 'CHF' ? 'CHF' : displayCcy === 'SEK' ? 'kr' :
              displayCcy === 'NOK' ? 'kr' : displayCcy === 'DKK' ? 'kr' :
              displayCcy === 'USD' ? '$' : displayCcy === 'GBP' ? '£' : displayCcy

  const rows = positions.map((p: any) => {
    const live = allScored.find(s => s.ticker === p.ticker && s.exchange === p.exchange)
    const lastPx   = live?.price      ?? p.buy_price
    const chg1d    = live?.change1d   ?? null
    const pCcy     = getCcy(p.exchange)
    const costVal  = toCcy(p.qty * p.buy_price, pCcy, displayCcy)
    const mktVal   = toCcy(p.qty * lastPx,      pCcy, displayCcy)
    const gainCcy  = mktVal - costVal
    const gainPct  = costVal > 0 ? gainCcy / costVal * 100 : null
    const dailyChg = chg1d != null ? mktVal * chg1d / 100 : null
    return { ...p, lastPx, chg1d, costVal, mktVal, gainEur:gainCcy, gainPct, dailyChg, pCcy }
  })

  const totalCost    = rows.reduce((a:number, r:any) => a + r.costVal, 0)
  const totalMkt     = rows.reduce((a:number, r:any) => a + r.mktVal, 0)
  const totalGain    = totalMkt - totalCost
  const totalGainPct = totalCost > 0 ? totalGain / totalCost * 100 : null
  const totalDaily   = rows.reduce((a:number, r:any) => a + (r.dailyChg||0), 0)
  const ewChg1d      = rows.length > 0
    ? rows.reduce((a:number,r:any)=> a + (r.chg1d||0)*r.mktVal, 0) / (totalMkt||1)
    : null

  // Weight = market value / total market value
  const rowsWithWeight = rows.map((r:any) => ({
    ...r, weight: totalMkt > 0 ? r.mktVal / totalMkt * 100 : 0
  }))

  // Sector breakdown
  const sectorMap: Record<string, number> = {}
  rowsWithWeight.forEach((r:any) => {
    const sec = r.sector || 'Other'
    sectorMap[sec] = (sectorMap[sec] || 0) + r.weight
  })

  // Country breakdown
  const countryMap: Record<string, number> = {}
  rowsWithWeight.forEach((r:any) => {
    const c = r.country || 'Other'
    countryMap[c] = (countryMap[c] || 0) + r.weight
  })

  // ── WEIGHTED PORTFOLIO METRICS ──────────────────────────────
  const live = allScored
  const getM = (ticker: string, exchange: string, field: string): number | null => {
    const s = live.find((x: any) => x.ticker === ticker && x.exchange === exchange) as any
    const v = s ? s[field] : null
    return v != null && !isNaN(v) ? v : null
  }
  const wM = (field: string) => wAvg(rowsWithWeight, (r: any) => getM(r.ticker, r.exchange, field))
  const wMetrics = {
    peTrail: wM('peTrail'), peFwd: wM('peFwd'),
    epsGrowth: wM('epsGrowth'), revGrowth: wM('revGrowth'),
    chg1d: wM('change1d'),
    mom1w: wM('mom1w'), mom6m: wM('mom6m'), mom12m: wM('mom12m'),
    valueScore: wM('valueScore'), growthScore: wM('growthScore'),
  }

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:16 }} className="fade-in">
      <div className="section-hdr">💼 Portfolio Management</div>
      <div style={{ background:'rgba(249,115,22,0.08)', border:'1px solid rgba(249,115,22,0.2)',
        borderRadius:3, padding:'8px 12px', fontSize:11, color:'var(--text3)' }}>
        ⚠️ Beta: portfolios stored in browser. Cloud sync via Supabase coming in full version.
      </div>

      {/* Portfolio tabs */}
      <div style={{ display:'flex', flexWrap:'wrap', alignItems:'center', gap:8 }}>
        {Object.keys(portfolios).map(name => (
          <button key={name} onClick={() => setActive(name)}
            className={`tab-btn ${active===name?'active':''}`}>
            {name} ({(portfolios[name]||[]).length})
          </button>
        ))}
        <div style={{ display:'flex', gap:6, marginLeft:'auto' }}>
          <input value={newName} onChange={e=>setNewName(e.target.value)}
            placeholder="New portfolio name" className="input-field" style={{ width:160 }}
            onKeyDown={e=>e.key==='Enter'&&createPortfolio()} />
          <button onClick={createPortfolio} className="btn-ghost">+ Create</button>
        </div>
      </div>

      {/* ── STOCK SEARCH ── */}
      <div style={{ background:'var(--surface)', border:'1px solid var(--border)', borderRadius:4, padding:16 }}>
        <div style={{ fontSize:11, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
          letterSpacing:'0.1em', textTransform:'uppercase', color:'var(--orange)', marginBottom:12 }}>
          + Add Stock to {active}
        </div>
        <div style={{ position:'relative', marginBottom: searchRes.length > 0 ? 0 : 12 }}>
          <Search size={14} style={{ position:'absolute', left:10, top:'50%',
            transform:'translateY(-50%)', color:'var(--text4)', pointerEvents:'none' }} />
          <input value={searchQ} onChange={e=>{setSearchQ(e.target.value);setSelectedStock(null)}}
            placeholder="Search by ticker or company name (e.g. ENI, ASML, Intesa...)"
            className="input-field" style={{ paddingLeft:32, fontSize:13 }} />
          {searchQ && (
            <button onClick={()=>{setSearchQ('');setSearchRes([]);setSelectedStock(null)}}
              style={{ position:'absolute', right:10, top:'50%', transform:'translateY(-50%)',
                color:'var(--text4)', background:'none', border:'none', cursor:'pointer' }}>
              <X size={14} />
            </button>
          )}
        </div>
        {searchRes.length > 0 && (
          <div style={{ border:'1px solid var(--border2)', borderRadius:3, overflow:'hidden', marginBottom:12, marginTop:4 }}>
            {searchRes.map((s,i) => (
              <div key={i} onClick={()=>selectStock(s)}
                style={{ padding:'9px 12px',
                  borderBottom: i<searchRes.length-1?'1px solid var(--border)':'none',
                  display:'flex', alignItems:'center', gap:12, cursor:'pointer',
                  background: selectedStock?.ticker===s.ticker
                    ? 'rgba(249,115,22,0.1)' : i%2===0 ? 'var(--surface)' : 'var(--surface2)',
                  transition:'background 0.1s' }}>
                <span style={{ fontSize:16 }}>{s.flag}</span>
                <span style={{ fontFamily:'IBM Plex Mono', fontWeight:700, color:'var(--orange)', fontSize:13, width:60 }}>{s.ticker}</span>
                <span style={{ color:'var(--text2)', fontSize:12, flex:1 }}>{s.company}</span>
                <span style={{ color:'var(--text3)', fontSize:11 }}>{s.sector || '—'}</span>
                <span style={{ color:'var(--text3)', fontSize:11 }}>{s.exchange}</span>
                <span style={{ fontFamily:'IBM Plex Mono', color:'var(--text)', fontSize:12, fontWeight:600 }}>
                  €{s.price?.toFixed(2)||'—'}
                </span>
              </div>
            ))}
          </div>
        )}
        {selectedStock && (
          <div style={{ display:'flex', alignItems:'flex-end', gap:10, flexWrap:'wrap',
            background:'var(--bg2)', border:'1px solid var(--orange)', borderRadius:3, padding:12 }}>
            <div style={{ display:'flex', alignItems:'center', gap:8, flex:1, minWidth:180 }}>
              <span style={{ fontSize:20 }}>{selectedStock.flag}</span>
              <div>
                <div style={{ fontFamily:'IBM Plex Mono', fontWeight:700, color:'var(--orange)', fontSize:15 }}>
                  {selectedStock.ticker}
                </div>
                <div style={{ fontSize:11, color:'var(--text3)' }}>{selectedStock.company}</div>
                <div style={{ fontSize:10, color:'var(--text4)' }}>
                  Last: €{selectedStock.price?.toFixed(2)||'—'} · {selectedStock.sector}
                </div>
              </div>
            </div>
            <div>
              <div style={{ fontSize:10, color:'var(--text3)', marginBottom:4,
                fontFamily:'IBM Plex Sans Condensed', fontWeight:700, textTransform:'uppercase', letterSpacing:'0.1em' }}>
                Quantity
              </div>
              <input type="number" placeholder="100" value={addQty}
                onChange={e=>setAddQty(e.target.value)}
                className="input-field" style={{ width:90 }} />
            </div>
            <div>
              <div style={{ fontSize:10, color:'var(--text3)', marginBottom:4,
                fontFamily:'IBM Plex Sans Condensed', fontWeight:700, textTransform:'uppercase', letterSpacing:'0.1em' }}>
                Buy Price €
              </div>
              <input type="number" value={addPrice}
                onChange={e=>setAddPrice(e.target.value)}
                className="input-field" style={{ width:100 }} />
            </div>
            <button onClick={addToPortfolio} className="btn-primary">➕ Add</button>
            <button onClick={()=>{setSelectedStock(null);setSearchQ('');setAddQty('');setAddPrice('')}}
              style={{ color:'var(--text4)', background:'none', border:'none', cursor:'pointer' }}>
              <X size={16} />
            </button>
          </div>
        )}
      </div>

      {/* ── CURRENCY SELECTOR ── */}
      <div style={{ display:'flex', alignItems:'center', gap:8 }}>
        <span style={{ fontSize:11, color:'var(--text3)', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, textTransform:'uppercase', letterSpacing:'0.1em' }}>Display Currency:</span>
        {DISPLAY_CURRENCIES.map(ccy => (
          <button key={ccy} onClick={() => setDisplayCcy(ccy)}
            style={{ padding:'4px 10px', borderRadius:3, border:'1px solid',
              borderColor: displayCcy===ccy ? 'var(--orange)' : 'var(--border)',
              background: displayCcy===ccy ? 'var(--orange)' : 'transparent',
              color: displayCcy===ccy ? '#000' : 'var(--text3)',
              fontSize:11, fontFamily:'IBM Plex Mono', fontWeight:600, cursor:'pointer' }}>
            {ccy}
          </button>
        ))}
      </div>

      {/* ── KPI SUMMARY ── */}
      <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr) repeat(3,1fr)', gap:8 }}>
        {[
          ['Cost Value',    sym+totalCost.toLocaleString('de-DE',{maximumFractionDigits:0}),    null],
          ['Market Value',  sym+totalMkt.toLocaleString('de-DE',{maximumFractionDigits:0}),     null],
          ['Total Gain',    sym+(totalGain>=0?'+':'')+totalGain.toLocaleString('de-DE',{maximumFractionDigits:0}), totalGain],
          ['Total Gain %',  fp(totalGainPct),    totalGainPct],
          ['Daily Change',  sym+(totalDaily>=0?'+':'')+totalDaily.toLocaleString('de-DE',{maximumFractionDigits:0}), totalDaily],
          ['Daily Change %',fp(ewChg1d),         ewChg1d],
        ] as Array<[string,string,number|null]>).map(([label,value,colorVal]) => (
          <div key={label} className="metric-card">
            <div className="metric-label">{label}</div>
            <div className="metric-value" style={{
              color: colorVal != null
                ? colorVal > 0 ? 'var(--green)' : colorVal < 0 ? 'var(--red)' : 'var(--text3)'
                : 'var(--orange)'
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
        <>
          {/* ── POSITIONS TABLE ── */}
          <div style={{ background:'var(--surface)', border:'1px solid var(--border)', borderRadius:4, overflow:'hidden' }}>
            <div style={{ overflowX:'auto' }}>
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Ticker</th>
                    <th>Company</th>
                    <th>Sector</th>
                    <th>Qty</th>
                    <th>Buy €</th>
                    <th>Last €</th>
                    <th>1D %</th>
                    <th>Cost Val €</th>
                    <th>Mkt Val €</th>
                    <th>Weight %</th>
                    <th>Gain €</th>
                    <th>Gain %</th>
                    <th>Daily € Chg</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {rowsWithWeight.map((r:any, i:number) => (
                    <tr key={i}>
                      <td>
                        <span style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700, color:'var(--orange)' }}>
                          {r.flag} {r.ticker}
                        </span>
                      </td>
                      <td><span style={{ color:'var(--text2)', fontSize:12 }}>{r.company}</span></td>
                      <td><span style={{ color:'var(--text3)', fontSize:11 }}>{r.sector||'—'}</span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono' }}>{r.qty}</span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono' }}>€{(+r.buy_price).toFixed(2)}</span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono', color:'var(--text)' }}>€{r.lastPx.toFixed(2)}</span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:600,
                        color: r.chg1d!=null?(r.chg1d>=0?'var(--green)':'var(--red)'):'var(--text3)' }}>
                        {fp(r.chg1d)}
                      </span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono' }}>€{r.costVal.toLocaleString('de-DE',{maximumFractionDigits:0})}</span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:600, color:'var(--text)' }}>
                        €{r.mktVal.toLocaleString('de-DE',{maximumFractionDigits:0})}
                      </span></td>
                      <td>
                        <div style={{ display:'flex', alignItems:'center', gap:5 }}>
                          <div style={{ height:4, background:'var(--orange)',
                            borderRadius:2, width:`${Math.min(r.weight,100)}%`, minWidth:2,
                            maxWidth:60, flexShrink:0 }} />
                          <span style={{ fontFamily:'IBM Plex Mono', fontSize:11, color:'var(--text2)' }}>
                            {r.weight.toFixed(1)}%
                          </span>
                        </div>
                      </td>
                      <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:600,
                        color: r.gainEur>=0?'var(--green)':'var(--red)' }}>
                        €{r.gainEur>=0?'+':''}{r.gainEur.toLocaleString('de-DE',{maximumFractionDigits:0})}
                      </span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:600,
                        color: r.gainPct!=null?(r.gainPct>=0?'var(--green)':'var(--red)'):'var(--text3)' }}>
                        {fp(r.gainPct)}
                      </span></td>
                      <td><span style={{ fontFamily:'IBM Plex Mono',
                        color: r.dailyChg!=null?(r.dailyChg>=0?'var(--green)':'var(--red)'):'var(--text3)' }}>
                        {r.dailyChg!=null ? `€${r.dailyChg>=0?'+':''}${r.dailyChg.toLocaleString('de-DE',{maximumFractionDigits:0})}` : '—'}
                      </span></td>
                      <td>
                        <button onClick={()=>removePosition(i)}
                          style={{ color:'var(--red)', fontSize:12, cursor:'pointer',
                            background:'none', border:'none', padding:'2px 8px' }}>
                          ✕
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
                {/* ── TOTALS ROW ── */}
                <tfoot>
                  <tr style={{ background:'var(--surface2)', borderTop:'2px solid var(--border)' }}>
                    <td colSpan={3} style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
                      fontSize:11, color:'var(--orange)', textTransform:'uppercase', letterSpacing:'0.08em' }}>
                      TOTAL ({positions.length} positions)
                    </td>
                    <td></td><td></td><td></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:700,
                      color: ewChg1d!=null?(ewChg1d>=0?'var(--green)':'var(--red)'):'var(--text3)' }}>
                      {fp(ewChg1d)}
                    </span></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:700 }}>
                      €{totalCost.toLocaleString('de-DE',{maximumFractionDigits:0})}
                    </span></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:700, color:'var(--text)' }}>
                      €{totalMkt.toLocaleString('de-DE',{maximumFractionDigits:0})}
                    </span></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:700, color:'var(--orange)' }}>100%</span></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:700,
                      color: totalGain>=0?'var(--green)':'var(--red)' }}>
                      €{totalGain>=0?'+':''}{totalGain.toLocaleString('de-DE',{maximumFractionDigits:0})}
                    </span></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:700,
                      color: totalGainPct!=null?(totalGainPct>=0?'var(--green)':'var(--red)'):'var(--text3)' }}>
                      {fp(totalGainPct)}
                    </span></td>
                    <td><span style={{ fontFamily:'IBM Plex Mono', fontWeight:700,
                      color: totalDaily>=0?'var(--green)':'var(--red)' }}>
                      €{totalDaily>=0?'+':''}{totalDaily.toLocaleString('de-DE',{maximumFractionDigits:0})}
                    </span></td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          {/* ── WEIGHTED PORTFOLIO METRICS ── */}
          <div style={{ background:'var(--surface)', border:'1px solid var(--border)', borderRadius:4, padding:16 }}>
            <div style={{ fontSize:10, fontFamily:'IBM Plex Sans Condensed', fontWeight:700,
              letterSpacing:'0.12em', textTransform:'uppercase', color:'var(--text3)', marginBottom:12,
              paddingBottom:8, borderBottom:'1px solid var(--border)' }}>
              Portfolio Weighted Metrics — Market Value Weighted Averages
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8, marginBottom:12 }}>
              {/* Valuation */}
              <div style={{ gridColumn:'1/-1', fontSize:9, fontFamily:'IBM Plex Sans Condensed',
                fontWeight:700, letterSpacing:'0.1em', textTransform:'uppercase',
                color:'var(--orange)', marginBottom:4 }}>Valuation</div>
              {[
                ['Wgt Avg P/E Trailing', fv(wMetrics.peTrail,1), null],
                ['Wgt Avg P/E Forward',  fv(wMetrics.peFwd,1),   null],
              ] as Array<[string,string,number|null]>).map(([label,value,colorVal]) => (
                <div key={label} className="metric-card">
                  <div className="metric-label">{label}</div>
                  <div className="metric-value" style={{ fontSize:'0.95rem',
                    color: colorVal != null
                      ? colorVal > 0 ? 'var(--green)' : colorVal < 0 ? 'var(--red)' : 'var(--text3)'
                      : 'var(--orange)' }}>
                    {value}
                  </div>
                </div>
              ))}
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:8 }}>
              {/* Growth & Momentum */}
              <div style={{ gridColumn:'1/-1', fontSize:9, fontFamily:'IBM Plex Sans Condensed',
                fontWeight:700, letterSpacing:'0.1em', textTransform:'uppercase',
                color:'var(--orange)', marginBottom:4 }}>Growth & Momentum</div>
              {[
                ['Wgt Avg EPS Growth %',  fp(wMetrics.epsGrowth ? wMetrics.epsGrowth*100 : null, 1), wMetrics.epsGrowth],
                ['Wgt Avg Rev Growth %',  fp(wMetrics.revGrowth ? wMetrics.revGrowth*100 : null, 1), wMetrics.revGrowth],
                ['Wgt Avg 1D %',          fp(wMetrics.chg1d,1),       wMetrics.chg1d],
                ['Wgt Avg Mom 1W %',      fp(wMetrics.mom1w ? wMetrics.mom1w*100 : null, 1),  wMetrics.mom1w],
                ['Wgt Avg Mom 6M %',      fp(wMetrics.mom6m ? wMetrics.mom6m*100 : null, 1),  wMetrics.mom6m],
                ['Wgt Avg Mom 12M %',     fp(wMetrics.mom12m ? wMetrics.mom12m*100 : null, 1), wMetrics.mom12m],
              ] as Array<[string,string,number|null]>).map(([label,value,colorVal]) => (
                <div key={label} className="metric-card">
                  <div className="metric-label">{label}</div>
                  <div className="metric-value" style={{ fontSize:'0.95rem',
                    color: colorVal != null
                      ? colorVal > 0 ? 'var(--green)' : colorVal < 0 ? 'var(--red)' : 'var(--text3)'
                      : 'var(--orange)' }}>
                    {value}
                  </div>
                </div>
              ))}
            </div>
            {/* Value & Growth Scores */}
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:8, marginTop:8 }}>
              <div style={{ gridColumn:'1/-1', fontSize:9, fontFamily:'IBM Plex Sans Condensed',
                fontWeight:700, letterSpacing:'0.1em', textTransform:'uppercase',
                color:'var(--orange)', marginBottom:4, marginTop:4 }}>Composite Scores (1-100)</div>
              {[
                ['Weighted Value Score',  wMetrics.valueScore],
                ['Weighted Growth Score', wMetrics.growthScore],
              ] as Array<[string,number|null]>).map(([label,val]) => (
                <div key={label} className="metric-card" style={{ display:'flex', alignItems:'center', gap:16 }}>
                  <div style={{ flex:1 }}>
                    <div className="metric-label">{label}</div>
                    <div style={{ fontFamily:'IBM Plex Mono', fontSize:'1.4rem', fontWeight:700,
                      color: val != null ? val >= 60 ? 'var(--green)' : val >= 40 ? 'var(--orange)' : 'var(--red)' : 'var(--text3)' }}>
                      {val != null ? Math.round(val) : '—'}
                    </div>
                  </div>
                  {/* Score bar */}
                  {val != null && (
                    <div style={{ width:80 }}>
                      <div style={{ height:8, background:'var(--border)', borderRadius:4, overflow:'hidden' }}>
                        <div style={{ height:'100%', borderRadius:4, width:`${Math.min(val,100)}%`,
                          background: val >= 60 ? 'var(--green)' : val >= 40 ? 'var(--orange)' : 'var(--red)',
                          transition:'width 0.4s ease' }} />
                      </div>
                      <div style={{ fontSize:9, color:'var(--text3)', textAlign:'right', marginTop:3,
                        fontFamily:'IBM Plex Mono' }}>{Math.round(val)}/100</div>
                    </div>
                  )}
                </div>
              ))}
            </div>
            <div style={{ fontSize:10, color:'var(--text4)', marginTop:10, fontStyle:'italic' }}>
              All metrics are weighted by market value weight of each position.
              Formula: Rank(x) = (count(xi &lt; x) + 0.5 × count(xi = x)) / N × 100
            </div>
          </div>

          {/* ── PIE CHARTS ── */}
          {Object.keys(sectorMap).length > 0 && (
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:12 }}>
              <PieChart data={sectorMap} title="Sector Exposure (Market Value Weight %)" />
              <PieChart data={countryMap} title="Country Exposure (Market Value Weight %)" />
            </div>
          )}
        </>
      )}
    </div>
  )
}

