import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    ads_perf_api_key: str
    ads_perf_base_url: str
    metabase_session: str
    metabase_base_url: str
    metabase_db_id: int

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        return cls(
            ads_perf_api_key=os.environ.get("ADS_PERF_API_KEY", ""),
            ads_perf_base_url=os.environ.get("ADS_PERF_BASE_URL", "https://ads-perf.newtail.com.br"),
            metabase_session=os.environ.get("METABASE_SESSION", ""),
            metabase_base_url=os.environ.get("METABASE_BASE_URL", "https://metabase.newtail.com.br"),
            metabase_db_id=int(os.environ.get("METABASE_DB_ID", "20")),
        )

    def has_metabase(self) -> bool:
        return bool(self.metabase_session)

    def has_ads_perf(self) -> bool:
        return bool(self.ads_perf_api_key)
