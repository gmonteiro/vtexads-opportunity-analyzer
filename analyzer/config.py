import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    ads_perf_api_key: str
    ads_perf_base_url: str
    metabase_session: str
    metabase_username: str
    metabase_password: str
    metabase_base_url: str
    metabase_db_id: int
    metabase_opp_db_id: int

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        return cls(
            ads_perf_api_key=os.environ.get("ADS_PERF_API_KEY", ""),
            ads_perf_base_url=os.environ.get("ADS_PERF_BASE_URL", "https://ads-perf.newtail.com.br"),
            metabase_session=os.environ.get("METABASE_SESSION", ""),
            metabase_username=os.environ.get("METABASE_USERNAME", ""),
            metabase_password=os.environ.get("METABASE_PASSWORD", ""),
            metabase_base_url=os.environ.get("METABASE_BASE_URL", "https://metabase.newtail.com.br"),
            metabase_db_id=int(os.environ.get("METABASE_DB_ID", "20")),
            metabase_opp_db_id=int(os.environ.get("METABASE_OPP_DB_ID", "13")),
        )

    def has_metabase(self) -> bool:
        return bool(self.metabase_session) or (bool(self.metabase_username) and bool(self.metabase_password))

    def has_ads_perf(self) -> bool:
        return bool(self.ads_perf_api_key)

    def build_metabase_client(self):
        from analyzer.clients.metabase import MetabaseClient
        return MetabaseClient(
            base_url=self.metabase_base_url,
            db_id=self.metabase_db_id,
            session_token=self.metabase_session,
            username=self.metabase_username,
            password=self.metabase_password,
        )
