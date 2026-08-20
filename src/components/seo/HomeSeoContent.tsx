/**
 * Contenuto della homepage leggibile dai motori di ricerca.
 *
 * PERCHE' ESISTE: `src/app/page.tsx` avvolge tutto in
 * `<Suspense fallback={null}>`. Finche' i dati non arrivano, l'HTML
 * iniziale e' VUOTO: Googlebot vedeva 60 caratteri di testo sulla pagina
 * piu' importante del sito. Una homepage vuota non si posiziona e non
 * trasmette autorita' alle 7.900 schede titolo, che quindi partono in
 * salita.
 *
 * Questo componente NON dipende dal caricamento: e' presente nell'HTML
 * fin dal primo byte.
 *
 * REGOLA SUI DATI (imposta da Andrea, 20/8/2026):
 *   - si mostrano SOLO informazioni pubbliche e descrittive
 *   - NESSUN punteggio proprietario, nemmeno di esempio
 *   - NESSUNA classifica ne' elenco ordinato per punteggio: il valore di
 *     ForwardAlpha non e' il punteggio del singolo titolo ma la classifica,
 *     ed e' quella che va protetta
 *
 * I numeri qui sono volutamente arrotondati e stabili nel tempo, per non
 * dover aggiornare il testo a ogni variazione dell'universo.
 */
export default function HomeSeoContent() {
  return (
    <section
      style={{
        position: 'absolute',
        width: 1,
        height: 1,
        padding: 0,
        margin: -1,
        overflow: 'hidden',
        clip: 'rect(0,0,0,0)',
        whiteSpace: 'nowrap',
        border: 0,
      }}
    >
      <h1>ForwardAlpha — ricerca azionaria quantitativa su oltre 7.900 titoli globali</h1>

      <p>
        ForwardAlpha e&apos; una piattaforma di ricerca azionaria quantitativa che analizza
        ogni giorno oltre 7.900 titoli quotati sui principali mercati mondiali, attribuendo
        a ciascuno punteggi proprietari di valutazione e di crescita costruiti con metodo
        istituzionale. La piattaforma e&apos; sviluppata da Andrea Meschini, gestore di
        portafoglio con esperienza in J.P. Morgan Asset Management e nella gestione di
        portafogli istituzionali per fondi pensione, CFA, sui mercati dal 1999.
      </p>

      <h2>Mercati coperti</h2>
      <p>
        Europa: Italia, Germania, Francia, Regno Unito, Svizzera, Spagna, Paesi Bassi,
        Belgio, Portogallo, Austria, Irlanda, Grecia, Svezia, Norvegia, Danimarca,
        Finlandia. Nord America: Stati Uniti e Canada. Asia-Pacifico: Giappone, Hong Kong,
        Australia, Corea del Sud, Singapore. I prezzi vengono aggiornati piu&apos; volte al
        giorno, dopo la chiusura di ciascun mercato.
      </p>

      <h2>Metodo di analisi</h2>
      <p>
        L&apos;approccio si fonda sui principi della finanza comportamentale: individuare le
        societa&apos; che il mercato sottovaluta secondo i parametri di valutazione classici
        ma che presentano un profilo di crescita superiore alla media. Ogni titolo viene
        confrontato con tutte le altre societa&apos; del proprio mercato di quotazione, cosi&apos;
        che il giudizio sia relativo a un insieme omogeneo e non a una media globale che
        mescolerebbe realta&apos; molto diverse.
      </p>
      <p>
        La valutazione considera il rapporto fra prezzo e utili, storico e prospettico, e il
        rapporto fra prezzo e patrimonio netto. La crescita considera l&apos;andamento atteso
        degli utili e dei ricavi, insieme al comportamento del prezzo su orizzonti di sei e
        dodici mesi depurato dalle oscillazioni di breve periodo. I dati fondamentali
        provengono da TIKR, i prezzi e i rendimenti da Yahoo Finance.
      </p>

      <h2>Reverse earnings model</h2>
      <p>
        Per i titoli statunitensi la piattaforma calcola inoltre le aspettative di crescita
        degli utili implicite nel prezzo di mercato: anziche&apos; stimare quanto vale una
        societa&apos;, il modello ricava quali risultati il mercato stia gia&apos; scontando in
        quella quotazione. E&apos; uno strumento utile a capire quanto sia ambiziosa la
        valutazione corrente prima di prendere una posizione.
      </p>

      <h2>Cosa offre la piattaforma</h2>
      <p>
        Schede dettagliate per ogni titolo con grafico dei prezzi a cinque anni, rendimenti
        a una settimana, un mese, sei mesi, dodici mesi, tre e cinque anni, multipli di
        valutazione e confronto con la media del settore. Strumenti di selezione per
        mercato, settore e caratteristiche di valutazione e crescita. Analisi aggregate di
        settore per area geografica.
      </p>

      <h2>Accesso</h2>
      <p>
        La consultazione dei punteggi proprietari e degli strumenti di selezione richiede la
        registrazione, che e&apos; gratuita. Per informazioni sull&apos;accesso professionale e
        sulla copertura completa dell&apos;universo si puo&apos; scrivere a
        andrea@forwardalpha.pro.
      </p>

      <h2>Avvertenza</h2>
      <p>
        ForwardAlpha fornisce ricerca e analisi quantitativa a scopo informativo. Non
        costituisce consulenza finanziaria personalizzata ne&apos; sollecitazione
        all&apos;investimento. I modelli calcolano indicatori statistici e non esprimono
        raccomandazioni di acquisto o vendita.
      </p>
    </section>
  )
}
