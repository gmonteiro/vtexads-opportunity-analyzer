from analyzer.clients.metabase import MetabaseClient
from analyzer.models import PublisherGapReport, PublisherStatus

S = MetabaseClient.SCHEMA


def _get_all_publishers(mb: MetabaseClient) -> list[dict]:
    return mb.query(f"""
        SELECT publisher_id, name
        FROM {S}.publishers
        WHERE deleted_at IS NULL
    """)


def _get_advertiser_publisher_ids(mb: MetabaseClient, advertiser_name: str) -> set[str]:
    safe = mb.sanitize(advertiser_name)
    rows = mb.query(f"""
        SELECT DISTINCT ap.publisher_id
        FROM {S}.advertisers_publishers ap
        JOIN {S}.advertisers a ON ap.advertiser_id = a.advertiser_id
        WHERE (a.name = '{safe}' OR a.advertiser_id = '{safe}')
          AND ap.deleted_at IS NULL
    """)
    return {r["publisher_id"] for r in rows}


def _get_network_spend_by_publisher(mb: MetabaseClient, days: int) -> dict[str, dict]:
    rows = mb.query(f"""
        SELECT
            am.publisher_id,
            ROUND(SUM(am.total_clicks_cost + am.total_impressions_cost)::numeric, 2) AS total_spend,
            COUNT(DISTINCT c.advertiser_id) AS advertiser_count
        FROM {S}.ads_metrics am
        JOIN {S}.campaigns c ON am.campaign_id = c.campaign_id
        WHERE am.day >= CURRENT_DATE - {days}
        GROUP BY am.publisher_id
    """)
    return {
        r["publisher_id"]: {
            "total_spend": float(r["total_spend"] or 0),
            "advertiser_count": int(r["advertiser_count"] or 0),
        }
        for r in rows
    }


def generate(advertiser_name: str, mb: MetabaseClient, days: int = 30) -> PublisherGapReport:
    all_pubs = _get_all_publishers(mb)
    adv_pub_ids = _get_advertiser_publisher_ids(mb, advertiser_name)
    network_spend = _get_network_spend_by_publisher(mb, days)

    publishers = []
    for pub in all_pubs:
        pid = pub["publisher_id"]
        spend_info = network_spend.get(pid, {"total_spend": 0, "advertiser_count": 0})
        publishers.append(PublisherStatus(
            publisher_id=pid,
            publisher_name=pub["name"] or pid,
            advertiser_active=pid in adv_pub_ids,
            network_spend_30d=spend_info["total_spend"],
            advertiser_count=spend_info["advertiser_count"],
        ))

    return PublisherGapReport(
        advertiser_name=advertiser_name,
        days=days,
        publishers=publishers,
    )
