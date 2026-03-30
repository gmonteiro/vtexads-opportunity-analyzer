import time
import requests


class AdsPerfClient:
    def __init__(self, api_key: str, base_url: str = "https://ads-perf.newtail.com.br"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "x-api-key": api_key,
        })
        self._last_response_id: str | None = None

    def ask(
        self,
        question: str,
        use_context: bool = False,
        poll_interval: float = 3.0,
        timeout: float = 180.0,
    ) -> dict:
        """Ask the agent a question via async job flow.

        Returns dict with keys: reply, response_id, job_id.
        """
        body = {"message": question}
        if use_context and self._last_response_id:
            body["previous_response_id"] = self._last_response_id

        resp = self.session.post(f"{self.base_url}/api/chat/jobs", json=body)
        resp.raise_for_status()
        job = resp.json()
        job_id = job["job_id"]

        start = time.time()
        while time.time() - start < timeout:
            time.sleep(poll_interval)
            resp = self.session.get(f"{self.base_url}/api/chat/jobs/{job_id}")
            resp.raise_for_status()
            result = resp.json()

            if result["status"] == "succeeded":
                self._last_response_id = result.get("response_id")
                return {
                    "reply": result["reply"],
                    "response_id": result.get("response_id"),
                    "job_id": job_id,
                }
            elif result["status"] == "failed":
                raise RuntimeError(f"Agent job {job_id} failed: {result.get('error')}")

        raise TimeoutError(f"Agent job {job_id} timed out after {timeout}s")

    def reset_context(self):
        self._last_response_id = None
