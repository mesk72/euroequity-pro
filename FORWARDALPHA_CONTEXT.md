# FORWARDALPHA — CONTEXT & FORMULE CORE
# Leggere all'inizio di ogni sessione prima di toccare qualsiasi codice

## REGOLE FONDAMENTALI
- Non modificare mai le formule rank senza esplicita approvazione di Andrea
- Sempre leggere il file completo prima di modificarlo
- Sempre verificare il build Vercel prima di considerare un fix completato
- In caso di dubbio, ripristinare dal commit pulito
- pb<50 VIETATO — nessun limite su PB

## COMMIT DI RIFERIMENTO PULITI
- page.tsx: 41924e25 (ultimo build passato)
- stock/[id]/page.tsx: verificare ultimo build passato

## FORMULA VALUE SCORE
- Parametri: r_eyt (EY trailing = 1/PE_trail), r_eyf (EY forward = 1/PE_fwd), r_pb (1/PB)
- Minimo: 2 parametri su 3
- Formula: pct_rank(val_sums, sum(val_inputs))
- EY anche negativo — nessun caso speciale
- PB: nessun limite (pb<50 VIETATO)

## FORMULA GROWTH SCORE
- Parametri: r_epsg (EPS growth), r_revg (Rev growth), r_m6 (mom6m-mom1w), r_m12 (mom12m-mom1m)
- Minimo: 3 parametri su 4
- Formula: pct_rank(gr_sums, sum(gr_inputs))
- mom6m_adj = mom6m - mom1w (aggiustato per overbought)
- mom12m_adj = mom12m - mom1m (aggiustato per overbought)

## FORMULA COMBINED/BEST SCORE
- SOLO se titolo ha ENTRAMBI value_score AND growth_score
- Formula: pct_rank(sum_arr, value_score + growth_score)
- Se manca value O growth → combined_rank = NULL
- Prima di salvare combined_rank: PATCH combined_rank=NULL per tutti gli exchange

## FORMULA PERCENTILE RANK
- pct_rank(values, v) = round(below / len(valid) * 100)
- Range: 0-100 (1=peggiore, 99=migliore)

## CALENDARIZZAZIONE EPS
- FY end + 60 giorni = pub_date
- Se pub_date > oggi → non ancora riportato
- W_NEXT = giorni_da_pub_date / giorni_totali_anno
- W_CURR = 1 - W_NEXT
- eps_ltm = W_CURR*fy0 + W_NEXT*fy1
- eps_ntm = W_CURR*fy1 + W_NEXT*fy2
- eps_ntm1 = W_CURR*fy2 + W_NEXT*fy3
- eps_ntm2 = W_CURR*fy3 + W_NEXT*fy4 (quando disponibile FY2029)
- FY fissi: fy0=FY2025, fy1=FY2026, fy2=FY2027, fy3=FY2028, fy4=FY2029

## RANK GROUPS EU
- ITA: MIL
- DEU: XETRA
- FRA: PA
- GBR: LSE (non AIM)
- SWE: OM
- NOR: OB
- CHE: SWX
- NLD: AS
- BEL: BR
- FIN: HE
- ESP: MC
- DNK: CPSE
- POR: LS
- NO_RANK: VI, IR, NGM, AIM (GR eliminata)

## UNIVERSO
- EU: ~2,064 titoli in_universe=true
- US: 1,972 titoli in_universe=true
- Exchange eliminati: GR (tutti i titoli rimossi dal DB)

## LOCKED PER GUEST (non loggati)
- valueScore, growthScore, combinedRank
- mom1w, mom1m, mom6m, mom12m
- Tab Best Value, Best Growth, Best Combined → LoginGate

## SUPABASE
- URL: https://mlqkisnizgyvvqajdvbh.supabase.co
- Tabelle: stocks, fundamentals, prices_eod, fx_rates, daily_log
- Storage bucket: tikr-uploads
- File: tikr_eu_latest.csv, tikr_us_latest.csv, fiscal_year_end.csv
- Limit default: 100 — usare sempre limit=1000

## GITHUB ACTIONS
- daily_eu.yml: cron 0 19 * * 1-5 (21:00 CET = 19:00 UTC)
- daily_us.yml: cron separato
- weekly_eu.yml: cron 0 7 * * 0 (domenica 09:00 CET)
- weekly_us.yml: cron 0 7 * * 0
- NOTA: GitHub API ritorna 403 per file in .github/workflows/ — modificare manualmente

## STACK
- Next.js 14, Vercel Pro, Supabase, GitHub Actions
- Font: IBM Plex Sans, IBM Plex Mono, IBM Plex Sans Condensed
- Colori: bg #0d1017, surface #111827, orange #f59e0b, green #22d48a, red #e84560

## EXCHANGE → SUFFISSO FMP
- AS → .AS, BR → .BR, LS → .LS, OB → .OL
- VI → .VI, IR → .IR, HE → .HE, CPSE → .CO
- OM → .ST, MC → .MC, LSE → .L, AIM → .L
- FMP endpoint: /stable/profile (NON /api/v3/profile — deprecato agosto 2025)

## ISIN MANCANTI (da riprovare con ticker alternativi)
- AS: ERC, KORPT, OBAM, CABLE, BACE, LKFT, SWICH, TRIO
- BR: ENRGY, NYXH, numerici vari, DEXB
- LS: ALSMB, MLARR, MLATR, MLCIA, MLGSH, MLORE, MLVDN
- OB: GENO, EISP, COSH, VIEI, SOMA, CAPT
- VI: ATH, BMAG, EIOS, GHC, HRX5, HST, HUI, ICG, K2G, MWB, REGU, RWT, UKO, VAS, ZHT
- IR: SENUS
- HE: AUROORA, CANATU, CITYVA
