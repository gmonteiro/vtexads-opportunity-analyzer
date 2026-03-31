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

            # 1. Active campaigns with ad count
            campaigns = mb.query(f"""
                SELECT c.campaign_id, c.name, c.ad_type, c.status, c.daily_budget,
                       a.name AS advertiser,
                       COUNT(DISTINCT ad.ad_id) AS ad_count
                FROM {S}.campaigns c
                JOIN {S}.advertisers a ON c.advertiser_id = a.advertiser_id
                LEFT JOIN {S}.ads ad ON ad.campaign_id = c.campaign_id AND ad.deleted_at IS NULL
                WHERE c.publisher_id = '{NETWORK_ID}'
                  AND c.deleted_at IS NULL
                  AND c.is_active = true
                GROUP BY c.campaign_id, c.name, c.ad_type, c.status, c.daily_budget, a.name
                ORDER BY ad_count DESC
            """)

            if not campaigns:
                self._json(200, [])
                return

            # 2. Batch: placements used per campaign (last 30d)
            ids_sql = ", ".join(f"'{mb.sanitize(c['campaign_id'])}'" for c in campaigns)
            used_rows = mb.query(f"""
                SELECT a.campaign_id,
                       COUNT(DISTINCT ei.placement_name || '|' || ei.context) AS used_placements
                FROM {S}.event_impressions ei
                JOIN {S}.ads a ON ei.ad_id = a.ad_id
                WHERE a.campaign_id IN ({ids_sql})
                  AND ei.day >= CURRENT_DATE - 30
                  AND ei.valid = true
                GROUP BY a.campaign_id
            """)
            used_map = {r["campaign_id"]: int(r["used_placements"] or 0) for r in used_rows}

            # 3. Available placements per ad_type on network
            avail_rows = mb.query(f"""
                SELECT UPPER(ad_type) AS ad_type,
                       COUNT(DISTINCT placement_name || '|' || context) AS available_placements
                FROM {S}.mv_event_queries_placements
                WHERE publisher_id = '{NETWORK_ID}'
                  AND day >= CURRENT_DATE - 30
                  AND total_requests > 0
                GROUP BY UPPER(ad_type)
            """)
            avail_map = {r["ad_type"]: int(r["available_placements"] or 0) for r in avail_rows}

            # 4. Merge
            result = []
            for c in campaigns:
                used = used_map.get(c["campaign_id"], 0)
                ad_type_upper = (c["ad_type"] or "").upper()
                available = avail_map.get(ad_type_upper, 0)
                coverage = round(used / available * 100, 1) if available > 0 else 0

                result.append({
                    "campaign_id": c["campaign_id"],
                    "name": c["name"] or "",
                    "advertiser": c["advertiser"] or "",
                    "ad_type": c["ad_type"] or "",
                    "status": c["status"] or "",
                    "daily_budget": float(c["daily_budget"] or 0),
                    "ad_count": int(c["ad_count"] or 0),
                    "used_placements": used,
                    "available_placements": available,
                    "coverage_pct": coverage,
                })

            self._json(200, result)

        except Exception as e:
            self._json(500, {"error": str(e)})

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode("utf-8"))
