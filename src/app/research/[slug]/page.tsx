import { Metadata } from 'next'
import { notFound } from 'next/navigation'
import Link from 'next/link'

interface Note {
  ticker: string
  exchange: string
  slug: string
  company: string
  sector: string
  subsector: string
  flag: string
  country: string
  value_score: number
  growth_score: number
  universe: string
  pdf: string
  tagline: string
  subtitle: string
  kpis: [string, string, string][]
  highlights: string[]
  thesis: string
}

const NOTES: Note[] = [
  {
    ticker: 'ASML', exchange: 'AS', slug: 'asml',
    company: 'ASML Holding N.V.', sector: 'Information Technology', subsector: 'Technology / Semiconductors',
    flag: '🇳🇱', country: 'Netherlands', value_score: 19, growth_score: 86, universe: 'Top Growth',
    pdf: '/research/ASML_ForwardAlpha.pdf',
    tagline: 'The Quantitative Growth Engine — Monopoly in EUV Lithography',
    subtitle: 'ASML is not merely an equipment manufacturer; it is the gatekeeper of the global semiconductor roadmap.',
    kpis: [['Value Score','19/100','Growth-driven premium valuation'],['Growth Score','86/100','Top Growth classification'],['NTM P/E','40.9x','Premium multiple for monopoly moat'],['ROE FY2026E','54.7%','Exceptional capital efficiency'],['Fwd 2-Yr EPS CAGR','+28.7%','Structural compounding'],['Net Debt/EBITDA','-0.67x','Net cash position']],
    highlights: ['<strong>Top-Line Momentum:</strong> Revenue projected to grow +19.4% in 2026, reaching over €39 billion.','<strong>Capital Efficiency:</strong> ROE forecast to jump from 49.3% in 2025 to 54.7% in 2026.','<strong>Balance Sheet Fortress:</strong> Net cash position (Net Debt/EBITDA -0.67x) providing massive financial flexibility.','<strong>Operating Leverage:</strong> EBIT margins expected to expand to 36.4% in 2026.'],
    thesis: 'ASML holds a 100% monopoly on EUV lithography machines — the only technology capable of producing chips below 7nm. With Growth Score 86/100, revenue growth +19.4% and ROE of 54.7%, ASML represents the gold standard of high-growth technology compounders in the European universe.',
  },
  {
    ticker: 'BNP', exchange: 'PA', slug: 'bnp',
    company: 'BNP Paribas S.A.', sector: 'Financials', subsector: 'Financials / Banking',
    flag: '🇫🇷', country: 'France', value_score: 79, growth_score: 64, universe: 'Top 20%',
    pdf: '/research/BNP_ForwardAlpha.pdf',
    tagline: 'Deep Value & Resilient Income Engine',
    subtitle: 'BNP Paribas presents a classic case of an institutional-grade value compounder trading at a massive disconnect from its fundamental strength.',
    kpis: [['Value Score','79/100','Strong discount across multiples'],['Growth Score','64/100','Stable capital compounding'],['NTM P/E','7.80x','Deeply compressed multiple'],['Price / Book','0.78x','22% discount to book value'],['Dividend Yield','6.6%','+14.4% DPS growth 2026E'],['Fwd 2-Yr EPS CAGR','+7.6%','Resilient earnings growth']],
    highlights: ['<strong>Valuation Gap:</strong> Trading at 7.80x NTM P/E and 0.78x P/BV — massive margin of safety.','<strong>Growing Cash Machine:</strong> Net Income scaling from €12,225M to €13,283M by next fiscal cycle.','<strong>Operational Efficiency:</strong> ROE structurally expanding from 9.6% toward 10.77%.','<strong>Income Engine:</strong> 6.6% dividend yield with +14.4% YoY DPS growth.'],
    thesis: 'BNP Paribas ranks in the Top 20% of our European Universe with Value Score 79/100. Trading at 7.80x NTM P/E and 0.78x P/BV, investors buy one of Europe\'s largest systemically important banks at a 22% discount to book value.',
  },
  {
    ticker: 'ENR', exchange: 'XETRA', slug: 'enr',
    company: 'Siemens Energy AG', sector: 'Industrials', subsector: 'Industrials / Energy',
    flag: '🇩🇪', country: 'Germany', value_score: 17, growth_score: 87, universe: 'Top Growth',
    pdf: '/research/ENR_ForwardAlpha.pdf',
    tagline: 'Hyper-Growth in the AI Grid Supercycle',
    subtitle: 'The most explosive multi-baggers occur when an essential infrastructure player completes an operational turnaround just as its sector enters a multi-decade supercycle.',
    kpis: [['Value Score','17/100','Growth-driven valuation'],['Growth Score','87/100','Premier large-cap growth'],['NTM P/E','32.08x','Compressing from 65.90x LTM'],['FCF FY2026E','€6,994M','+70.7% YoY surge'],['LTM ROIC','17.8%','Sharp margin inflection'],['Fwd 2-Yr EPS CAGR','+92.9%','Explosive earnings recovery']],
    highlights: ['<strong>Violent Margin Rebound:</strong> EBIT on track to triple to €5,022M in FY2026 (+113.3% YoY).','<strong>Unprecedented Grid Demand:</strong> AI data center power loads feed directly into a decade-long order backlog.','<strong>Stabilized Foundations:</strong> Siemens Gamesa issues systematically managed — earnings power unlocked.','<strong>Net Cash Fortress:</strong> Net Cash position of €7,965M.'],
    thesis: 'Siemens Energy checks every box for a structural growth compounder with Growth Score 87/100. With EBIT tripling to €5,022M, FCF surging +70.7% YoY, and Forward 2-Year EPS CAGR of +92.9%, ENR sits at the intersection of AI infrastructure demand and European grid modernisation.',
  },
  {
    ticker: 'EQNR', exchange: 'OB', slug: 'eqnr',
    company: 'Equinor ASA', sector: 'Energy', subsector: 'Energy / Oil & Gas',
    flag: '🇳🇴', country: 'Norway', value_score: 59, growth_score: 63, universe: 'Top 20%',
    pdf: '/research/EQNR_ForwardAlpha.pdf',
    tagline: 'The Deep Value & Cash Engine — 2026 Earnings Inflection',
    subtitle: 'Equinor represents a textbook asymmetric risk-reward setup combining deeply compressed valuation with an imminent operational inflection point.',
    kpis: [['Value Score','59/100','Compressed multiples'],['Growth Score','63/100','Earnings inflection ahead'],['NTM P/E','7.88x','Rock-bottom valuation'],['NTM EV/EBITDA','2.21x','Exceptional margin of safety'],['EPS Growth 2026E','+99.8%','YoY EPS doubling'],['Net Debt/EBITDA','0.14x','Near-zero leverage FY2026E']],
    highlights: ['<strong>EPS Explosion:</strong> Normalised EPS projected to jump from 2.47 in 2025 to 4.93 in 2026 (+99.8% YoY).','<strong>Top-Tier Returns:</strong> LTM ROIC of 29.5% with ROE forecast to expand to 27.3% by FY2026.','<strong>Deleveraging Power:</strong> Net Debt/EBITDA dropping to 0.14x in 2026 — securing the 4.4% Dividend Yield.','<strong>Depressed Multiples:</strong> NTM EV/EBITDA of 2.21x and MC/FCF of 8.87x.'],
    thesis: 'Equinor ranks in the Top 20% combining Value Score 59 and Growth Score 63. Trading at 7.88x NTM P/E with EPS projected to nearly double (+99.8% YoY) and ROIC of 29.5%, EQNR offers one of the most compelling risk-reward setups in European Energy.',
  },
  {
    ticker: 'IFX', exchange: 'XETRA', slug: 'ifx',
    company: 'Infineon Technologies AG', sector: 'Information Technology', subsector: 'Information Technology / Semiconductors',
    flag: '🇩🇪', country: 'Germany', value_score: 21, growth_score: 86, universe: 'Top Growth',
    pdf: '/research/IFX_ForwardAlpha.pdf',
    tagline: 'Violent Multiple Compression in the Tech Arena',
    subtitle: 'Retail screeners flag trailing multi-digit P/Es as value traps, but institutional alpha thrives in cyclical inflections.',
    kpis: [['Value Score','21/100','Cyclical trough trailing metrics'],['Growth Score','86/100','Top Growth — sharp earnings reversal'],['LTM P/E','93.58x','Trailing trough — rearview mirror'],['NTM P/E','35.03x','Steep forward compression'],['Fwd 2-Yr EPS CAGR','+36.0%','+47pp swing from historical lows'],['Net Debt/EBITDA','1.00x','Deleveraging from 1.38x']],
    highlights: ['<strong>Front-Loaded Inflection:</strong> +66.9% YoY GAAP EPS surge from FY2025 to FY2026.','<strong>Secular Mega-Trends:</strong> Dominance in Silicon Carbide (SiC) chips and booming EV content requirements.','<strong>Quality Deleveraging:</strong> Balance sheet optimisation during intensive capacity ramp.','<strong>Multiple Compression:</strong> LTM P/E of 93.58x compresses to 35.03x NTM.'],
    thesis: 'Infineon registers Growth Score 86/100 — Top Growth backed by violent earnings reversal. The LTM P/E of 93.58x masks a forward story where EPS surges +66.9% YoY and NTM P/E compresses to 35.03x. Global leader in SiC power semiconductors for EV and industrial applications.',
  },
  {
    ticker: 'INGA', exchange: 'AS', slug: 'inga',
    company: 'ING Groep N.V.', sector: 'Financials', subsector: 'Financials / Banking',
    flag: '🇳🇱', country: 'Netherlands', value_score: 75, growth_score: 60, universe: 'Top 20%',
    pdf: '/research/INGA_ForwardAlpha.pdf',
    tagline: 'A Rare Blueprint for Financial Sector GARP',
    subtitle: 'Can a legacy European banking giant secretly double as a high-efficiency growth compounder? ING Groep N.V. makes the case.',
    kpis: [['Value Score','75/100','Strong downside buffer'],['Growth Score','60/100','High-efficiency profile'],['LTM P/E','9.35x','Deeply discounted entry'],['NTM P/E','10.83x','Modest multiple expansion'],['Fwd 2-Yr EPS CAGR','+14.7%','Resilient compounding'],['Dividend Yield','4.4%','+15.3% DPS growth 2026E']],
    highlights: ['<strong>GARP Synthesis:</strong> Single-digit multiples alongside LTM ROE of 16.6%.','<strong>Intact Momentum:</strong> Historical 3-year EPS CAGR of +28.9% with FY2026E Normalized EPS +13.2%.','<strong>Premium Efficiency:</strong> Mid-teens capital return profile most peers cannot replicate.','<strong>Income Floor:</strong> 4.4% dividend yield with +15.3% DPS growth.'],
    thesis: 'ING Groep ranks in the Top 20% on both Value (75/100) and Growth (60/100) — a textbook GARP profile. With LTM P/E 9.35x, ROE 16.6%, historical 3-year EPS CAGR +28.9% and 4.4% dividend yield, INGA is one of the few large-cap financials scoring well on both Value and Growth screens.',
  },
  {
    ticker: 'PRY', exchange: 'MIL', slug: 'pry',
    company: 'Prysmian S.p.A.', sector: 'Industrials', subsector: 'Industrials / Cables',
    flag: '🇮🇹', country: 'Italy', value_score: 17, growth_score: 85, universe: 'Top Growth',
    pdf: '/research/PRY_ForwardAlpha.pdf',
    tagline: 'The Infrastructure Backlog Powering the Green Transition',
    subtitle: 'Prysmian operates as a premium picks-and-shovels provider for global grid modernization — the world leader in submarine and underground cable systems.',
    kpis: [['Value Score','17/100','Premium moat valuation'],['Growth Score','85/100','Top Growth — visible backlogs'],['NTM P/E','11.23x','Reasonable for moat quality'],['LTM ROIC','13.5%','Exceptional capital deployment'],['LTM ROE','19.8%','Deep profitability'],['Net Debt/EBITDA','1.40x','Compressing from 1.63x']],
    highlights: ['<strong>Protected Earnings Power:</strong> EPS expanding from €5.35 to €6.24, scaling to €6.71.','<strong>Self-Sustaining Flywheel:</strong> Net Income rising to €1,847M as submarine interconnectors grow.','<strong>Infrastructure Mandate:</strong> Offshore wind and AI data centers cannot scale without Prysmian HV cables.','<strong>Capital Efficiency:</strong> LTM ROIC 13.5% and ROE 19.8% confirm expanding moat.'],
    thesis: 'Prysmian scores 85/100 on Growth — a core Top Growth play. At 11.23x NTM P/E with ROE 19.8% and ROIC 13.5%, Prysmian offers institutional-grade exposure to the energy transition. You cannot connect offshore wind farms to the grid without Prysmian.',
  },
  {
    ticker: 'RIO', exchange: 'LSE', slug: 'rio',
    company: 'Rio Tinto Group', sector: 'Basic Materials', subsector: 'Basic Materials / Mining',
    flag: '🇬🇧', country: 'United Kingdom', value_score: 46, growth_score: 74, universe: 'Top Growth',
    pdf: '/research/RIO_ForwardAlpha.pdf',
    tagline: 'The Institutional Quality Blueprint — Energy Transition Proxy',
    subtitle: 'Rio Tinto represents the textbook definition of a Quality Play within basic materials, evolved into a strategic proxy for the global energy transition.',
    kpis: [['Value Score','46/100','Balanced quality profile'],['Growth Score','74/100','Strong transition metals growth'],['Net Debt/EBITDA','0.46x','FY2026E — fortress balance sheet'],['ROE FY2026E','21.6%','Expanding from LTM levels'],['FCF Growth 2026E','+69.8%','YoY surge'],['Fwd 2-Yr EPS CAGR','+12.4%','Resilient compounding']],
    highlights: ['<strong>Fortress Balance Sheet:</strong> LTM Net Debt/EBITDA at 0.69x, compressing to 0.46x by FY2026.','<strong>Cash Generation:</strong> Free Cash Flow projected to surge +69.8% YoY.','<strong>Shareholder Returns:</strong> DPS projected +22.4% YoY in FY2026.','<strong>Bottom-Line Inflection:</strong> Normalised Net Income forecast +27.0% YoY.'],
    thesis: 'Rio Tinto offers a rare combination for institutional portfolios: de-risked balance sheet, defensive yield, and pure exposure to transition metals (Copper, Aluminium, Lithium). With Growth Score 74 and FCF surging +69.8% YoY, RIO is the sleep-well-at-night compounder for macro-uncertain environments.',
  },
  {
    ticker: 'SHEL', exchange: 'LSE', slug: 'shel',
    company: 'Shell plc', sector: 'Energy', subsector: 'Energy / Oil, Gas and Consumable Fuels',
    flag: '🇬🇧', country: 'United Kingdom', value_score: 66, growth_score: 71, universe: 'Top 20%',
    pdf: '/research/SHEL_ForwardAlpha.pdf',
    tagline: 'High-Yielding Cash Machine & Structural Turnaround',
    subtitle: 'Shell ranks in the Top 20% of our European Universe, offering an asymmetric combination of deep valuation discount and imminent earnings turnaround.',
    kpis: [['Value Score','66/100','Forward multiples deeply compressed'],['Growth Score','71/100','Structural profitability turnaround'],['NTM P/E','7.98x','Single-digit despite strong EPS growth'],['NTM EV/EBITDA','4.05x','Exceptionally low enterprise multiple'],['EPS Growth 2026E','+72.9%','YoY normalised EPS acceleration'],['Dividend Yield','3.7%','+7.2% DPS growth projected']],
    highlights: ['<strong>Valuation Disconnect:</strong> 7.98x NTM P/E despite +23.8% Forward 2-Year EPS CAGR.','<strong>Growth Reversal:</strong> Normalised EPS jumping from 3.15 to 5.45 (+72.9% YoY).','<strong>Robust Efficiency:</strong> LTM ROIC of 11.7% and ROE projected toward 16.78%.','<strong>Cash Generation:</strong> NTM MC/FCF of 7.62x — massive FCF supporting capital returns.'],
    thesis: 'Shell ranks Top 20% with Value Score 66 and Growth Score 71. Despite 28.5% annual return, 7.98x NTM P/E and 4.05x NTM EV/EBITDA show the market has not yet priced in the fundamental acceleration. EPS projected to surge +72.9% YoY.',
  },
  {
    ticker: 'UBSG', exchange: 'SWX', slug: 'ubsg',
    company: 'UBS Group AG', sector: 'Financials', subsector: 'Financials / Banking',
    flag: '🇨🇭', country: 'Switzerland', value_score: 69, growth_score: 65, universe: 'Top 20%',
    pdf: '/research/UBSG_ForwardAlpha.pdf',
    tagline: 'Operational Leverage at Scale — Margin Expansion & Earnings Re-Rating',
    subtitle: 'Forward-looking data tells a story of margin expansion and earnings growth that challenges traditional banking sector conventions.',
    kpis: [['Value Score','69/100','Near top 20% on value'],['Growth Score','65/100','Near top 20% on growth'],['NTM P/E','13.07x','Compressing from 16.88x LTM'],['EBIT Margin 2026E','26.5%','From 18.9% — 760bps expansion'],['Net Income Growth','+36.1%','YoY GAAP FY2026E'],['Fwd 2-Yr EPS CAGR','+17.0%','Tech-like growth for a bank']],
    highlights: ['<strong>Margin Step-Change:</strong> EBIT margins expanding from 18.9% to 26.5% — 760bps improvement.','<strong>Tech-Like Growth:</strong> GAAP Net Income projected +36.1% YoY for FY2026.','<strong>ROE Threshold Crossed:</strong> ROE jumping from 8.80% LTM to 11.84%.','<strong>Attractive Valuation:</strong> 13.07x NTM P/E with 2.7% dividend yield.'],
    thesis: 'UBS is proving that operational efficiency from the Credit Suisse integration can generate growth rates usually reserved for technology. With Growth Score 65 and Value Score 69, at 13x forward earnings with +17% EPS CAGR and 760bps EBIT margin expansion.',
  },
  {
    ticker: 'VOW3', exchange: 'XETRA', slug: 'vow3',
    company: 'Volkswagen AG', sector: 'Consumer Discretionary', subsector: 'Consumer Discretionary / Automotive',
    flag: '🇩🇪', country: 'Germany', value_score: 96, growth_score: 43, universe: 'Top 5% Value',
    pdf: '/research/VOW3_ForwardAlpha.pdf',
    tagline: 'The Ultimate Value Paradox — Deep Value vs. Structural Headwinds',
    subtitle: 'How does a global automaker with 1.2% revenue growth generate a 36.8% Forward 2-Year EPS CAGR? Welcome to the complex case of VOW3.',
    kpis: [['Value Score','96/100','Top 5% European Universe'],['Growth Score','43/100','Restructuring-driven growth'],['NTM P/E','4.34x','Extreme discount to earnings'],['Price / Book','0.26x','74% discount to book value'],['Fwd 2-Yr EPS CAGR','+36.8%','Operational leverage play'],['Dividend Yield','6.8%','+13.5% DPS growth 2026E']],
    highlights: ['<strong>Operational Leverage:</strong> EBIT margins projected to nearly double from 2.8% to 4.9% in 2026.','<strong>Earnings Inflection:</strong> Normalised Net Income forecast to surge +51.2% YoY in FY2026.','<strong>High Yield to Wait:</strong> 6.8% Dividend Yield with +13.5% DPS growth.','<strong>Structural Risks:</strong> €205.5B LTM Net Debt, fierce global EV competition.'],
    thesis: 'Volkswagen holds Value Score 96/100 — top 5% of our European equity universe. At 4.34x NTM P/E and 0.26x P/BV, the market prices in extreme scepticism. The bull case: if EBIT margins double and net income surges +51.2%, the re-rating potential is massive.',
  },
  {
    ticker: 'MC', exchange: 'PA', slug: 'mc',
    company: 'LVMH Moët Hennessy Louis Vuitton', sector: 'Consumer Discretionary', subsector: 'Consumer Discretionary / Luxury Goods',
    flag: '🇫🇷', country: 'France', value_score: 8, growth_score: 36, universe: 'Excluded — Red Flag',
    pdf: '/research/MC_ForwardAlpha_v2.pdf',
    tagline: 'The Premium Illusion — Why Our Model Flags LVMH as a Quantitative Red Flag',
    subtitle: 'The era of effortless luxury compounding has transitioned into structural stagnation.',
    kpis: [['Value Score','8/100','Extreme fundamental overvaluation'],['Growth Score','36/100','Structural stagnation'],['NTM P/E','20.51x','Premium for flatline growth'],['2026E Revenue Growth','+0.2%','Dead flat YoY'],['EBITDA Growth','(4.2%)','Margin compression'],['Interest Expense','+102.1%','Debt servicing explosion']],
    highlights: ['<strong>Flatlined Top Line:</strong> 2026E Revenue at €80,940M — dead flat +0.2% YoY after 2025 contraction. Zero growth narrative.','<strong>Frozen Earnings:</strong> GAAP EPS growth stalled at +0.2% (€21.90) — failing to recover from the -13.0% drop in 2025.','<strong>Margin Compression:</strong> EBITDA contracting -4.2%, margins falling from 31.9% to 30.5%. ROE deteriorating 16.12% → 15.43%.','<strong>Interest Expense Shock:</strong> Debt servicing costs projected to explode +102.1% from -€401M to -€810M — capital efficiency decay accelerating.'],
    thesis: 'LVMH scores Value 8/100 and Growth 36/100 — bottom tier of our European universe. The era of effortless luxury compounding is over: revenue flat at +0.2%, EBITDA -4.2%, ROE deteriorating, interest expense doubling to €810M, CF/Share -11.6% and DPS frozen. Paying 20.51x NTM P/E for structural stagnation and zero margin of safety. Stripping away the luxury hype, the numbers do not lie.',
  },

  {
    ticker: 'ABBN', exchange: 'SWX', slug: 'abbn',
    company: 'ABB Ltd', sector: 'Industrials', subsector: 'Industrials / Electrification & Automation',
    flag: '🇨🇭', country: 'Switzerland', value_score: 17, growth_score: 82, universe: 'Top Growth',
    pdf: '/research/ABBN_ForwardAlpha.pdf',
    tagline: 'Industrial Megatrends Unleashed — The Quality Growth Profile',
    subtitle: 'ABB targets structural momentum where execution justifies a premium — Growth Rank 82/100.',
    kpis: [['Value Score','17/100','Quality premium valuation'],['Growth Score','82/100','Top Growth — Top 20%'],['Revenue Growth 2026E','+12.8%','CHF 37.5B'],['Net Income Growth','+26.5%','YoY to CHF 6.0B'],['LTM ROE','33.6%','Expanding to 34.5%'],['Net Debt/EBITDA','0.44x','Moving to net cash']],
    highlights: ['<strong>Top-Line Velocity:</strong> Revenues projected to surge +12.8% YoY to CHF 37,481M by late 2026.','<strong>Profitability Inflection:</strong> Normalised Net Income jumping +26.5% YoY to CHF 6,022M.','<strong>Elite Capital Returns:</strong> LTM ROE of 33.6% expanding to 34.5%, alongside ROIC of 24.5%.','<strong>Fortress Balance Sheet:</strong> Net Debt/EBITDA at 0.44x moving to net cash (-CHF 3,900M).'],
    thesis: 'ABB Ltd scores Growth 82/100 — top 20% of our entire European coverage universe. With Value Score 17/100, it trades at an institutional quality premium backed by exploding demand for electrification, smart motion and automation. Revenue +12.8%, Net Income +26.5%, ROE 33.6%, ROIC 24.5% and a Forward 2-Year EPS CAGR of 14.4%. The definitive structural growth compounder for the modern industrial era.',
  },
  {
    ticker: 'BARC', exchange: 'LSE', slug: 'barc',
    company: 'Barclays PLC', sector: 'Financials', subsector: 'Financials / Banking',
    flag: '🇬🇧', country: 'United Kingdom', value_score: 77, growth_score: 62, universe: 'Top 20%',
    pdf: '/research/BARC_ForwardAlpha.pdf',
    tagline: 'Re-Accelerating Capital Machine — The Quantitative Case for Barclays',
    subtitle: 'Value 77/100 combined with Growth 62/100 — a powerful mix of valuation discount and earnings acceleration.',
    kpis: [['Value Score','77/100','Top 20% European Universe'],['Growth Score','62/100','Structural earnings acceleration'],['LTM P/BV','0.98x','Below tangible book value'],['NTM P/E','8.40x','Deeply discounted'],['Fwd 2-Yr EPS CAGR','+21.5%','High-octane growth'],['DPS Growth 2026E','+75.7%','Massive payout expansion']],
    highlights: ['<strong>Valuation Disconnect:</strong> 0.98x P/BV and 8.40x NTM P/E — buying a global banking powerhouse below tangible assets.','<strong>EPS Acceleration:</strong> Forward 2-Year EPS CAGR of +21.5% — far above European banking peers.','<strong>Profitability Leap:</strong> Net Income scaling from £6,209M to £7,114M (+14.6% YoY).','<strong>Dividend Surge:</strong> DPS projected +75.7% YoY from £0.09 to £0.15, supported by EBIT margins expanding to 42.2%.'],
    thesis: 'Barclays scores Value 77/100 and Growth 62/100 — firmly in the Top 20% of our 3,700+ European equity universe. Trading at 0.98x P/BV and 8.40x NTM P/E, the market heavily discounts a structurally more profitable business. ROE expanding from 8.29% to 10.70% is the primary catalyst for re-rating. With +21.5% Forward EPS CAGR and +75.7% DPS growth, BARC is a high-conviction compounder.',
  },
]

