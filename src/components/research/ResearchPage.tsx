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
    id: 'bnp-2026-06',
    ticker: 'BNP',
    exchange: 'PA',
    company: 'BNP Paribas S.A.',
    title: 'Value 90 & Growth 80: The Institutional Mispricing of BNP Paribas',
    subtitle: 'Value 90 · Growth 80 · Best 97 · P/B 0.78x · Dividend 6.6%',
    date: 'June 2026',
    sector: 'Financials',
    tags: ['Deep Value', 'Top 5%', 'Dividend 6.6%', 'P/B 0.78x'],
    summary: 'BNP scores Value 90 and Growth 80. Trading at 7.8x NTM P/E and 0.78x P/B with 6.6% dividend yield and +14% dividend growth YoY.',
    pdf_url: '/research/BNP_ForwardAlpha_Analysis.pdf',
    flag: '🇫🇷',
  },
  {
    id: 'enr-2026-06',
    ticker: 'ENR',
    exchange: 'XETRA',
    company: 'Siemens Energy AG',
    title: 'Growth Score 98/100: Is Siemens Energy the Ultimate AI Infrastructure Winner?',
    subtitle: 'Value 4 · Growth 98 · Best 53 · FCF +70% YoY · Net Cash',
    date: 'June 2026',
    sector: 'Industrials',
    tags: ['Top Growth', 'AI Infrastructure', 'FCF +70%', 'Net Cash'],
    summary: 'Siemens Energy scores Growth 98/100. Net income +160% YoY, FCF margin 16%, EPS growth 93% annually. Net cash position with ROIC 17.8%.',
    pdf_url: '/research/ENR_ForwardAlpha_Analysis.pdf',
    flag: '🇩🇪',
  },
  {
    id: 'asml-2026-06',
    ticker: 'ASML',
    exchange: 'AS',
    company: 'ASML Holding N.V.',
    title: 'Growth Score 98/100: Decoding ASML's Monopoly Power',
    subtitle: 'Value 2 · Growth 98 · Best 51 · EPS +29% · ROE 50%+',
    date: 'June 2026',
    sector: 'Information Technology',
    tags: ['EUV Monopoly', 'EPS +29%', 'Net Cash', 'AI Infrastructure'],
    summary: 'ASML scores Growth 98/100. Revenue +20% YoY, EBIT margins above 36%, EPS growth ~29% annually. Net cash position and ROE expanding to mid-50s.',
    pdf_url: '/research/ASML_ForwardAlpha_Analysis.pdf',
    flag: '🇳🇱',
  },
  {
    id: 'ifx-2026-06',
    ticker: 'IFX',
    exchange: 'XETRA',
    company: 'Infineon Technologies AG',
    title: 'Growth Rank 99: Why IFX is a True Growth Story',
    subtitle: 'Value 5 · Growth 99 · Best 56 · EPS +36% · +160% 12M',
    date: 'June 2026',
    sector: 'Information Technology',
    tags: ['Top Growth', 'SiC Leader', 'EPS +36%', 'EV Plays'],
    summary: 'Infineon scores Growth 99/100. EPS growth ~36% annually, near-term EPS +65%. Trailing multiple compressing 60%+ on forward estimates. +160.1% 12M return.',
    pdf_url: '/research/IFX_ForwardAlpha_Analysis.pdf',
    flag: '🇩🇪',
  },
  {
    id: 'abbn-2026-06',
    ticker: 'ABBN',
    exchange: 'SWX',
    company: 'ABB Ltd',
    title: 'Growth Score 97/100: Why the Market is Paying a Premium for ABB',
    subtitle: 'Value 6 · Growth 97 · Best 56 · ROIC 25% · Net Debt/EBITDA <0.5x',
    date: 'June 2026',
    sector: 'Industrials',
    tags: ['Top Growth', 'Automation', 'Electrification', 'ROIC 25%'],
    summary: 'ABB scores Growth 97/100 with +80% 12M return. EPS growth ~14% annually, ROIC 25%, Net Debt/EBITDA below 0.5x. Trading at 32x NTM P/E.',
    pdf_url: '/research/ABBN_ForwardAlpha_Analysis.pdf',
    flag: '🇨🇭',
  },
  {
    id: 'shel-2026-06',
    ticker: 'SHEL',
    exchange: 'LSE',
    company: 'Shell plc',
    title: 'Value 75 & Growth 92: The Rare GARP Engine Hidden in Big Oil',
    subtitle: 'Value 75 · Growth 92 · Best 96 · NTM P/E 7.9x · Dividend 3.7%',
    date: 'June 2026',
    sector: 'Energy',
    tags: ['GARP', 'Top 20%', 'EPS +24%', 'Dividend 3.7%'],
    summary: 'Shell triggers a rare dual signal: Growth Score 92 and Value Score 75. NTM P/E 7.9x with +30% 12M return and projected EPS growth of 24% per year.',
    pdf_url: '/research/SHEL_ForwardAlpha_Analysis.pdf',
    flag: '🇬🇧',
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
