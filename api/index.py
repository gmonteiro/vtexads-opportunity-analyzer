from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode("utf-8"))


HTML = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VTEX Ads — Opportunity Analyzer</title>
<style>
:root {
    --bg: #0a0a0f; --surface: #13131a; --surface2: #1a1a24; --border: #2a2a3a;
    --text: #e4e4ed; --text2: #8888a0; --accent: #7c3aed; --accent2: #2563eb;
    --green: #22c55e; --yellow: #eab308; --red: #ef4444; --orange: #f97316; --blue: #3b82f6;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
.container { max-width: 1300px; margin: 0 auto; padding: 1.5rem; }
h1 { font-size: 1.6rem; background: linear-gradient(135deg, var(--accent), var(--accent2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.subtitle { color: var(--text2); font-size: 0.85rem; margin-top: 0.25rem; }

/* Summary cards */
.summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.8rem; margin: 1.2rem 0; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 1rem 1.2rem; }
.card .label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.5px; color: var(--text2); margin-bottom: 0.3rem; }
.card .value { font-size: 1.5rem; font-weight: 700; font-variant-numeric: tabular-nums; }
.card .value.accent { color: var(--accent); }
.card .value.green { color: var(--green); }
.card .value.blue { color: var(--blue); }
.card .value.orange { color: var(--orange); }

/* Filters */
.filters { display: flex; gap: 0.6rem; margin-bottom: 1rem; flex-wrap: wrap; align-items: center; }
.filters input { flex: 1; min-width: 220px; padding: 0.65rem 0.9rem; border: 1px solid var(--border); border-radius: 8px; background: var(--surface); color: var(--text); font-size: 0.9rem; outline: none; }
.filters input:focus { border-color: var(--accent); }
.filters select { padding: 0.55rem 0.7rem; border: 1px solid var(--border); border-radius: 6px; background: var(--surface); color: var(--text); font-size: 0.82rem; cursor: pointer; }

/* Accordion */
.adv-list { display: flex; flex-direction: column; gap: 0.5rem; }
.adv-card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; }
.adv-header { display: flex; align-items: center; gap: 0.8rem; padding: 0.9rem 1.2rem; cursor: pointer; user-select: none; transition: background 0.1s; }
.adv-header:hover { background: var(--surface2); }
.adv-toggle { font-size: 0.7rem; color: var(--text2); transition: transform 0.2s; width: 1rem; text-align: center; }
.adv-card.open .adv-toggle { transform: rotate(90deg); }
.adv-name { font-weight: 600; font-size: 0.95rem; flex: 1; }
.adv-stats { display: flex; gap: 1.2rem; font-size: 0.78rem; color: var(--text2); }
.adv-stats strong { color: var(--text); }
.adv-body { display: none; border-top: 1px solid var(--border); }
.adv-card.open .adv-body { display: block; }

/* Gap sections inside accordion */
.gap-section { border-bottom: 1px solid var(--border); }
.gap-section:last-child { border-bottom: none; }
.gap-header { display: flex; align-items: center; gap: 0.6rem; padding: 0.6rem 1.2rem; background: var(--surface2); cursor: pointer; user-select: none; }
.gap-header:hover { background: rgba(124,58,237,0.05); }
.gap-toggle { font-size: 0.6rem; color: var(--text2); width: 0.8rem; transition: transform 0.2s; }
.gap-section.open .gap-toggle { transform: rotate(90deg); }
.gap-title { font-size: 0.8rem; font-weight: 600; flex: 1; }
.gap-count { font-size: 0.72rem; color: var(--text2); background: var(--surface); padding: 2px 8px; border-radius: 10px; }
.gap-body { display: none; }
.gap-section.open .gap-body { display: block; }

/* Table inside gaps */
.gap-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; }
.gap-table th { padding: 0.45rem 0.8rem; text-align: left; font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.4px; color: var(--text2); font-weight: 600; background: var(--surface); border-bottom: 1px solid var(--border); }
.gap-table th.r { text-align: right; }
.gap-table td { padding: 0.4rem 0.8rem; border-bottom: 1px solid rgba(42,42,58,0.5); white-space: nowrap; }
.gap-table td.r { text-align: right; font-variant-numeric: tabular-nums; }
.gap-table tr:last-child td { border-bottom: none; }
.gap-table tr:hover { background: rgba(124,58,237,0.03); }

