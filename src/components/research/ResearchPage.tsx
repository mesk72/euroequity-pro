'use client'

import { useState } from 'react'
import { FileText, Download, ArrowUpRight, Calendar } from 'lucide-react'

interface ResearchNote {
  id: string
  ticker: string
  exchange: string
  company: string
  title: string
  subtitle: string
  date: string
  sector: string
  tags: string[]
  summary: string
  pdf_url: string
  flag: string
}

const NOTES: ResearchNote[] = [
  {
    id: 'asml-2026-05',
    ticker: 'ASML',
    exchange: 'AS',
    company: 'ASML Holding N.V.',
    title: 'The Monopoly at the Heart of the Semiconductor Industry',
    subtitle: 'EUV Lithography · Pricing Power · AI Infrastructure Play',
    date: 'May 2026',
    sector: 'Information Technology',
    tags: ['Monopoly', 'EUV', 'AI Infrastructure', 'Pricing Power'],
    summary: 'ASML holds a 100% monopoly on EUV lithography machines — the only technology capable of producing chips below 7nm. Every leading semiconductor fab depends entirely on ASML. A structural compounder with unmatched pricing power.',
    pdf_url: '/research/ASML_ForwardAlpha.pdf',
    flag: '🇳🇱',
  },
  {
    id: 'bnp-2026-05',
    ticker: 'BNP',
    exchange: 'PA',
    company: 'BNP Paribas SA',
    title: 'Why BNP Paribas is a Textbook Value Play',
    subtitle: 'Deep Discount · 6.6% Dividend Yield · Income Engine',
    date: 'May 2026',
    sector: 'Financials',
    tags: ['Deep Value', 'Dividend 6.6%', 'Banking', 'Income'],
    summary: 'BNP trades at 7.8x NTM P/E and 0.78x P/B — buying one of Europe\'s largest banks at a 22% discount to book value. Net Income scaling from €12.2B to €13.3B with +14.4% DPS growth. ROE improving from 9.6% to 10.8%.',
    pdf_url: '/research/BNP_ForwardAlpha.pdf',
    flag: '🇫🇷',
  },
  {
    id: 'enr-2026-05',
    ticker: 'ENR',
    exchange: 'XETRA',
    company: 'Siemens Energy AG',
    title: 'From Turnaround to Secular Winner',
    subtitle: 'Upward Revision Cycle · AI Grid Supercycle · Margin Inflection',
    date: 'May 2026',
    sector: 'Industrials',
    tags: ['Energy Transition', 'AI Grid', 'Turnaround', 'FCF Inflection'],
    summary: 'Revenue guidance raised to 14–16%, FCF guidance doubled to ~€8B, Grid Technologies growing 25–27%. Net Income target €4B. Gamesa break-even removes legacy discount. ENR sits at the intersection of AI power demand and European grid modernisation.',
    pdf_url: '/research/ENR_ForwardAlpha.pdf',
    flag: '🇩🇪',
  },
  {
    id: 'eqnr-2026-05',
    ticker: 'EQNR',
    exchange: 'OB',
    company: 'Equinor ASA',
    title: 'The Energy Transition Paradox',
    subtitle: 'Oil & Gas Cash Machine · Renewable Pivot · Deep Value',
    date: 'May 2026',
    sector: 'Energy',
    tags: ['Deep Value', 'Dividend', 'Energy Transition', 'Oil & Gas'],
    summary: 'Equinor combines best-in-class oil & gas cash generation with an accelerating renewable energy pivot. Trading at a significant discount to peers with a robust dividend yield, EQNR offers asymmetric risk-reward for energy investors.',
    pdf_url: '/research/EQNR_ForwardAlpha.pdf',
    flag: '🇳🇴',
  },
  {
    id: 'ifx-2026-05',
    ticker: 'IFX',
    exchange: 'XETRA',
    company: 'Infineon Technologies AG',
    title: 'A Growth Story — Multiple Compression Driven by Earnings Reversal',
    subtitle: 'Multiple Compression · Earnings Reversal · SiC Structural Tailwinds',
    date: 'May 2026',
    sector: 'Information Technology',
    tags: ['Semiconductors', 'SiC Power', 'Earnings Reversal', 'EV Megatrend'],
    summary: 'LTM P/E of 93.58x compresses to 35.03x NTM as earnings reverse from -11.0% historical EPS CAGR to +36.0% forward. GAAP EPS +66.9% YoY in 2026. Global leader in SiC power semiconductors for EV and industrial applications.',
    pdf_url: '/research/IFX_ForwardAlpha.pdf',
    flag: '🇩🇪',
  },
  {
    id: 'inga-2026-05',
    ticker: 'INGA',
    exchange: 'AS',
    company: 'ING Groep N.V.',
    title: 'A GARP Case Study — Value Floor Meets Growth Engine',
    subtitle: 'Value Floor · Growth Engine · Elite Capital Returns',
    date: 'May 2026',
    sector: 'Financials',
    tags: ['GARP', 'Banking', 'ROE 16.6%', 'EPS Growth'],
    summary: 'INGA blurs the line between Value and Growth: 9.35x LTM P/E with 16.6% ROE, +28.9% historical 3-year EPS CAGR and +14.7% forward 2-year CAGR, plus 4.4% dividend yield growing +15.3% in 2026. Textbook GARP in European banking.',
    pdf_url: '/research/INGA_ForwardAlpha.pdf',
    flag: '🇳🇱',
  },
  {
    id: 'mt-2026-05',
    ticker: 'MT',
    exchange: 'AS',
    company: 'ArcelorMittal SA',
    title: 'The Steel Giant Hiding in Plain Sight',
    subtitle: 'Deep Value · Infrastructure Supercycle · Shareholder Returns',
    date: 'May 2026',
    sector: 'Basic Materials',
    tags: ['Deep Value', 'Steel', 'Infrastructure', 'Buybacks'],
    summary: 'ArcelorMittal is the world\'s leading steel producer trading at a deep discount to intrinsic value. Infrastructure spending supercycle and green steel transition position MT for a structural re-rating.',
    pdf_url: '/research/MT_ForwardAlpha.pdf',
    flag: '🇱🇺',
  },
  {
    id: 'pry-2026-05',
    ticker: 'PRY',
    exchange: 'MIL',
    company: 'Prysmian S.p.A.',
    title: 'Behind the Global Grid Upgrade',
    subtitle: 'EPS Acceleration · ROIC 13.5% · Picks & Shovels for the Green Transition',
    date: 'May 2026',
    sector: 'Industrials',
    tags: ['Green Transition', 'Submarine Cables', 'ROIC 13.5%', 'Compounder'],
    summary: 'Global leader in submarine/underground cables. NTM P/E 11.23x with ROE 19.8% and ROIC 13.5%. EPS expanding €5.35→€6.71, Net Income crossing €1.8B. The ultimate picks-and-shovels play for offshore wind and AI data center infrastructure.',
    pdf_url: '/research/PRY_ForwardAlpha.pdf',
    flag: '🇮🇹',
  },
  {
    id: 'rio-2026-05',
    ticker: 'RIO',
    exchange: 'LSE',
    company: 'Rio Tinto Group',
    title: 'The Institutional Quality Blueprint',
    subtitle: 'Fortress Balance Sheet · Capital Efficiency · Energy Transition Exposure',
    date: 'May 2026',
    sector: 'Basic Materials',
    tags: ['Quality Play', 'Dividend Growth', 'Energy Transition'],
    summary: 'RIO offers a rare combination: a de-risked balance sheet at 0.69x Net Debt/EBITDA, best-in-class ROIC of 15.3%, and a +69.8% FCF surge projected for FY2026 — all backed by structural demand for transition metals.',
    pdf_url: '/research/RIO_ForwardAlpha.pdf',
    flag: '🇬🇧',
  },
  {
    id: 'shel-2026-05',
    ticker: 'SHEL',
    exchange: 'LSE',
    company: 'Shell PLC',
    title: 'The Cash Flow Fortress',
    subtitle: 'FCF Generation · Shareholder Returns · Energy Transition Pivot',
    date: 'May 2026',
    sector: 'Energy',
    tags: ['Cash Flow', 'Dividend', 'Buybacks', 'Energy Transition'],
    summary: 'Shell generates exceptional free cash flow supporting aggressive shareholder returns through dividends and buybacks. Trading at a discount to US energy peers despite superior capital discipline and a credible energy transition strategy.',
    pdf_url: '/research/SHEL_ForwardAlpha.pdf',
    flag: '🇬🇧',
  },
  {
    id: 'ubsg-2026-05',
    ticker: 'UBSG',
    exchange: 'SWX',
    company: 'UBS Group AG',
    title: 'The Quantitative Case for UBS — Operational Leverage at Scale',
    subtitle: 'Margin Expansion · Earnings Re-Rating · ROE Step-Change',
    date: 'May 2026',
    sector: 'Financials',
    tags: ['Operational Leverage', 'Wealth Management', 'Earnings Growth'],
    summary: 'EBIT margins expanding from 18.9% to 26.5%, GAAP Net Income +36.1% YoY and EPS 2-Year CAGR of 17.0%. At 13.07x NTM P/E with 2.7% dividend yield, UBS is generating growth rates normally reserved for technology companies.',
    pdf_url: '/research/UBSG_ForwardAlpha.pdf',
    flag: '🇨🇭',
  },
  {
    id: 'vow3-2026-05',
    ticker: 'VOW3',
    exchange: 'XETRA',
    company: 'Volkswagen AG',
    title: 'The Ultimate Value Paradox',
    subtitle: 'Deep Value Signal · Operational Leverage · Structural Headwinds',
    date: 'May 2026',
    sector: 'Consumer Discretionary',
    tags: ['Deep Value', 'Value Trap?', 'Restructuring', 'Dividend'],
    summary: 'VOW3 trades at 0.26x P/B and 4.34x NTM P/E. A +51.2% Net Income surge projected for 2026 driven by margin expansion (2.8% → 4.9% EBIT), offset by €205B net debt at 8.78x leverage. Classic bull vs bear case.',
    pdf_url: '/research/VOW3_ForwardAlpha.pdf',
    flag: '🇩🇪',
  },
]

