import { createClient } from '@supabase/supabase-js' // rebuild

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseKey)

// ── DATABASE TYPES ────────────────────────────────────────────────
export interface UserProfile {
  id:         string
  email:      string
  name:       string
  country:    string
  created_at: string
  newsletter: boolean
}

export interface Portfolio {
  id:         string
  user_id:    string
  name:       string
  positions:  PortfolioPosition[]
  updated_at: string
}

export interface PortfolioPosition {
  ticker:    string
  exchange:  string
  company:   string
  qty:       number
  buy_price: number
  added_at:  string
}

// ── SQL SCHEMA (run once in Supabase SQL editor) ──────────────────
export const SCHEMA_SQL = `
-- User profiles (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS profiles (
  id         UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email      TEXT NOT NULL,
  name       TEXT NOT NULL,
  country    TEXT NOT NULL DEFAULT '',
  newsletter BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Portfolios
CREATE TABLE IF NOT EXISTS portfolios (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name       TEXT NOT NULL DEFAULT 'Portfolio 1',
  positions  JSONB DEFAULT '[]'::jsonb,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- RLS: users can only see their own data
ALTER TABLE profiles   ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own profile"    ON profiles   FOR ALL USING (auth.uid() = id);
CREATE POLICY "Users see own portfolios" ON portfolios FOR ALL USING (auth.uid() = user_id);

-- Admin view (for newsletter export)
CREATE OR REPLACE VIEW public.newsletter_subscribers AS
  SELECT email, name, country, created_at
  FROM profiles
  WHERE newsletter = TRUE
  ORDER BY created_at DESC;
`

// ── USER OPERATIONS ───────────────────────────────────────────────
export async function getUserProfile(userId: string): Promise<UserProfile | null> {
  const { data } = await supabase
    .from('profiles')
    .select('*')
    .eq('id', userId)
    .single()
  return data
}

export async function createProfile(
  userId: string, email: string, name: string, country: string
): Promise<boolean> {
  const { error } = await supabase.from('profiles').insert({
    id: userId, email, name, country, newsletter: true
  })
  return !error
}

// ── PORTFOLIO OPERATIONS ──────────────────────────────────────────
export async function getPortfolios(userId: string): Promise<Portfolio[]> {
  const { data } = await supabase
    .from('portfolios')
    .select('*')
    .eq('user_id', userId)
    .order('name')
  return data || []
}

export async function savePortfolio(
  portfolioId: string, positions: PortfolioPosition[]
): Promise<boolean> {
  const { error } = await supabase
    .from('portfolios')
    .update({ positions, updated_at: new Date().toISOString() })
    .eq('id', portfolioId)
  return !error
}

export async function createPortfolio(
  userId: string, name: string
): Promise<Portfolio | null> {
  const { data } = await supabase
    .from('portfolios')
    .insert({ user_id: userId, name, positions: [] })
    .select()
    .single()
  return data
}

export async function ensureDefaultPortfolios(userId: string) {
  const existing = await getPortfolios(userId)
  if (existing.length === 0) {
    await Promise.all([
      createPortfolio(userId, 'Portfolio 1'),
      createPortfolio(userId, 'Portfolio 2'),
      createPortfolio(userId, 'Portfolio 3'),
    ])
  }
}
