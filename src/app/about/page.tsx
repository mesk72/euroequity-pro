export default function AboutPage() {
  const sections = [
    {
      title: 'Our Philosophy',
      content: `ForwardAlpha was built on a simple but powerful conviction: European equity markets are systematically underanalyzed, and the tools available to serious investors have not kept pace with the opportunity.

While most financial platforms focus on US markets, Europe offers over 3,700 listed companies across 18 exchanges — from the Eurozone blue chips to Nordic growth companies and UK mid-caps — with valuation levels that have historically been more attractive than their American counterparts.

We combine two of the most proven investment philosophies — Value Investing and Growth Investing — into a single, transparent quantitative framework. Our goal is to give independent investors access to the same analytical rigor used by institutional portfolio managers.`
    },
    {
      {
      title: 'The Best Score',
      content: `The Best Score is ForwardAlpha's combined ranking — a single number that captures both the valuation attractiveness and growth momentum of a stock relative to the entire European universe.

It is calculated as the simple average of the Value Score and Growth Score, then re-ranked from 1 to 100 across all European stocks regardless of country.

A Best Score of 90 means the stock ranks in the top 10% of all European equities on our combined Value and Growth metrics — it is both attractively valued and showing strong growth momentum relative to the full European universe.

The Best Score is our primary screening tool for identifying European equity opportunities that combine both value and growth characteristics.`,
    },
    {title: 'Who We Are',
      content: `ForwardAlpha was founded by Andrea Meschini, a professional investor with over 15 years of institutional experience in European equity and alternative investment management.

Andrea began his career at Gestiveneto SGR, one of Italy's established asset management firms, before joining J.P. Morgan where he spent four years as Investment Analyst, Assistant Portfolio Manager and Junior Portfolio Manager, developing deep expertise in quantitative equity analysis and portfolio construction.

He subsequently joined Zenit SGR, where he spent eight years across two distinct roles: three years as Investment Analyst covering Funds of Hedge Funds, and five years as Portfolio Manager running a dedicated Eurozone equity mandate for a pension fund, applying both fundamental and quantitative approaches to stock selection.

Prior to founding ForwardAlpha, Andrea served as Senior Hedge Fund Analyst at Integrated Alternative Investments in London, where he focused on institutional-grade due diligence across alternative strategies.

This background informs every aspect of ForwardAlpha's methodology — from the way we construct our scoring models to the emphasis on data quality and intellectual honesty about what the numbers can and cannot tell us.`
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

• EPS Growth Rank — ranks stocks by expected earnings per share growth over the next 12 months. Calculated as EPS NTM divided by EPS LTM. Companies with negative trailing EPS receive a neutral rank of 50.
• Revenue Growth Rank — ranks stocks by top-line growth momentum using a time-weighted blend of fiscal year estimates. Revenue growth validates earnings growth and signals genuine business expansion. Companies with negative trailing revenue receive a neutral rank of 50.
• Price Momentum Rank (6M) — ranks stocks by medium-term price momentum, measuring the 6-month return excluding the most recent week to reduce short-term noise.
• Price Momentum Rank (12M) — ranks stocks by long-term price momentum, measuring the 12-month return excluding the most recent month.

The four components are averaged and re-ranked to produce the final Growth Score. All ranks are calculated within the stock's country universe.

A Growth Score of 70 means the stock has stronger growth characteristics than 70% of its European peers.`,
    },
    {
      title: 'How to Use ForwardAlpha',
      content: `Best Ideas — Value Score >= 70 and Growth Score >= 70
The sweet spot. Companies that are reasonably priced and growing faster than their peers. These are rare, and historically the most rewarding investments.

Best Value — Value Score >= 80 and Growth Score >= 30
Deep value opportunities. Companies trading at significant discounts to peers with at least some growth. Classic value investing territory.

Best Growth — Growth Score >= 80
High-growth companies regardless of valuation. Suitable for investors willing to pay a premium for exceptional growth.

Practical tips:
• Start with Best Ideas — the intersection of value and growth is where the best risk-adjusted returns are historically found.
• Use country filters — different European markets have different characteristics. Italian and Spanish financials often score high on value; Nordic technology companies often lead on growth.
• Check the sector — a P/E of 15x means very different things for a utility versus a software company.
• Look at the full picture — a high Value Score with negative EPS growth may signal a value trap. A high Growth Score with an extreme P/E may not leave a margin of safety.`
    },
    {
      title: 'Key Parameters',
      content: null,
      table: [
        ['P/E Forward', 'Price divided by next 12 months estimated earnings. Our primary valuation metric.'],
        ['P/E Trailing', 'Price divided by last 12 months actual earnings.'],
        ['P/B', 'Price-to-book ratio. Net asset value anchor, key for financials.'],
        ['EPS Growth %', 'Expected earnings per share growth, next 12 months vs trailing.'],
        ['Rev Growth %', 'Expected revenue growth, next 12 months.'],
        ['Mom 1M / 6M / 12M', 'Total return price performance over 1, 6 and 12 months in local currency.'],
        ['Value Score', 'Composite ranking on valuation metrics (1-100). Higher = cheaper vs peers.'],
        ['Growth Score', 'Composite ranking on growth and momentum metrics (1-100). Higher = faster growing.'],
      ]
    },
    {
      title: 'Data & Methodology',
      content: `Universe: 3,700+ stocks across 18 European exchanges including Borsa Italiana, Xetra, Euronext Paris, London Stock Exchange, Nasdaq Stockholm, Oslo Bors, SIX Swiss Exchange, Copenhagen, Helsinki and others.

Fundamentals: Sourced from institutional-grade data providers. Updated weekly every Friday after market close.

Prices: End-of-day prices in local currency. Updated daily after market close.

Scores: Value Score and Growth Score recalculated daily after market close using the latest prices and weekly fundamentals.

Currency: All market caps displayed in EUR billions. Prices shown in local currency.

Beta version: ForwardAlpha is currently in beta. Fundamental data is updated as of May 22, 2026. We are working to bring you daily updates. If you find this tool useful, register your interest at andrea@forwardalpha.pro`
    },
    {
      title: 'Disclaimer',
      content: `ForwardAlpha is a screening and research tool, not a registered investment advisor. All data and scores are provided for informational and educational purposes only and do not constitute investment advice or a recommendation to buy, sell or hold any security.

Investing in financial markets involves risk, including the possible loss of principal. Past performance is not indicative of future results. Always conduct your own due diligence and consider seeking advice from a qualified financial professional before making investment decisions.

ForwardAlpha makes no representation as to the accuracy, completeness or timeliness of the data presented.`
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
