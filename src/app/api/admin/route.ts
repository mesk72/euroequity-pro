import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

// Admin route — uses service role key (server-side only, never exposed to client)
export async function GET(req: NextRequest) {
  const adminKey = req.headers.get('x-admin-key')
  if (adminKey !== process.env.ADMIN_SECRET) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const supabaseAdmin = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  )

  const { data, error } = await supabaseAdmin
    .from('profiles')
    .select('email, name, country, newsletter, created_at')
    .order('created_at', { ascending: false })

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  // Return as CSV for easy import into email tools
  const format = req.nextUrl.searchParams.get('format') || 'json'
  if (format === 'csv') {
    const csv = [
      'email,name,country,newsletter,registered_at',
      ...(data || []).map(u =>
        `${u.email},"${u.name}",${u.country},${u.newsletter},${u.created_at}`
      )
    ].join('\n')
    return new NextResponse(csv, {
      headers: {
        'Content-Type': 'text/csv',
        'Content-Disposition': 'attachment; filename="euroequity-users.csv"'
      }
    })
  }

  return NextResponse.json({
    total:       data?.length || 0,
    newsletter:  data?.filter(u => u.newsletter).length || 0,
    users:       data,
  })
}
