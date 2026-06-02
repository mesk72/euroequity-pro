export default function AboutPage() {
  const sections = [
    {
      title: 'Our Philosophy',
      content: `ForwardAlpha was built on a simple but powerful conviction: European equity markets are underserved by modern financial technology.

While most financial platforms focus on US markets, Europe offers over 3,700 listed companies across 16 exchanges — a rich universe of opportunities that remains largely inaccessible to independent investors without institutional-grade tools.

We combine two of the most proven investment philosophies — Value Investing and Growth Investing — into a single, transparent quantitative framework. Our goal is to give independent investors access to the same analytical rigor used by institutional portfolio managers.`,
    },
    {
      title: 'Who We Are',
      content: `ForwardAlpha was founded by Andrea Meschini, a professional investor with over 15 years of experience in European equity research and portfolio management.

Andrea began his career at Gestiveneto SGR, one of Italy's established asset management firms, before moving to JPMorgan Asset Management in London, where he worked as a European equity analyst covering multiple sectors.

He subsequently joined Zenit SGR, where he spent eight years across two distinct roles: three years as a portfolio manager running long-only European equity mandates, followed by five years as Head of Equity Research, overseeing a team of analysts covering the Italian and broader European equity universe.

Prior to founding ForwardAlpha, Andrea served as Senior Hedge Fund Analyst at Integrated Alternative Investments, focusing on manager selection and due diligence across European long/short equity strategies.

This background informs every aspect of ForwardAlpha's methodology — from the way we construct our scoring models to the metrics we prioritise and the rigour we apply to data quality.`,
    },
    {
      title: 'The Value Score',
      content: `The Value Score measures how attractively priced a stock is relative to its peers in the same market.

Inspired by the principles of Benjamin Graham and Warren Buffett, value investing rests on a fundamental truth: markets are often irrational in the short term. Great companies get temporarily mispriced. Patient investors who identify these opportunities and buy at a discount to fair value are rewarded over time.

Our Value Score combines three rank components, each calculated relative to all stocks listed on the same exchange:

• PE LTM Rank — ranks stocks by trailing earnings yield (1/PE). A high rank means the stock earns more relative to its price than its peers. Negative earnings are excluded.
• PE NTM Rank — ranks stocks by forward earnings yield based on next-twelve-month consensus estimates. Forward-looking and more predictive than trailing earnings.
• PB Rank — ranks stocks by Price/Book ratio. Lower P/B means more assets per dollar of market value. Negative book value stocks receive rank 0.

Each component is ranked from 1 to 100 within the stock's country. The three ranks are averaged and re-ranked to produce the final Value Score. A minimum of two components must be available; otherwise the stock receives a neutral score of 50.

A Value Score of 80 means the stock is cheaper than 80% of its peers on our combined valuation metrics.`,
    },
    {
      title: 'The Growth Score',
      content: `The Growth Score measures a company's growth momentum across earnings, revenue, and price — the three pillars of fundamental momentum investing.

Growth investing seeks companies that are expanding faster than the market expects. The most durable returns come from businesses where earnings, revenues, and market recognition are all moving in the same direction.

Our Growth Score combines four rank components, each calculated relative to all stocks listed on the same exchange:

• EPS Growth Rank — ranks stocks by expected earnings per share growth over the next 12 months, calculated as EPS NTM divided by EPS LTM using the absolute value of the denominator. This means turnaround companies with negative trailing EPS are included in the ranking.
• Revenue Growth Rank — ranks stocks by top-line growth momentum using a time-weighted blend of fiscal year estimates. Revenue growth validates earnings growth and signals genuine business expansion. Companies with negative trailing revenue receive a neutral rank of 50.
• Price Momentum — we rank stocks based on medium and long-term price momentum, using 6-month and 12-month return windows. Short-term noise is reduced by excluding the most recent period from each window. Markets tend to anticipate future growth; stocks that have outperformed over these horizons often continue to do so.

The four components are averaged and re-ranked to produce the final Growth Score. All ranks are calculated within the stock's country universe.

A Growth Score of 70 means the stock has stronger growth characteristics than 70% of its peers.`,
    },
    {
      title: 'The Best Score',
      content: `The Best Score is ForwardAlpha's combined ranking — a single number that captures both the valuation attractiveness and growth momentum of a stock relative to the entire European universe.

It is calculated as the simple average of the Value Score and Growth Score, then re-ranked from 1 to 100 across all European stocks regardless of country.

A Best Score of 80 or above places a stock in the top 20% of all European equities — combining both attractive valuation and strong growth momentum. These are ForwardAlpha's Best Ideas: stocks where value and growth reinforce each other.

The Best Score is our primary screening tool for identifying European equity opportunities.`,
    },
    {
      title: 'How to Use ForwardAlpha',
      content: `ForwardAlpha is designed for investors who want a rigorous, data-driven starting point for European equity research.

Key parameters to focus on:

• Best Score ≥ 80 — the top 20% of European equities combining Value and Growth. Our primary Best Ideas filter.
• Value Score — use to identify attractively valued stocks within a sector or country.
• Growth Score — use to identify companies with strong earnings, revenue and price momentum.
• Momentum 6M and 12M — medium and long-term price performance indicators.

All data is updated weekly. Fundamental data (PE, PB, Revenue, EPS) reflects the latest available consensus estimates. Last updated: 1 June 2026.`,
    },
  ]


  return (
    <div style={{ background:'#0a0e1a', minHeight:'100vh', color:'#e2e8f0', fontFamily:'IBM Plex Sans, sans-serif', padding:'40px 24px' }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap');`}</style>
      <div style={{ maxWidth:800, margin:'0 auto' }}>

        {/* Header */}
        <div style={{ marginBottom:32, borderBottom:'2px solid #f97316', paddingBottom:16 }}>
          <a href="/" style={{ textDecoration:'none' }}>
            <div style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:24, color:'#f97316' }}>
              FORWARD<span style={{ color:'#94a3b8' }}>ALPHA</span>
            </div>
          </a>
          <div style={{ fontSize:9, color:'#64748b', marginTop:4, letterSpacing:'0.14em', fontFamily:'IBM Plex Sans Condensed', fontWeight:600 }}>
            EUROPEAN EQUITY RESEARCH · METHODOLOGY · PHILOSOPHY
          </div>
        </div>

        {/* Title */}
        <div style={{ marginBottom:32 }}>
          <h1 style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:28, color:'#e2e8f0', margin:0, marginBottom:8 }}>
            About ForwardAlpha
          </h1>
          <p style={{ fontSize:14, color:'#64748b', lineHeight:1.7, margin:0 }}>
            A quantitative framework for European equity research, built by an institutional investor for serious investors.
          </p>
        </div>

        {/* Sections */}
        {sections.map(({ title, content, table }: any) => (
          <div key={title} style={{ marginBottom:16, background:'#111827', border:'1px solid #1e2d45', borderRadius:6, overflow:'hidden' }}>
            <div style={{ background:'#161d2e', padding:'12px 20px', borderBottom:'1px solid #1e2d45', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:14, color:'#f97316' }}>
              {title}
            </div>
            <div style={{ padding:'16px 20px' }}>
              {content && content.split('\n\n').map((para: string, i: number) => (
                <p key={i} style={{ fontSize:13, color:'#94a3b8', lineHeight:1.8, margin:0, marginBottom: i < content.split('\n\n').length-1 ? 12 : 0, whiteSpace:'pre-line' }}>
                  {para}
                </p>
              ))}
              {table && (
                <table style={{ width:'100%', borderCollapse:'collapse' }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign:'left', fontSize:10, color:'#64748b', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, letterSpacing:'0.1em', textTransform:'uppercase', paddingBottom:8, borderBottom:'1px solid #1e2d45', width:'35%' }}>Parameter</th>
                      <th style={{ textAlign:'left', fontSize:10, color:'#64748b', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, letterSpacing:'0.1em', textTransform:'uppercase', paddingBottom:8, borderBottom:'1px solid #1e2d45' }}>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {table.map(([param, desc]: [string, string], i: number) => (
                      <tr key={param} style={{ borderBottom: i < table.length-1 ? '1px solid rgba(30,45,69,0.5)' : 'none' }}>
                        <td style={{ padding:'8px 0', paddingRight:16, fontSize:12, color:'#f97316', fontFamily:'IBM Plex Sans Condensed', fontWeight:600 }}>{param}</td>
                        <td style={{ padding:'8px 0', fontSize:12, color:'#64748b', lineHeight:1.6 }}>{desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        ))}

        {/* Contact CTA */}
        <div style={{ marginBottom:16, background:'linear-gradient(135deg, #1a1f35, #161d2e)', border:'1px solid #f97316', borderRadius:6, padding:'24px 20px', textAlign:'center' }}>
          <div style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:16, color:'#f97316', marginBottom:8 }}>
            Interested in ForwardAlpha?
          </div>
          <p style={{ fontSize:13, color:'#94a3b8', lineHeight:1.7, margin:0, marginBottom:16 }}>
            ForwardAlpha is currently in beta. Register your interest to be notified at launch and receive early access.
          </p>
          <a href="mailto:andrea@forwardalpha.pro"
            style={{ display:'inline-block', background:'#f97316', color:'#0a0e1a', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:13, padding:'10px 24px', borderRadius:4, textDecoration:'none', letterSpacing:'0.05em' }}>
            CONTACT US
          </a>
        </div>

        {/* Footer */}
        <div style={{ fontSize:10, color:'#3d5068', textAlign:'center', paddingTop:16, borderTop:'1px solid #1e2d45', marginTop:8 }}>
          ForwardAlpha · Verona, Italy · © 2026 Andrea Meschini · <a href="/legal" style={{ color:'#f97316' }}>Legal & Privacy</a>
        </div>
      </div>
    </div>
  )
}
