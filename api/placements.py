import os
import sys
import json
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.config import Config
from analyzer.clients.metabase import MetabaseClient

S = MetabaseClient.SCHEMA


def _quality(requests: int, fill_rate: float) -> str:
    if requests > 100_000 and fill_rate > 50:
        return "high"
    if requests > 10_000 and fill_rate > 20:
        return "medium"
    return "low"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            config = Config.from_env()
            mb = config.build_metabase_client()

            rows = mb.query(f"""
                SELECT
                    p.name AS publisher_name,
                    eq.publisher_id,
                    eq.placement_name,
                    eq.context,
                    eq.ad_type,
                    SUM(eq.total_requests) AS total_requests,
                    SUM(eq.request_with_ads) AS filled_requests,
                    SUM(eq.total_impressions) AS total_impressions,
                    SUM(eq.total_clicks) AS total_clicks,
                    ROUND(SUM(eq.request_with_ads)::float / NULLIF(SUM(eq.total_requests), 0) * 100, 2) AS fill_rate
                FROM {S}.mv_event_queries_placements eq
                JOIN {S}.publishers p ON eq.publisher_id = p.publisher_id
                WHERE eq.day >= CURRENT_DATE - 30
                  AND eq.total_requests > 0
                GROUP BY p.name, eq.publisher_id, eq.placement_name, eq.context, eq.ad_type
                ORDER BY total_requests DESC
            """)

            placements = []
            for r in rows:
                reqs = int(r["total_requests"] or 0)
                fr = float(r["fill_rate"] or 0)
                placements.append({
                    "publisher_name": r["publisher_name"] or "",
                    "publisher_id": r["publisher_id"] or "",
                    "placement_name": r["placement_name"] or "",
                    "context": r["context"] or "",
                    "ad_type": r["ad_type"] or "",
                    "total_requests": reqs,
                    "filled_requests": int(r["filled_requests"] or 0),
                    "total_impressions": int(r["total_impressions"] or 0),
                    "total_clicks": int(r["total_clicks"] or 0),
                    "fill_rate": fr,
                    "quality": _quality(reqs, fr),
                })

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(placements, ensure_ascii=False).encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
