// ── EXCHANGES ────────────────────────────────────────────────────
export const EXCHANGES: Record<string, { flag: string; label: string; market: string; isin: string }> = {
  MIL:   { flag: '🇮🇹', label: 'Italy',       market: 'FTSE MIB — Borsa Italiana',    isin: 'IT' },
  XETRA: { flag: '🇩🇪', label: 'Germany',     market: 'DAX — Deutsche Börse',         isin: 'DE' },
  PA:    { flag: '🇫🇷', label: 'France',      market: 'CAC 40 — Euronext Paris',      isin: 'FR' },
  AS:    { flag: '🇳🇱', label: 'Netherlands', market: 'AEX — Euronext Amsterdam',     isin: 'NL' },
  MC:    { flag: '🇪🇸', label: 'Spain',       market: 'IBEX 35 — BME Madrid',         isin: 'ES' },
  BR:    { flag: '🇧🇪', label: 'Belgium',     market: 'BEL 20 — Euronext Brussels',   isin: 'BE' },
  LS:    { flag: '🇵🇹', label: 'Portugal',    market: 'PSI — Euronext Lisbon',        isin: 'PT' },
  VI:    { flag: '🇦🇹', label: 'Austria',     market: 'ATX — Wiener Börse',           isin: 'AT' },
  HE:    { flag: '🇫🇮', label: 'Finland',     market: 'OMX Helsinki',                 isin: 'FI' },
  IR:    { flag: '🇮🇪', label: 'Ireland',     market: 'ISEQ — Euronext Dublin',       isin: 'IE' },
  AT:    { flag: '🇬🇷', label: 'Greece',      market: 'ASE — Athens SE',              isin: 'GR' },
}

// ── INDICES ──────────────────────────────────────────────────────
export const INDICES = [
  { name: 'Euro Stoxx 50',      ticker: 'STOXX50E.INDX' },
  { name: 'FTSE MIB',           ticker: 'FTSEMIB.INDX'  },
  { name: 'FTSE MIB All Share', ticker: 'ITLMS.INDX'    },
  { name: 'DAX',                ticker: 'GDAXI.INDX'    },
  { name: 'CAC 40',             ticker: 'FCHI.INDX'     },
  { name: 'AEX',                ticker: 'AEX.INDX'      },
  { name: 'IBEX 35',            ticker: 'IBEX.INDX'     },
  { name: 'BEL 20',             ticker: 'BFX.INDX'      },
  { name: 'PSI',                ticker: 'PSI20.INDX'    },
  { name: 'ATX',                ticker: 'ATX.VI'        },
  { name: 'OMX Helsinki 25',    ticker: 'OMXH25.HE'    },
  { name: 'ISEQ',               ticker: 'ISEQ.IR'       },
  { name: 'ASE',                ticker: 'ATG.AT'        },
]

// ── SECTORS ──────────────────────────────────────────────────────
export const SECTOR_COLORS: Record<string, string> = {
  'Financials':             '#3b82f6',
  'Technology':             '#8b5cf6',
  'Health Care':            '#10b981',
  'Energy':                 '#f59e0b',
  'Industrials':            '#6366f1',
  'Consumer Discretionary': '#ec4899',
  'Consumer Staples':       '#14b8a6',
  'Materials':              '#f97316',
  'Utilities':              '#06b6d4',
  'Communication':          '#84cc16',
  'Real Estate':            '#a855f7',
  'Insurance':              '#0ea5e9',
  'Other':                  '#6b7280',
}

export const MAX_SCREEN = 100
export const LEEWAY_BASE = 'https://api.leeway.tech/api/v1/public'
