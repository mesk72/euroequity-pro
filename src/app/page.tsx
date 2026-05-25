@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap');
@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --bg:      #07090d;
  --surface: #0d1017;
  --border:  #1e2840;
  --gold:    #c8982a;
  --green:   #22d48a;
  --red:     #e84560;
  --text:    #dde4f0;
  --muted:   #5a6880;
  --sub:     #8a9ab8;
}

* { box-sizing: border-box; }

body {
  background: var(--bg);
  color: var(--text);
  font-family: 'Outfit', sans-serif;
}

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 2px; }

/* Input fields */
.input-field {
  @apply w-full bg-bg border border-border rounded-md px-3 py-2 text-sm text-text
         focus:outline-none focus:border-gold transition-colors;
}

select.input-field option {
  background: var(--surface);
  color: var(--text);
}

/* Section header */
.section-hdr {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--muted);
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 12px;
}

/* Metric card */
.metric-card {
  @apply bg-surface border border-border rounded-md p-3;
}
.metric-label {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 4px;
}
.metric-value {
  font-family: 'Fira Code', monospace;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--gold);
}

/* Index card */
.index-card {
  @apply bg-surface border border-border rounded-md p-2.5 min-w-[110px] flex-shrink-0;
}

/* Table */
.data-table {
  @apply w-full text-sm;
  border-collapse: collapse;
}
.data-table th {
  @apply text-left py-2 px-3 text-xs font-700 text-muted uppercase tracking-wide
         border-b border-border sticky top-0 bg-surface cursor-pointer select-none;
}
.data-table th:hover { color: var(--text); }
.data-table td {
  @apply py-2 px-3 border-b border-border/50 font-mono text-xs;
}
.data-table tr:hover td { background: rgba(255,255,255,0.02); }

/* Button variants */
.btn-primary {
  @apply bg-gold text-bg font-700 px-4 py-2 rounded-md text-sm
         hover:bg-yellow-500 transition-colors disabled:opacity-50;
}
.btn-ghost {
  @apply border border-border text-muted px-4 py-2 rounded-md text-sm
         hover:border-gold hover:text-gold transition-colors;
}

/* Badge */
.badge {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 3px;
}
.badge-beta  { background: rgba(200,152,42,0.15); color: #c8982a; border: 1px solid rgba(200,152,42,0.4); }
.badge-live  { background: rgba(34,212,138,0.1);  color: #22d48a; border: 1px solid rgba(34,212,138,0.3); }
.badge-delay { background: rgba(90,104,128,0.2);  color: #8a9ab8; border: 1px solid rgba(90,104,128,0.3); }

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: none; }
}
.fade-in { animation: fadeIn 0.2s ease forwards; }

@keyframes shimmer {
  0%, 100% { opacity: 1; }
  50%       { opacity: 0.4; }
}
.shimmer {
  animation: shimmer 1.5s ease infinite;
  background: var(--border);
  border-radius: 4px;
}

/* Positive / Negative */
.pos { color: var(--green); }
.neg { color: var(--red); }
.neu { color: var(--sub); }

/* Responsive sidebar */
@media (max-width: 768px) {
  .sidebar { display: none; }
  .sidebar.open { display: flex; position: fixed; inset: 0; z-index: 50; }
}
