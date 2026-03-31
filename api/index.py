from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode("utf-8"))


HTML = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>VTEX Ads Network Explorer</title>
<style>
:root {
    --bg: #0a0a0f;
    --surface: #13131a;
    --surface2: #1a1a24;
    --border: #2a2a3a;
    --text: #e4e4ed;
    --text2: #8888a0;
    --accent: #7c3aed;
    --accent2: #2563eb;
    --green: #22c55e;
    --yellow: #eab308;
    --red: #ef4444;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
.container { max-width: 1200px; margin: 0 auto; padding: 1.5rem; }
header { margin-bottom: 1.5rem; }
h1 { font-size: 1.6rem; background: linear-gradient(135deg, var(--accent), var(--accent2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.subtitle { color: var(--text2); font-size: 0.9rem; margin-top: 0.3rem; }

/* Search */
.search-bar { margin-bottom: 1rem; }
.search-bar input {
    width: 100%; padding: 0.7rem 1rem; border: 1px solid var(--border); border-radius: 8px;
    background: var(--surface); color: var(--text); font-size: 0.95rem; outline: none;
}
.search-bar input:focus { border-color: var(--accent); }
.search-bar input::placeholder { color: var(--text2); }

/* Stats bar */
.stats { display: flex; gap: 1.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
.stat { font-size: 0.85rem; color: var(--text2); }
.stat strong { color: var(--text); }

/* Table */
.table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
thead th { background: var(--surface2); color: var(--text2); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; padding: 0.7rem 1rem; text-align: left; border-bottom: 1px solid var(--border); white-space: nowrap; }
tbody tr { cursor: pointer; transition: background 0.15s; border-bottom: 1px solid var(--border); }
tbody tr:last-child { border-bottom: none; }
tbody tr:hover { background: var(--surface2); }
td { padding: 0.6rem 1rem; white-space: nowrap; }
td.name { font-weight: 500; color: var(--text); max-width: 300px; overflow: hidden; text-overflow: ellipsis; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.badge.active { background: rgba(34,197,94,0.15); color: var(--green); }
.badge.inactive { background: rgba(239,68,68,0.15); color: var(--red); }

/* Detail view */
.detail-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.back-btn { background: var(--surface2); border: 1px solid var(--border); color: var(--text); padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }
.back-btn:hover { background: var(--border); }
.detail-header h2 { font-size: 1.3rem; }
.detail-meta { display: flex; gap: 1rem; flex-wrap: wrap; font-size: 0.8rem; color: var(--text2); }
.detail-meta span { background: var(--surface2); padding: 3px 10px; border-radius: 4px; }

/* Ad type sections */
.ad-type-section { margin-bottom: 1.5rem; }
.ad-type-header { display: flex; align-items: center; justify-content: space-between; padding: 0.7rem 1rem; background: var(--surface2); border: 1px solid var(--border); border-radius: 8px 8px 0 0; cursor: pointer; }
.ad-type-header h3 { font-size: 0.95rem; font-weight: 600; }
.ad-type-header .count { font-size: 0.8rem; color: var(--text2); }
.ad-type-header .arrow { transition: transform 0.2s; color: var(--text2); }
.ad-type-header.collapsed .arrow { transform: rotate(-90deg); }
.ad-type-body { border: 1px solid var(--border); border-top: none; border-radius: 0 0 8px 8px; overflow: hidden; }
.ad-type-body.hidden { display: none; }

/* Context group */
.context-label { padding: 0.4rem 1rem; background: rgba(124,58,237,0.08); color: var(--accent); font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }

/* Loading / Error */
.loading { text-align: center; padding: 3rem; color: var(--text2); }
.error { text-align: center; padding: 2rem; color: var(--red); }

@media (max-width: 768px) {
    .container { padding: 1rem; }
    td, th { padding: 0.5rem 0.6rem; font-size: 0.8rem; }
}
</style>
</head>
<body>
<div class="container">
    <header>
        <h1>VTEX Ads Network Explorer</h1>
        <p class="subtitle">Publishers, formatos e placements disponiveis</p>
    </header>
    <div id="app"></div>
</div>

<script>
const $ = s => document.querySelector(s);
const app = $('#app');

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s || '';
    return d.innerHTML;
}

function fmt(n) {
    if (n == null) return '0';
    return Number(n).toLocaleString('pt-BR');
}

function pct(n) {
    if (n == null) return '0%';
    return Number(n).toFixed(1) + '%';
}

// Router
function route() {
    const params = new URLSearchParams(location.search);
    const pubId = params.get('publisher');
    if (pubId) {
        renderDetail(pubId);
    } else {
        renderList();
    }
}

// Publishers list
async function renderList() {
    app.innerHTML = '<div class="loading">Carregando publishers...</div>';

    try {
        const resp = await fetch('/api/publishers');
        if (!resp.ok) throw new Error('Erro ao carregar publishers');
        const data = await resp.json();
        if (data.error) throw new Error(data.error);

        const withTraffic = data.filter(p => p.total_requests_30d > 0);
        const totalPlacements = data.reduce((s, p) => s + p.placement_count, 0);

        let html = `
            <div class="search-bar">
                <input type="text" id="search" placeholder="Buscar publisher..." oninput="filterTable()" />
            </div>
            <div class="stats">
                <div class="stat"><strong>${data.length}</strong> publishers</div>
                <div class="stat"><strong>${withTraffic.length}</strong> com trafego (30d)</div>
                <div class="stat"><strong>${fmt(totalPlacements)}</strong> placements</div>
            </div>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Publisher</th>
                            <th style="text-align:right">Placements</th>
                            <th style="text-align:right">Ad Types</th>
                            <th style="text-align:right">Requests (30d)</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody id="tbody">`;

        for (const p of data) {
            const badge = p.active
                ? '<span class="badge active">Ativo</span>'
                : '<span class="badge inactive">Inativo</span>';
            html += `
                <tr data-id="${esc(p.publisher_id)}" data-name="${esc((p.name||'').toLowerCase())}">
                    <td class="name">${esc(p.name || p.publisher_id)}</td>
                    <td class="num">${fmt(p.placement_count)}</td>
                    <td class="num">${p.ad_type_count}</td>
                    <td class="num">${fmt(p.total_requests_30d)}</td>
                    <td>${badge}</td>
                </tr>`;
        }

        html += '</tbody></table></div>';
        app.innerHTML = html;

        $('#tbody').addEventListener('click', function(e) {
            const tr = e.target.closest('tr');
            if (tr && tr.dataset.id) navigate(tr.dataset.id);
        });
    } catch (e) {
        app.innerHTML = '<div class="error">' + e.message + '</div>';
    }
}

function filterTable() {
    const q = $('#search').value.toLowerCase();
    document.querySelectorAll('#tbody tr').forEach(tr => {
        tr.style.display = tr.dataset.name.includes(q) ? '' : 'none';
    });
}

function navigate(pubId) {
    history.pushState(null, '', '/?publisher=' + pubId);
    renderDetail(pubId);
}

function goBack() {
    history.pushState(null, '', '/');
    renderList();
}

// Publisher detail
async function renderDetail(pubId) {
    app.innerHTML = '<div class="loading">Carregando placements...</div>';

    try {
        const resp = await fetch('/api/publisher-detail?id=' + encodeURIComponent(pubId));
        if (!resp.ok) throw new Error('Erro ao carregar publisher');
        const data = await resp.json();
        if (data.error) throw new Error(data.error);

        // Group by ad_type then context
        const groups = {};
        for (const p of data.placements) {
            if (!groups[p.ad_type]) groups[p.ad_type] = {};
            if (!groups[p.ad_type][p.context]) groups[p.ad_type][p.context] = [];
            groups[p.ad_type][p.context].push(p);
        }

        const adTypes = Object.keys(groups).sort();
        const totalPlacements = data.placements.length;

        let html = `
            <div class="detail-header">
                <button class="back-btn" onclick="goBack()">← Voltar</button>
                <div>
                    <h2>${esc(data.name)}</h2>
                    <div class="detail-meta">
                        <span>${totalPlacements} placements</span>
                        <span>${adTypes.length} ad types</span>
                        <span>${data.active ? 'Ativo' : 'Inativo'}</span>
                        ${data.allow_offsite ? '<span>Offsite habilitado</span>' : ''}
                        ${data.min_cpc ? '<span>CPC min: ' + data.currency_code + ' ' + data.min_cpc.toFixed(2) + '</span>' : ''}
                        ${data.min_cpm ? '<span>CPM min: ' + data.currency_code + ' ' + data.min_cpm.toFixed(2) + '</span>' : ''}
                    </div>
                </div>
            </div>`;

        for (const adType of adTypes) {
            const contexts = Object.keys(groups[adType]).sort();
            const count = Object.values(groups[adType]).reduce((s, arr) => s + arr.length, 0);

            html += `
            <div class="ad-type-section">
                <div class="ad-type-header" onclick="toggleSection(this)">
                    <h3>${esc(adType)}</h3>
                    <div>
                        <span class="count">${count} placements</span>
                        <span class="arrow"> ▼</span>
                    </div>
                </div>
                <div class="ad-type-body">`;

            for (const ctx of contexts) {
                const placements = groups[adType][ctx];
                html += `<div class="context-label">${esc(ctx)}</div>`;
                html += `<table><thead><tr>
                    <th>Placement</th>
                    <th style="text-align:right">Requests</th>
                    <th style="text-align:right">Impressoes</th>
                    <th style="text-align:right">Cliques</th>
                    <th style="text-align:right">Fill Rate</th>
                </tr></thead><tbody>`;

                for (const p of placements) {
                    html += `<tr>
                        <td>${esc(p.placement_name)}</td>
                        <td class="num">${fmt(p.total_requests)}</td>
                        <td class="num">${fmt(p.total_impressions)}</td>
                        <td class="num">${fmt(p.total_clicks)}</td>
                        <td class="num">${pct(p.fill_rate)}</td>
                    </tr>`;
                }
                html += '</tbody></table>';
            }

            html += '</div></div>';
        }

        app.innerHTML = html;
    } catch (e) {
        app.innerHTML = `<div class="detail-header"><button class="back-btn" onclick="goBack()">← Voltar</button></div><div class="error">${e.message}</div>`;
    }
}

function toggleSection(el) {
    el.classList.toggle('collapsed');
    el.nextElementSibling.classList.toggle('hidden');
}

// Handle browser back/forward
window.addEventListener('popstate', route);
route();
</script>
</body>
</html>"""
