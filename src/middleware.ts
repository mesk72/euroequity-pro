import { NextRequest, NextResponse } from 'next/server'

// Protezione temporanea dell'intero sito con Basic Auth, finche' non e'
// pronto un vero sistema di login per tutti gli utenti. Blocca l'accesso
// a chiunque non conosca la password condivisa, impedendo lo scraping
// pubblico del database e della metodologia mentre il sito e' ancora
// esposto senza autenticazione reale.
//
// Le credenziali si impostano su Vercel (Project Settings -> Environment
// Variables), MAI scritte qui nel codice:
//   SITE_BASIC_AUTH_USER = un nome utente a scelta
//   SITE_BASIC_AUTH_PASS = una password forte a scelta
//
// Per rimuovere la protezione in futuro (quando il vero login sara'
// pronto), basta cancellare o svuotare queste due variabili d'ambiente
// su Vercel — non serve toccare questo file.

export function middleware(req: NextRequest) {
  const expectedUser = process.env.SITE_BASIC_AUTH_USER
  const expectedPass = process.env.SITE_BASIC_AUTH_PASS

  // Se le variabili non sono impostate, la protezione e' disattivata
  // (utile per lo sviluppo locale, o dopo aver attivato il vero login).
  if (!expectedUser || !expectedPass) {
    return NextResponse.next()
  }

  const authHeader = req.headers.get('authorization')

  if (authHeader) {
    const [scheme, encoded] = authHeader.split(' ')
    if (scheme === 'Basic' && encoded) {
      const decoded = Buffer.from(encoded, 'base64').toString('utf-8')
      const separatorIndex = decoded.indexOf(':')
      const user = decoded.slice(0, separatorIndex)
      const pass = decoded.slice(separatorIndex + 1)
      if (user === expectedUser && pass === expectedPass) {
        return NextResponse.next()
      }
    }
  }

  return new NextResponse('Authentication required', {
    status: 401,
    headers: { 'WWW-Authenticate': 'Basic realm="ForwardAlpha"' },
  })
}

// Esclude i file statici/interni di Next.js dalla protezione, per non
// rompere caricamento di immagini, font, ecc. — la pagina stessa resta
// comunque protetta perche' il suo HTML/dati passano comunque da qui.
export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