export async function generateStaticParams() {
  return NOTES.map(note => ({ slug: note.slug }))
}

export async function generateMetadata({ params }: { params: { slug: string } }): Promise<Metadata> {
  const note = NOTES.find(n => n.slug === params.slug)
  if (!note) return { title: 'Research | ForwardAlpha' }
  return {
    title: `${note.ticker} — ${note.tagline} | ForwardAlpha`,
    description: note.thesis.slice(0, 160),
    openGraph: {
      title: `${note.company} (${note.ticker}) — ForwardAlpha Quantitative Research`,
      description: note.thesis.slice(0, 200),
      url: `https://forwardalpha.pro/research/${note.slug}`,
      siteName: 'ForwardAlpha',
      type: 'article',
    },
  }
}

function JsonLd({ note }: { note: Note }) {
  const schema = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    'headline': `${note.company} (${note.ticker}) — ${note.tagline}`,
    'description': note.thesis.slice(0, 200),
    'author': { '@type': 'Organization', 'name': 'ForwardAlpha', 'url': 'https://forwardalpha.pro' },
    'publisher': { '@type': 'Organization', 'name': 'ForwardAlpha', 'url': 'https://forwardalpha.pro' },
    'datePublished': '2026-05-01',
    'dateModified': '2026-05-29',
    'url': `https://forwardalpha.pro/research/${note.slug}`,
    'about': {
      '@type': 'Corporation',
      'name': note.company,
      'tickerSymbol': note.ticker,
      'exchange': note.exchange,
    },
    'keywords': `${note.ticker}, ${note.company}, ${note.sector}, quantitative research, European equities, ForwardAlpha`,
  }
  return <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }} />
}

