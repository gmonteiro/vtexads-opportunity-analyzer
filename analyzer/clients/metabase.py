import re
import requests


class MetabaseClient:
    SCHEMA = "vtex_ads_snowflake_silver_iceberg"

    def __init__(
        self,
        base_url: str = "https://metabase.newtail.com.br",
        db_id: int = 20,
        session_token: str = "",
        username: str = "",
        password: str = "",
    ):
        self.db_id = db_id
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers["Content-Type"] = "application/json"

        if session_token:
            self._set_token(session_token)
        elif username and password:
            self._login(username, password)

    def _set_token(self, token: str):
        self.session.headers["X-Metabase-Session"] = token

    def _login(self, username: str, password: str):
        resp = self.session.post(
            f"{self.base_url}/api/session",
            json={"username": username, "password": password},
        )
        resp.raise_for_status()
        token = resp.json().get("id")
        if not token:
            raise RuntimeError("Metabase login failed: no session token returned")
        self._set_token(token)

    @staticmethod
    def sanitize(value: str) -> str:
        """Sanitize a value for safe SQL interpolation (identifiers/UUIDs only)."""
        return re.sub(r"[^a-zA-Z0-9_\-]", "", value)

    def query(self, sql: str) -> list[dict]:
        """Execute a native SQL query and return rows as list of dicts."""
        resp = self.session.post(
            f"{self.base_url}/api/dataset",
            json={
                "type": "native",
                "native": {"query": sql},
                "database": self.db_id,
                "parameters": [],
            },
        )
        resp.raise_for_status()
        data = resp.json()

        if "error" in data and data["error"]:
            raise RuntimeError(f"Metabase query error: {data['error']}")

        cols = [c["name"] for c in data.get("data", {}).get("cols", [])]
        rows = data.get("data", {}).get("rows", [])
        return [dict(zip(cols, row)) for row in rows]
