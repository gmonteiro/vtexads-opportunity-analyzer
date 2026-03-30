from analyzer.clients.metabase import MetabaseClient
from analyzer.models import PlacementGapReport, PlacementStatus

S = MetabaseClient.SCHEMA


def _get_advertiser_publishers(mb: MetabaseClient, advertiser_name: str) -> list[dict]:
    safe = mb.sanitize(advertiser_name)
    return mb.query(f"""
        SELECT DISTINCT ap.publisher_id, p.name AS publisher_name
        FROM {S}.advertisers_publishers ap
        JOIN {S}.publishers p ON ap.publisher_id = p.publisher_id
        JOIN {S}.advertisers a ON ap.advertiser_id = a.advertiser_id
        WHERE (a.name = '{safe}' OR a.advertiser_id = '{safe}')
          AND ap.deleted_at IS NULL
    """)


def _get_available_placements(mb: MetabaseClient, publisher_ids: list[str], days: int) -> list[dict]:
    ids = ", ".join(f"'{mb.sanitize(pid)}'" for pid in publisher_ids)
    return mb.query(f"""
        SELECT
            publisher_id,
            placement_name,
            context,
            ad_type,
            SUM(total_requests) AS total_requests
        FROM {S}.mv_event_queries_placements
        WHERE publisher_id IN ({ids})
          AND day >= CURRENT_DATE - {days}
        GROUP BY publisher_id, placement_name, context, ad_type
        HAVING SUM(total_requests) > 0
        ORDER BY publisher_id, total_requests DESC
    """)


def _get_advertiser_placements(mb: MetabaseClient, advertiser_name: str, publisher_ids: list[str], days: int) -> set[tuple]:
    safe = mb.sanitize(advertiser_name)
    ids = ", ".join(f"'{mb.sanitize(pid)}'" for pid in publisher_ids)
    rows = mb.query(f"""
        SELECT DISTINCT
            mc.publisher_id,
            mc.placement_name,
            mc.context
        FROM {S}.mv_metrics_context mc
        JOIN {S}.advertisers a ON mc.advertiser_id = a.advertiser_id
        WHERE (a.name = '{safe}' OR a.advertiser_id = '{safe}')
          AND mc.publisher_id IN ({ids})
          AND mc.day >= CURRENT_DATE - {days}
          AND mc.total_impressions > 0
    """)
    return {(r["publisher_id"], r["placement_name"], r["context"]) for r in rows}


def generate(advertiser_name: str, mb: MetabaseClient, days: int = 30) -> PlacementGapReport:
    # 1. Get advertiser's publishers
    adv_pubs = _get_advertiser_publishers(mb, advertiser_name)
    if not adv_pubs:
        return PlacementGapReport(advertiser_name=advertiser_name, days=days)

    pub_id_to_name = {r["publisher_id"]: r["publisher_name"] for r in adv_pubs}
    publisher_ids = list(pub_id_to_name.keys())

    # 2. Get all available placements on those publishers
    available = _get_available_placements(mb, publisher_ids, days)

    # 3. Get placements where advertiser delivered
    used = _get_advertiser_placements(mb, advertiser_name, publisher_ids, days)

    # 4. Build report
    placements = []
    for row in available:
        key = (row["publisher_id"], row["placement_name"], row["context"])
        placements.append(PlacementStatus(
            publisher_name=pub_id_to_name.get(row["publisher_id"], row["publisher_id"]),
            placement_name=row["placement_name"] or "(sem nome)",
            context=row["context"] or "(sem contexto)",
            ad_type=row["ad_type"] or "(sem tipo)",
            total_requests=int(row["total_requests"] or 0),
            in_use=key in used,
        ))

    return PlacementGapReport(
        advertiser_name=advertiser_name,
        days=days,
        placements=placements,
    )