interface Props {
  onSelectStock?: (ticker: string, exchange: string) => void
}

export default function ResearchPage({ onSelectStock }: Props) {
  return (
    <div className="space-y-6 fade-in">
      <div className="section-hdr flex items-center gap-2">
        <FileText size={18} className="text-orange-400" />
        ForwardAlpha Research Notes
      </div>
      <p className="text-xs text-muted leading-relaxed">
        Quantitative equity research combining our proprietary Value &amp; Growth scoring models with fundamental analysis.
        <span className="ml-2 italic opacity-70">Not investment advice — for informational purposes only.</span>
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {NOTES.map(note => (
          <div key={note.id}
            className="bg-surface border border-border rounded-lg overflow-hidden">

            <div style={{ background: 'linear-gradient(135deg, #0f1923 0%, #1e3a5f 100%)', padding: '16px 20px' }}>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-xl">{note.flag}</span>
                    <span className="font-700 text-sm" style={{ color: 'var(--orange)' }}>{note.ticker}</span>
                    <span className="text-[10px] text-muted border border-white/10 rounded px-1.5 py-0.5">{note.exchange}</span>
                  </div>
                  <div className="text-xs" style={{ color: '#94a3b8' }}>{note.company}</div>
                </div>
                <div className="text-[10px] flex items-center gap-1" style={{ color: '#64748b' }}>
                  <Calendar size={10} />
                  {note.date}
                </div>
              </div>
            </div>

            <div className="p-4 space-y-3">
              <div>
                <div className="text-[10px] font-700 uppercase tracking-wide mb-1" style={{ color: 'var(--orange)', letterSpacing: '0.08em' }}>
                  {note.sector}
                </div>
                <h3 className="font-700 text-sm leading-snug" style={{ color: 'var(--text)' }}>{note.title}</h3>
                <p className="text-[11px] mt-0.5" style={{ color: 'var(--text3)' }}>{note.subtitle}</p>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {note.tags.map(tag => (
                  <span key={tag} className="text-[10px] px-2 py-0.5 rounded-full border border-border" style={{ color: 'var(--text4)' }}>
                    {tag}
                  </span>
                ))}
              </div>

              <p className="text-xs leading-relaxed" style={{ color: 'var(--text3)' }}>{note.summary}</p>

              <div className="flex gap-2 pt-1">
                <a href={note.pdf_url} target="_blank" rel="noopener noreferrer"
                  className="flex-1 flex items-center justify-center gap-1.5 py-2 rounded text-xs font-700"
                  style={{ background: 'var(--orange)', color: '#000' }}>
                  <Download size={12} />
                  Download PDF
                </a>
                <button
                  onClick={() => window.location.href = `/stock/${note.ticker}-${note.exchange}`}
                  className="flex items-center gap-1.5 px-3 py-2 rounded text-xs font-600 border border-border"
                  style={{ color: 'var(--text3)' }}>
                  <ArrowUpRight size={12} />
                  Stock Page
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="text-center py-6 text-xs" style={{ color: 'var(--text4)' }}>
        New research notes published regularly · Follow us on{' '}
        <a href="https://linkedin.com/in/andreameschini" target="_blank" rel="noopener noreferrer"
          className="underline" style={{ color: 'var(--orange)' }}>LinkedIn</a>{' '}
        for updates
      </div>
    </div>
  )
}

export { NOTES }
export type { ResearchNote }
