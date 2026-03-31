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
<title>Catalogo de Placements — VTEX Ads Network</title>
<style>
:root {
    --bg: #0a0a0f; --surface: #13131a; --surface2: #1a1a24; --border: #2a2a3a;
    --text: #e4e4ed; --text2: #8888a0; --accent: #7c3aed; --accent2: #2563eb;
    --green: #22c55e; --yellow: #eab308; --red: #ef4444; --blue: #3b82f6;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
.container { max-width: 1400px; margin: 0 auto; padding: 1.5rem; }
header { margin-bottom: 1.5rem; display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
.back-link { color: var(--text2); text-decoration: none; font-size: 0.85rem; padding: 0.4rem 0.8rem; border: 1px solid var(--border); border-radius: 6px; }
.back-link:hover { color: var(--text); background: var(--surface2); }
h1 { font-size: 1.5rem; background: linear-gradient(135deg, var(--accent), var(--accent2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.subtitle { color: var(--text2); font-size: 0.85rem; }

.filters { display: flex; gap: 0.6rem; margin-bottom: 1rem; flex-wrap: wrap; align-items: center; }
.filters input { flex: 1; min-width: 200px; padding: 0.6rem 0.8rem; border: 1px solid var(--border); border-radius: 8px; background: var(--surface); color: var(--text); font-size: 0.9rem; outline: none; }
.filters input:focus { border-color: var(--accent); }
.filters select { padding: 0.5rem 0.7rem; border: 1px solid var(--border); border-radius: 6px; background: var(--surface); color: var(--text); font-size: 0.85rem; }

.stats { display: flex; gap: 1.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
.stat { font-size: 0.85rem; color: var(--text2); }
.stat strong { color: var(--text); }

.table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }
table { width: 100%; border-collapse: collapse; font-size: 0.82rem; }
thead th { background: var(--surface2); color: var(--text2); font-weight: 600; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.5px; padding: 0.6rem 0.8rem; text-align: left; border-bottom: 1px solid var(--border); white-space: nowrap; cursor: pointer; user-select: none; }
thead th:hover { color: var(--text); }
tbody tr { border-bottom: 1px solid var(--border); transition: background 0.1s; }
tbody tr:last-child { border-bottom: none; }
tbody tr:hover { background: var(--surface2); }
td { padding: 0.5rem 0.8rem; white-space: nowrap; }
td.name { font-weight: 500; max-width: 220px; overflow: hidden; text-overflow: ellipsis; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }

.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 600; }
.badge.product { background: rgba(59,130,246,0.1); color: var(--blue); }
.badge.banner { background: rgba(124,58,237,0.1); color: var(--accent); }
.badge.sbrand { background: rgba(34,197,94,0.1); color: var(--green); }
.badge.q-high { background: rgba(34,197,94,0.15); color: var(--green); }
.badge.q-med { background: rgba(234,179,8,0.15); color: var(--yellow); }
.badge.q-low { background: rgba(239,68,68,0.15); color: var(--red); }

.fill-bar { display: inline-flex; align-items: center; gap: 0.4rem; }
.fill-track { width: 50px; height: 6px; background: var(--surface2); border-radius: 3px; overflow: hidden; }
.fill-val { height: 100%; border-radius: 3px; }
.fill-val.high { background: var(--green); }
.fill-val.med { background: var(--yellow); }
.fill-val.low { background: var(--red); }

.loading { text-align: center; padding: 3rem; color: var(--text2); }
.error { text-align: center; padding: 2rem; color: var(--red); }

@media (max-width: 768px) {
    .container { padding: 1rem; }
    td, th { padding: 0.4rem 0.5rem; font-size: 0.75rem; }
}
</style>
</head>
<body>
<div class="container">
    <header>
        <a href="/" class="back-link">&#8592; Explorer</a>
        <div>
            <h1>Catalogo de Placements</h1>
            <p class="subtitle">Inventario completo com indicadores de qualidade — ultimos 30 dias</p>
        </div>
    </header>
    <div id="app"><div class="loading">Carregando catalogo de placements...</div></div>
</div>

<script>
const $ = s => document.querySelector(s);
const app = $('#app');

function esc(s) { const d = document.createElement('div'); d.textContent = s == null ? '' : String(s); return d.innerHTML; }
function fmt(n) { return n == null ? '0' : Number(n).toLocaleString('pt-BR'); }
function pct(n) { return n == null ? '0%' : Number(n).toFixed(1) + '%'; }

function adTypeBadge(t) {
    if (t === 'product' || t === 'PRODUCT') return 'product';
    if (/banner/i.test(t)) return 'banner';
    if (/sponsored/i.test(t)) return 'sbrand';
    return '';
}

let allData = [];
let sortState = { col: 'total_requests', asc: false };

async function init() {
    try {
        const resp = await fetch('/api/placements');
        if (!resp.ok) throw new Error('Erro ao carregar placements');
        const data = await resp.json();
        if (data.error) throw new Error(data.error);
        allData = data;
        render();
    } catch (e) { app.innerHTML = '<div class="error">' + esc(e.message) + '</div>'; }
}

function render() {
    let data = [...allData];

    const q = ($('#s') || {}).value || '';
    const pubF = ($('#fp') || {}).value || 'all';
    const typeF = ($('#ft') || {}).value || 'all';
    const qualF = ($('#fq') || {}).value || 'hide-low';

    if (q) { const ql = q.toLowerCase(); data = data.filter(p => p.placement_name.toLowerCase().includes(ql) || p.publisher_name.toLowerCase().includes(ql) || p.context.toLowerCase().includes(ql)); }
    if (pubF !== 'all') data = data.filter(p => p.publisher_id === pubF);
    if (typeF !== 'all') data = data.filter(p => p.ad_type === typeF);
    if (qualF === 'hide-low') data = data.filter(p => p.quality !== 'low');
    else if (qualF !== 'all') data = data.filter(p => p.quality === qualF);

    data.sort((a, b) => {
        let va = a[sortState.col], vb = b[sortState.col];
        if (typeof va === 'string') { va = va.toLowerCase(); vb = (vb||'').toLowerCase(); }
        if (va < vb) return sortState.asc ? -1 : 1;
        if (va > vb) return sortState.asc ? 1 : -1;
        return 0;
    });

    const pubs = [...new Map(allData.map(p => [p.publisher_id, p.publisher_name])).entries()].sort((a,b) => a[1].localeCompare(b[1]));
    const types = [...new Set(allData.map(p => p.ad_type))].sort();
    const high = data.filter(p => p.quality === 'high').length;
    const med = data.filter(p => p.quality === 'medium').length;
    const low = data.filter(p => p.quality === 'low').length;
    const avgFill = data.length ? Math.round(data.reduce((s, p) => s + p.fill_rate, 0) / data.length) : 0;

    const si = col => sortState.col === col ? (sortState.asc ? ' &#9650;' : ' &#9660;') : '';

    let html = `
        <div class="filters">
            <input type="text" id="s" placeholder="Buscar placement, publisher ou contexto..." value="${esc(q)}" oninput="render()" />
            <select id="fp" onchange="render()">
                <option value="all">Todos publishers</option>
                ${pubs.map(([id, nm]) => '<option value="' + esc(id) + '"' + (id === pubF ? ' selected' : '') + '>' + esc(nm) + '</option>').join('')}
            </select>
            <select id="ft" onchange="render()">
                <option value="all">Todos tipos</option>
                ${types.map(t => '<option value="' + esc(t) + '"' + (t === typeF ? ' selected' : '') + '>' + esc(t) + '</option>').join('')}
            </select>
            <select id="fq" onchange="render()">
                <option value="hide-low"${qualF==='hide-low'?' selected':''}>Sem baixa qualidade</option>
                <option value="all"${qualF==='all'?' selected':''}>Todos</option>
                <option value="high"${qualF==='high'?' selected':''}>Somente alta</option>
                <option value="medium"${qualF==='medium'?' selected':''}>Somente media</option>
                <option value="low"${qualF==='low'?' selected':''}>Somente baixa</option>
            </select>
        </div>
        <div class="stats">
            <div class="stat"><strong>${fmt(data.length)}</strong> placements</div>
            <div class="stat" style="color:var(--green)"><strong>${fmt(high)}</strong> alta</div>
            <div class="stat" style="color:var(--yellow)"><strong>${fmt(med)}</strong> media</div>
            <div class="stat" style="color:var(--red)"><strong>${fmt(low)}</strong> baixa</div>
            <div class="stat"><strong>${avgFill}%</strong> fill rate medio</div>
        </div>
        <div class="table-wrap"><table><thead><tr>
            <th onclick="doSort('publisher_name')">Publisher${si('publisher_name')}</th>
            <th onclick="doSort('placement_name')">Placement${si('placement_name')}</th>
            <th onclick="doSort('context')">Contexto${si('context')}</th>
            <th onclick="doSort('ad_type')">Tipo${si('ad_type')}</th>
            <th style="text-align:right" onclick="doSort('total_requests')">Requests${si('total_requests')}</th>
            <th style="text-align:right" onclick="doSort('total_impressions')">Impressoes${si('total_impressions')}</th>
            <th style="text-align:right" onclick="doSort('total_clicks')">Cliques${si('total_clicks')}</th>
            <th style="text-align:right" onclick="doSort('fill_rate')">Fill Rate${si('fill_rate')}</th>
            <th onclick="doSort('quality')">Qualidade${si('quality')}</th>
        </tr></thead><tbody>`;

    for (const p of data) {
        const qc = p.quality === 'high' ? 'q-high' : p.quality === 'medium' ? 'q-med' : 'q-low';
        const ql = p.quality === 'high' ? 'Alta' : p.quality === 'medium' ? 'Media' : 'Baixa';
        const fl = p.fill_rate >= 50 ? 'high' : p.fill_rate >= 20 ? 'med' : 'low';
        html += `<tr>
            <td class="name">${esc(p.publisher_name)}</td>
            <td>${esc(p.placement_name)}</td>
            <td>${esc(p.context)}</td>
            <td><span class="badge ${adTypeBadge(p.ad_type)}">${esc(p.ad_type)}</span></td>
            <td class="num">${fmt(p.total_requests)}</td>
            <td class="num">${fmt(p.total_impressions)}</td>
            <td class="num">${fmt(p.total_clicks)}</td>
            <td class="num"><div class="fill-bar"><div class="fill-track"><div class="fill-val ${fl}" style="width:${Math.min(p.fill_rate,100)}%"></div></div>${pct(p.fill_rate)}</div></td>
            <td><span class="badge ${qc}">${ql}</span></td></tr>`;
    }

    html += '</tbody></table></div>';
    app.innerHTML = html;
}

function doSort(col) {
    if (sortState.col === col) sortState.asc = !sortState.asc;
    else { sortState.col = col; sortState.asc = col === 'publisher_name' || col === 'placement_name' || col === 'context'; }
    render();
}

init();
</script>
</body>
</html>"""
