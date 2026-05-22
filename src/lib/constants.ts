// ── EXCHANGES EMU ─────────────────────────────────────────────────
export const EXCHANGES: Record<string, { flag: string; label: string; market: string; isin: string }> = {
  MIL:   { flag: '🇮🇹', label: 'Italy',       market: 'Borsa Italiana MTA',     isin: 'IT' },
  XETRA: { flag: '🇩🇪', label: 'Germany',     market: 'Deutsche Börse XETRA',   isin: 'DE' },
  PA:    { flag: '🇫🇷', label: 'France',      market: 'Euronext Paris',         isin: 'FR' },
  AS:    { flag: '🇳🇱', label: 'Netherlands', market: 'Euronext Amsterdam',     isin: 'NL' },
  MC:    { flag: '🇪🇸', label: 'Spain',       market: 'BME Madrid',             isin: 'ES' },
  BR:    { flag: '🇧🇪', label: 'Belgium',     market: 'Euronext Brussels',      isin: 'BE' },
  LS:    { flag: '🇵🇹', label: 'Portugal',    market: 'Euronext Lisbon',        isin: 'PT' },
  VI:    { flag: '🇦🇹', label: 'Austria',     market: 'Wiener Börse',           isin: 'AT' },
  HE:    { flag: '🇫🇮', label: 'Finland',     market: 'Nasdaq Helsinki',        isin: 'FI' },
  IR:    { flag: '🇮🇪', label: 'Ireland',     market: 'Euronext Dublin',        isin: 'IE' },
  AT:    { flag: '🇬🇷', label: 'Greece',      market: 'Athens SE',              isin: 'GR' },
}

// ── EXCHANGES EX-EMU ──────────────────────────────────────────────
export const EXCHANGES_EXEMU: Record<string, { flag: string; label: string; market: string; currency: string }> = {
  LSE:  { flag: '🇬🇧', label: 'UK (LSE)',      market: 'London Stock Exchange',  currency: 'GBP' },
  AIM:  { flag: '🇬🇧', label: 'UK (AIM)',      market: 'AIM London',             currency: 'GBP' },
  SWX:  { flag: '🇨🇭', label: 'Switzerland',   market: 'SIX Swiss Exchange',     currency: 'CHF' },
  OM:   { flag: '🇸🇪', label: 'Sweden (OM)',   market: 'Nasdaq Stockholm',       currency: 'SEK' },
  NGM:  { flag: '🇸🇪', label: 'Sweden (NGM)',  market: 'NGM Stockholm',          currency: 'SEK' },
  OB:   { flag: '🇳🇴', label: 'Norway',        market: 'Oslo Børs',              currency: 'NOK' },
  CPSE: { flag: '🇩🇰', label: 'Denmark',       market: 'Nasdaq Copenhagen',      currency: 'DKK' },
}

// Tutti gli exchange
export const ALL_EXCHANGES = [
  ...Object.keys(EXCHANGES),
  ...Object.keys(EXCHANGES_EXEMU),
]

// Exchange EMU only
export const EMU_EXCHANGES = Object.keys(EXCHANGES)

// ── FX rates ─────────────────────────────────────────────────────
// Market cap da TIKR è in USD per tutti i titoli
// Conversione USD → EUR per normalizzare la market cap
export const USD_TO_EUR = 0.8615  // aggiornato via ExchangeRate-API

// Valuta locale per exchange (per i prezzi — non per market cap)
export const EXCHANGE_CURRENCY: Record<string, string> = {
  MIL:'EUR', XETRA:'EUR', PA:'EUR', AS:'EUR', MC:'EUR',
  BR:'EUR', LS:'EUR', VI:'EUR', HE:'EUR', IR:'EUR', AT:'EUR',
  LSE:'GBP', AIM:'GBP', SWX:'CHF', OM:'SEK', NGM:'SEK',
  OB:'NOK', CPSE:'DKK',
}

// ── INDICES ───────────────────────────────────────────────────────
// source: 'eodhd' | 'yahoo'
export const INDICES: { name: string; ticker: string; source: 'eodhd' | 'yahoo'; flag: string }[] = [
  // EMU
  { name: 'STOXX 600',     ticker: 'SXXP.INDX',     source: 'eodhd', flag: '🌍' },
  { name: 'Euro Stoxx 50', ticker: 'STOXX50E.INDX',  source: 'eodhd', flag: '🇪🇺' },
  { name: 'FTSE MIB',      ticker: 'FTSEMIB.MI',     source: 'yahoo', flag: '🇮🇹' },
  { name: 'DAX',           ticker: 'GDAXI.INDX',     source: 'eodhd', flag: '🇩🇪' },
  { name: 'CAC 40',        ticker: 'FCHI.INDX',      source: 'eodhd', flag: '🇫🇷' },
  { name: 'IBEX 35',       ticker: 'IBEX.INDX',      source: 'eodhd', flag: '🇪🇸' },
  { name: 'AEX',           ticker: 'AEX.INDX',       source: 'eodhd', flag: '🇳🇱' },
  { name: 'BEL 20',        ticker: 'BFX.INDX',       source: 'eodhd', flag: '🇧🇪' },
  { name: 'ATX',           ticker: 'ATX.INDX',       source: 'eodhd', flag: '🇦🇹' },
  { name: 'OMX Helsinki',  ticker: 'OMXHPI.INDX',    source: 'eodhd', flag: '🇫🇮' },
  { name: 'PSI 20',        ticker: 'PSI20.INDX',     source: 'eodhd', flag: '🇵🇹' },
  // Ex-EMU
  { name: 'FTSE 100',      ticker: '^FTSE',           source: 'yahoo', flag: '🇬🇧' },
  { name: 'SMI',           ticker: 'SSMI.INDX',      source: 'eodhd', flag: '🇨🇭' },
  { name: 'OMX Stockholm', ticker: 'OMXS30.INDX',    source: 'eodhd', flag: '🇸🇪' },
  { name: 'OBX',           ticker: 'OBX.OL',         source: 'eodhd', flag: '🇳🇴' },
  { name: 'OMX Copenhagen',ticker: 'OMXC25.INDX',    source: 'eodhd', flag: '🇩🇰' },
]

// ── SECTORS ───────────────────────────────────────────────────────
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
  'Communication Services': '#84cc16',
  'Real Estate':            '#a855f7',
  'Other':                  '#6b7280',
}
