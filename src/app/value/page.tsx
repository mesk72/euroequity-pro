'use client'

import { useState, useEffect } from 'react'
import { RefreshCw, ArrowLeft } from 'lucide-react'

const SECTOR_COLORS: Record<string, string> = {
  'Financials':'#3b82f6','Technology':'#8b5cf6','Health Care':'#10b981',
  'Energy':'#f59e0b','Industrials':'#6366f1','Consumer Discretionary':'#ec4899',
  'Consumer Staples':'#14b8a6','Materials':'#f97316','Utilities':'#06b6d4',
  'Communication Services':'#84cc16','Real Estate':'#a855f7','Other':'#6b7280',
}

function fp(v?:number|null,d=1):string{ if(v==null||isNaN(v))return'-'; return `${v>=0?'+':''}${v.toFixed(d)}%` }
function fv(v?:number|null,d=2):string{ if(v==null||isNaN(v))return'-'; return (v as number).toFixed(d) }
function fn(v?:number|null):string{ if(v==null||isNaN(v as number))return'-'; return String(Math.round(v as number)) }

function ScoreBar({value,label}:{value:number|null|undefined,label:string}) {
  if(value==null) return <div><div style={{fontSize:9,color:'#6b7280',textTransform:'uppercase',letterSpacing:'0.1em',marginBottom:4}}>{label}</div><div style={{fontSize:12,color:'#6b7280',fontFamily:'IBM Plex Mono'}}>-</div></div>
  const color = value>=70?'#22c55e':value>=40?'#f97316':'#ef4444'
  return (
    <div>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',marginBottom:4}}>
        <span style={{fontSize:9,color:'#6b7280',textTransform:'uppercase',letterSpacing:'0.1em'}}>{label}</span>
        <span style={{fontSize:12,fontWeight:700,fontFamily:'IBM Plex Mono',color}}>{Math.round(value)}</span>
      </div>
      <div style={{height:4,background:'rgba(255,255,255,0.1)',borderRadius:2,overflow:'hidden'}}>
        <div style={{height:'100%',borderRadius:2,width:`${value}%`,background:color,transition:'width 0.3s'}}/>
      </div>
    </div>
  )
}

type Tab = 'value' | 'growth' | 'combined' | 'dividend'

