import os
import sys
import json
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.config import Config

S = "vtex_ads_snowflake_silver_iceberg"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            config = Config.from_env()
            mb = config.build_metabase_client()

            rows = mb.query(f"""
                SELECT
                    p.publisher_id,
                    p.name,
                    p.active,
                    COUNT(DISTINCT eq.placement_name) AS placement_count,
                    COUNT(DISTINCT eq.ad_type) AS ad_type_count,
                    SUM(eq.total_requests) AS total_requests_30d
                FROM {S}.publishers p
                LEFT JOIN {S}.mv_event_queries_placements eq
                    ON p.publisher_id = eq.publisher_id
                    AND eq.day >= CURRENT_DATE - 30
                WHERE p.deleted_at IS NULL
                GROUP BY p.publisher_id, p.name, p.active
                ORDER BY total_requests_30d DESC NULLS LAST
            """)

            publishers = []
            for r in rows:
                publishers.append({
                    "publisher_id": r["publisher_id"],
                    "name": r["name"] or r["publisher_id"],
                    "active": bool(r["active"]),
                    "placement_count": int(r["placement_count"] or 0),
                    "ad_type_count": int(r["ad_type_count"] or 0),
                    "total_requests_30d": int(r["total_requests_30d"] or 0),
                })

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(publishers, ensure_ascii=False).encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
