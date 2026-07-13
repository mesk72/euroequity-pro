-- Tabelle separate per i dati di test Twelvedata, isolate da prices_eod
-- e fundamentals (che restano invariate, alimentate da Leeway/TIKR).
-- Stessa struttura delle tabelle esistenti, cosi' il confronto e' diretto.

CREATE TABLE prices_eod_twelvedata (
    ticker text NOT NULL,
    exchange text NOT NULL,
    date date NOT NULL,
    adj_close numeric,
    created_at timestamptz DEFAULT now(),
    PRIMARY KEY (ticker, exchange, date)
);

CREATE TABLE fundamentals_twelvedata (
    ticker text NOT NULL,
    exchange text NOT NULL,
    price numeric,
    mkt_cap numeric,
    pe_trailing numeric,
    pe_forward numeric,
    pb numeric,
    eps_growth numeric,
    rev_growth numeric,
    eps_fy0 numeric,
    eps_fy1 numeric,
    eps_fy2 numeric,
    last_reporting_date date,
    created_at timestamptz DEFAULT now(),
    PRIMARY KEY (ticker, exchange)
);

-- Abilita l'accesso tramite le API REST, stesso schema di sicurezza
-- delle altre tabelle (service_role puo' leggere/scrivere liberamente).
ALTER TABLE prices_eod_twelvedata ENABLE ROW LEVEL SECURITY;
ALTER TABLE fundamentals_twelvedata ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_full_access_prices_td" ON prices_eod_twelvedata
    FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "service_role_full_access_fund_td" ON fundamentals_twelvedata
    FOR ALL USING (true) WITH CHECK (true);
