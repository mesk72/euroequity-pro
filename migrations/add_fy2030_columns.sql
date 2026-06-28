-- Aggiungi colonne FY2029 e FY2030 alla tabella fundamentals
-- Da eseguire su Supabase Dashboard → SQL Editor

ALTER TABLE fundamentals 
ADD COLUMN IF NOT EXISTS eps_fy4 FLOAT,
ADD COLUMN IF NOT EXISTS eps_cagr_3y FLOAT,
ADD COLUMN IF NOT EXISTS implied_growth FLOAT,
ADD COLUMN IF NOT EXISTS ke FLOAT,
ADD COLUMN IF NOT EXISTS beta_local FLOAT,
ADD COLUMN IF NOT EXISTS rf_rate FLOAT;
