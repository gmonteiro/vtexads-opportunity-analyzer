import argparse
import sys

from analyzer.config import Config
from analyzer.clients.metabase import MetabaseClient
from analyzer.clients.ads_perf import AdsPerfClient
from analyzer.reports import placement_gap, publisher_gap, opportunity_sizing
from analyzer.formatter import format_placement_gap, format_publisher_gap, format_opportunity_sizing


REPORTS = {
    "placement-gap": ("Placement Gap", placement_gap.generate, format_placement_gap),
    "publisher-gap": ("Publisher Gap", publisher_gap.generate, format_publisher_gap),
    "opportunity-sizing": ("Opportunity Sizing", opportunity_sizing.generate, format_opportunity_sizing),
}


def main():
    parser = argparse.ArgumentParser(
        description="VTEX Ads Opportunity Analyzer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python -m analyzer --advertiser LOREALDCAVTEXADS --report all
  python -m analyzer --advertiser LOREALDCAVTEXADS --report placement-gap
  python -m analyzer --advertiser LOREALDCAVTEXADS --report opportunity-sizing --days 15
  python -m analyzer --advertiser LOREALDCAVTEXADS --report all --output relatorio.md
        """,
    )
    parser.add_argument("--advertiser", required=True, help="Nome ou ID do advertiser")
    parser.add_argument(
        "--report",
        choices=list(REPORTS.keys()) + ["all"],
        default="all",
        help="Qual relatorio gerar (default: all)",
    )
    parser.add_argument("--days", type=int, default=30, help="Janela de lookback em dias (default: 30)")
    parser.add_argument("--output", "-o", help="Arquivo de saida (default: stdout)")

    args = parser.parse_args()

    # Load config
    config = Config.from_env()

    if not config.has_metabase():
        print("ERRO: METABASE_SESSION nao configurado no .env", file=sys.stderr)
        print("Configure o token de sessao do Metabase para continuar.", file=sys.stderr)
        sys.exit(1)

    mb = MetabaseClient(
        session_token=config.metabase_session,
        base_url=config.metabase_base_url,
        db_id=config.metabase_db_id,
    )

    # Determine which reports to run
    if args.report == "all":
        report_keys = list(REPORTS.keys())
    else:
        report_keys = [args.report]

    output_parts = []

    for key in report_keys:
        label, gen_fn, fmt_fn = REPORTS[key]
        print(f"Gerando {label}...", file=sys.stderr)
        try:
            report = gen_fn(args.advertiser, mb, days=args.days)
            output_parts.append(fmt_fn(report))
        except Exception as e:
            print(f"ERRO ao gerar {label}: {e}", file=sys.stderr)
            output_parts.append(f"# {label} — ERRO\n\n{e}\n")

    result = "\n---\n\n".join(output_parts)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result)
        print(f"Relatorio salvo em {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
