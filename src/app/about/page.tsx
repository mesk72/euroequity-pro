export default function AboutPage() {
  const sections = [
    {
      title: 'Our Philosophy',
      content: `ForwardAlpha applies a quantitative methodology used by institutional portfolio managers to analyse global equities.

We cover approximately 8,500 stocks across three continents: roughly 2,100 stocks across 16 European exchanges, approximately 3,400 stocks in North America (US and Canada), and approximately 2,350 stocks across Asia Pacific (Japan, Hong Kong, Australia, Korea and Singapore).

We combine two of the most proven investment philosophies — Value Investing and Growth Investing — into a single, transparent quantitative framework. Our goal is to give independent investors access to the same analytical rigor used by institutional portfolio managers.`,
    },
    {
      title: 'Who We Are',
      content: `ForwardAlpha was founded by Andrea Meschini, a professional investor with over 15 years of experience in European equity research and portfolio management.

Andrea began his career at Gestiveneto SGR, one of Italy's established asset management firms, before moving to JPMorgan Asset Management in London, where he worked as a European equity analyst covering multiple sectors.

He subsequently joined Zenit SGR, where he spent eight years across two distinct roles: three years as Investment Analyst on Hedge Fund and Value Fund strategies, and five years as Portfolio Manager running long-only Euroequity and Italian Equity portfolios equity mandates, followed by five years as Head of Equity Research, overseeing a team of analysts covering the Italian and broader European equity universe.

Prior to founding ForwardAlpha, Andrea served as Senior Hedge Fund Analyst at Integrated Alternative Investments, focusing on manager selection and due diligencee diligence across European long/short equity strategies.

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

Each component is ranked from 1 to 100 within the stock's country. The three ranks are averaged and re-ranked to produce the final Value Score.

A Value Score of 80 means the stock is cheaper than 80% of its peers on our combined valuation metrics.`,
    },
    {
      title: 'The Growth Score',
      content: `The Growth Score measures a company's growth momentum across earnings, revenue, and price — the three pillars of fundamental momentum investing.

Our Growth Score combines four rank components, each calculated relative to all stocks listed on the same exchange:

• EPS Growth Rank — ranks stocks by expected earnings per share growth over the next 12 months.
• Revenue Growth Rank — ranks stocks by top-line growth momentum using a time-weighted blend of fiscal year estimates.
• Price Momentum 6M — 6-month price return, adjusted for overbought.
• Price Momentum 12M — 12-month price return, adjusted for overbought.

The four components are averaged and re-ranked to produce the final Growth Score.

A Growth Score of 70 means the stock has stronger growth characteristics than 70% of its peers.`,
    },
    {
      title: 'The Best Score',
      content: `The Best Score is ForwardAlpha's combined ranking — a single number that captures both the valuation attractiveness and growth momentum of a stock relative to its continental universe.

It is calculated as the sum of the Value Score and Growth Score, then re-ranked from 1 to 100 within Europe or North America respectively.

A Best Score of 80 or above places a stock in the top 20% of its universe — combining both attractive valuation and strong growth momentum.`,
    },
    {
      title: 'The Reverse Earnings Model',
      content: `Currently available for US stocks only.

Starting from the current price and the next-twelve-month EPS estimate, and holding a 2.5% terminal growth rate constant, the model solves backward for the earnings growth rate the market would need over the next ten years to justify today's price.

You can then compare that implied rate against faster or slower growth assumptions and see how the resulting price would change.

It is a way to read what growth the market is currently pricing in — not a price target, a projection, or a recommendation to buy or sell.`,
    },
    {
      title: 'How to Use ForwardAlpha',
      content: `Key parameters to focus on:

• Best Score ≥ 80 — the top 20% of equities combining Value and Growth. Our primary Best Ideas filter.
• Value Score — use to identify attractively valued stocks within a sector or country.
• Growth Score — use to identify companies with strong earnings, revenue and price momentum.
• Momentum 1W, 1M, 6M, 12M — short, medium and long-term price performance indicators, calculated on calendar days.

Prices are updated automatically every trading day. Fundamental data (PE, PB, Revenue, EPS) reflects the latest available consensus estimates and is updated weekly.

Coverage note: Value Score, Growth Score and Best Score are available for the following exchanges: London (LSE), Stockholm (OM), Paris (PA), Frankfurt (XETRA), Milan (MIL), Oslo (OB), Zurich (SWX), Helsinki (HE), Madrid (MC), Amsterdam (AS), Brussels (BR), Athens (GR), Copenhagen (CPSE), Vienna (VI), Dublin (IR), Lisbon (LS), New York/Nasdaq (US), Toronto (TSX), Tokyo (JPX), Hong Kong (HKEX), Seoul (KRX), Sydney (ASX) and Singapore (SGX). We are evaluating whether to add further markets in the future.

For smaller markets — Vienna (VI), Lisbon (LS) and Dublin (IR) — individual rank components are available but aggregate scores are not calculated.`,
    },
  ]

  return (
    <div style={{ background: '#0a0e1a', minHeight: '100vh', color: '#e2e8f0', fontFamily: 'IBM Plex Sans, sans-serif', padding: '40px 24px' }}>
      <div style={{ maxWidth: 800, margin: '0 auto' }}>

        <div style={{ marginBottom: 32, borderBottom: '2px solid #f97316', paddingBottom: 16 }}>
          <a href="/" style={{ textDecoration: 'none' }}>
            <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 24, color: '#f97316' }}>
              FORWARD<span style={{ color: '#94a3b8' }}>ALPHA</span>
            </div>
          </a>
          <div style={{ fontSize: 9, color: '#64748b', marginTop: 4, letterSpacing: '0.14em', fontFamily: 'IBM Plex Sans Condensed', fontWeight: 600 }}>
            GLOBAL EQUITY RESEARCH · METHODOLOGY · PHILOSOPHY
          </div>
        </div>

        <div style={{ marginBottom: 32 }}>
          <h1 style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 28, color: '#e2e8f0', margin: 0, marginBottom: 8 }}>
            About ForwardAlpha
          </h1>
          <p style={{ fontSize: 14, color: '#64748b', lineHeight: 1.7, margin: 0 }}>
            A quantitative framework for global equity research, built by an institutional investor for serious investors.
          </p>
        </div>

        {sections.map(({ title, content }: any) => (
          <div key={title} style={{ marginBottom: 16, background: '#111827', border: '1px solid #1e2d45', borderRadius: 6, overflow: 'hidden' }}>
            <div style={{ background: '#161d2e', padding: '12px 20px', borderBottom: '1px solid #1e2d45', fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 14, color: '#f97316' }}>
              {title}
            </div>
            <div style={{ padding: '16px 20px' }}>
              {content.split('\n\n').map((para: string, i: number) => (
                <p key={i} style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.8, margin: 0, marginBottom: i < content.split('\n\n').length - 1 ? 12 : 0, whiteSpace: 'pre-line' }}>
                  {para}
                </p>
              ))}
            </div>
          </div>
        ))}

        <div style={{ marginBottom: 16, background: 'linear-gradient(135deg, #1a1f35, #161d2e)', border: '1px solid #f97316', borderRadius: 6, padding: '24px 20px', textAlign: 'center' }}>
          <div style={{ fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 16, color: '#f97316', marginBottom: 8 }}>
            Interested in ForwardAlpha?
          </div>
          <p style={{ fontSize: 13, color: '#94a3b8', lineHeight: 1.7, margin: 0, marginBottom: 16 }}>
            ForwardAlpha is currently in beta. Register your interest to be notified at launch and receive early access.
          </p>
          <a href="mailto:andrea@forwardalpha.pro"
            style={{ display: 'inline-block', background: '#f97316', color: '#0a0e1a', fontFamily: 'IBM Plex Sans Condensed', fontWeight: 700, fontSize: 13, padding: '10px 24px', borderRadius: 4, textDecoration: 'none', letterSpacing: '0.05em' }}>
            CONTACT US
          </a>
        </div>

        <div style={{ fontSize: 10, color: '#3d5068', textAlign: 'center', paddingTop: 16, borderTop: '1px solid #1e2d45', marginTop: 8 }}>
          ForwardAlpha · Verona, Italy · © 2026 Andrea Meschini · <a href="/legal" style={{ color: '#f97316' }}>Legal &amp; Privacy</a>
        </div>

      </div>
    </div>
  )
}
