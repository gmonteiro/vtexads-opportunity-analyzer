import os
import sys
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.config import Config
from analyzer.clients.metabase import MetabaseClient

S = MetabaseClient.SCHEMA
NETWORK_ID = "398d7097-d673-4f6e-882a-80397c154789"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            campaign_id = qs.get("id", [None])[0]

            if not campaign_id:
                self._json(400, {"error": "id parameter required"})
                return

            config = Config.from_env()
            mb = config.build_metabase_client()
            safe_id = mb.sanitize(campaign_id)

            # 1. Campaign info
            camp_rows = mb.query(f"""
                SELECT c.campaign_id, c.name, c.ad_type, c.status, c.is_active, c.daily_budget,
                       a.name AS advertiser
                FROM {S}.campaigns c
                JOIN {S}.advertisers a ON c.advertiser_id = a.advertiser_id
                WHERE c.campaign_id = '{safe_id}'
            """)
            if not camp_rows:
                self._json(404, {"error": "campaign not found"})
                return

            camp = camp_rows[0]

            # 2. Placements used by this campaign (via event_impressions + ads)
            used_rows = mb.query(f"""
                SELECT
                    ei.placement_name,
                    ei.context,
                    ei.ad_type,
                    COUNT(*) AS impressions
                FROM {S}.event_impressions ei
                JOIN {S}.ads a ON ei.ad_id = a.ad_id
                WHERE a.campaign_id = '{safe_id}'
                  AND ei.day >= CURRENT_DATE - 30
                  AND ei.valid = true
                GROUP BY ei.placement_name, ei.context, ei.ad_type
                ORDER BY impressions DESC
            """)

            used_set = set()
            used_placements = []
            for r in used_rows:
                key = (r["placement_name"], r["context"], r["ad_type"])
                used_set.add(key)
                used_placements.append({
                    "placement_name": r["placement_name"] or "",
                    "context": r["context"] or "",
                    "ad_type": r["ad_type"] or "",
                    "impressions": int(r["impressions"] or 0),
                    "status": "active",
                })

            # 3. All available placements on the network (same ad_type as campaign)
            campaign_ad_type = camp["ad_type"] or ""
            available_rows = mb.query(f"""
                SELECT
                    placement_name,
                    context,
                    ad_type,
                    SUM(total_requests) AS total_requests,
                    SUM(total_impressions) AS total_impressions
                FROM {S}.mv_event_queries_placements
                WHERE publisher_id = '{NETWORK_ID}'
                  AND day >= CURRENT_DATE - 30
                  AND UPPER(ad_type) = UPPER('{mb.sanitize(campaign_ad_type)}')
                GROUP BY placement_name, context, ad_type
                HAVING SUM(total_requests) > 0
                ORDER BY total_requests DESC
            """)

            # If no network-level placements found, also check across all publishers
            # that the campaign actually delivered to (placements vary by publisher)
            if not available_rows:
                available_rows = mb.query(f"""
                    SELECT
                        placement_name,
                        context,
                        ad_type,
                        SUM(total_requests) AS total_requests,
                        SUM(total_impressions) AS total_impressions
                    FROM {S}.mv_event_queries_placements
                    WHERE day >= CURRENT_DATE - 30
                      AND UPPER(ad_type) = UPPER('{mb.sanitize(campaign_ad_type)}')
                    GROUP BY placement_name, context, ad_type
                    HAVING SUM(total_requests) > 100
                    ORDER BY total_requests DESC
                """)

            gap_placements = []
            for r in available_rows:
                key = (r["placement_name"], r["context"], r["ad_type"])
                if key not in used_set:
                    gap_placements.append({
                        "placement_name": r["placement_name"] or "",
                        "context": r["context"] or "",
                        "ad_type": r["ad_type"] or "",
                        "total_requests": int(r["total_requests"] or 0),
                        "total_impressions": int(r["total_impressions"] or 0),
                        "status": "gap",
                    })

            result = {
                "campaign_id": camp["campaign_id"],
                "name": camp["name"],
                "advertiser": camp["advertiser"],
                "ad_type": campaign_ad_type,
                "status": camp["status"],
                "is_active": bool(camp["is_active"]),
                "daily_budget": float(camp["daily_budget"] or 0),
                "used_placements": used_placements,
                "gap_placements": gap_placements,
            }

            self._json(200, result)

        except Exception as e:
            self._json(500, {"error": str(e)})

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode("utf-8"))