export default function ValuePage() {
  const [stocks,  setStocks]  = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [tab,     setTab]     = useState<Tab>('combined')
  const [exchange,setExchange]= useState('All')

  useEffect(() => {
    setLoading(true)
    fetch('/api/db/stocks')
      .then(r => r.ok ? r.json() : { stocks: [] })
      .then(d => { setStocks(d.stocks||[]); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const exchanges = ['All', ...Array.from(new Set(stocks.map((s:any)=>s.exchange))).sort()] as string[]
  const filtered  = exchange==='All' ? stocks : stocks.filter((s:any)=>s.exchange===exchange)

  const sorted = [...filtered].filter((s:any) => {
    if (tab==='value')    return s.valueScore!=null
    if (tab==='growth')   return s.growthScore!=null
    if (tab==='combined') return s.valueScore!=null && s.growthScore!=null
    if (tab==='dividend') return s.divYield!=null && s.divYield>0
    return true
  }).sort((a:any,b:any) => {
    if (tab==='value')    return (b.valueScore||0)-(a.valueScore||0)
    if (tab==='growth')   return (b.growthScore||0)-(a.growthScore||0)
    if (tab==='combined') return ((b.valueScore||0)+(b.growthScore||0))-((a.valueScore||0)+(a.growthScore||0))
    if (tab==='dividend') return (b.divYield||0)-(a.divYield||0)
    return 0
  }).slice(0, 100)

  const tabs: {id:Tab,label:string}[] = [
    {id:'combined', label:'⭐ Best Combined'},
    {id:'value',    label:'💎 Best Value'},
    {id:'growth',   label:'🚀 Best Growth'},
    {id:'dividend', label:'💰 Best Dividend'},
  ]

  return (
    <div style={{ background:'var(--bg)',minHeight:'100vh',color:'var(--text)',
      fontFamily:'IBM Plex Sans, sans-serif',padding:24 }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap');
      *{box-sizing:border-box;margin:0;padding:0}
      table{width:100%;border-collapse:collapse;font-size:12px}
      th{padding:8px 10px;text-align:left;border-bottom:1px solid #1e2840;font-size:9px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;color:#6b7280;white-space:nowrap}
      td{padding:7px 10px;border-bottom:1px solid #0f1623;white-space:nowrap}
      tr:hover td{background:rgba(255,255,255,0.03)}
      select{background:#0f1623;border:1px solid #1e2840;color:#e2e8f0;padding:6px 10px;border-radius:4px;font-size:12px;font-family:inherit}
      `}</style>

      <a href="/" style={{ display:'flex',alignItems:'center',gap:8,color:'#f97316',textDecoration:'none',fontSize:13,marginBottom:20 }}>
        <ArrowLeft size={14}/> Back
      </a>

      <div style={{ fontFamily:'IBM Plex Sans Condensed',fontWeight:700,fontSize:22,marginBottom:4 }}>
        ⭐ Best Opportunities — All Europe
      </div>
      <div style={{ fontSize:11,color:'#6b7280',marginBottom:20 }}>
        Top 100 stocks by score · Ranks calculated per country
      </div>

      {/* Tabs */}
      <div style={{ display:'flex',gap:8,marginBottom:16,flexWrap:'wrap' }}>
        {tabs.map(t=>(
          <button key={t.id} onClick={()=>setTab(t.id)}
            style={{ padding:'8px 16px',borderRadius:4,border:'1px solid',cursor:'pointer',fontSize:12,fontWeight:600,fontFamily:'IBM Plex Sans Condensed',
              background:tab===t.id?'#f97316':'transparent',
              borderColor:tab===t.id?'#f97316':'#1e2840',
              color:tab===t.id?'#fff':'#94a3b8' }}>
            {t.label}
          </button>
        ))}
        <select value={exchange} onChange={e=>setExchange(e.target.value)} style={{ marginLeft:'auto' }}>
          {exchanges.map(e=><option key={e}>{e}</option>)}
        </select>
      </div>

      {loading ? (
        <div style={{ textAlign:'center',padding:60,color:'#6b7280' }}>
          <RefreshCw size={24} style={{ animation:'spin 1s linear infinite',margin:'0 auto 12px',display:'block' }}/>
          Loading data…
        </div>
      ) : (
        <div style={{ background:'#0d1220',border:'1px solid #1e2840',borderRadius:4,overflowX:'auto' }}>
          <table>
            <thead><tr>
              <th>Ticker</th><th>Company</th><th>Sector</th><th>Exchange</th>
              <th>Price</th><th>1D %</th><th>Mkt Cap B</th>
              <th>P/E</th><th>P/B</th>
              {tab==='dividend'&&<th>Div Yield</th>}
              <th style={{minWidth:120}}>Value Score</th>
              <th style={{minWidth:120}}>Growth Score</th>
            </tr></thead>
            <tbody>
              {sorted.map((s:any,i:number)=>(
                <tr key={i} onClick={()=>window.location.href=`/stock/${s.ticker}-${s.exchange}`}
                  style={{ cursor:'pointer' }}>
                  <td style={{ fontFamily:'IBM Plex Sans Condensed',fontWeight:700,color:'#f97316' }}>{s.flag} {s.ticker}</td>
                  <td style={{ color:'#94a3b8',maxWidth:160,overflow:'hidden',textOverflow:'ellipsis' }}>{s.company}</td>
                  <td style={{ fontSize:10,fontWeight:600,color:SECTOR_COLORS[s.sector||'']||'#6b7280' }}>{s.sector||'-'}</td>
                  <td style={{ fontSize:10,color:'#6b7280' }}>{s.exchange}</td>
                  <td style={{ fontFamily:'IBM Plex Mono' }}>{fv(s.price,2)}</td>
                  <td style={{ fontFamily:'IBM Plex Mono',color:(s.change1d||0)>=0?'#22c55e':'#ef4444' }}>{fp(s.change1d)}</td>
                  <td style={{ fontFamily:'IBM Plex Mono',color:'#94a3b8' }}>{fv(s.mktCap,1)}</td>
                  <td style={{ fontFamily:'IBM Plex Mono',color:'#94a3b8' }}>{fv(s.peTrail,1)}</td>
                  <td style={{ fontFamily:'IBM Plex Mono',color:'#94a3b8' }}>{fv(s.pb,2)}</td>
                  {tab==='dividend'&&<td style={{ fontFamily:'IBM Plex Mono',color:'#22c55e',fontWeight:700 }}>{fv(s.divYield,2)}%</td>}
                  <td style={{ minWidth:120,paddingRight:16 }}>
                    <ScoreBar value={s.valueScore} label="Value"/>
                  </td>
                  <td style={{ minWidth:120,paddingRight:16 }}>
                    <ScoreBar value={s.growthScore} label="Growth"/>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ textAlign:'center',padding:8,fontSize:10,color:'#6b7280' }}>
            Top 100 · {filtered.length} total stocks in universe
          </div>
        </div>
      )}
    </div>
  )
}
