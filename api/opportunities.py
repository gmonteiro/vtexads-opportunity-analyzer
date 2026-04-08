import os
import sys
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.config import Config
from analyzer.clients.metabase import MetabaseClient


def build_query(currency_code: str, advertiser_id: str | None = None) -> str:
    safe_currency = MetabaseClient.sanitize(currency_code)
    adv_filter = ""
    if advertiser_id:
        safe_adv = MetabaseClient.sanitize(advertiser_id)
        adv_filter = f"AND cmd.advertiser_id = '{safe_adv}'"

    return f"""
WITH params AS (
  SELECT
    current_date AS today,
    (date_trunc('month', current_date) + interval '1 month - 1 day')::date AS month_end,
    ((date_trunc('month', current_date) + interval '1 month - 1 day')::date - current_date + 1)::int AS days_to_month_end
),
placement_benchmark AS (
  SELECT
    cmd.publisher_id,
    c.ad_type::text AS ad_type,
    c.targeting_type::text AS targeting_type,
    ads.settings ->> 'ad_size' AS ad_size_name,
    (ad_sizes.width || 'x' || ad_sizes.height) AS ad_size,
    SUM(COALESCE(cmd.total_clicks_cost,0) + COALESCE(cmd.total_impressions_cost,0))::float AS spend_30d,
    SUM(COALESCE(cmd.total_impressions,0))::float / NULLIF(SUM(COALESCE(cmd.total_clicks_cost,0) + COALESCE(cmd.total_impressions_cost,0)),0) AS imps_per_cost,
    SUM(COALESCE(cmd.total_conversions,0))::float / NULLIF(SUM(COALESCE(cmd.total_clicks_cost,0) + COALESCE(cmd.total_impressions_cost,0)),0) AS conv_per_cost,
    SUM(COALESCE(cmd.total_conversions_value,0))::float / NULLIF(SUM(COALESCE(cmd.total_clicks_cost,0) + COALESCE(cmd.total_impressions_cost,0)),0) AS gmv_per_cost,
    SUM(COALESCE(cmd.total_clicks_cost,0) + COALESCE(cmd.total_impressions_cost,0))::float / 30.0 AS placement_spend_daily_universe
  FROM campaigns_metrics_network_day cmd
  JOIN campaigns c ON c.id = cmd.campaign_id
  LEFT JOIN ads ON ads.id = cmd.ad_id AND ads.campaign_id = cmd.campaign_id
  LEFT JOIN ad_sizes ON ad_sizes.publisher_id = cmd.publisher_id AND UPPER(ad_sizes.name) = UPPER(ads.settings ->> 'ad_size')
  WHERE cmd.day::date >= current_date - interval '30 days' AND cmd.day::date < current_date
    AND cmd.currency_code = '{safe_currency}'
  GROUP BY cmd.publisher_id, c.ad_type::text, c.targeting_type::text, ads.settings ->> 'ad_size', (ad_sizes.width || 'x' || ad_sizes.height)
),
publisher_capacity_universe AS (
  SELECT publisher_id, SUM(placement_spend_daily_universe) AS publisher_spend_daily_universe
  FROM placement_benchmark GROUP BY publisher_id
),
placement_share_in_publisher AS (
  SELECT pb.publisher_id, pb.ad_type, pb.targeting_type, pb.ad_size_name, pb.ad_size,
    pb.placement_spend_daily_universe, pb.imps_per_cost, pb.conv_per_cost, pb.gmv_per_cost,
    pb.placement_spend_daily_universe / NULLIF(SUM(pb.placement_spend_daily_universe) OVER (PARTITION BY pb.publisher_id),0) AS share_in_publisher
  FROM placement_benchmark pb
),
publisher_benchmark_eff AS (
  SELECT pb.publisher_id,
    SUM(pb.placement_spend_daily_universe * pb.imps_per_cost) / NULLIF(SUM(pb.placement_spend_daily_universe),0) AS imps_per_cost,
    SUM(pb.placement_spend_daily_universe * pb.conv_per_cost) / NULLIF(SUM(pb.placement_spend_daily_universe),0) AS conv_per_cost,
    SUM(pb.placement_spend_daily_universe * pb.gmv_per_cost) / NULLIF(SUM(pb.placement_spend_daily_universe),0) AS gmv_per_cost
  FROM placement_benchmark pb GROUP BY pb.publisher_id
),
adv_base_30d AS (
  SELECT cmd.publisher_id, cmd.advertiser_id, cmd.campaign_id,
    c.ad_type::text AS ad_type, c.targeting_type::text AS targeting_type,
    ads.settings ->> 'ad_size' AS ad_size_name, (ad_sizes.width || 'x' || ad_sizes.height) AS ad_size,
    SUM(COALESCE(cmd.total_impressions,0))::float AS imps_30d,
    SUM(COALESCE(cmd.total_conversions,0))::float AS conv_30d,
    SUM(COALESCE(cmd.total_conversions_value,0))::float AS gmv_30d,
    SUM(COALESCE(cmd.total_clicks_cost,0) + COALESCE(cmd.total_impressions_cost,0))::float AS spend_30d
  FROM campaigns_metrics_network_day cmd
  JOIN campaigns c ON c.id = cmd.campaign_id
  LEFT JOIN ads ON ads.id = cmd.ad_id AND ads.campaign_id = cmd.campaign_id
  LEFT JOIN ad_sizes ON ad_sizes.publisher_id = cmd.publisher_id AND UPPER(ad_sizes.name) = UPPER(ads.settings ->> 'ad_size')
  WHERE cmd.day::date >= current_date - interval '30 days' AND cmd.day::date < current_date
    AND cmd.currency_code = '{safe_currency}'
    {adv_filter}
  GROUP BY cmd.publisher_id, cmd.advertiser_id, cmd.campaign_id, c.ad_type::text, c.targeting_type::text, ads.settings ->> 'ad_size', (ad_sizes.width || 'x' || ad_sizes.height)
),
adv_daily_placement AS (
  SELECT publisher_id, advertiser_id, campaign_id, ad_type, targeting_type, ad_size_name, ad_size,
    spend_30d / 30.0 AS spend_daily,
    imps_30d / NULLIF(spend_30d,0) AS imps_per_cost,
    conv_30d / NULLIF(spend_30d,0) AS conv_per_cost,
    gmv_30d / NULLIF(spend_30d,0) AS gmv_per_cost
  FROM adv_base_30d
),
perf_by_campaign_hour AS (
  SELECT am.campaign_id, EXTRACT(HOUR FROM am.date_hour) AS hod,
    SUM(COALESCE(am.total_cost::float, 0)) AS cost_7d
  FROM ads_metrics am
  WHERE am.date_hour::date >= current_date - interval '7 days' AND am.date_hour::date < current_date
    AND COALESCE(am.total_cost::float, 0) > 0
  GROUP BY am.campaign_id, EXTRACT(HOUR FROM am.date_hour)
),
avg_perf_hour AS (
  SELECT campaign_id, hod, cost_7d / 7.0 AS avg_cost_per_day_at_hod FROM perf_by_campaign_hour
),
budget_log_intervals AS (
  SELECT cl.campaign_id,
    GREATEST(cl.created_at, current_timestamp - interval '24 hours') AS start_ts,
    COALESCE(LEAD(cl.created_at) OVER (PARTITION BY cl.campaign_id ORDER BY cl.created_at), current_timestamp) AS end_ts
  FROM campaign_budget_log cl
  WHERE cl.updated_at >= current_timestamp - interval '24 hours' AND cl.status = 'out_of_budget_in_period'
),
lost_hours_expanded AS (
  SELECT i.campaign_id, EXTRACT(HOUR FROM gs.h) AS hod,
    EXTRACT(EPOCH FROM (LEAST(i.end_ts, date_trunc('hour', gs.h) + interval '1 hour') - GREATEST(i.start_ts, date_trunc('hour', gs.h)))) / 3600.0 AS lost_hour_fraction
  FROM budget_log_intervals i
  JOIN LATERAL generate_series(date_trunc('hour', i.start_ts), date_trunc('hour', i.end_ts), interval '1 hour') gs(h) ON true
  WHERE i.end_ts > i.start_ts
),
extra_budget_campaign AS (
  SELECT l.campaign_id, SUM(l.lost_hour_fraction * COALESCE(aph.avg_cost_per_day_at_hod,0)) AS extra_daily_budget_needed
  FROM lost_hours_expanded l
  LEFT JOIN avg_perf_hour aph ON aph.campaign_id = l.campaign_id AND aph.hod = l.hod
  GROUP BY l.campaign_id
),
adv_campaign_spend_daily AS (
  SELECT campaign_id, SUM(spend_daily) AS campaign_spend_daily FROM adv_daily_placement GROUP BY campaign_id
),
adv_placement_with_corrected_spend AS (
  SELECT dp.*,
    COALESCE(ebc.extra_daily_budget_needed,0) AS extra_daily_budget_campaign,
    CASE WHEN COALESCE(csd.campaign_spend_daily,0) = 0 THEN 0
      ELSE COALESCE(ebc.extra_daily_budget_needed,0) * (dp.spend_daily / csd.campaign_spend_daily) END AS extra_daily_budget_allocated,
    dp.spend_daily + CASE WHEN COALESCE(csd.campaign_spend_daily,0) = 0 THEN 0
      ELSE COALESCE(ebc.extra_daily_budget_needed,0) * (dp.spend_daily / csd.campaign_spend_daily) END AS corrected_spend_daily
  FROM adv_daily_placement dp
  LEFT JOIN extra_budget_campaign ebc ON ebc.campaign_id = dp.campaign_id
  LEFT JOIN adv_campaign_spend_daily csd ON csd.campaign_id = dp.campaign_id
),
actual_placement_spend AS (
  SELECT advertiser_id, publisher_id, ad_type, targeting_type, ad_size_name, ad_size,
    SUM(spend_daily) AS actual_spend_daily,
    SUM(spend_daily * imps_per_cost) / NULLIF(SUM(spend_daily),0) AS imps_per_cost,
    SUM(spend_daily * conv_per_cost) / NULLIF(SUM(spend_daily),0) AS conv_per_cost,
    SUM(spend_daily * gmv_per_cost) / NULLIF(SUM(spend_daily),0) AS gmv_per_cost
  FROM adv_daily_placement
  GROUP BY advertiser_id, publisher_id, ad_type, targeting_type, ad_size_name, ad_size
),
corrected_placement_spend AS (
  SELECT advertiser_id, publisher_id, ad_type, targeting_type, ad_size_name, ad_size,
    SUM(corrected_spend_daily) AS corrected_spend_daily
  FROM adv_placement_with_corrected_spend
  GROUP BY advertiser_id, publisher_id, ad_type, targeting_type, ad_size_name, ad_size
),
actual_publisher_spend AS (
  SELECT advertiser_id, publisher_id, SUM(actual_spend_daily) AS actual_spend_daily_in_publisher
  FROM actual_placement_spend GROUP BY advertiser_id, publisher_id
),
corrected_publisher_spend AS (
  SELECT advertiser_id, publisher_id, SUM(corrected_spend_daily) AS corrected_spend_daily_in_publisher
  FROM corrected_placement_spend GROUP BY advertiser_id, publisher_id
),
actual_publisher_ad_type_spend AS (
  SELECT advertiser_id, publisher_id, ad_type, SUM(actual_spend_daily) AS actual_spend_daily_in_publisher_ad_type
  FROM actual_placement_spend GROUP BY advertiser_id, publisher_id, ad_type
),
advertiser_corrected_spend_total AS (
  SELECT advertiser_id, SUM(corrected_spend_daily_in_publisher) AS advertiser_corrected_spend_daily_total
  FROM corrected_publisher_spend GROUP BY advertiser_id
),
relevant_advertiser_publishers AS (
  SELECT cps.advertiser_id, cps.publisher_id, cps.corrected_spend_daily_in_publisher,
    acst.advertiser_corrected_spend_daily_total,
    cps.corrected_spend_daily_in_publisher / NULLIF(acst.advertiser_corrected_spend_daily_total,0) AS spend_share_in_advertiser
  FROM corrected_publisher_spend cps
  JOIN advertiser_corrected_spend_total acst ON acst.advertiser_id = cps.advertiser_id
  WHERE cps.corrected_spend_daily_in_publisher > 0
    AND (cps.corrected_spend_daily_in_publisher / NULLIF(acst.advertiser_corrected_spend_daily_total,0) >= 0.05 OR cps.corrected_spend_daily_in_publisher >= 10)
),
relevant_publishers_count_by_advertiser AS (
  SELECT advertiser_id, COUNT(DISTINCT publisher_id) AS relevant_publishers_count
  FROM relevant_advertiser_publishers GROUP BY advertiser_id
),
filtered_relevant_advertiser_publishers AS (
  SELECT rap.* FROM relevant_advertiser_publishers rap
  JOIN relevant_publishers_count_by_advertiser rpc ON rpc.advertiser_id = rap.advertiser_id
  WHERE rpc.relevant_publishers_count BETWEEN 1 AND 15
),
advertiser_pairs_overlap AS (
  SELECT a.advertiser_id AS advertiser_id_left, b.advertiser_id AS advertiser_id_right,
    COUNT(DISTINCT a.publisher_id) AS common_publishers
  FROM filtered_relevant_advertiser_publishers a
  JOIN filtered_relevant_advertiser_publishers b ON b.publisher_id = a.publisher_id AND b.advertiser_id > a.advertiser_id
  GROUP BY a.advertiser_id, b.advertiser_id
),
advertiser_profile_size AS (
  SELECT advertiser_id, COUNT(DISTINCT publisher_id) AS relevant_publishers_count
  FROM filtered_relevant_advertiser_publishers GROUP BY advertiser_id
),
advertiser_similarity AS (
  SELECT apo.advertiser_id_left, apo.advertiser_id_right, apo.common_publishers,
    (aps1.relevant_publishers_count + aps2.relevant_publishers_count - apo.common_publishers) AS union_publishers,
    apo.common_publishers::float / NULLIF((aps1.relevant_publishers_count + aps2.relevant_publishers_count - apo.common_publishers),0) AS jaccard_similarity
  FROM advertiser_pairs_overlap apo
  JOIN advertiser_profile_size aps1 ON aps1.advertiser_id = apo.advertiser_id_left
  JOIN advertiser_profile_size aps2 ON aps2.advertiser_id = apo.advertiser_id_right
  WHERE apo.common_publishers >= 2
),
advertiser_neighbors AS (
  SELECT advertiser_id_left AS advertiser_id, advertiser_id_right AS neighbor_advertiser_id, jaccard_similarity AS similarity
  FROM advertiser_similarity WHERE jaccard_similarity >= 0.20
  UNION ALL
  SELECT advertiser_id_right, advertiser_id_left, jaccard_similarity
  FROM advertiser_similarity WHERE jaccard_similarity >= 0.20
),
cluster_candidate_publishers AS (
  SELECT n.advertiser_id, rap.publisher_id,
    COUNT(DISTINCT n.neighbor_advertiser_id) AS neighbor_occurrences, SUM(n.similarity) AS similarity_score
  FROM advertiser_neighbors n
  JOIN filtered_relevant_advertiser_publishers rap ON rap.advertiser_id = n.neighbor_advertiser_id
  LEFT JOIN filtered_relevant_advertiser_publishers self_pub ON self_pub.advertiser_id = n.advertiser_id AND self_pub.publisher_id = rap.publisher_id
  WHERE self_pub.publisher_id IS NULL
  GROUP BY n.advertiser_id, rap.publisher_id
  HAVING COUNT(DISTINCT n.neighbor_advertiser_id) >= 2
),
eligible_publishers AS (
  SELECT ccp.advertiser_id, ccp.publisher_id, ccp.neighbor_occurrences, ccp.similarity_score
  FROM cluster_candidate_publishers ccp
),
advertiser_observed_spend AS (
  SELECT frap.advertiser_id, SUM(cps.corrected_spend_daily_in_publisher) AS observed_spend_daily
  FROM filtered_relevant_advertiser_publishers frap
  JOIN corrected_publisher_spend cps ON cps.advertiser_id = frap.advertiser_id AND cps.publisher_id = frap.publisher_id
  GROUP BY frap.advertiser_id
),
advertiser_observed_inventory AS (
  SELECT frap.advertiser_id, SUM(pcu.publisher_spend_daily_universe) AS observed_inventory_daily
  FROM filtered_relevant_advertiser_publishers frap
  JOIN publisher_capacity_universe pcu ON pcu.publisher_id = frap.publisher_id
  GROUP BY frap.advertiser_id
),
advertiser_inventory_intensity AS (
  SELECT aos.advertiser_id, aos.observed_spend_daily, aoi.observed_inventory_daily,
    aos.observed_spend_daily / NULLIF(aoi.observed_inventory_daily,0) AS inventory_intensity
  FROM advertiser_observed_spend aos
  JOIN advertiser_observed_inventory aoi ON aoi.advertiser_id = aos.advertiser_id
  WHERE aos.observed_spend_daily > 0 AND aoi.observed_inventory_daily > 0
),
expected_publisher_spend AS (
  SELECT aii.advertiser_id, ep.publisher_id, ep.neighbor_occurrences, ep.similarity_score,
    pcu.publisher_spend_daily_universe,
    pcu.publisher_spend_daily_universe * aii.inventory_intensity AS expected_spend_daily_publisher
  FROM advertiser_inventory_intensity aii
  JOIN eligible_publishers ep ON ep.advertiser_id = aii.advertiser_id
  JOIN publisher_capacity_universe pcu ON pcu.publisher_id = ep.publisher_id
),
expected_placement_spend AS (
  SELECT eps.advertiser_id, ps.publisher_id, eps.neighbor_occurrences, eps.similarity_score,
    ps.ad_type, ps.targeting_type, ps.ad_size_name, ps.ad_size,
    eps.expected_spend_daily_publisher * ps.share_in_publisher AS expected_spend_daily,
    ps.imps_per_cost AS imps_per_cost_bmk, ps.conv_per_cost AS conv_per_cost_bmk, ps.gmv_per_cost AS gmv_per_cost_bmk
  FROM expected_publisher_spend eps
  JOIN placement_share_in_publisher ps ON ps.publisher_id = eps.publisher_id
),
placement_opportunity AS (
  SELECT eps.advertiser_id, eps.publisher_id, 'placement_gap'::text AS opportunity_type,
    eps.neighbor_occurrences, eps.similarity_score, eps.ad_type, eps.targeting_type, eps.ad_size_name, eps.ad_size,
    GREATEST(eps.expected_spend_daily - COALESCE(aps.actual_spend_daily,0), 0) AS extra_spend_daily,
    eps.imps_per_cost_bmk, eps.conv_per_cost_bmk, eps.gmv_per_cost_bmk
  FROM expected_placement_spend eps
  LEFT JOIN actual_placement_spend aps ON aps.advertiser_id = eps.advertiser_id AND aps.publisher_id = eps.publisher_id
    AND aps.ad_type = eps.ad_type AND COALESCE(aps.targeting_type,'') = COALESCE(eps.targeting_type,'')
    AND COALESCE(aps.ad_size,'') = COALESCE(eps.ad_size,'')
  WHERE GREATEST(eps.expected_spend_daily - COALESCE(aps.actual_spend_daily,0), 0) > 0
    AND LOWER(COALESCE(eps.ad_type,'')) NOT IN ('product', 'product_ads', 'sponsored_products')
),
publisher_opportunity AS (
  SELECT eps.advertiser_id, eps.publisher_id, 'publisher_gap'::text AS opportunity_type,
    MAX(eps.neighbor_occurrences) AS neighbor_occurrences, MAX(eps.similarity_score) AS similarity_score,
    NULL::text AS ad_type, NULL::text AS targeting_type, NULL::text AS ad_size_name, NULL::text AS ad_size,
    GREATEST(MAX(eps.expected_spend_daily_publisher) - COALESCE(MAX(aps.actual_spend_daily_in_publisher),0), 0) AS extra_spend_daily,
    pbe.imps_per_cost AS imps_per_cost_bmk, pbe.conv_per_cost AS conv_per_cost_bmk, pbe.gmv_per_cost AS gmv_per_cost_bmk
  FROM expected_publisher_spend eps
  LEFT JOIN actual_publisher_spend aps ON aps.advertiser_id = eps.advertiser_id AND aps.publisher_id = eps.publisher_id
  LEFT JOIN publisher_benchmark_eff pbe ON pbe.publisher_id = eps.publisher_id
  GROUP BY eps.advertiser_id, eps.publisher_id, pbe.imps_per_cost, pbe.conv_per_cost, pbe.gmv_per_cost
  HAVING GREATEST(MAX(eps.expected_spend_daily_publisher) - COALESCE(MAX(aps.actual_spend_daily_in_publisher),0), 0) > 0
),
ad_type_opportunity AS (
  SELECT eps.advertiser_id, eps.publisher_id, 'ad_type_gap'::text AS opportunity_type,
    MAX(eps.neighbor_occurrences) AS neighbor_occurrences, MAX(eps.similarity_score) AS similarity_score,
    eps.ad_type, NULL::text AS targeting_type, NULL::text AS ad_size_name, NULL::text AS ad_size,
    GREATEST(SUM(eps.expected_spend_daily) - COALESCE(MAX(apats.actual_spend_daily_in_publisher_ad_type),0), 0) AS extra_spend_daily,
    SUM(eps.expected_spend_daily * eps.imps_per_cost_bmk) / NULLIF(SUM(eps.expected_spend_daily),0) AS imps_per_cost_bmk,
    SUM(eps.expected_spend_daily * eps.conv_per_cost_bmk) / NULLIF(SUM(eps.expected_spend_daily),0) AS conv_per_cost_bmk,
    SUM(eps.expected_spend_daily * eps.gmv_per_cost_bmk) / NULLIF(SUM(eps.expected_spend_daily),0) AS gmv_per_cost_bmk
  FROM expected_placement_spend eps
  LEFT JOIN actual_publisher_ad_type_spend apats ON apats.advertiser_id = eps.advertiser_id
    AND apats.publisher_id = eps.publisher_id AND apats.ad_type = eps.ad_type
  GROUP BY eps.advertiser_id, eps.publisher_id, eps.ad_type
  HAVING GREATEST(SUM(eps.expected_spend_daily) - COALESCE(MAX(apats.actual_spend_daily_in_publisher_ad_type),0), 0) > 0
),
context_opportunity AS (
  SELECT advertiser_id, publisher_id, 'context_gap'::text AS opportunity_type,
    MAX(neighbor_occurrences) AS neighbor_occurrences, MAX(similarity_score) AS similarity_score,
    ad_type, targeting_type, NULL::text AS ad_size_name, NULL::text AS ad_size,
    SUM(extra_spend_daily) AS extra_spend_daily,
    SUM(extra_spend_daily * imps_per_cost_bmk) / NULLIF(SUM(extra_spend_daily),0) AS imps_per_cost_bmk,
    SUM(extra_spend_daily * conv_per_cost_bmk) / NULLIF(SUM(extra_spend_daily),0) AS conv_per_cost_bmk,
    SUM(extra_spend_daily * gmv_per_cost_bmk) / NULLIF(SUM(extra_spend_daily),0) AS gmv_per_cost_bmk
  FROM placement_opportunity GROUP BY advertiser_id, publisher_id, ad_type, targeting_type
),
ad_size_opportunity AS (
  SELECT advertiser_id, publisher_id, 'ad_size_gap'::text AS opportunity_type,
    MAX(neighbor_occurrences) AS neighbor_occurrences, MAX(similarity_score) AS similarity_score,
    ad_type, targeting_type, ad_size_name, ad_size,
    SUM(extra_spend_daily) AS extra_spend_daily,
    SUM(extra_spend_daily * imps_per_cost_bmk) / NULLIF(SUM(extra_spend_daily),0) AS imps_per_cost_bmk,
    SUM(extra_spend_daily * conv_per_cost_bmk) / NULLIF(SUM(extra_spend_daily),0) AS conv_per_cost_bmk,
    SUM(extra_spend_daily * gmv_per_cost_bmk) / NULLIF(SUM(extra_spend_daily),0) AS gmv_per_cost_bmk
  FROM placement_opportunity GROUP BY advertiser_id, publisher_id, ad_type, targeting_type, ad_size_name, ad_size
),
all_opps AS (
  SELECT * FROM placement_opportunity UNION ALL SELECT * FROM publisher_opportunity
  UNION ALL SELECT * FROM ad_type_opportunity UNION ALL SELECT * FROM context_opportunity
  UNION ALL SELECT * FROM ad_size_opportunity
),
final AS (
  SELECT o.*,
    ROUND(COALESCE(o.extra_spend_daily,0)::numeric, 2) AS extra_spend_daily_r,
    ROUND((COALESCE(o.extra_spend_daily,0) * COALESCE(o.imps_per_cost_bmk,0))::numeric, 0)::bigint AS extra_imps_daily,
    ROUND((COALESCE(o.extra_spend_daily,0) * COALESCE(o.conv_per_cost_bmk,0))::numeric, 0)::bigint AS extra_conv_daily,
    ROUND((COALESCE(o.extra_spend_daily,0) * COALESCE(o.gmv_per_cost_bmk,0))::numeric, 2) AS extra_gmv_daily,
    ROUND((COALESCE(o.extra_spend_daily,0) * p.days_to_month_end)::numeric, 2) AS extra_spend_to_month_end,
    ROUND((COALESCE(o.extra_spend_daily,0) * 30)::numeric, 2) AS extra_spend_30d,
    ROUND((COALESCE(o.extra_spend_daily,0) * COALESCE(o.conv_per_cost_bmk,0) * p.days_to_month_end)::numeric, 0)::bigint AS extra_conv_to_month_end,
    ROUND((COALESCE(o.extra_spend_daily,0) * COALESCE(o.gmv_per_cost_bmk,0) * p.days_to_month_end)::numeric, 2) AS extra_gmv_to_month_end,
    ROUND((COALESCE(o.extra_spend_daily,0) * COALESCE(o.conv_per_cost_bmk,0) * 30)::numeric, 0)::bigint AS extra_conv_30d,
    ROUND((COALESCE(o.extra_spend_daily,0) * COALESCE(o.gmv_per_cost_bmk,0) * 30)::numeric, 2) AS extra_gmv_30d
  FROM all_opps o CROSS JOIN params p
  WHERE COALESCE(o.extra_spend_daily,0) > 0
)
SELECT
  f.advertiser_id, adv.name AS advertiser_name,
  f.publisher_id, pub.name AS publisher_name,
  f.opportunity_type,
  CASE
    WHEN f.opportunity_type = 'placement_gap' THEN 'Placement Gap'
    WHEN f.opportunity_type = 'publisher_gap' THEN 'Publisher Gap'
    WHEN f.opportunity_type = 'ad_type_gap' THEN 'Ad Type Gap'
    WHEN f.opportunity_type = 'context_gap' THEN 'Context Gap'
    WHEN f.opportunity_type = 'ad_size_gap' THEN 'Ad Size Gap'
    ELSE f.opportunity_type
  END AS opportunity_label,
  f.neighbor_occurrences,
  ROUND(f.similarity_score::numeric, 4) AS similarity_score,
  f.ad_type, f.targeting_type, f.ad_size_name, f.ad_size,
  f.extra_spend_daily_r AS extra_spend_daily,
  f.extra_imps_daily, f.extra_conv_daily, f.extra_gmv_daily,
  f.extra_spend_to_month_end, f.extra_conv_to_month_end, f.extra_gmv_to_month_end,
  f.extra_spend_30d, f.extra_conv_30d, f.extra_gmv_30d
FROM final f
LEFT JOIN advertisers adv ON adv.id = f.advertiser_id
LEFT JOIN publishers pub ON pub.id = f.publisher_id
ORDER BY extra_gmv_30d DESC, similarity_score DESC
"""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            qs = parse_qs(urlparse(self.path).query)
            currency_code = (qs.get("currency_code") or ["BRL"])[0]
            advertiser_id = (qs.get("advertiser_id") or [None])[0]

            config = Config.from_env()
            mb = config.build_metabase_client()

            sql = build_query(currency_code, advertiser_id)
            rows = mb.query(sql, db_id=config.metabase_opp_db_id)

            data = []
            for r in rows:
                data.append({
                    "advertiser_id": r["advertiser_id"] or "",
                    "advertiser_name": r["advertiser_name"] or "",
                    "publisher_id": r["publisher_id"] or "",
                    "publisher_name": r["publisher_name"] or "",
                    "opportunity_type": r["opportunity_type"] or "",
                    "opportunity_label": r["opportunity_label"] or "",
                    "neighbor_occurrences": int(r["neighbor_occurrences"] or 0),
                    "similarity_score": float(r["similarity_score"] or 0),
                    "ad_type": r["ad_type"] or "",
                    "targeting_type": r["targeting_type"] or "",
                    "ad_size_name": r["ad_size_name"] or "",
                    "ad_size": r["ad_size"] or "",
                    "extra_spend_daily": float(r["extra_spend_daily"] or 0),
                    "extra_imps_daily": int(r["extra_imps_daily"] or 0),
                    "extra_conv_daily": int(r["extra_conv_daily"] or 0),
                    "extra_gmv_daily": float(r["extra_gmv_daily"] or 0),
                    "extra_spend_to_month_end": float(r["extra_spend_to_month_end"] or 0),
                    "extra_conv_to_month_end": int(r["extra_conv_to_month_end"] or 0),
                    "extra_gmv_to_month_end": float(r["extra_gmv_to_month_end"] or 0),
                    "extra_spend_30d": float(r["extra_spend_30d"] or 0),
                    "extra_conv_30d": int(r["extra_conv_30d"] or 0),
                    "extra_gmv_30d": float(r["extra_gmv_30d"] or 0),
                })

            self._json(200, {"total": len(data), "data": data})

        except Exception as e:
            self._json(500, {"error": str(e)})

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode("utf-8"))