/* Badges */
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.68rem; font-weight: 600; }
.badge.pub-gap { background: rgba(34,197,94,0.12); color: var(--green); }
.badge.adtype-gap { background: rgba(59,130,246,0.12); color: var(--blue); }
.badge.ctx-gap { background: rgba(234,179,8,0.12); color: var(--yellow); }
.badge.size-gap { background: rgba(249,115,22,0.12); color: var(--orange); }
.badge.plc-gap { background: rgba(124,58,237,0.12); color: var(--accent); }

/* Similarity indicator */
.sim { display: inline-flex; align-items: center; gap: 0.3rem; }
.sim-bar { width: 40px; height: 5px; background: var(--surface2); border-radius: 3px; overflow: hidden; }
.sim-fill { height: 100%; border-radius: 3px; background: var(--accent); }

/* Loading */
.loading { text-align: center; padding: 4rem 2rem; }
.loading .spinner { width: 36px; height: 36px; border: 3px solid var(--border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; margin: 0 auto 1rem; }
@keyframes spin { to { transform: rotate(360deg); } }
.loading .msg { color: var(--text2); font-size: 0.9rem; }
.loading .elapsed { color: var(--text2); font-size: 0.78rem; margin-top: 0.4rem; }
.error { text-align: center; padding: 3rem; color: var(--red); }

/* Load more */
.load-more { text-align: center; padding: 1rem; }
.load-more button { padding: 0.6rem 2rem; border: 1px solid var(--border); border-radius: 8px; background: var(--surface); color: var(--text); font-size: 0.85rem; cursor: pointer; transition: all 0.15s; }
.load-more button:hover { border-color: var(--accent); color: var(--accent); }

@media (max-width: 768px) {
    .container { padding: 1rem; }
    .summary { grid-template-columns: repeat(2, 1fr); }
    .adv-stats { display: none; }
    .gap-table td, .gap-table th { padding: 0.3rem 0.5rem; font-size: 0.72rem; }
}
</style>
</head>
<body>
<div class="container">
    <header>
        <h1>Opportunity Analyzer</h1>
        <p class="subtitle">Oportunidades de investimento na rede VTEX Ads</p>
    </header>
    <div id="app"><div class="loading"><div class="spinner"></div><div class="msg">Analisando oportunidades da rede...</div><div class="elapsed" id="timer"></div></div></div>
</div>

<script>
const app = document.getElementById('app');
function esc(s) { const d = document.createElement('div'); d.textContent = s == null ? '' : String(s); return d.innerHTML; }
function fmt(n) { return n == null ? '0' : Number(n).toLocaleString('pt-BR'); }
function cur(n) { return n == null ? 'R$ 0' : Number(n).toLocaleString('pt-BR', {style:'currency', currency:'BRL', minimumFractionDigits:0, maximumFractionDigits:0}); }
function curD(n) { return n == null ? 'R$ 0' : Number(n).toLocaleString('pt-BR', {style:'currency', currency:'BRL', minimumFractionDigits:2}); }
function compact(n) {
    if (n == null) return 'R$ 0';
    const v = Number(n);
    if (v >= 1e6) return 'R$ ' + (v/1e6).toFixed(1).replace('.', ',') + 'M';
    if (v >= 1e3) return 'R$ ' + (v/1e3).toFixed(1).replace('.', ',') + 'k';
    return cur(v);
}

const GAP_META = {
    publisher_gap: { label: 'Publisher Gap', badge: 'pub-gap', icon: '&#9670;' },
    ad_type_gap:   { label: 'Ad Type Gap',   badge: 'adtype-gap', icon: '&#9672;' },
    context_gap:   { label: 'Context Gap',    badge: 'ctx-gap', icon: '&#9673;' },
    ad_size_gap:   { label: 'Ad Size Gap',    badge: 'size-gap', icon: '&#9674;' },
    placement_gap: { label: 'Placement Gap',  badge: 'plc-gap', icon: '&#9675;' },
};
const GAP_ORDER = ['publisher_gap', 'ad_type_gap', 'context_gap', 'ad_size_gap', 'placement_gap'];

let allData = [];
let timerInterval;

// Start timer
const startTime = Date.now();
timerInterval = setInterval(() => {
    const el = document.getElementById('timer');
    if (el) el.textContent = Math.floor((Date.now() - startTime) / 1000) + 's';
}, 1000);

async function init() {
    try {
        const resp = await fetch('/api/opportunities?currency_code=BRL');
        clearInterval(timerInterval);
        if (!resp.ok) throw new Error('Erro ' + resp.status);
        const json = await resp.json();
        if (json.error) throw new Error(json.error);
        allData = json.data || [];
        render();
    } catch (e) {
        clearInterval(timerInterval);
        app.innerHTML = '<div class="error">' + esc(e.message) + '</div>';
    }
}

function render() {
    let data = [...allData];

    // Apply filters
    const q = (document.getElementById('search') || {}).value || '';
    const typeF = (document.getElementById('ftype') || {}).value || 'all';
    const adTypeF = (document.getElementById('fadtype') || {}).value || 'all';

    if (q) {
        const ql = q.toLowerCase();
        data = data.filter(d => (d.advertiser_name||'').toLowerCase().includes(ql) || (d.publisher_name||'').toLowerCase().includes(ql));
    }
    if (typeF !== 'all') data = data.filter(d => d.opportunity_type === typeF);
    if (adTypeF !== 'all') data = data.filter(d => d.ad_type === adTypeF);

    // Group by advertiser
    const advMap = new Map();
    for (const d of data) {
        const key = d.advertiser_id;
        if (!advMap.has(key)) advMap.set(key, { id: key, name: d.advertiser_name, opps: [] });
        advMap.get(key).opps.push(d);
    }

    // Sort advertisers by total GMV 30d desc
    const advs = [...advMap.values()].map(a => {
        a.totalGmv30d = a.opps.reduce((s, o) => s + o.extra_gmv_30d, 0);
        a.totalSpendDaily = a.opps.reduce((s, o) => s + o.extra_spend_daily, 0);
        return a;
    }).sort((a, b) => b.totalGmv30d - a.totalGmv30d);

    // Totals
    const totalOpps = data.length;
    const totalAdvs = advs.length;
    const totalSpend = data.reduce((s, d) => s + d.extra_spend_daily, 0);
    const totalGmv = data.reduce((s, d) => s + d.extra_gmv_30d, 0);
    const totalConv = data.reduce((s, d) => s + d.extra_conv_30d, 0);

    // Unique filter values
    const oppTypes = [...new Set(allData.map(d => d.opportunity_type))].filter(Boolean).sort();
    const adTypes = [...new Set(allData.map(d => d.ad_type))].filter(Boolean).sort();

    let html = `
    <div class="filters">
        <input type="text" id="search" placeholder="Buscar advertiser ou publisher..." value="${esc(q)}" oninput="render()" />
        <select id="ftype" onchange="render()">
            <option value="all">Todos os tipos</option>
            ${oppTypes.map(t => '<option value="'+esc(t)+'"'+(t===typeF?' selected':'')+'>'+(GAP_META[t]?.label||t)+'</option>').join('')}
        </select>
        <select id="fadtype" onchange="render()">
            <option value="all">Todos ad types</option>
            ${adTypes.map(t => '<option value="'+esc(t)+'"'+(t===adTypeF?' selected':'')+'>'+ esc(t)+'</option>').join('')}
        </select>
    </div>
    <div class="summary">
        <div class="card"><div class="label">Advertisers</div><div class="value accent">${fmt(totalAdvs)}</div></div>
        <div class="card"><div class="label">Oportunidades</div><div class="value blue">${fmt(totalOpps)}</div></div>
        <div class="card"><div class="label">Extra Spend / dia</div><div class="value orange">${compact(totalSpend)}</div></div>
        <div class="card"><div class="label">GMV Potencial 30d</div><div class="value green">${compact(totalGmv)}</div></div>
        <div class="card"><div class="label">Conversoes 30d</div><div class="value">${fmt(totalConv)}</div></div>
    </div>
    <div class="adv-list">`;

    for (const adv of advs) {
        // Group opps by gap type
        const byGap = new Map();
        for (const g of GAP_ORDER) byGap.set(g, []);
        for (const o of adv.opps) {
            const list = byGap.get(o.opportunity_type);
            if (list) list.push(o); else { byGap.set(o.opportunity_type, [o]); }
        }

        html += `
        <div class="adv-card" onclick="toggleAdv(event, this)">
            <div class="adv-header">
                <span class="adv-toggle">&#9654;</span>
                <span class="adv-name">${esc(adv.name)}</span>
                <div class="adv-stats">
                    <span><strong>${adv.opps.length}</strong> opps</span>
                    <span><strong>${compact(adv.totalSpendDaily)}</strong>/dia</span>
                    <span><strong>${compact(adv.totalGmv30d)}</strong> GMV 30d</span>
                </div>
            </div>
            <div class="adv-body">`;

        for (const [gapType, opps] of byGap) {
            if (opps.length === 0) continue;
            const meta = GAP_META[gapType] || { label: gapType, badge: '', icon: '' };
            const gapGmv = opps.reduce((s, o) => s + o.extra_gmv_30d, 0);

            // Columns vary by gap type
            const showAdType = gapType !== 'publisher_gap';
            const showTargeting = gapType === 'context_gap' || gapType === 'placement_gap';
            const showSize = gapType === 'ad_size_gap' || gapType === 'placement_gap';

            html += `
            <div class="gap-section" onclick="toggleGap(event, this)">
                <div class="gap-header">
                    <span class="gap-toggle">&#9654;</span>
                    <span class="badge ${meta.badge}">${meta.label}</span>
                    <span class="gap-title">${compact(gapGmv)} GMV potencial</span>
                    <span class="gap-count">${opps.length}</span>
                </div>
                <div class="gap-body">
                    <table class="gap-table"><thead><tr>
                        <th>Publisher</th>
                        ${showAdType ? '<th>Ad Type</th>' : ''}
                        ${showTargeting ? '<th>Targeting</th>' : ''}
                        ${showSize ? '<th>Ad Size</th>' : ''}
                        <th class="r">Spend/dia</th>
                        <th class="r">Imps/dia</th>
                        <th class="r">Conv 30d</th>
                        <th class="r">GMV 30d</th>
                        <th>Similaridade</th>
                    </tr></thead><tbody>`;

            // Sort by GMV desc within gap
            opps.sort((a, b) => b.extra_gmv_30d - a.extra_gmv_30d);

            for (const o of opps) {
                const simPct = Math.min(100, (o.similarity_score / (opps[0]?.similarity_score || 1)) * 100);
                html += `<tr>
                    <td>${esc(o.publisher_name)}</td>
                    ${showAdType ? '<td><span class="badge adtype-gap">'+esc(o.ad_type)+'</span></td>' : ''}
                    ${showTargeting ? '<td>'+esc(o.targeting_type)+'</td>' : ''}
                    ${showSize ? '<td>'+esc(o.ad_size || o.ad_size_name)+'</td>' : ''}
                    <td class="r">${curD(o.extra_spend_daily)}</td>
                    <td class="r">${fmt(o.extra_imps_daily)}</td>
                    <td class="r">${fmt(o.extra_conv_30d)}</td>
                    <td class="r" style="font-weight:600;color:var(--green)">${cur(o.extra_gmv_30d)}</td>
                    <td><div class="sim"><div class="sim-bar"><div class="sim-fill" style="width:${simPct.toFixed(0)}%"></div></div><span style="font-size:0.7rem;color:var(--text2)">${o.neighbor_occurrences}</span></div></td>
                </tr>`;
            }

            html += '</tbody></table></div></div>';
        }

        html += '</div></div>';
    }

    html += '</div>';

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    html += '<div style="text-align:center;padding:1.5rem;color:var(--text2);font-size:0.75rem">' + fmt(allData.length) + ' oportunidades carregadas em ' + elapsed + 's</div>';

    app.innerHTML = html;
}

function toggleAdv(e, el) {
    if (e.target.closest('.gap-section')) return;
    el.classList.toggle('open');
}
function toggleGap(e, el) {
    e.stopPropagation();
    el.classList.toggle('open');
}

init();
</script>
</body>
</html>"""
