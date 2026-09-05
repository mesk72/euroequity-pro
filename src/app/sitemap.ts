import { MetadataRoute } from 'next'

// SITEMAP RIDOTTA — 5/9/2026, richiesta di Andrea.
// ForwardAlpha torna a essere a uso personale: nessuna pagina deve essere
// proposta a Google. La sitemap dichiara solo la homepage.
//
// Le 7.841 schede titolo sono state rimosse da qui e portano tutte il tag
// noindex (impostato nel layout radice): e' quello che ne provoca la
// rimozione dall'indice. Togliere la sitemap da solo NON basta — serve a
// non segnalare piu' le pagine, ma quelle gia' indicizzate restano finche'
// Google non legge il noindex.
export const revalidate = 3600

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: 'https://www.forwardalpha.pro',
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 1.0,
    },
  ]
}
