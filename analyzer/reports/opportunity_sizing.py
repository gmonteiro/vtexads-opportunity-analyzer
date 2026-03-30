from analyzer.clients.metabase import MetabaseClient
from analyzer.models import OpportunitySizingReport, OpportunityProjection

S = MetabaseClient.SCHEMA

# Ad types we project opportunity for (relative to 'product' spend)
TARGET_AD_TYPES = ("banner", "banner_off_site", "sponsored_brand")


def _get_advertiser_product_spend(mb: MetabaseClient, advertiser_name: str, days: int) -> list[dict]:
    safe = mb.sanitize(advertiser_name)
    return mb.query(f"""
        SELECT
            am.publisher_id,
            p.name AS publisher_name,
            ROUND(SUM(am.total_clicks_cost + am.total_impressions_cost)::numeric, 2) AS product_spend,
            SUM(am.total_impressions) AS impressions,
            SUM(am.total_clicks) AS clicks,
            SUM(am.total_conversions) AS conversions,
            ROUND(SUM(am.total_conversions_value)::numeric, 2) AS revenue
        FROM {S}.ads_metrics am
        JOIN {S}.campaigns c ON am.campaign_id = c.campaign_id
        JOIN {S}.advertisers a ON c.advertiser_id = a.advertiser_id
        JOIN {S}.publishers p ON am.publisher_id = p.publisher_id
        WHERE (a.name = '{safe}' OR a.advertiser_id = '{safe}')
          AND c.ad_type = 'product'
          AND am.day >= CURRENT_DATE - {days}
        GROUP BY am.publisher_id, p.name
        HAVING SUM(am.total_clicks_cost + am.total_impressions_cost) > 0
    """)


def _get_benchmark_ratios(mb: MetabaseClient, publisher_ids: list[str], days: int) -> list[dict]:
    """Get median ratio of each target ad_type spend relative to product spend, per publisher."""
    ids = ", ".join(f"'{mb.sanitize(pid)}'" for pid in publisher_ids)
    ad_types_sql = ", ".join(f"'{t}'" for t in TARGET_AD_TYPES)

    return mb.query(f"""
        WITH advertiser_spend AS (
            SELECT
                c.advertiser_id,
                am.publisher_id,
                c.ad_type,
                SUM(am.total_clicks_cost + am.total_impressions_cost) AS spend
            FROM {S}.ads_metrics am
            JOIN {S}.campaigns c ON am.campaign_id = c.campaign_id
            WHERE am.day >= CURRENT_DATE - {days}
              AND am.publisher_id IN ({ids})
            GROUP BY c.advertiser_id, am.publisher_id, c.ad_type
        ),
        pivoted AS (
            SELECT
                advertiser_id,
                publisher_id,
                SUM(CASE WHEN ad_type = 'product' THEN spend ELSE 0 END) AS product_spend,
                SUM(CASE WHEN ad_type IN ({ad_types_sql}) THEN spend ELSE 0 END) AS other_spend,
                ad_type AS target_ad_type,
                spend AS target_spend
            FROM advertiser_spend
            WHERE ad_type = 'product' OR ad_type IN ({ad_types_sql})
            GROUP BY advertiser_id, publisher_id, ad_type, spend
        ),
        ratios AS (
            SELECT
                p.publisher_id,
                p.target_ad_type,
                p.target_spend / NULLIF(prod.product_spend, 0) AS ratio
            FROM (
                SELECT advertiser_id, publisher_id, target_ad_type, target_spend
                FROM pivoted
                WHERE target_ad_type IN ({ad_types_sql})
            ) p
            JOIN (
                SELECT advertiser_id, publisher_id, SUM(CASE WHEN target_ad_type = 'product' THEN target_spend ELSE 0 END) AS product_spend
                FROM pivoted
                GROUP BY advertiser_id, publisher_id
            ) prod ON p.advertiser_id = prod.advertiser_id AND p.publisher_id = prod.publisher_id
            WHERE prod.product_spend > 0
        )
        SELECT
            publisher_id,
            target_ad_type AS ad_type,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ratio) AS median_ratio,
            COUNT(*) AS sample_size,
            AVG(ratio) AS avg_ratio
        FROM ratios
        GROUP BY publisher_id, target_ad_type
    """)


