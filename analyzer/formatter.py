from analyzer.models import (
    PlacementGapReport,
    PublisherGapReport,
    OpportunitySizingReport,
)


def _fmt_number(n: int | float) -> str:
    if isinstance(n, float):
        return f"{n:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{n:,}".replace(",", ".")


def _fmt_brl(n: float) -> str:
    return f"R$ {_fmt_number(n)}"


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    header_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers)) + " |"
    sep_line = "| " + " | ".join("-" * col_widths[i] for i in range(len(headers))) + " |"
    data_lines = []
    for row in rows:
        data_lines.append("| " + " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)) + " |")

    return "\n".join([header_line, sep_line] + data_lines)


def format_placement_gap(report: PlacementGapReport) -> str:
    lines = [
        f"# Placement Gap — {report.advertiser_name}",
        f"Periodo: ultimos {report.days} dias",
        f"Total placements analisados: {len(report.placements)} | Ativos: {len(report.active)} | Gaps: {len(report.gaps)}",
        "",
    ]

    publishers = sorted(set(p.publisher_name for p in report.placements))
    for pub in publishers:
        pub_placements = [p for p in report.placements if p.publisher_name == pub]
        pub_gaps = [p for p in pub_placements if not p.in_use]
        pub_active = [p for p in pub_placements if p.in_use]

        lines.append(f"## {pub}")
        lines.append(f"Placements: {len(pub_placements)} | Ativos: {len(pub_active)} | Gaps: {len(pub_gaps)}")
        lines.append("")

        if pub_gaps:
            lines.append("### Gaps (placements nao utilizados)")
            rows = []
            for p in sorted(pub_gaps, key=lambda x: -x.total_requests):
                rows.append([p.placement_name, p.context, p.ad_type, _fmt_number(p.total_requests)])
            lines.append(_md_table(["Placement", "Contexto", "Ad Type", "Requests (volume)"], rows))
            lines.append("")

        if pub_active:
            lines.append("### Ativos")
            rows = []
            for p in sorted(pub_active, key=lambda x: -x.total_requests):
                rows.append([p.placement_name, p.context, p.ad_type, _fmt_number(p.total_requests)])
            lines.append(_md_table(["Placement", "Contexto", "Ad Type", "Requests (volume)"], rows))
            lines.append("")

    return "\n".join(lines)


def format_publisher_gap(report: PublisherGapReport) -> str:
    lines = [
        f"# Publisher Gap — {report.advertiser_name}",
        f"Periodo: ultimos {report.days} dias",
        f"Total publishers: {len(report.publishers)} | Ativos: {len(report.active)} | Ausentes: {len(report.gaps)}",
        "",
    ]

    if report.gaps:
        lines.append("## Publishers ausentes (oportunidade)")
        rows = []
        for p in sorted(report.gaps, key=lambda x: -x.network_spend_30d):
            rows.append([p.publisher_name, _fmt_brl(p.network_spend_30d), str(p.advertiser_count), p.status])
        lines.append(_md_table(["Publisher", "Spend Rede (30d)", "Advertisers", "Status"], rows))
        lines.append("")

    if report.active:
        lines.append("## Publishers ativos")
        rows = []
        for p in sorted(report.active, key=lambda x: -x.network_spend_30d):
            rows.append([p.publisher_name, _fmt_brl(p.network_spend_30d), str(p.advertiser_count), p.status])
        lines.append(_md_table(["Publisher", "Spend Rede (30d)", "Advertisers", "Status"], rows))
        lines.append("")

    return "\n".join(lines)


def format_opportunity_sizing(report: OpportunitySizingReport) -> str:
    lines = [
        f"# Opportunity Sizing — {report.advertiser_name}",
        f"Periodo: ultimos {report.days} dias",
        f"Modelo: Peer Benchmarking (mediana de spend ratio por publisher)",
        "",
    ]

    publishers = sorted(set(p.publisher_name for p in report.projections))
    for pub in publishers:
        projs = [p for p in report.projections if p.publisher_name == pub]
        if not projs:
            continue

        product_spend = projs[0].current_product_spend
        lines.append(f"## {pub}")
        lines.append(f"Product Spend (periodo): {_fmt_brl(product_spend)}")
        lines.append("")

        rows = []
        for p in projs:
            rows.append([
                p.ad_type,
                _fmt_brl(p.projected_spend),
                _fmt_number(p.estimated_impressions),
                _fmt_number(p.estimated_clicks),
                _fmt_number(p.estimated_conversions),
                f"{p.estimated_roas:.1f}x",
                f"{p.confidence} ({p.sample_size})",
            ])
        lines.append(_md_table(
            ["Ad Type", "Invest. Projetado", "Impressoes", "Cliques", "Conv.", "ROAS Est.", "Confianca (n)"],
            rows,
        ))
        lines.append("")

    return "\n".join(lines)
