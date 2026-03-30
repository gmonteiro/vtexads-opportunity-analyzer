from dataclasses import dataclass, field


@dataclass
class PlacementStatus:
    publisher_name: str
    placement_name: str
    context: str
    ad_type: str
    total_requests: int
    in_use: bool

    @property
    def status(self) -> str:
        return "ativo" if self.in_use else "gap"


@dataclass
class PublisherStatus:
    publisher_id: str
    publisher_name: str
    advertiser_active: bool
    network_spend_30d: float
    advertiser_count: int

    @property
    def status(self) -> str:
        return "ativo" if self.advertiser_active else "ausente"


@dataclass
class OpportunityProjection:
    publisher_name: str
    ad_type: str
    current_product_spend: float
    benchmark_ratio: float
    sample_size: int
    projected_spend: float
    estimated_impressions: int
    estimated_clicks: int
    estimated_conversions: float
    estimated_roas: float

    @property
    def confidence(self) -> str:
        if self.sample_size >= 10:
            return "Alta"
        elif self.sample_size >= 5:
            return "Media"
        return "Baixa"


@dataclass
class PlacementGapReport:
    advertiser_name: str
    days: int
    placements: list[PlacementStatus] = field(default_factory=list)

    @property
    def gaps(self) -> list[PlacementStatus]:
        return [p for p in self.placements if not p.in_use]

    @property
    def active(self) -> list[PlacementStatus]:
        return [p for p in self.placements if p.in_use]


@dataclass
class PublisherGapReport:
    advertiser_name: str
    days: int
    publishers: list[PublisherStatus] = field(default_factory=list)

    @property
    def gaps(self) -> list[PublisherStatus]:
        return [p for p in self.publishers if not p.advertiser_active]

    @property
    def active(self) -> list[PublisherStatus]:
        return [p for p in self.publishers if p.advertiser_active]


@dataclass
class OpportunitySizingReport:
    advertiser_name: str
    days: int
    projections: list[OpportunityProjection] = field(default_factory=list)
