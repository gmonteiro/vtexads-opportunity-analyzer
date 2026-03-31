import os
import sys
import json
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.config import Config
from analyzer.clients.metabase import MetabaseClient

S = MetabaseClient.SCHEMA
NETWORK_ID = "398d7097-d673-4f6e-882a-80397c154789"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            config = Config.from_env()
            mb = config.build_metabase_client()

            rows = mb.query(f"""
                SELECT
                    a.name AS advertiser,
                    c.campaign_id,
                    c.name AS campaign,
                    c.ad_type,
                    c.status,
                    c.is_active,
                    c.daily_budget,
                    c.start_at,
                    c.end_at
                FROM {S}.campaigns c
                JOIN {S}.advertisers a ON c.advertiser_id = a.advertiser_id
                WHERE c.publisher_id = '{NETWORK_ID}'
                  AND c.deleted_at IS NULL
                ORDER BY a.name, c.name
            """)

            campaigns = []
            for r in rows:
                campaigns.append({
                    "advertiser": r["advertiser"] or "",
                    "campaign_id": r["campaign_id"],
                    "campaign": r["campaign"] or "",
                    "ad_type": r["ad_type"] or "",
                    "status": r["status"] or "",
                    "is_active": bool(r["is_active"]),
                    "daily_budget": float(r["daily_budget"] or 0),
                    "start_at": r["start_at"] or "",
                    "end_at": r["end_at"] or "",
                })

            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(campaigns, ensure_ascii=False, default=str).encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
