'use client'

import { useState, useEffect } from 'react'
import { RefreshCw, ArrowLeft } from 'lucide-react'

const SECTOR_COLORS: Record<string, string> = {
  'Financials':'#3b82f6','Technology':'#8b5cf6','Health Care':'#10b981',
  'Energy':'#f59e0b','Industrials':'#6366f1','Consumer Discretionary':'#ec4899',
  'Consumer Staples':'#14b8a6','Materials':'#f97316','Utilities':'#06b6d4',
  'Communication Services':'#84cc16','Real Estate':'#a855f7','Other':'#6b7280',
}

function fp(v?: number|null,d=2):string{ if(v==null||isNaN(v))return'-'; return `${v>=0?'+':''}${v.toFixed(d)}%` }
function fv(v?: number|null,d=2):string{ if(v==null||isNaN(v))return'-'; return (v as number).toFixed(d) }
function fn(v?: number|null):string{ if(v==null||isNaN(v as number))return'-'; return String(Math.round(v as number)) }

export default function DividendsPage() {
  const [stocks,   setStocks]   = useState<any[]>([])
  const [loading,  setLoading]  = useState(true)
  const [minYield, setMinYield] = useState(2)
  const [maxPayout,setMaxPayout]= useState(100)
  const [sector,   setSector]   = useState('All')
  const [exchange, setExchange] = useState('All')

  useEffect(() => {
    const load = () => {
      fetch('/api/db/stocks')
        .then(r => r.ok ? r.json() : { stocks: [] })
        .then(d => {
          const divStocks = (d.stocks || []).filter((s: any) => s.divYield && s.divYield > 0)
          setStocks(divStocks)
          setLoading(false)
        })
        .catch(() => setLoading(false))
    }
    load()
    const interval = setInterval(load, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [])

  const sectors   = ['All', ...Array.from(new Set(stocks.map((s:any)=>s.sector).filter(Boolean))).sort()] as string[]
  const exchanges = ['All', ...Array.from(new Set(stocks.map((s:any)=>s.exchange))).sort()] as string[]

  const filtered = stocks.filter((s:any) => {
    if ((s.divYield||0) < minYield) return false
    if (maxPayout < 100 && s.divPayout != null && s.divPayout > maxPayout) return false
    if (sector !== 'All' && s.sector !== sector) return false
    if (exchange !== 'All' && s.exchange !== exchange) return false
    return true
  }).sort((a:any,b:any) => (b.divYield||0)-(a.divYield||0))

  const avgYield = filtered.length > 0
    ? filtered.reduce((acc:number,s:any)=>acc+(s.divYield||0),0)/filtered.length
    : 0
  const highYield = filtered.filter((s:any)=>(s.divYield||0)>=5).length
  const maxY = filtered.length > 0 ? Math.max(...filtered.map((s:any)=>s.divYield||0)) : 0

  return (
    <div style={{ background:'var(--bg)', minHeight:'100vh', color:'var(--text)',
      fontFamily:'IBM Plex Sans, sans-serif', padding:24 }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap');
      *{box-sizing:border-box;margin:0;padding:0}
      table{width:100%;border-collapse:collapse;font-size:12px}
      th{padding:8px 10px;text-align:left;border-bottom:1px solid #1e2840;font-size:9px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#6b7280;white-space:nowrap;cursor:pointer}
      td{padding:7px 10px;border-bottom:1px solid #0f1623;white-space:nowrap}
      tr:hover td{background:rgba(255,255,255,0.03)}
      input,select{background:#0f1623;border:1px solid #1e2840;color:#e2e8f0;padding:6px 10px;border-radius:4px;font-size:12px;font-family:inherit}
      `}</style>

      <a href="/" style={{ display:'flex',alignItems:'center',gap:8,color:'var(--orange,#f97316)',
        textDecoration:'none',fontSize:13,marginBottom:20 }}>
        <ArrowLeft size={14}/> Back to Dashboard
      </a>

      <div style={{ fontFamily:'IBM Plex Sans Condensed',fontWeight:700,fontSize:22,marginBottom:4 }}>
        💰 Dividend Stocks
      </div>
      <div style={{ fontSize:11,color:'#6b7280',marginBottom:20 }}>
        Fundamentals updated daily
      </div>

      {/* KPI */}
      <div style={{ display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12,marginBottom:20 }}>
        {[
          { label:'Dividend Stocks',        value: loading?'…':filtered.length.toString() },
          { label:'Avg Dividend Yield (EW)', value: loading?'…':`${avgYield.toFixed(2)}%` },
          { label:'High Yield (≥5%)',        value: loading?'…':highYield.toString() },
          { label:'Highest Yield',           value: loading?'…':`${maxY.toFixed(2)}%` },
        ].map(({label,value})=>(
          <div key={label} style={{ background:'#0d1220',border:'1px solid #1e2840',borderRadius:4,padding:'12px 16px' }}>
            <div style={{ fontSize:9,fontFamily:'IBM Plex Sans Condensed',fontWeight:700,letterSpacing:'0.1em',textTransform:'uppercase',color:'#6b7280',marginBottom:6 }}>{label}</div>
            <div style={{ fontFamily:'IBM Plex Mono',fontSize:20,fontWeight:700,color:'#22c55e' }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div style={{ background:'#0d1220',border:'1px solid #1e2840',borderRadius:4,padding:16,marginBottom:16,display:'flex',flexWrap:'wrap',gap:12,alignItems:'center' }}>
        <div>
          <div style={{ fontSize:9,color:'#6b7280',marginBottom:4,textTransform:'uppercase',letterSpacing:'0.1em' }}>Min Yield %</div>
          <input type="number" value={minYield} onChange={e=>setMinYield(+e.target.value||0)} style={{ width:80 }}/>
        </div>
        <div>
          <div style={{ fontSize:9,color:'#6b7280',marginBottom:4,textTransform:'uppercase',letterSpacing:'0.1em' }}>Max Payout %</div>
          <input type="number" value={maxPayout} onChange={e=>setMaxPayout(+e.target.value||100)} style={{ width:80 }}/>
        </div>
        <div>
          <div style={{ fontSize:9,color:'#6b7280',marginBottom:4,textTransform:'uppercase',letterSpacing:'0.1em' }}>Sector</div>
          <select value={sector} onChange={e=>setSector(e.target.value)} style={{ width:160 }}>
            {sectors.map(s=><option key={s}>{s}</option>)}
          </select>
        </div>
        <div>
          <div style={{ fontSize:9,color:'#6b7280',marginBottom:4,textTransform:'uppercase',letterSpacing:'0.1em' }}>Exchange</div>
          <select value={exchange} onChange={e=>setExchange(e.target.value)} style={{ width:100 }}>
            {exchanges.map(e=><option key={e}>{e}</option>)}
          </select>
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign:'center',padding:60,color:'#6b7280' }}>
          <RefreshCw size={24} style={{ animation:'spin 1s linear infinite',margin:'0 auto 12px',display:'block' }}/>
          Loading dividend stocks…
        </div>
      ) : (
        <div style={{ background:'#0d1220',border:'1px solid #1e2840',borderRadius:4,overflowX:'auto' }}>
          <table>
            <thead><tr>
              <th>Ticker</th><th>Company</th><th>Sector</th><th>Price</th>
              <th>Div Yield %</th><th>Payout %</th><th>P/E Tr.</th><th>P/B</th>
              <th>ROE %</th><th>Value</th><th>Growth</th>
            </tr></thead>
            <tbody>
              {filtered.slice(0,200).map((s:any,i:number)=>(
                <tr key={i} onClick={()=>window.location.href=`/stock/${s.ticker}-${s.exchange}`}
                  style={{ cursor:'pointer' }}>
                  <td style={{ fontFamily:'IBM Plex Sans Condensed',fontWeight:700,color:'#f97316' }}>{s.flag} {s.ticker}</td>
                  <td style={{ color:'#94a3b8',maxWidth:160,overflow:'hidden',textOverflow:'ellipsis' }}>{s.company}</td>
                  <td style={{ fontSize:10,fontWeight:600,color:SECTOR_COLORS[s.sector||'']||'#6b7280' }}>{s.sector||'-'}</td>
                  <td style={{ fontFamily:'IBM Plex Mono' }}>{fv(s.price,2)}</td>
                  <td style={{ fontFamily:'IBM Plex Mono',fontWeight:700,color:'#22c55e' }}>{fv(s.divYield,2)}%</td>
                  <td style={{ fontFamily:'IBM Plex Mono',color:'#94a3b8' }}>{s.divPayout!=null?`${fv(s.divPayout,1)}%`:'-'}</td>
                  <td style={{ fontFamily:'IBM Plex Mono',color:'#94a3b8' }}>{fv(s.peTrail,1)}</td>
                  <td style={{ fontFamily:'IBM Plex Mono',color:'#94a3b8' }}>{fv(s.pb,2)}</td>
                  <td style={{ fontFamily:'IBM Plex Mono',color:(s.roe||0)>0?'#22c55e':'#ef4444' }}>{fp(s.roe)}</td>
                  <td style={{ fontFamily:'IBM Plex Mono',fontWeight:700,
                    color:(s.valueScore||0)>=70?'#22c55e':(s.valueScore||0)>=40?'#f97316':'#ef4444' }}>
                    {fn(s.valueScore)}
                  </td>
                  <td style={{ fontFamily:'IBM Plex Mono',fontWeight:700,
                    color:(s.growthScore||0)>=70?'#22c55e':(s.growthScore||0)>=40?'#f97316':'#ef4444' }}>
                    {fn(s.growthScore)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length > 200 && (
            <div style={{ textAlign:'center',padding:8,fontSize:10,color:'#6b7280' }}>
              Showing top 200 of {filtered.length} dividend stocks by yield
            </div>
          )}
        </div>
      )}
    </div>
  )
}