export default function ResearchNotePage({ params }: { params: { slug: string } }) {
  const note = NOTES.find(n => n.slug === params.slug)
  if (!note) notFound()

  const valueColor = note.value_score >= 70 ? '#3b82f6' : note.value_score >= 50 ? '#f59e0b' : '#94a3b8'
  const growthColor = note.growth_score >= 70 ? '#22c55e' : note.growth_score >= 50 ? '#f59e0b' : '#94a3b8'

  return (
    <>
    <JsonLd note={note} />
    <div style={{ minHeight: '100vh', background: 'var(--bg, #0d1117)', color: 'var(--text, #e2e8f0)', fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ maxWidth: 800, margin: '0 auto', padding: '32px 20px' }}>

        {/* Back */}
        <Link href="/research" style={{ color: '#f97316', fontSize: 13, textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 24 }}>
          ← Back to Research
        </Link>

        {/* Header */}
        <div style={{ borderBottom: '2px solid #f97316', paddingBottom: 16, marginBottom: 24 }}>
          <div style={{ fontSize: 11, fontWeight: 700, color: '#f97316', letterSpacing: '0.1em', textTransform: 'uppercase', marginBottom: 4 }}>
            ForwardAlpha Quantitative Research · May 2026
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
            <span style={{ fontSize: 28 }}>{note.flag}</span>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 28, fontWeight: 800, color: '#f97316' }}>{note.ticker}</span>
                <span style={{ fontSize: 12, padding: '2px 8px', border: '1px solid #334155', borderRadius: 4, color: '#cbd5e1' }}>{note.exchange}</span>
              </div>
              <div style={{ fontSize: 14, color: '#e2e8f0' }}>{note.company}</div>
            </div>
          </div>
          <h1 style={{ fontSize: 22, fontWeight: 800, margin: '8px 0 4px', lineHeight: 1.3 }}>{note.tagline}</h1>
          <p style={{ fontSize: 13, color: '#cbd5e1', margin: 0 }}>{note.subsector}</p>
        </div>

        {/* Scores */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 24 }}>
          {[
            { label: 'Value Score', value: note.value_score + '/100', color: valueColor, bg: '#eff6ff' },
            { label: 'Growth Score', value: note.growth_score + '/100', color: growthColor, bg: '#f0fdf4' },
            { label: 'Universe', value: note.universe, color: '#f97316', bg: '#fff7ed' },
          ].map(s => (
            <div key={s.label} style={{ background: s.bg, borderRadius: 8, padding: '14px 12px', textAlign: 'center', border: `1px solid ${s.color}33` }}>
              <div style={{ fontSize: 10, color: '#e2e8f0', marginBottom: 4 }}>{s.label}</div>
              <div style={{ fontSize: 22, fontWeight: 800, color: s.color }}>{s.value}</div>
            </div>
          ))}
        </div>

        {/* KPIs */}
        <div style={{ marginBottom: 28 }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#94a3b8', marginBottom: 12 }}>Key Quantitative Metrics</h2>
          <div style={{ border: '1px solid #334155', borderRadius: 8, overflow: 'hidden' }}>
            {note.kpis.map(([label, value, insight], i) => (
              <div key={label} style={{ display: 'grid', gridTemplateColumns: '160px 100px 1fr', gap: 0, borderBottom: i < note.kpis.length - 1 ? '1px solid #334155' : 'none', background: i % 2 === 0 ? '#111827' : '#0f172a' }}>
                <div style={{ padding: '10px 14px', fontSize: 12, color: '#e2e8f0', fontWeight: 600 }}>{label}</div>
                <div style={{ padding: '10px 14px', fontSize: 13, fontWeight: 800, color: '#ffffff' }}>{value}</div>
                <div style={{ padding: '10px 14px', fontSize: 11, color: '#cbd5e1' }}>{insight}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Highlights */}
        <div style={{ marginBottom: 28 }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#94a3b8', marginBottom: 12 }}>Investment Highlights</h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {note.highlights.map((h, i) => (
              <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'flex-start' }}>
                <span style={{ color: '#f97316', fontSize: 16, marginTop: 1, flexShrink: 0 }}>→</span>
                <p style={{ margin: 0, fontSize: 13, lineHeight: 1.6, color: '#f1f5f9' }} dangerouslySetInnerHTML={{ __html: h }} />
              </div>
            ))}
          </div>
        </div>

        {/* Thesis */}
        <div style={{ background: '#0f1923', border: '1px solid #f9731633', borderRadius: 8, padding: '20px 24px', marginBottom: 28 }}>
          <h2 style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#f97316', marginBottom: 10 }}>ForwardAlpha Investment Thesis</h2>
          <p style={{ margin: 0, fontSize: 13, lineHeight: 1.7, color: '#f1f5f9' }}>{note.thesis}</p>
        </div>

        {/* Download */}
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <a href={note.pdf} target="_blank" rel="noopener noreferrer"
            style={{ display: 'inline-flex', alignItems: 'center', gap: 10, background: '#f97316', color: '#000', padding: '14px 32px', borderRadius: 8, fontWeight: 800, fontSize: 14, textDecoration: 'none' }}>
            ↓ Download Full {note.ticker} Quantitative Research Report — PDF
          </a>
          <p style={{ fontSize: 11, color: '#94a3b8', marginTop: 8 }}>
            Free access during Beta · No credit card required ·{' '}
            <Link href="/" style={{ color: '#f97316', textDecoration: 'none' }}>Access the full ForwardAlpha screener →</Link>
          </p>
        </div>

        {/* Related Notes — Internal Linking */}
        {(() => {
          const related = NOTES.filter(n => n.slug !== note.slug && n.sector === note.sector).slice(0, 3)
          if (related.length === 0) return null
          return (
            <div style={{ marginBottom: 28 }}>
              <h2 style={{ fontSize: 13, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em', color: '#475569', marginBottom: 12 }}>
                Related Research
              </h2>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 10 }}>
                {related.map(r => (
                  <Link key={r.slug} href={`/research/${r.slug}`} style={{ textDecoration: 'none' }}>
                    <div style={{ background: '#0f1923', border: '1px solid #334155', borderRadius: 6, padding: '12px 14px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                        <span>{r.flag}</span>
                        <span style={{ fontWeight: 700, color: '#f97316', fontSize: 13 }}>{r.ticker}</span>
                      </div>
                      <div style={{ fontSize: 11, color: '#cbd5e1', lineHeight: 1.3 }}>{r.tagline.slice(0, 60)}...</div>
                    </div>
                  </Link>
                ))}
              </div>
            </div>
          )
        })()}

        {/* Disclaimer */}
        <div style={{ borderTop: '1px solid #1e293b', paddingTop: 16 }}>
          <p style={{ fontSize: 10, color: '#94a3b8', lineHeight: 1.5, margin: 0 }}>
            <strong>DISCLAIMER — NOT INVESTMENT ADVICE.</strong> This document is produced by ForwardAlpha (forwardalpha.pro) for informational and educational purposes only.
            It does not constitute investment advice, a solicitation, or a recommendation to buy, sell or hold any financial instrument.
            ForwardAlpha is not a registered investment adviser. All data and projections are sourced from third-party providers and believed to be reliable but not guaranteed.
            Past performance is not indicative of future results. Always consult a qualified financial adviser.
            © 2026 ForwardAlpha · andrea@forwardalpha.pro
          </p>
        </div>

      </div>
    </div>
    </>
  )
}
