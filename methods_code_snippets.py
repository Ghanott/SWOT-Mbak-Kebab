
"""
methods_code_snippets.py
Jalankan file ini di IDE/laptop untuk menarik data Overpass real dari OpenStreetMap.
"""

import json
import time
from pathlib import Path
import requests

BASE = Path(__file__).resolve().parent
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
]
MAX_RETRIES = 3
RETRY_WAIT_SECONDS = 5


def fetch_overpass(query: str):
    last_error = None

    for url in OVERPASS_URLS:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = requests.post(
                    url,
                    data={"data": query},
                    headers={"User-Agent": "mbak-kebab-sleman-analysis/1.0"},
                    timeout=120,
                )
                response.raise_for_status()
                return response.json()
            except (requests.RequestException, ValueError) as exc:
                last_error = exc
                if attempt == MAX_RETRIES:
                    print(f"Endpoint failed after {MAX_RETRIES} attempts: {url}")
                    break
                wait_seconds = RETRY_WAIT_SECONDS * attempt
                print(f"Retry {attempt}/{MAX_RETRIES - 1} on {url} after error: {exc}")
                time.sleep(wait_seconds)

    raise last_error

def run_overpass():
    queries = json.loads((BASE / "overpass_queries.json").read_text(encoding="utf-8"))
    combined = {"elements": []}

    for zone, payload in queries.items():
        print("Fetching", zone)
        data = fetch_overpass(payload["query"])
        file_name = f"overpass_raw_{zone.lower().replace(' ', '_')}.json"
        (BASE / file_name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        for el in data.get("elements", []):
            el["zone_name_query"] = zone
            combined["elements"].append(el)

        time.sleep(3)

    (BASE / "overpass_raw_combined.json").write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Done. Raw Overpass JSON saved.")

if __name__ == "__main__":
    run_overpass()
