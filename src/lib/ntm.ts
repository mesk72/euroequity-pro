/**
 * EUROEQUITY PRO — Calcolo Metriche NTM Calendarizzate
 *
 * Metodologia professionale per eliminare il cliff effect
 * nel cambio anno fiscale.
 *
 * LOGICA CHIAVE:
 * mp = (CM - FM + 12) % 12   → mesi passati dall'ultima chiusura
 * mr = 12 - mp               → mesi mancanti alla prossima chiusura
 *
 * Caso mp=0 (siamo nel mese di chiusura):
 *   FY1 è praticamente chiuso → EPS_NTM = FY2 (il vero forward)
 *   EPS_LTM = FY1 (l'anno quasi concluso)
 *
 * Caso mp>0:
 *   EPS_NTM = (mr/12)×FY1 + (mp/12)×FY2
 *   EPS_LTM = (mp/12)×FY1 + (mr/12)×FY0
 */

export interface FiscalEstimates {
  eps_fy0:      number | null  // EPS effettivo ultimo anno riportato
  eps_fy1:      number | null  // Stima EPS prossimo anno fiscale
  eps_fy2:      number | null  // Stima EPS anno fiscale successivo
  rev_fy0:      number | null  // Revenue effettiva ultimo anno (€M)
  rev_fy1:      number | null  // Stima Revenue prossimo anno
  rev_fy2:      number | null  // Stima Revenue anno successivo
  eps_fy1_30d:  number | null  // Stima FY1 di 30 giorni fa
  eps_fy2_30d:  number | null  // Stima FY2 di 30 giorni fa
  rev_fy1_30d:  number | null
  rev_fy2_30d:  number | null
  fiscal_month: number         // Mese chiusura bilancio (1-12)
  price:        number | null  // Ultimo prezzo di chiusura
}

export interface NTMMetrics {
  eps_ntm:      number | null  // EPS NTM calendarizzato
  eps_ltm:      number | null  // EPS LTM calendarizzato
  eps_ntm_30d:  number | null  // EPS NTM di 30 giorni fa
  rev_ntm:      number | null
  rev_ltm:      number | null
  pe_forward:   number | null  // Prezzo / EPS_NTM
  pe_trailing:  number | null  // Prezzo / EPS_LTM
  eps_growth:   number | null  // (EPS_NTM - EPS_LTM) / |EPS_LTM| × 100
  rev_growth:   number | null  // (REV_NTM - REV_LTM) / |REV_LTM| × 100
  eps_mom_30d:  number | null  // (EPS_NTM - EPS_NTM_30d) / |EPS_NTM_30d| × 100
  months_passed:     number
  months_remaining:  number
  months_passed_30d: number
}

function monthsPassed(currentMonth: number, fiscalMonth: number): number {
  return (currentMonth - fiscalMonth + 12) % 12
}

/**
 * Calendarizza EPS/REV su orizzonte NTM (forward 12 mesi).
 *
 * mp=0 → siamo nel mese di chiusura → FY1 quasi chiuso → NTM = FY2
 * mp>0 → NTM = (mr/12)×FY1 + (mp/12)×FY2
 */
function calendarizeNTM(
  fy1: number | null,
  fy2: number | null,
  mp: number
): number | null {
  if (mp === 0) return fy2   // FY1 praticamente chiuso, il forward è FY2
  if (fy1 == null) return null
  if (fy2 == null) return fy1
  const mr = 12 - mp
  return (mr / 12) * fy1 + (mp / 12) * fy2
}

/**
 * Calendarizza EPS/REV su orizzonte LTM (trailing 12 mesi).
 *
 * mp=0 → LTM = FY1 (anno quasi concluso)
 * mp>0 → LTM = (mp/12)×FY1 + (mr/12)×FY0
 */
function calendarizeLTM(
  fy0: number | null,
  fy1: number | null,
  mp: number
): number | null {
  if (mp === 0) return fy1   // FY1 quasi chiuso è il trailing
  if (fy0 == null) return null
  if (fy1 == null) return fy0
  const mr = 12 - mp
  return (mp / 12) * fy1 + (mr / 12) * fy0
}

function growthPct(current: number | null, base: number | null): number | null {
  if (current == null || base == null || base === 0) return null
  return ((current - base) / Math.abs(base)) * 100
}

export function computeNTMMetrics(
  est: FiscalEstimates,
  referenceDate: Date = new Date()
): NTMMetrics {
  const cm    = referenceDate.getMonth() + 1
  const fm    = est.fiscal_month
  const date30d = new Date(referenceDate)
  date30d.setDate(date30d.getDate() - 30)
  const cm30d = date30d.getMonth() + 1

  const mp     = monthsPassed(cm,    fm)
  const mp30d  = monthsPassed(cm30d, fm)
  const mr     = 12 - mp

  // Calendarizzazione
  const eps_ntm     = calendarizeNTM(est.eps_fy1, est.eps_fy2, mp)
  const eps_ltm     = calendarizeLTM(est.eps_fy0, est.eps_fy1, mp)
  const eps_ntm_30d = calendarizeNTM(est.eps_fy1_30d, est.eps_fy2_30d, mp30d)
  const rev_ntm     = calendarizeNTM(est.rev_fy1, est.rev_fy2, mp)
  const rev_ltm     = calendarizeLTM(est.rev_fy0, est.rev_fy1, mp)

  // PE ratios
  const pe_forward  = est.price && eps_ntm && eps_ntm > 0
    ? est.price / eps_ntm : null
  const pe_trailing = est.price && eps_ltm && eps_ltm > 0
    ? est.price / eps_ltm : null

  return {
    eps_ntm, eps_ltm, eps_ntm_30d, rev_ntm, rev_ltm,
    pe_forward, pe_trailing,
    eps_growth:  growthPct(eps_ntm, eps_ltm),
    rev_growth:  growthPct(rev_ntm, rev_ltm),
    eps_mom_30d: growthPct(eps_ntm, eps_ntm_30d),
    months_passed:     mp,
    months_remaining:  mr,
    months_passed_30d: mp30d,
  }
}
