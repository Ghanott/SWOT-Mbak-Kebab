import csv
import difflib
import math
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
BASELINE_INPUT = BASE_DIR / "poi_baseline.csv"
FINAL_INPUT = BASE_DIR / "data" / "clean" / "poi_final.csv"
OSM_INPUT = BASE_DIR / "data" / "clean" / "poi_osm_clean.csv"
COMPETITOR_INPUT = BASE_DIR / "competitor_menu_price.csv"
OUTPUT_PATH = BASE_DIR / "data" / "clean" / "competitor_match_audit.csv"

OUTPUT_COLUMNS = [
    "poi_id",
    "baseline_name",
    "baseline_zone",
    "baseline_latitude",
    "baseline_longitude",
    "match_status",
    "validation_status",
    "match_method",
    "matched_osm_type",
    "matched_osm_id",
    "matched_zone",
    "nearest_osm_name",
    "nearest_osm_category",
    "nearest_osm_zone",
    "nearest_distance_meters",
    "name_similarity",
    "audit_note",
]


def norm(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def find_final_match(baseline_row: dict, final_rows: list[dict]) -> dict:
    for row in final_rows:
        if row["poi_id"] == baseline_row["poi_id"]:
            return row
    return {}


def nearest_osm_candidate(baseline_row: dict, osm_rows: list[dict]) -> dict:
    if not baseline_row.get("latitude") or not baseline_row.get("longitude"):
        return {}

    best = None
    baseline_name = norm(baseline_row["name"])
    for row in osm_rows:
        if not row.get("latitude") or not row.get("longitude"):
            continue
        distance = haversine_meters(
            float(baseline_row["latitude"]),
            float(baseline_row["longitude"]),
            float(row["latitude"]),
            float(row["longitude"]),
        )
        similarity = difflib.SequenceMatcher(None, baseline_name, norm(row["name"])).ratio()
        score = (similarity, -distance)
        if best is None or score > best["score"]:
            best = {
                "score": score,
                "distance": round(distance),
                "similarity": round(similarity, 3),
                "name": row.get("name", ""),
                "category": row.get("category", ""),
                "zone": row.get("zone", ""),
            }
    return best or {}


def main() -> None:
    baseline_rows = load_rows(BASELINE_INPUT)
    final_rows = load_rows(FINAL_INPUT)
    osm_rows = load_rows(OSM_INPUT)
    competitor_rows = load_rows(COMPETITOR_INPUT)
    competitor_names = {norm(row.get("competitor_name", "")) for row in competitor_rows}

    audit_rows = []
    for baseline in baseline_rows:
        if baseline.get("category") != "direct_kebab_competitor" and baseline.get("poi_id") not in {"P-010", "P-011"}:
            continue

        final_match = find_final_match(baseline, final_rows)
        nearest = nearest_osm_candidate(baseline, osm_rows)
        matched = bool(final_match and final_match.get("osm_id"))
        validation_status = final_match.get("validation_status", "")
        baseline_known_in_competitor_sheet = norm(baseline.get("name", "")) in competitor_names

        audit_rows.append(
            {
                "poi_id": baseline["poi_id"],
                "baseline_name": baseline["name"],
                "baseline_zone": baseline["zone"],
                "baseline_latitude": baseline["latitude"],
                "baseline_longitude": baseline["longitude"],
                "match_status": "matched" if matched else "not_matched_to_osm",
                "validation_status": (
                    "matched_osm"
                    if matched
                    else (validation_status or ("verified_baseline_only" if baseline_known_in_competitor_sheet else "needs_manual_validation"))
                ),
                "match_method": final_match.get("match_method", "") if matched else "",
                "matched_osm_type": final_match.get("osm_type", ""),
                "matched_osm_id": final_match.get("osm_id", ""),
                "matched_zone": final_match.get("zone", ""),
                "nearest_osm_name": nearest.get("name", ""),
                "nearest_osm_category": nearest.get("category", ""),
                "nearest_osm_zone": nearest.get("zone", ""),
                "nearest_distance_meters": nearest.get("distance", ""),
                "name_similarity": nearest.get("similarity", ""),
                "audit_note": (
                    "Matched to OSM and already enriched in poi_final."
                    if matched
                    else (
                        "Baseline record is supported by external public listing, but no reliable OSM object was found."
                        if (validation_status == "verified_baseline_only" or baseline_known_in_competitor_sheet)
                        else "No strong OSM match found automatically; keep baseline record and validate manually if needed."
                    )
                ),
            }
        )

    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in audit_rows:
            writer.writerow(row)

    print("Generate competitor match audit selesai.")
    print(f"Rows: {len(audit_rows)}")
    print(f"CSV: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
