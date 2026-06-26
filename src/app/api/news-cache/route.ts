import { NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_KEY || process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

export const revalidate = 1800 // 30 min cache Vercel Edge

export async function GET(req: Request) {
  const { searchParams } = new URL(req.url)
  const region = searchParams.get('region') || 'americas'
  const limit  = parseInt(searchParams.get('limit') || '500')

  const { data, error } = await supabase
    .from('news_cache')
    .select('*')
    .eq('region', region)
    .gte('pub_date', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
    .order('best_score', { ascending: false, nullsFirst: false })
    .limit(limit)

  if (error) return NextResponse.json({ items: [] })

  const response = NextResponse.json({ items: data || [] })
  response.headers.set('Cache-Control', 'public, s-maxage=1800, stale-while-revalidate=3600')
  return response
}
