export default function LegalPage() {
  const sections = [
    {
      title: '1. Terms of Use',
      items: [
        ['Operator', 'ForwardAlpha is operated by Andrea Meschini, Verona, Italy. Contact: andrea@forwardalpha.pro . Contact: andrea@forwardalpha.pro · '],
        ['Acceptance of Terms', 'By accessing or using ForwardAlpha, you confirm that you have read, understood, and agree to be bound by these Terms. If you do not agree, do not use this service.'],
        ['Description of Service', 'ForwardAlpha provides financial data, quantitative analytics, equity screening tools, and portfolio tracking for informational purposes only. Market data is sourced from Leeway (leeway.tech) under commercial licence.'],
        ['Free Trial', 'New registered users receive a 14-day free trial with full access to all features. No credit card is required to start the trial.'],
        ['Subscription', 'After the trial, access to premium features requires a paid subscription of €4.99/month (IVA inclusa dove applicabile), automatically renewed unless cancelled.'],
        ['Cancellation', 'You may cancel at any time. In accordance with D.Lgs. 206/2005 (Codice del Consumo) and EU Consumer Rights Directive 2011/83/EU, you have a 14-day cooling-off right from initial subscription. Refund requests: andrea@forwardalpha.pro.'],
        ['Prohibited Uses', 'You may not reverse-engineer, bulk-scrape, or resell data; share account credentials; or use the service to provide unauthorised investment advice to third parties.'],
        ['Governing Law', 'These Terms are governed exclusively by Italian law. Any disputes shall be subject to the exclusive jurisdiction of the Court of Verona (Tribunale di Verona), without prejudice to mandatory EU consumer protection rights.'],
      ]
    },
    {
      title: '2. Disclaimer — No Investment Advice',
      items: [
        ['Not Investment Advice', 'ForwardAlpha is a personal financial data and research tool operated by Andrea Meschini as an individual. All data, analytics, and tools are provided for informational and educational purposes only. Nothing on this platform constitutes investment advice, financial advice, or a personal recommendation to buy, sell, or hold any financial instrument within the meaning of D.Lgs. 58/1998 (TUF), MiFID II (Directive 2014/65/EU), or any other applicable regulation.'],
        ['Not Authorised to Advise', 'Andrea Meschini has passed the CFA Program Level III examination and the IMC (Investment Management Certificate) examination and has extensive professional experience in investment management. However, he is not currently registered as an authorised financial advisor (consulente finanziario abilitato all\'offerta fuori sede) with the OCF (Organismo di vigilanza e tenuta dell\'albo unico dei Consulenti Finanziari), nor with the FCA or any other regulatory authority. ForwardAlpha does not provide regulated investment services.'],
        ['No Offer or Solicitation', 'Nothing on ForwardAlpha constitutes an offer or solicitation to buy or sell any financial instrument in any jurisdiction. Past performance is not indicative of future results.'],
        ['Data Accuracy & Delay', 'Market prices are delayed by 15-20 minutes from real-time and are provided by Leeway (leeway.tech). Fundamental data (P/E, EPS, dividends, etc.) is updated at end of trading day. Andrea Meschini makes no warranty as to accuracy, completeness, timeliness, or fitness for purpose of any data displayed.'],
        ['EPS & Earnings Dates', 'On corporate earnings reporting dates, forward EPS estimates may roll to the new fiscal year. Exercise caution around earnings announcement dates as estimates may be substantially revised.'],
        ['Quantitative Models', 'Value Score and Growth Score are proprietary quantitative ranking models developed by Andrea Meschini. Formula: Rank(x) = (count(xi < x) + 0.5 x count(xi = x)) / N x 100, yielding integers from 1 (worst) to 100 (best). These scores do not guarantee future performance.'],
        ['Portfolio Tools', 'Portfolio tracking tools are for personal record-keeping only. Values are indicative and may not reflect actual execution prices. Tools do not account for transaction costs, taxes, currency risk, or market impact.'],
      ]
    },
    {
      title: '3. Limitation of Liability',
      items: [
        ['Maximum Exclusion', 'To the maximum extent permitted by Italian and EU law, Andrea Meschini shall not be liable for any direct, indirect, incidental, special, consequential, or punitive damages arising from: (a) use of or inability to use the service; (b) reliance on data or analysis; (c) investment decisions based on information from this platform; (d) interruption or termination of the service.'],
        ['No Guarantee of Accuracy', 'Andrea Meschini does not guarantee the accuracy, completeness, or timeliness of any data provided. Market data is sourced from third-party providers and may contain errors.'],
        ['Consumer Rights', 'Nothing in this limitation of liability excludes or restricts any rights you have under mandatory Italian consumer protection law (D.Lgs. 206/2005 — Codice del Consumo) or EU consumer protection directives.'],
      ]
    },
    {
      title: '4. Intellectual Property',
      items: [
        ['Proprietary Content', 'All quantitative models (Value Score, Growth Score), ranking algorithms, software, design, and original text content on ForwardAlpha are the intellectual property of Andrea Meschini, protected by Italian copyright law (L. 633/1941) and applicable EU intellectual property law.'],
        ['Market Data', 'Market data is provided by Leeway (leeway.tech) under commercial licence. Users may not redistribute, resell, or commercially exploit this data without written permission.'],
        ['Permitted Use', 'Users may access and use data solely for personal, non-commercial investment research. Any other use requires prior written consent from Andrea Meschini.'],
      ]
    },
    {
      title: '5. Privacy Policy (GDPR / D.Lgs. 196/2003)',
      items: [
        ['Data Controller', 'The data controller is Andrea Meschini, 37139 Verona VR, Italy. Contact for data protection matters: andrea@forwardalpha.pro'],
        ['Data We Collect', 'We collect: full name, email address, country of residence, hashed password, newsletter preference, and anonymised usage data.'],
        ['Legal Basis (GDPR Art. 6)', 'Contract performance (Art. 6.1.b): processing necessary to provide the service. Legitimate interest (Art. 6.1.f): security and fraud prevention. Consent (Art. 6.1.a): marketing communications, only if you opt in.'],
        ['Data Sharing', 'Data is shared only with: Supabase Inc. (database infrastructure, EU Frankfurt servers, under Standard Contractual Clauses) and Stripe Inc. (payment processing, under SCCs). No personal data is sold or shared with advertising networks.'],
        ['Your Rights', 'Under GDPR and D.Lgs. 196/2003 you have the right to: access (Art. 15), rectify (Art. 16), erase (Art. 17), restrict processing (Art. 18), data portability (Art. 20), and object to processing (Art. 21). Contact andrea@forwardalpha.pro — responses within 30 days. You may lodge a complaint with the Garante per la protezione dei dati personali (garanteprivacy.it) or your local EU data protection authority.'],
        ['Retention', 'Account data retained for the duration of your account plus 2 years after closure. Payment records retained for 10 years (Italian tax law, Art. 2220 c.c.). You may request deletion of personal data at any time, subject to legal retention obligations.'],
        ['Newsletter', 'If you opt in, your email will be used to send product updates and market commentary. You may unsubscribe at any time via any email link or by contacting andrea@forwardalpha.pro.'],
      ]
    },
    {
      title: '6. Cookie Policy',
      items: [
        ['Strictly Necessary Cookies', 'ForwardAlpha uses only strictly necessary cookies for session management and security (CSRF protection). These do not require your consent under Art. 122 D.Lgs. 196/2003 and cannot be disabled without affecting service functionality.'],
        ['No Advertising or Tracking', 'ForwardAlpha does not use advertising cookies, third-party tracking cookies, or analytics cookies. No data is shared with advertising or analytics networks.'],
        ['Future Changes', 'If analytics or other non-essential cookies are introduced in the future, you will be informed in advance and explicit consent will be requested.'],
      ]
    },
  ]

  return (
    <div style={{ background:'#0a0e1a', minHeight:'100vh', color:'#e2e8f0', fontFamily:'IBM Plex Sans, sans-serif', padding:'40px 24px' }}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Sans+Condensed:wght@600;700&display=swap');`}</style>
      <div style={{ maxWidth:760, margin:'0 auto' }}>

        <div style={{ marginBottom:28, borderBottom:'2px solid #f97316', paddingBottom:16 }}>
          <a href="/" style={{ textDecoration:'none' }}>
            <div style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:22, color:'#f97316' }}>
              EURO<span style={{ color:'#94a3b8' }}>EQUITY</span> <span style={{ color:'#64748b', fontSize:14 }}>PRO</span>
            </div>
          </a>
          <div style={{ fontSize:9, color:'#64748b', marginTop:4, letterSpacing:'0.14em', fontFamily:'IBM Plex Sans Condensed', fontWeight:600 }}>
            LEGAL DOCUMENTATION · ANDREA MESCHINI · VERONA, ITALY
          </div>
          <div style={{ fontSize:11, color:'#64748b', marginTop:8 }}>
            Last updated: May 2026 · <a href="mailto:andrea@forwardalpha.pro" style={{ color:'#f97316' }}>andrea@forwardalpha.pro</a>
          </div>
        </div>

        {sections.map(({ title, items }) => (
          <div key={title} style={{ marginBottom:12, background:'#111827', border:'1px solid #1e2d45', borderRadius:4, overflow:'hidden' }}>
            <div style={{ background:'#161d2e', padding:'10px 16px', borderBottom:'1px solid #1e2d45', fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:13, color:'#f97316' }}>
              {title}
            </div>
            <div style={{ padding:'12px 16px' }}>
              {items.map(([label, text], i) => (
                <div key={label} style={{ marginBottom: i < items.length-1 ? 10 : 0, paddingBottom: i < items.length-1 ? 10 : 0, borderBottom: i < items.length-1 ? '1px solid rgba(30,45,69,0.6)' : 'none' }}>
                  <div style={{ fontFamily:'IBM Plex Sans Condensed', fontWeight:700, fontSize:10, color:'#94a3b8', marginBottom:3, textTransform:'uppercase', letterSpacing:'0.1em' }}>
                    {label}
                  </div>
                  <div style={{ fontSize:11.5, color:'#64748b', lineHeight:1.7 }}>{text}</div>
                </div>
              ))}
            </div>
          </div>
        ))}

        <div style={{ fontSize:10, color:'#3d5068', textAlign:'center', paddingTop:16, borderTop:'1px solid #1e2d45', marginTop:8 }}>
          Andrea Meschini ·, 37139 Verona VR, Italy · andrea@forwardalpha.pro · © 2026
        </div>
      </div>
    </div>
  )
}
