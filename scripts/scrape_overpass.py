import json
import time
from datetime import datetime, timezone
from pathlib import Path

import requests


BASE_DIR = Path(__file__).resolve().parent.parent
QUERY_FILE = BASE_DIR / "overpass_queries.json"
RAW_DIR = BASE_DIR / "data" / "raw"
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]
REQUEST_TIMEOUT_SECONDS = 120
REQUEST_DELAY_SECONDS = 3
MAX_RETRIES_PER_ENDPOINT = 2


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify_zone(zone_name: str) -> str:
    return zone_name.lower().replace(" ", "_")


def load_queries() -> dict:
    with QUERY_FILE.open(encoding="utf-8") as handle:
        return json.load(handle)


def fetch_zone(zone_name: str, query: str) -> tuple[dict, str]:
    last_error = None

    for endpoint in OVERPASS_URLS:
        for attempt in range(1, MAX_RETRIES_PER_ENDPOINT + 1):
            try:
                response = requests.post(
                    endpoint,
                    data={"data": query},
                    headers={"User-Agent": "mbak-kebab-sleman-analysis/1.0"},
                    timeout=REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()
                payload = response.json()
                return payload, endpoint
            except (requests.Timeout, requests.RequestException, ValueError) as exc:
                last_error = exc
                print(f"[{zone_name}] attempt {attempt}/{MAX_RETRIES_PER_ENDPOINT} failed on {endpoint}: {exc}")
                if attempt < MAX_RETRIES_PER_ENDPOINT:
                    time.sleep(2 * attempt)
        print(f"[{zone_name}] switching endpoint after failures: {endpoint}")

    raise RuntimeError(f"Failed to fetch zone '{zone_name}' from all endpoints.") from last_error


def save_zone_payload(zone_name: str, payload: dict, endpoint_used: str) -> list[dict]:
    zone_elements = payload.get("elements", [])
    fetched_at = utc_timestamp()

    for element in zone_elements:
        element["zone_name_query"] = zone_name
        element["source"] = "OpenStreetMap Overpass"
        element["source_url"] = endpoint_used
        element["extracted_at"] = fetched_at

    output = {
        "zone": zone_name,
        "endpoint_used": endpoint_used,
        "extracted_at": fetched_at,
        "element_count": len(zone_elements),
        "elements": zone_elements,
    }

    output_path = RAW_DIR / f"overpass_raw_{slugify_zone(zone_name)}.json"
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[{zone_name}] saved {len(zone_elements)} elements to {output_path}")
    return zone_elements


def save_combined_payload(all_elements: list[dict], zone_results: list[dict]) -> None:
    combined_payload = {
        "source": "OpenStreetMap Overpass",
        "extracted_at": utc_timestamp(),
        "zone_results": zone_results,
        "element_count": len(all_elements),
        "elements": all_elements,
    }
    output_path = RAW_DIR / "overpass_raw_combined.json"
    output_path.write_text(json.dumps(combined_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[combined] saved {len(all_elements)} elements to {output_path}")


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    queries = load_queries()
    combined_elements = []
    zone_results = []

    for zone_name, payload in queries.items():
        print(f"Fetching zone: {zone_name}")
        zone_payload, endpoint_used = fetch_zone(zone_name, payload["query"])
        zone_elements = save_zone_payload(zone_name, zone_payload, endpoint_used)
        combined_elements.extend(zone_elements)
        zone_results.append(
            {
                "zone": zone_name,
                "endpoint_used": endpoint_used,
                "element_count": len(zone_elements),
            }
        )
        time.sleep(REQUEST_DELAY_SECONDS)

    save_combined_payload(combined_elements, zone_results)
    print("Scraping Overpass selesai.")


if __name__ == "__main__":
    main()
