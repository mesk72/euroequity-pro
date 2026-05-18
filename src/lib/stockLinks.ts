// Link ufficiali alle borse per ogni titolo MSCI EMU
// Formato: { isin, borseUrl, companyUrl }
export const STOCK_LINKS: Record<string, { isin: string; borseUrl: string; companyUrl: string }> = {
  // ── ITALY ─────────────────────────────────────────────────────
  'ENI.MIL':    { isin:'IT0003132476', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0003132476-MTAA.html', companyUrl:'https://www.eni.com' },
  'ENEL.MIL':   { isin:'IT0003128367', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0003128367-MTAA.html', companyUrl:'https://www.enel.com' },
  'ISP.MIL':    { isin:'IT0000072618', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0000072618-MTAA.html', companyUrl:'https://group.intesasanpaolo.com' },
  'UCG.MIL':    { isin:'IT0005239360', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0005239360-MTAA.html', companyUrl:'https://www.unicreditgroup.eu' },
  'RACE.MIL':   { isin:'NL0011585146', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/NL0011585146-MTAA.html', companyUrl:'https://www.ferrari.com' },
  'STM.MIL':    { isin:'NL0000226223', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/NL0000226223-MTAA.html', companyUrl:'https://www.st.com' },
  'G.MIL':      { isin:'IT0000062072', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0000062072-MTAA.html', companyUrl:'https://www.generali.com' },
  'MB.MIL':     { isin:'IT0000062957', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0000062957-MTAA.html', companyUrl:'https://www.mediobanca.com' },
  'STLAM.MIL':  { isin:'NL00150001Q9', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/NL00150001Q9-MTAA.html', companyUrl:'https://www.stellantis.com' },
  'BAMI.MIL':   { isin:'IT0005218380', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0005218380-MTAA.html', companyUrl:'https://www.bancobpm.it' },
  'NEXI.MIL':   { isin:'IT0005366767', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0005366767-MTAA.html', companyUrl:'https://www.nexigroup.com' },
  'BPER.MIL':   { isin:'IT0000066123', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0000066123-MTAA.html', companyUrl:'https://www.bper.it' },
  'A2A.MIL':    { isin:'IT0001233417', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0001233417-MTAA.html', companyUrl:'https://www.a2a.eu' },
  'TIT.MIL':    { isin:'IT0003497168', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0003497168-MTAA.html', companyUrl:'https://www.gruppotim.it' },
  'ERG.MIL':    { isin:'IT0001179392', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0001179392-MTAA.html', companyUrl:'https://www.erg.eu' },
  'TRN.MIL':    { isin:'IT0003242622', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0003242622-MTAA.html', companyUrl:'https://www.terna.it' },
  'PSTM.MIL':   { isin:'IT0003796171', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0003796171-MTAA.html', companyUrl:'https://www.posteitaliane.it' },
  'AMP.MIL':    { isin:'IT0004056980', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0004056980-MTAA.html', companyUrl:'https://www.amplifon.com' },
  'MONC.MIL':   { isin:'IT0004965148', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0004965148-MTAA.html', companyUrl:'https://www.monclergroup.com' },
  'EXPD.MIL':   { isin:'IT0000072986', borseUrl:'https://www.borsaitaliana.it/borsa/azioni/scheda/IT0000072986-MTAA.html', companyUrl:'https://www.mediobanca.com/it/premier' },

  // ── GERMANY ───────────────────────────────────────────────────
  'SAP.XETRA':   { isin:'DE0007164600', borseUrl:'https://www.boerse-frankfurt.de/equity/sap-se', companyUrl:'https://www.sap.com' },
  'ALV.XETRA':   { isin:'DE0008404005', borseUrl:'https://www.boerse-frankfurt.de/equity/allianz-se-vink-namens-aktien-eo-8', companyUrl:'https://www.allianz.com' },
  'SIE.XETRA':   { isin:'DE0007236101', borseUrl:'https://www.boerse-frankfurt.de/equity/siemens-ag-namens-aktien-o-n', companyUrl:'https://www.siemens.com' },
  'MUV2.XETRA':  { isin:'DE0008430026', borseUrl:'https://www.boerse-frankfurt.de/equity/muenchener-rueckvers-ges-ag-vink-namens-aktien-eo-5-46', companyUrl:'https://www.munichre.com' },
  'DTE.XETRA':   { isin:'DE0005140008', borseUrl:'https://www.boerse-frankfurt.de/equity/deutsche-telekom-ag-namens-aktien-o-n', companyUrl:'https://www.telekom.com' },
  'MBG.XETRA':   { isin:'DE0007100000', borseUrl:'https://www.boerse-frankfurt.de/equity/mercedes-benz-group-ag', companyUrl:'https://www.mercedes-benz.com' },
  'BMW.XETRA':   { isin:'DE0005190003', borseUrl:'https://www.boerse-frankfurt.de/equity/bayerische-motoren-werke-ag-stamm-aktien-eo-1', companyUrl:'https://www.bmwgroup.com' },
  'ADS.XETRA':   { isin:'DE000A1EWWW0', borseUrl:'https://www.boerse-frankfurt.de/equity/adidas-ag-namens-aktien-o-n', companyUrl:'https://www.adidas-group.com' },
  'BAYN.XETRA':  { isin:'DE000BAY0017', borseUrl:'https://www.boerse-frankfurt.de/equity/bayer-ag-namens-aktien-o-n', companyUrl:'https://www.bayer.com' },
  'DBK.XETRA':   { isin:'DE0005140008', borseUrl:'https://www.boerse-frankfurt.de/equity/deutsche-bank-ag-namens-aktien-o-n', companyUrl:'https://www.db.com' },
  'VOW3.XETRA':  { isin:'DE0007664039', borseUrl:'https://www.boerse-frankfurt.de/equity/volkswagen-ag-vorzugs-aktien-eo-5', companyUrl:'https://www.volkswagenag.com' },
  'EOAN.XETRA':  { isin:'DE000ENAG999', borseUrl:'https://www.boerse-frankfurt.de/equity/e-on-se-namens-aktien-o-n', companyUrl:'https://www.eon.com' },
  'RWE.XETRA':   { isin:'DE0007037129', borseUrl:'https://www.boerse-frankfurt.de/equity/rwe-ag-inhaber-aktien-a-o-n', companyUrl:'https://www.rwe.com' },
  'HEI.XETRA':   { isin:'DE0006047004', borseUrl:'https://www.boerse-frankfurt.de/equity/heidelberg-materials-ag-inhaber-aktien-o-n', companyUrl:'https://www.heidelbergmaterials.com' },
  'HFCL.XETRA':  { isin:'DE0006048432', borseUrl:'https://www.boerse-frankfurt.de/equity/henkel-ag-co-kgaa-vorzugs-aktien-o-n', companyUrl:'https://www.henkel.com' },
  'BEI.XETRA':   { isin:'DE0005200000', borseUrl:'https://www.boerse-frankfurt.de/equity/beiersdorf-ag-inhaber-aktien-o-n', companyUrl:'https://www.beiersdorf.com' },
  'MRK.XETRA':   { isin:'DE0006599905', borseUrl:'https://www.boerse-frankfurt.de/equity/merck-kgaa-inhaber-aktien-o-n', companyUrl:'https://www.merckgroup.com' },
  'MTX.XETRA':   { isin:'DE000A0D9PT0', borseUrl:'https://www.boerse-frankfurt.de/equity/mtu-aero-engines-ag-namens-aktien-o-n', companyUrl:'https://www.mtu.de' },
  'SHL.XETRA':   { isin:'DE000SHL1006', borseUrl:'https://www.boerse-frankfurt.de/equity/siemens-healthineers-ag-namens-aktien-eo-1', companyUrl:'https://www.siemens-healthineers.com' },

  // ── FRANCE ────────────────────────────────────────────────────
  'MC.PA':    { isin:'FR0000121014', borseUrl:'https://live.euronext.com/en/product/equities/FR0000121014-XPAR', companyUrl:'https://www.lvmh.com' },
  'TTE.PA':   { isin:'FR0014000MR3', borseUrl:'https://live.euronext.com/en/product/equities/FR0014000MR3-XPAR', companyUrl:'https://totalenergies.com' },
  'SAN.PA':   { isin:'FR0000120578', borseUrl:'https://live.euronext.com/en/product/equities/FR0000120578-XPAR', companyUrl:'https://www.sanofi.com' },
  'BNP.PA':   { isin:'FR0000131104', borseUrl:'https://live.euronext.com/en/product/equities/FR0000131104-XPAR', companyUrl:'https://group.bnpparibas' },
  'AIR.PA':   { isin:'NL0000235190', borseUrl:'https://live.euronext.com/en/product/equities/NL0000235190-XPAR', companyUrl:'https://www.airbus.com' },
  'OR.PA':    { isin:'FR0000120321', borseUrl:'https://live.euronext.com/en/product/equities/FR0000120321-XPAR', companyUrl:'https://www.loreal.com' },
  'AXA.PA':   { isin:'FR0000120628', borseUrl:'https://live.euronext.com/en/product/equities/FR0000120628-XPAR', companyUrl:'https://www.axa.com' },
  'KER.PA':   { isin:'FR0000121485', borseUrl:'https://live.euronext.com/en/product/equities/FR0000121485-XPAR', companyUrl:'https://www.kering.com' },
  'DG.PA':    { isin:'FR0000125486', borseUrl:'https://live.euronext.com/en/product/equities/FR0000125486-XPAR', companyUrl:'https://www.vinci.com' },
  'CAP.PA':   { isin:'FR0000125338', borseUrl:'https://live.euronext.com/en/product/equities/FR0000125338-XPAR', companyUrl:'https://www.capgemini.com' },
  'SU.PA':    { isin:'FR0000121972', borseUrl:'https://live.euronext.com/en/product/equities/FR0000121972-XPAR', companyUrl:'https://www.se.com' },
  'SGO.PA':   { isin:'FR0000125007', borseUrl:'https://live.euronext.com/en/product/equities/FR0000125007-XPAR', companyUrl:'https://www.saint-gobain.com' },
  'RI.PA':    { isin:'FR0000120693', borseUrl:'https://live.euronext.com/en/product/equities/FR0000120693-XPAR', companyUrl:'https://www.pernod-ricard.com' },
  'GLE.PA':   { isin:'FR0000130809', borseUrl:'https://live.euronext.com/en/product/equities/FR0000130809-XPAR', companyUrl:'https://www.societegenerale.com' },
  'VIE.PA':   { isin:'FR0004514015', borseUrl:'https://live.euronext.com/en/product/equities/FR0004514015-XPAR', companyUrl:'https://www.veolia.com' },
  'STM.PA':   { isin:'NL0000226223', borseUrl:'https://live.euronext.com/en/product/equities/NL0000226223-XPAR', companyUrl:'https://www.st.com' },
  'DSY.PA':   { isin:'FR0014003TT8', borseUrl:'https://live.euronext.com/en/product/equities/FR0014003TT8-XPAR', companyUrl:'https://www.3ds.com' },
  'ML.PA':    { isin:'FR0000131906', borseUrl:'https://live.euronext.com/en/product/equities/FR0000131906-XPAR', companyUrl:'https://www.michelin.com' },

  // ── NETHERLANDS ───────────────────────────────────────────────
  'ASML.AS':  { isin:'NL0010273215', borseUrl:'https://live.euronext.com/en/product/equities/NL0010273215-XAMS', companyUrl:'https://www.asml.com' },
  'INGA.AS':  { isin:'NL0011821202', borseUrl:'https://live.euronext.com/en/product/equities/NL0011821202-XAMS', companyUrl:'https://www.ing.com' },
  'PHIA.AS':  { isin:'NL0000009538', borseUrl:'https://live.euronext.com/en/product/equities/NL0000009538-XAMS', companyUrl:'https://www.philips.com' },
  'AD.AS':    { isin:'NL0011794037', borseUrl:'https://live.euronext.com/en/product/equities/NL0011794037-XAMS', companyUrl:'https://www.aholddelhaize.com' },
  'RAND.AS':  { isin:'NL0000379121', borseUrl:'https://live.euronext.com/en/product/equities/NL0000379121-XAMS', companyUrl:'https://www.randstad.com' },
  'NN.AS':    { isin:'NL0010773842', borseUrl:'https://live.euronext.com/en/product/equities/NL0010773842-XAMS', companyUrl:'https://www.nn-group.com' },
  'HEIA.AS':  { isin:'NL0000009165', borseUrl:'https://live.euronext.com/en/product/equities/NL0000009165-XAMS', companyUrl:'https://www.theheinekencompany.com' },

  // ── SPAIN ─────────────────────────────────────────────────────
  'ITX.MC':   { isin:'ES0148396007', borseUrl:'https://www.bolsasymercados.es/bme-exchange/es/Mercados-y-Cotizaciones/Acciones/Mercado-Continuo/Precios/ITX', companyUrl:'https://www.inditex.com' },
  'BBVA.MC':  { isin:'ES0113211835', borseUrl:'https://www.bolsasymercados.es/bme-exchange/es/Mercados-y-Cotizaciones/Acciones/Mercado-Continuo/Precios/BBVA', companyUrl:'https://www.bbva.com' },
  'BSAN.MC':  { isin:'ES0113900J37', borseUrl:'https://www.bolsasymercados.es/bme-exchange/es/Mercados-y-Cotizaciones/Acciones/Mercado-Continuo/Precios/SAN', companyUrl:'https://www.santander.com' },
  'IBE.MC':   { isin:'ES0144580Y14', borseUrl:'https://www.bolsasymercados.es/bme-exchange/es/Mercados-y-Cotizaciones/Acciones/Mercado-Continuo/Precios/IBE', companyUrl:'https://www.iberdrola.com' },
  'TEF.MC':   { isin:'ES0178430E18', borseUrl:'https://www.bolsasymercados.es/bme-exchange/es/Mercados-y-Cotizaciones/Acciones/Mercado-Continuo/Precios/TEF', companyUrl:'https://www.telefonica.com' },
  'REP.MC':   { isin:'ES0173516115', borseUrl:'https://www.bolsasymercados.es/bme-exchange/es/Mercados-y-Cotizaciones/Acciones/Mercado-Continuo/Precios/REP', companyUrl:'https://www.repsol.com' },
  'AMS.MC':   { isin:'ES0109067019', borseUrl:'https://www.bolsasymercados.es/bme-exchange/es/Mercados-y-Cotizaciones/Acciones/Mercado-Continuo/Precios/AMS', companyUrl:'https://www.amadeus.com' },
  'ENG.MC':   { isin:'ES0130960018', borseUrl:'https://www.bolsasymercados.es/bme-exchange/es/Mercados-y-Cotizaciones/Acciones/Mercado-Continuo/Precios/ENG', companyUrl:'https://www.enagas.es' },

  // ── BELGIUM ───────────────────────────────────────────────────
  'ABI.BR':   { isin:'BE0974293251', borseUrl:'https://live.euronext.com/en/product/equities/BE0974293251-XBRU', companyUrl:'https://www.ab-inbev.com' },
  'UCB.BR':   { isin:'BE0003739530', borseUrl:'https://live.euronext.com/en/product/equities/BE0003739530-XBRU', companyUrl:'https://www.ucb.com' },
  'SOLB.BR':  { isin:'BE0003470755', borseUrl:'https://live.euronext.com/en/product/equities/BE0003470755-XBRU', companyUrl:'https://www.solvay.com' },
  'ARGX.BR':  { isin:'BE0003763779', borseUrl:'https://live.euronext.com/en/product/equities/BE0003763779-XBRU', companyUrl:'https://www.argenx.com' },

  // ── FINLAND ───────────────────────────────────────────────────
  'NOKIA.HE':  { isin:'FI0009000681', borseUrl:'https://live.euronext.com/en/product/equities/FI0009000681-XHEL', companyUrl:'https://www.nokia.com' },
  'FORTUM.HE': { isin:'FI0009007132', borseUrl:'https://live.euronext.com/en/product/equities/FI0009007132-XHEL', companyUrl:'https://www.fortum.com' },
  'SAMPO.HE':  { isin:'FI0009003305', borseUrl:'https://live.euronext.com/en/product/equities/FI0009003305-XHEL', companyUrl:'https://www.sampo.com' },

  // ── AUSTRIA ───────────────────────────────────────────────────
  'VER.VI':  { isin:'AT0000746409', borseUrl:'https://www.wienerborse.at/en/stocks-market/stocks/stock-detail/?ISIN=AT0000746409', companyUrl:'https://www.verbund.com' },
  'EBS.VI':  { isin:'AT0000652011', borseUrl:'https://www.wienerborse.at/en/stocks-market/stocks/stock-detail/?ISIN=AT0000652011', companyUrl:'https://www.erstegroup.com' },

  // ── PORTUGAL ──────────────────────────────────────────────────
  'GALP.LS': { isin:'PTGAL0AM0009', borseUrl:'https://live.euronext.com/en/product/equities/PTGAL0AM0009-XLIS', companyUrl:'https://www.galp.com' },
  'EDP.LS':  { isin:'PTEDP0AM0009', borseUrl:'https://live.euronext.com/en/product/equities/PTEDP0AM0009-XLIS', companyUrl:'https://www.edp.com' },

  // ── IRELAND ───────────────────────────────────────────────────
  'CRH.IR':   { isin:'IE0001827041', borseUrl:'https://live.euronext.com/en/product/equities/IE0001827041-XDUB', companyUrl:'https://www.crh.com' },
  'DRVN.IR':  { isin:'IE0004906560', borseUrl:'https://live.euronext.com/en/product/equities/IE0004906560-XDUB', companyUrl:'https://www.kerry.com' },

  // ── GREECE ────────────────────────────────────────────────────
  'OPAP.AT':  { isin:'GRS419003009', borseUrl:'https://www.athexgroup.gr/web/guest/market-shares?p_p_id=Athex_Equity_Prices_WAR_AthexPortletsharedservices&selectedId=GRS419003009', companyUrl:'https://www.opap.gr' },
  'ETE.AT':   { isin:'GRS003003014', borseUrl:'https://www.athexgroup.gr/web/guest/market-shares?p_p_id=Athex_Equity_Prices_WAR_AthexPortletsharedservices&selectedId=GRS003003014', companyUrl:'https://www.nbg.gr' },
}
