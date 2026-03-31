import os
import sys
import json
from http.server import BaseHTTPRequestHandler

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.config import Config
from analyzer.clients.metabase import MetabaseClient
from analyzer.reports import placement_gap, publisher_gap, opportunity_sizing
from analyzer.formatter import format_placement_gap, format_publisher_gap, format_opportunity_sizing

REPORTS = {
    "placement-gap": (placement_gap.generate, format_placement_gap),
    "publisher-gap": (publisher_gap.generate, format_publisher_gap),
    "opportunity-sizing": (opportunity_sizing.generate, format_opportunity_sizing),
}


def _run_report(advertiser: str, report_name: str, days: int, metabase_session: str) -> str:
    config = Config.from_env()
    if metabase_session:
        config.metabase_session = metabase_session

    if not config.has_metabase():
        return "ERRO: METABASE_SESSION nao configurado"

    mb = MetabaseClient(
        session_token=config.metabase_session,
        base_url=config.metabase_base_url,
        db_id=config.metabase_db_id,
    )

    if report_name == "all":
        keys = list(REPORTS.keys())
    else:
        keys = [report_name]

    parts = []
    for key in keys:
        gen_fn, fmt_fn = REPORTS[key]
        report = gen_fn(advertiser, mb, days=days)
        parts.append(fmt_fn(report))

    return "\n---\n\n".join(parts)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML_PAGE.encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        params = json.loads(body)

        advertiser = params.get("advertiser", "")
        report_name = params.get("report", "all")
        days = int(params.get("days", 30))
        metabase_session = params.get("metabase_session", "")

        if not advertiser:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "advertiser obrigatorio"}).encode())
            return

        try:
            result = _run_report(advertiser, report_name, days, metabase_session)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"result": result}).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())


HTML_PAGE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>VTEX Ads Opportunity Analyzer</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #0f1117; color: #e1e1e6; min-height: 100vh; }
        .container { max-width: 900px; margin: 0 auto; padding: 2rem; }
        h1 { font-size: 1.8rem; margin-bottom: 0.5rem; background: linear-gradient(135deg, #7c3aed, #2563eb); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .subtitle { color: #888; margin-bottom: 2rem; }
        .form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }
        .form-group { display: flex; flex-direction: column; gap: 0.4rem; }
        .form-group.full { grid-column: 1 / -1; }
        label { font-size: 0.85rem; color: #a1a1aa; font-weight: 500; }
        input, select { padding: 0.6rem 0.8rem; border: 1px solid #27272a; border-radius: 8px; background: #18181b; color: #e1e1e6; font-size: 0.95rem; }
        input:focus, select:focus { outline: none; border-color: #7c3aed; }
        button { padding: 0.7rem 1.5rem; border: none; border-radius: 8px; background: linear-gradient(135deg, #7c3aed, #2563eb); color: white; font-size: 1rem; font-weight: 600; cursor: pointer; margin-top: 0.5rem; }
        button:hover { opacity: 0.9; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .result { margin-top: 2rem; padding: 1.5rem; border-radius: 12px; background: #18181b; border: 1px solid #27272a; white-space: pre-wrap; font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 0.85rem; line-height: 1.6; max-height: 70vh; overflow-y: auto; }
        .spinner { display: none; margin-top: 1rem; color: #7c3aed; }
        .spinner.active { display: block; }
        table { border-collapse: collapse; width: 100%; margin: 0.5rem 0; }
        th, td { border: 1px solid #333; padding: 4px 8px; text-align: left; font-size: 0.8rem; }
        th { background: #27272a; }
    </style>
</head>
<body>
    <div class="container">
        <h1>VTEX Ads Opportunity Analyzer</h1>
        <p class="subtitle">Placement gaps, publisher gaps e opportunity sizing</p>

        <div class="form-grid">
            <div class="form-group">
                <label>Advertiser</label>
                <input type="text" id="advertiser" placeholder="Ex: LOREALDCAVTEXADS" />
            </div>
            <div class="form-group">
                <label>Relatorio</label>
                <select id="report">
                    <option value="all">Todos</option>
                    <option value="placement-gap">Placement Gap</option>
                    <option value="publisher-gap">Publisher Gap</option>
                    <option value="opportunity-sizing">Opportunity Sizing</option>
                </select>
            </div>
            <div class="form-group">
                <label>Dias (lookback)</label>
                <input type="number" id="days" value="30" min="1" max="90" />
            </div>
            <div class="form-group">
                <label>Metabase Session Token</label>
                <input type="password" id="metabase_session" placeholder="Token de sessao" />
            </div>
        </div>

        <button id="btn" onclick="runAnalysis()">Gerar Relatorio</button>
        <p class="spinner" id="spinner">Gerando relatorio... (pode levar alguns minutos)</p>
        <div class="result" id="result" style="display:none;"></div>
    </div>

    <script>
        async function runAnalysis() {
            const btn = document.getElementById('btn');
            const spinner = document.getElementById('spinner');
            const resultDiv = document.getElementById('result');
            const advertiser = document.getElementById('advertiser').value.trim();
            const report = document.getElementById('report').value;
            const days = document.getElementById('days').value;
            const metabase_session = document.getElementById('metabase_session').value.trim();

            if (!advertiser) { alert('Preencha o advertiser'); return; }
            if (!metabase_session) { alert('Preencha o Metabase Session Token'); return; }

            btn.disabled = true;
            spinner.classList.add('active');
            resultDiv.style.display = 'none';

            try {
                const resp = await fetch('/api', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ advertiser, report, days: parseInt(days), metabase_session })
                });
                const data = await resp.json();
                resultDiv.style.display = 'block';
                resultDiv.textContent = data.result || data.error || 'Erro desconhecido';
            } catch (e) {
                resultDiv.style.display = 'block';
                resultDiv.textContent = 'Erro: ' + e.message;
            } finally {
                btn.disabled = false;
                spinner.classList.remove('active');
            }
        }
    </script>
</body>
</html>
"""
