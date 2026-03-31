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
<title>VTEX Ads Network Explorer</title>
<style>
:root {
    --bg: #0a0a0f; --surface: #13131a; --surface2: #1a1a24; --border: #2a2a3a;
    --text: #e4e4ed; --text2: #8888a0; --accent: #7c3aed; --accent2: #2563eb;
    --green: #22c55e; --yellow: #eab308; --red: #ef4444; --orange: #f97316; --blue: #3b82f6;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }
.container { max-width: 1200px; margin: 0 auto; padding: 1.5rem; }
header { margin-bottom: 0.5rem; }
h1 { font-size: 1.6rem; background: linear-gradient(135deg, var(--accent), var(--accent2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.subtitle { color: var(--text2); font-size: 0.9rem; margin-top: 0.3rem; }

/* Tabs */
.tabs { display: flex; gap: 0; margin: 1rem 0; border-bottom: 1px solid var(--border); }
.tab { padding: 0.6rem 1.2rem; cursor: pointer; color: var(--text2); font-size: 0.9rem; font-weight: 500; border-bottom: 2px solid transparent; transition: all 0.15s; }
.tab:hover { color: var(--text); }
.tab.active { color: var(--accent); border-bottom-color: var(--accent); }

/* Search */
.search-bar { margin-bottom: 1rem; }
.search-bar input {
    width: 100%; padding: 0.7rem 1rem; border: 1px solid var(--border); border-radius: 8px;
    background: var(--surface); color: var(--text); font-size: 0.95rem; outline: none;
}
.search-bar input:focus { border-color: var(--accent); }
.search-bar input::placeholder { color: var(--text2); }

/* Stats */
.stats { display: flex; gap: 1.5rem; margin-bottom: 1rem; flex-wrap: wrap; }
.stat { font-size: 0.85rem; color: var(--text2); }
.stat strong { color: var(--text); }

/* Table */
.table-wrap { overflow-x: auto; border: 1px solid var(--border); border-radius: 10px; background: var(--surface); }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
thead th { background: var(--surface2); color: var(--text2); font-weight: 600; text-transform: uppercase; font-size: 0.75rem; letter-spacing: 0.5px; padding: 0.7rem 1rem; text-align: left; border-bottom: 1px solid var(--border); white-space: nowrap; cursor: pointer; }
thead th:hover { color: var(--text); }
tbody tr { transition: background 0.15s; border-bottom: 1px solid var(--border); }
tbody tr:last-child { border-bottom: none; }
tbody tr.clickable { cursor: pointer; }
tbody tr.clickable:hover { background: var(--surface2); }
td { padding: 0.6rem 1rem; white-space: nowrap; }
td.name { font-weight: 500; color: var(--text); max-width: 300px; overflow: hidden; text-overflow: ellipsis; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
td.wrap { white-space: normal; max-width: 350px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.badge.active { background: rgba(34,197,94,0.15); color: var(--green); }
.badge.inactive { background: rgba(239,68,68,0.15); color: var(--red); }
.badge.paused { background: rgba(234,179,8,0.15); color: var(--yellow); }
.badge.finished { background: rgba(136,136,160,0.15); color: var(--text2); }
.badge.oob { background: rgba(249,115,22,0.15); color: var(--orange); }
.badge.product { background: rgba(59,130,246,0.1); color: var(--blue); }
.badge.banner { background: rgba(124,58,237,0.1); color: var(--accent); }
.badge.sbrand { background: rgba(34,197,94,0.1); color: var(--green); }

/* Detail view */
.detail-header { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.back-btn { background: var(--surface2); border: 1px solid var(--border); color: var(--text); padding: 0.5rem 1rem; border-radius: 6px; cursor: pointer; font-size: 0.85rem; }
.back-btn:hover { background: var(--border); }
.detail-header h2 { font-size: 1.3rem; }
.detail-meta { display: flex; gap: 1rem; flex-wrap: wrap; font-size: 0.8rem; color: var(--text2); }
.detail-meta span { background: var(--surface2); padding: 3px 10px; border-radius: 4px; }

/* Sections */
.ad-type-section { margin-bottom: 1.5rem; }
.ad-type-header { display: flex; align-items: center; justify-content: space-between; padding: 0.7rem 1rem; background: var(--surface2); border: 1px solid var(--border); border-radius: 8px 8px 0 0; cursor: pointer; }
.ad-type-header h3 { font-size: 0.95rem; font-weight: 600; }
.ad-type-header .count { font-size: 0.8rem; color: var(--text2); }
.ad-type-header .arrow { transition: transform 0.2s; color: var(--text2); }
.ad-type-header.collapsed .arrow { transform: rotate(-90deg); }
.ad-type-body { border: 1px solid var(--border); border-top: none; border-radius: 0 0 8px 8px; overflow: hidden; }
.ad-type-body.hidden { display: none; }
.context-label { padding: 0.4rem 1rem; background: rgba(124,58,237,0.08); color: var(--accent); font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }

/* Loading / Error */
.loading { text-align: center; padding: 3rem; color: var(--text2); }
.error { text-align: center; padding: 2rem; color: var(--red); }

@media (max-width: 768px) {
    .container { padding: 1rem; }
    td, th { padding: 0.5rem 0.6rem; font-size: 0.8rem; }
    .tabs { overflow-x: auto; }
}
</style>
</head>
<body>
<div class="container">
    <header>
        <h1>VTEX Ads Network Explorer</h1>
        <p class="subtitle">Publishers, formatos, placements e campanhas</p>
    </header>
    <div class="tabs" id="tabs">
        <div class="tab active" data-tab="publishers">Publishers</div>
        <div class="tab" data-tab="campaigns">Campanhas Network</div>
    </div>
    <div id="app"></div>
</div>

<script>
const $ = s => document.querySelector(s);
const app = $('#app');
let currentTab = 'publishers';

function esc(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
}
function fmt(n) { return n == null ? '0' : Number(n).toLocaleString('pt-BR'); }
function pct(n) { return n == null ? '0%' : Number(n).toFixed(1) + '%'; }
function fmtBRL(n) { return 'R$ ' + fmt(n); }

// Tabs
$('#tabs').addEventListener('click', e => {
    const tab = e.target.closest('.tab');
    if (!tab) return;
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    currentTab = tab.dataset.tab;
    if (currentTab === 'publishers') {
        history.pushState(null, '', '/');
        route();
    } else if (currentTab === 'campaigns') {
        history.pushState(null, '', '/?tab=campaigns');
        renderCampaigns();
    }
});

// Router
function route() {
    const params = new URLSearchParams(location.search);
    const pubId = params.get('publisher');
    const tab = params.get('tab');
    const campId = params.get('campaign');
    if (tab === 'campaigns' && campId) {
        setActiveTab('campaigns');
        renderCampaignDetail(campId);
    } else if (tab === 'campaigns') {
        setActiveTab('campaigns');
        renderCampaigns();
    } else if (pubId) {
        setActiveTab('publishers');
        renderDetail(pubId);
    } else {
        setActiveTab('publishers');
        renderList();
    }
}

function setActiveTab(name) {
    currentTab = name;
    document.querySelectorAll('.tab').forEach(t => {
        t.classList.toggle('active', t.dataset.tab === name);
    });
}

// ==================== PUBLISHERS TAB ====================
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
            <div class="search-bar"><input type="text" id="search" placeholder="Buscar publisher..." oninput="filterRows('search','pub-tbody')" /></div>
            <div class="stats">
                <div class="stat"><strong>${data.length}</strong> publishers</div>
                <div class="stat"><strong>${withTraffic.length}</strong> com trafego (30d)</div>
                <div class="stat"><strong>${fmt(totalPlacements)}</strong> placements</div>
            </div>
            <div class="table-wrap"><table><thead><tr>
                <th>Publisher</th>
                <th style="text-align:right">Placements</th>
                <th style="text-align:right">Ad Types</th>
                <th style="text-align:right">Requests (30d)</th>
                <th>Status</th>
            </tr></thead><tbody id="pub-tbody">`;

        for (const p of data) {
            const badge = p.active ? '<span class="badge active">Ativo</span>' : '<span class="badge inactive">Inativo</span>';
            html += `<tr class="clickable" data-id="${esc(p.publisher_id)}" data-name="${esc((p.name||'').toLowerCase())}">
                <td class="name">${esc(p.name || p.publisher_id)}</td>
                <td class="num">${fmt(p.placement_count)}</td>
                <td class="num">${p.ad_type_count}</td>
                <td class="num">${fmt(p.total_requests_30d)}</td>
                <td>${badge}</td></tr>`;
        }
        html += '</tbody></table></div>';
        app.innerHTML = html;

        $('#pub-tbody').addEventListener('click', e => {
            const tr = e.target.closest('tr');
            if (tr && tr.dataset.id) navigate(tr.dataset.id);
        });
    } catch (e) { app.innerHTML = '<div class="error">' + esc(e.message) + '</div>'; }
}

function filterRows(inputId, tbodyId) {
    const q = $('#' + inputId).value.toLowerCase();
    document.querySelectorAll('#' + tbodyId + ' tr').forEach(tr => {
        const name = tr.dataset.name || tr.textContent.toLowerCase();
        tr.style.display = name.includes(q) ? '' : 'none';
    });
}

function navigate(pubId) {
    history.pushState(null, '', '/?publisher=' + encodeURIComponent(pubId));
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

        const groups = {};
        for (const p of data.placements) {
            if (!groups[p.ad_type]) groups[p.ad_type] = {};
            if (!groups[p.ad_type][p.context]) groups[p.ad_type][p.context] = [];
            groups[p.ad_type][p.context].push(p);
        }
        const adTypes = Object.keys(groups).sort();

        let html = `<div class="detail-header"><button class="back-btn" onclick="goBack()">&#8592; Voltar</button><div>
            <h2>${esc(data.name)}</h2>
            <div class="detail-meta">
                <span>${data.placements.length} placements</span><span>${adTypes.length} ad types</span>
                <span>${data.active ? 'Ativo' : 'Inativo'}</span>
                ${data.allow_offsite ? '<span>Offsite habilitado</span>' : ''}
                ${data.min_cpc ? '<span>CPC min: ' + esc(data.currency_code) + ' ' + data.min_cpc.toFixed(2) + '</span>' : ''}
                ${data.min_cpm ? '<span>CPM min: ' + esc(data.currency_code) + ' ' + data.min_cpm.toFixed(2) + '</span>' : ''}
            </div></div></div>`;

        for (const adType of adTypes) {
            const contexts = Object.keys(groups[adType]).sort();
            const count = Object.values(groups[adType]).reduce((s, a) => s + a.length, 0);
            html += `<div class="ad-type-section"><div class="ad-type-header" onclick="toggleSection(this)">
                <h3>${esc(adType)}</h3><div><span class="count">${count} placements</span><span class="arrow"> &#9660;</span></div>
                </div><div class="ad-type-body">`;
            for (const ctx of contexts) {
                html += `<div class="context-label">${esc(ctx)}</div>`;
                html += `<table><thead><tr><th>Placement</th><th style="text-align:right">Requests</th><th style="text-align:right">Impressoes</th><th style="text-align:right">Cliques</th><th style="text-align:right">Fill Rate</th></tr></thead><tbody>`;
                for (const p of groups[adType][ctx]) {
                    html += `<tr><td>${esc(p.placement_name)}</td><td class="num">${fmt(p.total_requests)}</td><td class="num">${fmt(p.total_impressions)}</td><td class="num">${fmt(p.total_clicks)}</td><td class="num">${pct(p.fill_rate)}</td></tr>`;
                }
                html += '</tbody></table>';
            }
            html += '</div></div>';
        }
        app.innerHTML = html;
    } catch (e) {
        app.innerHTML = `<div class="detail-header"><button class="back-btn" onclick="goBack()">&#8592; Voltar</button></div><div class="error">${esc(e.message)}</div>`;
    }
}

function toggleSection(el) {
    el.classList.toggle('collapsed');
    el.nextElementSibling.classList.toggle('hidden');
}

// ==================== CAMPAIGNS TAB ====================
async function renderCampaigns() {
    app.innerHTML = '<div class="loading">Carregando campanhas da network...</div>';
    try {
        const resp = await fetch('/api/campaigns');
        if (!resp.ok) throw new Error('Erro ao carregar campanhas');
        const data = await resp.json();
        if (data.error) throw new Error(data.error);

        // Group by advertiser
        const byAdv = {};
        for (const c of data) {
            if (!byAdv[c.advertiser]) byAdv[c.advertiser] = [];
            byAdv[c.advertiser].push(c);
        }

        const advertisers = Object.keys(byAdv).sort();
        const activeCount = data.filter(c => c.is_active).length;

        let html = `
            <div class="search-bar"><input type="text" id="camp-search" placeholder="Buscar advertiser ou campanha..." oninput="filterCampaigns()" /></div>
            <div class="stats">
                <div class="stat"><strong>${advertisers.length}</strong> advertisers</div>
                <div class="stat"><strong>${data.length}</strong> campanhas</div>
                <div class="stat"><strong>${activeCount}</strong> ativas</div>
            </div>`;

        for (const adv of advertisers) {
            const camps = byAdv[adv];
            const active = camps.filter(c => c.is_active).length;
            const types = [...new Set(camps.map(c => c.ad_type))];

            html += `<div class="ad-type-section advertiser-section" data-advname="${esc(adv.toLowerCase())}">
                <div class="ad-type-header" onclick="toggleSection(this)">
                    <h3>${esc(adv)}</h3>
                    <div>
                        <span class="count">${active} ativas / ${camps.length} total &nbsp; ${types.map(t => '<span class="badge ' + adTypeBadge(t) + '">' + esc(t) + '</span>').join(' ')}</span>
                        <span class="arrow"> &#9660;</span>
                    </div>
                </div>
                <div class="ad-type-body hidden">
                    <table><thead><tr>
                        <th>Campanha</th><th>Tipo</th><th style="text-align:right">Budget/dia</th><th>Status</th>
                    </tr></thead><tbody>`;

            for (const c of camps) {
                html += `<tr class="clickable" data-campid="${esc(c.campaign_id)}" data-name="${esc(c.campaign.toLowerCase())}">
                    <td class="wrap">${esc(c.campaign)}</td>
                    <td><span class="badge ${adTypeBadge(c.ad_type)}">${esc(c.ad_type)}</span></td>
                    <td class="num">${c.daily_budget ? fmtBRL(c.daily_budget) : '-'}</td>
                    <td>${statusBadge(c.status, c.is_active)}</td></tr>`;
            }
            html += '</tbody></table></div></div>';
        }

        app.innerHTML = html;

        // Campaign click delegation
        app.addEventListener('click', e => {
            const tr = e.target.closest('tr.clickable[data-campid]');
            if (tr) {
                history.pushState(null, '', '/?tab=campaigns&campaign=' + encodeURIComponent(tr.dataset.campid));
                renderCampaignDetail(tr.dataset.campid);
            }
        });
    } catch (e) { app.innerHTML = '<div class="error">' + esc(e.message) + '</div>'; }
}

function filterCampaigns() {
    const q = $('#camp-search').value.toLowerCase();
    document.querySelectorAll('.advertiser-section').forEach(sec => {
        const advMatch = sec.dataset.advname.includes(q);
        const rows = sec.querySelectorAll('tbody tr');
        let anyRow = false;
        rows.forEach(tr => {
            const match = advMatch || (tr.dataset.name && tr.dataset.name.includes(q));
            tr.style.display = match ? '' : 'none';
            if (match) anyRow = true;
        });
        sec.style.display = (advMatch || anyRow) ? '' : 'none';
        // Auto-expand if searching
        if (q && (advMatch || anyRow)) {
            sec.querySelector('.ad-type-header').classList.remove('collapsed');
            sec.querySelector('.ad-type-body').classList.remove('hidden');
        }
    });
}

// ==================== CAMPAIGN DETAIL ====================
function goBackCampaigns() {
    history.pushState(null, '', '/?tab=campaigns');
    renderCampaigns();
}

async function renderCampaignDetail(campId) {
    app.innerHTML = '<div class="loading">Analisando placements da campanha... (pode levar alguns segundos)</div>';
    try {
        const resp = await fetch('/api/campaign-detail?id=' + encodeURIComponent(campId));
        if (!resp.ok) throw new Error('Erro ao carregar campanha');
        const data = await resp.json();
        if (data.error) throw new Error(data.error);

        const usedCount = data.used_placements.length;
        const gapCount = data.gap_placements.length;

        let html = `<div class="detail-header"><button class="back-btn" onclick="goBackCampaigns()">&#8592; Voltar</button><div>
            <h2>${esc(data.name)}</h2>
            <div class="detail-meta">
                <span>${esc(data.advertiser)}</span>
                <span class="badge ${adTypeBadge(data.ad_type)}">${esc(data.ad_type)}</span>
                <span>${statusBadge(data.status, data.is_active)}</span>
                ${data.daily_budget ? '<span>Budget: ' + fmtBRL(data.daily_budget) + '/dia</span>' : ''}
            </div></div></div>`;

        html += `<div class="stats">
            <div class="stat"><strong>${usedCount}</strong> placements ativos</div>
            <div class="stat" style="color:var(--yellow)"><strong>${gapCount}</strong> placements disponiveis nao utilizados</div>
        </div>`;

        // Used placements grouped by context
        if (usedCount > 0) {
            const usedByCtx = {};
            for (const p of data.used_placements) {
                if (!usedByCtx[p.context]) usedByCtx[p.context] = [];
                usedByCtx[p.context].push(p);
            }
            html += `<div class="ad-type-section"><div class="ad-type-header" style="border-color:var(--green)" onclick="toggleSection(this)">
                <h3 style="color:var(--green)">Placements Ativos</h3>
                <div><span class="count">${usedCount} placements</span><span class="arrow"> &#9660;</span></div>
            </div><div class="ad-type-body">`;
            for (const ctx of Object.keys(usedByCtx).sort()) {
                html += `<div class="context-label">${esc(ctx)}</div>`;
                html += `<table><thead><tr><th>Placement</th><th style="text-align:right">Impressoes (30d)</th></tr></thead><tbody>`;
                for (const p of usedByCtx[ctx]) {
                    html += `<tr><td>${esc(p.placement_name)}</td><td class="num">${fmt(p.impressions)}</td></tr>`;
                }
                html += '</tbody></table>';
            }
            html += '</div></div>';
        }

        // Gap placements grouped by context
        if (gapCount > 0) {
            const gapByCtx = {};
            for (const p of data.gap_placements) {
                if (!gapByCtx[p.context]) gapByCtx[p.context] = [];
                gapByCtx[p.context].push(p);
            }
            html += `<div class="ad-type-section"><div class="ad-type-header" style="border-color:var(--yellow)" onclick="toggleSection(this)">
                <h3 style="color:var(--yellow)">Placements Disponiveis (Gap)</h3>
                <div><span class="count">${gapCount} oportunidades</span><span class="arrow"> &#9660;</span></div>
            </div><div class="ad-type-body">`;
            for (const ctx of Object.keys(gapByCtx).sort()) {
                html += `<div class="context-label">${esc(ctx)}</div>`;
                html += `<table><thead><tr><th>Placement</th><th style="text-align:right">Requests na rede (30d)</th><th style="text-align:right">Impressoes na rede (30d)</th></tr></thead><tbody>`;
                for (const p of gapByCtx[ctx]) {
                    html += `<tr><td>${esc(p.placement_name)}</td><td class="num">${fmt(p.total_requests)}</td><td class="num">${fmt(p.total_impressions)}</td></tr>`;
                }
                html += '</tbody></table>';
            }
            html += '</div></div>';
        }

        app.innerHTML = html;
    } catch (e) {
        app.innerHTML = `<div class="detail-header"><button class="back-btn" onclick="goBackCampaigns()">&#8592; Voltar</button></div><div class="error">${esc(e.message)}</div>`;
    }
}

function statusBadge(status, isActive) {
    if (isActive && (status === 'active' || status === 'running' || status === 'updating'))
        return '<span class="badge active">Ativa</span>';
    if (isActive && status === 'out_of_budget')
        return '<span class="badge oob">Sem budget</span>';
    if (status === 'paused')
        return '<span class="badge paused">Pausada</span>';
    if (status === 'finished')
        return '<span class="badge finished">Finalizada</span>';
    return '<span class="badge inactive">' + esc(status) + '</span>';
}

function adTypeBadge(t) {
    if (t === 'product') return 'product';
    if (t === 'banner' || t === 'banner_off_site' || t === 'banner_video') return 'banner';
    if (t === 'sponsored_brand' || t === 'sponsored_brand_video') return 'sbrand';
    return '';
}

// Handle browser back/forward
window.addEventListener('popstate', route);
route();
</script>
</body>
</html>"""