def _get_performance_benchmarks(mb: MetabaseClient, publisher_ids: list[str], days: int) -> list[dict]:
    """Get avg CTR, CVR, CPC, CPM per publisher per ad_type."""
    ids = ", ".join(f"'{mb.sanitize(pid)}'" for pid in publisher_ids)
    ad_types_sql = ", ".join(f"'{t}'" for t in TARGET_AD_TYPES)

    return mb.query(f"""
        SELECT
            am.publisher_id,
            c.ad_type,
            SUM(am.total_clicks)::float / NULLIF(SUM(am.total_impressions), 0) AS avg_ctr,
            SUM(am.total_conversions)::float / NULLIF(SUM(am.total_clicks), 0) AS avg_cvr,
            SUM(am.total_clicks_cost + am.total_impressions_cost)::float / NULLIF(SUM(am.total_clicks), 0) AS avg_cpc,
            (SUM(am.total_clicks_cost + am.total_impressions_cost)::float / NULLIF(SUM(am.total_impressions), 0)) * 1000 AS avg_cpm,
            SUM(am.total_conversions_value)::float / NULLIF(SUM(am.total_conversions), 0) AS avg_order_value,
            CASE WHEN SUM(am.total_clicks_cost + am.total_impressions_cost) > 0
                THEN SUM(am.total_conversions_value)::float / SUM(am.total_clicks_cost + am.total_impressions_cost)
                ELSE 0 END AS avg_roas
        FROM {S}.ads_metrics am
        JOIN {S}.campaigns c ON am.campaign_id = c.campaign_id
        WHERE am.publisher_id IN ({ids})
          AND c.ad_type IN ({ad_types_sql})
          AND am.day >= CURRENT_DATE - {days}
        GROUP BY am.publisher_id, c.ad_type
    """)


def generate(advertiser_name: str, mb: MetabaseClient, days: int = 30) -> OpportunitySizingReport:
    # 1. Advertiser's product spend per publisher
    product_spend_rows = _get_advertiser_product_spend(mb, advertiser_name, days)
    if not product_spend_rows:
        return OpportunitySizingReport(advertiser_name=advertiser_name, days=days)

    pub_id_to_name = {r["publisher_id"]: r["publisher_name"] for r in product_spend_rows}
    pub_product_spend = {r["publisher_id"]: float(r["product_spend"]) for r in product_spend_rows}
    publisher_ids = list(pub_id_to_name.keys())

    # 2. Benchmark ratios
    ratio_rows = _get_benchmark_ratios(mb, publisher_ids, days)
    # key: (publisher_id, ad_type) -> {median_ratio, sample_size}
    ratios = {}
    for r in ratio_rows:
        ratios[(r["publisher_id"], r["ad_type"])] = {
            "median_ratio": float(r["median_ratio"] or 0),
            "sample_size": int(r["sample_size"] or 0),
        }

    # 3. Performance benchmarks
    perf_rows = _get_performance_benchmarks(mb, publisher_ids, days)
    # key: (publisher_id, ad_type) -> metrics
    perf = {}
    for r in perf_rows:
        perf[(r["publisher_id"], r["ad_type"])] = {
            "avg_ctr": float(r["avg_ctr"] or 0),
            "avg_cvr": float(r["avg_cvr"] or 0),
            "avg_cpm": float(r["avg_cpm"] or 0),
            "avg_roas": float(r["avg_roas"] or 0),
        }

    # 4. Build projections
    projections = []
    for pub_id in publisher_ids:
        product_sp = pub_product_spend[pub_id]
        pub_name = pub_id_to_name[pub_id]

        for ad_type in TARGET_AD_TYPES:
            ratio_info = ratios.get((pub_id, ad_type))
            perf_info = perf.get((pub_id, ad_type))

            if not ratio_info or ratio_info["median_ratio"] <= 0:
                continue

            projected_spend = product_sp * ratio_info["median_ratio"]

            if perf_info and perf_info["avg_cpm"] > 0:
                est_impressions = int(projected_spend / perf_info["avg_cpm"] * 1000)
                est_clicks = int(est_impressions * perf_info["avg_ctr"])
                est_conversions = round(est_clicks * perf_info["avg_cvr"], 1)
                est_roas = perf_info["avg_roas"]
            else:
                est_impressions = 0
                est_clicks = 0
                est_conversions = 0
                est_roas = 0

            projections.append(OpportunityProjection(
                publisher_name=pub_name,
                ad_type=ad_type,
                current_product_spend=product_sp,
                benchmark_ratio=ratio_info["median_ratio"],
                sample_size=ratio_info["sample_size"],
                projected_spend=round(projected_spend, 2),
                estimated_impressions=est_impressions,
                estimated_clicks=est_clicks,
                estimated_conversions=est_conversions,
                estimated_roas=round(est_roas, 2),
            ))

    return OpportunitySizingReport(
        advertiser_name=advertiser_name,
        days=days,
        projections=projections,
    )
