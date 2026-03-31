import os
import sys
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.config import Config
from analyzer.clients.metabase import MetabaseClient

S = MetabaseClient.SCHEMA


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            publisher_id = qs.get("id", [None])[0]

            if not publisher_id:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "id parameter required"}).encode())
                return

            config = Config.from_env()
            mb = config.build_metabase_client()
            safe_id = mb.sanitize(publisher_id)

            # Get publisher info
            pub_rows = mb.query(f"""
                SELECT publisher_id, name, active, allow_offsite, currency_code, min_cpc, min_cpm
                FROM {S}.publishers
                WHERE publisher_id = '{safe_id}'
            """)

            if not pub_rows:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "publisher not found"}).encode())
                return

            pub = pub_rows[0]

            # Get placements
            placements = mb.query(f"""
                SELECT
                    placement_name,
                    ad_type,
                    context,
                    SUM(total_requests) AS total_requests,
                    SUM(request_with_ads) AS filled_requests,
                    SUM(total_impressions) AS total_impressions,
                    SUM(total_clicks) AS total_clicks,
                    ROUND(SUM(request_with_ads)::float / NULLIF(SUM(total_requests), 0) * 100, 2) AS fill_rate
                FROM {S}.mv_event_queries_placements
                WHERE publisher_id = '{safe_id}'
                  AND day >= CURRENT_DATE - 30
                GROUP BY placement_name, ad_type, context
                ORDER BY ad_type, context, total_requests DESC
            """)

            result = {
                "publisher_id": pub["publisher_id"],
                "name": pub["name"],
                "active": bool(pub["active"]),
                "allow_offsite": bool(pub.get("allow_offsite")),
                "currency_code": pub.get("currency_code", "BRL"),
                "min_cpc": float(pub["min_cpc"] or 0),
                "min_cpm": float(pub["min_cpm"] or 0),
                "placements": [
                    {
                        "placement_name": p["placement_name"] or "(sem nome)",
                        "ad_type": p["ad_type"] or "(sem tipo)",
                        "context": p["context"] or "(sem contexto)",
                        "total_requests": int(p["total_requests"] or 0),
                        "filled_requests": int(p["filled_requests"] or 0),
                        "total_impressions": int(p["total_impressions"] or 0),
                        "total_clicks": int(p["total_clicks"] or 0),
                        "fill_rate": float(p["fill_rate"] or 0),
                    }
                    for p in placements
                ],
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(result, ensure_ascii=False).encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
