import csv
import difflib
import json
import math
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
BASELINE_INPUT = BASE_DIR / "poi_baseline.csv"
OSM_INPUT = BASE_DIR / "data" / "clean" / "poi_osm_clean.csv"
OUTPUT_DIR = BASE_DIR / "data" / "clean"
CSV_OUTPUT = OUTPUT_DIR / "poi_final.csv"
JSON_OUTPUT = OUTPUT_DIR / "poi_final.json"
GEOJSON_OUTPUT = OUTPUT_DIR / "poi_final.geojson"
MATCH_DISTANCE_METERS = 120
FUZZY_MATCH_DISTANCE_METERS = 800

ZONE_BBOXES = {
    "Depok": {"south": -7.805, "west": 110.355, "north": -7.715, "east": 110.47},
    "Mlati": {"south": -7.795, "west": 110.315, "north": -7.69, "east": 110.39},
    "Gamping": {"south": -7.84, "west": 110.27, "north": -7.735, "east": 110.35},
    "Ngaglik Selatan": {"south": -7.745, "west": 110.355, "north": -7.675, "east": 110.435},
}

OUTPUT_COLUMNS = [
    "poi_id",
    "name",
    "name_clean",
    "category",
    "zone",
    "latitude",
    "longitude",
    "address",
    "source",
    "source_url",
    "confidence",
    "notes",
    "record_origin",
    "validation_status",
    "match_method",
    "osm_type",
    "osm_id",
    "extracted_at",
]

TRUSTED_BASELINE_SOURCES = {
    "GoFood/public listing",
    "Facebook public post",
    "Instagram public",
    "Waze/public map",
    "Corner/Google Maps coordinate",
    "public listing",
    "public web",
    "public/BPS context",
}


def load_csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_name(value: str) -> str:
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


def point_in_bbox(lat: float, lon: float, bbox: dict) -> bool:
    return bbox["south"] <= lat <= bbox["north"] and bbox["west"] <= lon <= bbox["east"]


def bbox_center(bbox: dict) -> tuple[float, float]:
    return ((bbox["south"] + bbox["north"]) / 2, (bbox["west"] + bbox["east"]) / 2)


def assign_primary_zone(zone_value: str, latitude: str, longitude: str) -> str:
    if latitude and longitude:
        lat = float(latitude)
        lon = float(longitude)
        matched_zones = [zone for zone, bbox in ZONE_BBOXES.items() if point_in_bbox(lat, lon, bbox)]
        if len(matched_zones) == 1:
            return matched_zones[0]
        if len(matched_zones) > 1:
            return min(
                matched_zones,
                key=lambda zone: haversine_meters(lat, lon, bbox_center(ZONE_BBOXES[zone])[0], bbox_center(ZONE_BBOXES[zone])[1]),
            )

    parts = [part.strip() for part in (zone_value or "").split("/") if part.strip()]
    for part in parts:
        if part in ZONE_BBOXES or part == "External/Ponorogo":
            return part
    return zone_value or "Unknown"


def similarity_ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, a, b).ratio()


def category_family(category: str) -> str:
    category = category or ""
    if "direct_kebab_competitor" in category:
        return "direct_kebab_competitor"
    if category in {"retail", "marketplace", "mall/titik_keramaian", "transport/titik_keramaian"}:
        return "activity_support"
    return category


def token_overlap_count(a: str, b: str) -> int:
    return len(set(a.split()) & set(b.split()))


def standardize_baseline_row(row: dict) -> dict:
    original_zone = row.get("zone", "")
    should_normalize_zone = not original_zone or "/" in original_zone
    assigned_zone = assign_primary_zone(original_zone, row.get("latitude", ""), row.get("longitude", "")) if should_normalize_zone else original_zone
    return {
        "poi_id": row.get("poi_id", ""),
        "name": row.get("name", ""),
        "name_clean": normalize_name(row.get("name", "")),
        "category": row.get("category", "") or "other",
        "zone": assigned_zone or "Unknown",
        "latitude": row.get("latitude", ""),
        "longitude": row.get("longitude", ""),
        "address": row.get("address", ""),
        "source": row.get("source", ""),
        "source_url": "",
        "confidence": row.get("confidence", ""),
        "notes": row.get("notes", "") if assigned_zone == original_zone else f"{row.get('notes', '')} | Zone normalized from {original_zone} to {assigned_zone}.",
        "record_origin": "baseline",
        "validation_status": baseline_validation_status(row),
        "match_method": "baseline_reference",
        "osm_type": "",
        "osm_id": "",
        "extracted_at": "",
    }


def standardize_osm_row(row: dict) -> dict:
    original_zone = row.get("zone", "")
    assigned_zone = assign_primary_zone(original_zone, row.get("latitude", ""), row.get("longitude", ""))
    return {
        "poi_id": row.get("poi_id", ""),
        "name": row.get("name", ""),
        "name_clean": row.get("name_clean", normalize_name(row.get("name", ""))),
        "category": row.get("category", "") or "other",
        "zone": assigned_zone or "Unknown",
        "latitude": row.get("latitude", ""),
        "longitude": row.get("longitude", ""),
        "address": "",
        "source": row.get("source", ""),
        "source_url": row.get("source_url", ""),
        "confidence": row.get("confidence", ""),
        "notes": (
            f"subcategory={row.get('subcategory', '')}; flags: direct={row.get('is_direct_competitor', '')}, "
            f"food={row.get('is_food_alternative', '')}, demand={row.get('is_demand_point', '')}, support={row.get('is_supporting_facility', '')}"
            + (f"; zone normalized from {original_zone} to {assigned_zone}" if assigned_zone != original_zone else "")
        ),
        "record_origin": "osm",
        "validation_status": "osm_only",
        "match_method": "osm_only",
        "osm_type": row.get("osm_type", ""),
        "osm_id": row.get("osm_id", ""),
        "extracted_at": row.get("extracted_at", ""),
    }


def baseline_validation_status(row: dict) -> str:
    source = (row.get("source") or "").strip()
    confidence = (row.get("confidence") or "").strip().lower()
    if confidence in {"medium", "medium-high", "high"}:
        return "verified_baseline_only"
    if source in TRUSTED_BASELINE_SOURCES:
        return "verified_baseline_only"
    return "needs_manual_validation"


def row_match_method(baseline: dict, osm_row: dict) -> str:
    if not baseline["name_clean"] or not osm_row["name_clean"]:
        return ""

    baseline_family = category_family(baseline["category"])
    osm_family = category_family(osm_row["category"])

    if baseline_family != osm_family:
        return ""

    ratio = similarity_ratio(baseline["name_clean"], osm_row["name_clean"])
    overlap = token_overlap_count(baseline["name_clean"], osm_row["name_clean"])
    exact_or_close_name = baseline["name_clean"] == osm_row["name_clean"] or ratio >= 0.78

    if baseline["latitude"] and osm_row["latitude"]:
        distance = haversine_meters(
            float(baseline["latitude"]),
            float(baseline["longitude"]),
            float(osm_row["latitude"]),
            float(osm_row["longitude"]),
        )
        if exact_or_close_name and distance <= MATCH_DISTANCE_METERS:
            return "name_and_distance_strict"
        if baseline_family == "activity_support" and overlap >= 2 and ratio >= 0.72 and distance <= 1000:
            return "activity_support_fuzzy"
        if baseline_family == "direct_kebab_competitor" and overlap >= 1 and ratio >= 0.72 and distance <= 5000:
            return "direct_competitor_fuzzy"
        if ratio >= 0.62 and distance <= FUZZY_MATCH_DISTANCE_METERS:
            return "name_distance_loose"
    elif exact_or_close_name:
        return "name_only"

    return ""


def enrich_baseline_with_osm(baseline_rows: list[dict], osm_rows: list[dict]) -> tuple[list[dict], set[str]]:
    matched_osm_ids = set()
    enriched_rows = []

    for baseline in baseline_rows:
        merged = dict(baseline)
        for osm_row in osm_rows:
            osm_key = f"{osm_row['osm_type']}:{osm_row['osm_id']}"
            if osm_key in matched_osm_ids:
                continue
            match_method = row_match_method(baseline, osm_row)
            if match_method:
                matched_osm_ids.add(osm_key)
                if osm_row["latitude"] and osm_row["longitude"]:
                    merged["latitude"] = osm_row["latitude"]
                    merged["longitude"] = osm_row["longitude"]
                if not merged["address"] and osm_row["address"]:
                    merged["address"] = osm_row["address"]
                merged["source"] = f"{baseline['source']} + {osm_row['source']}"
                merged["source_url"] = osm_row["source_url"]
                merged["confidence"] = "medium" if merged["confidence"] == "low" else merged["confidence"]
                merged["notes"] = f"{baseline['notes']} | Matched OSM {osm_key}."
                merged["validation_status"] = "matched_osm"
                merged["match_method"] = match_method
                merged["osm_type"] = osm_row["osm_type"]
                merged["osm_id"] = osm_row["osm_id"]
                merged["extracted_at"] = osm_row["extracted_at"]
                # Keep baseline zone if it is already a single valid zone (e.g. "Mlati")
                original_zone = baseline.get("zone", "")
                if not original_zone or "/" in original_zone:
                    merged["zone"] = assign_primary_zone(merged["zone"], merged["latitude"], merged["longitude"])
                break
        enriched_rows.append(merged)

    return enriched_rows, matched_osm_ids


def dedupe_final_rows(rows: list[dict]) -> list[dict]:
    deduped = []
    for row in rows:
        duplicate = False
        for existing in deduped:
            if row["name_clean"] and row["name_clean"] == existing["name_clean"] and row["category"] == existing["category"]:
                if row["latitude"] and existing["latitude"]:
                    distance = haversine_meters(
                        float(row["latitude"]),
                        float(row["longitude"]),
                        float(existing["latitude"]),
                        float(existing["longitude"]),
                    )
                    if distance <= MATCH_DISTANCE_METERS:
                        duplicate = True
                        break
                elif row["zone"] == existing["zone"]:
                    duplicate = True
                    break
        if not duplicate:
            deduped.append(row)
    return deduped


def write_csv(rows: list[dict]) -> None:
    with CSV_OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in OUTPUT_COLUMNS})


def write_json(rows: list[dict], summary: dict) -> None:
    payload = {
        "summary": summary,
        "records": rows,
    }
    JSON_OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_geojson(rows: list[dict]) -> None:
    features = []
    for row in rows:
        if not row["latitude"] or not row["longitude"]:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(row["longitude"]), float(row["latitude"])],
                },
                "properties": {column: row.get(column, "") for column in OUTPUT_COLUMNS if column not in {"latitude", "longitude"}},
            }
        )
    GEOJSON_OUTPUT.write_text(json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    baseline_rows = [standardize_baseline_row(row) for row in load_csv_rows(BASELINE_INPUT)]
    osm_rows = [standardize_osm_row(row) for row in load_csv_rows(OSM_INPUT)]

    enriched_baseline, matched_osm_ids = enrich_baseline_with_osm(baseline_rows, osm_rows)

    final_rows = list(enriched_baseline)
    for osm_row in osm_rows:
        osm_key = f"{osm_row['osm_type']}:{osm_row['osm_id']}"
        if osm_key in matched_osm_ids:
            continue
        if not osm_row["category"] or not osm_row["zone"]:
            continue
        final_rows.append(osm_row)

    final_rows = dedupe_final_rows(final_rows)
    write_csv(final_rows)
    write_json(
        final_rows,
        {
            "baseline_count": len(baseline_rows),
            "osm_clean_count": len(osm_rows),
            "matched_osm_count": len(matched_osm_ids),
            "verified_baseline_only_count": sum(1 for row in enriched_baseline if row.get("validation_status") == "verified_baseline_only"),
            "needs_manual_validation_count": sum(1 for row in enriched_baseline if row.get("validation_status") == "needs_manual_validation"),
            "final_count": len(final_rows),
        },
    )
    write_geojson(final_rows)

    print("Merge data selesai.")
    print(f"Baseline count: {len(baseline_rows)}")
    print(f"OSM clean count: {len(osm_rows)}")
    print(f"Matched OSM rows: {len(matched_osm_ids)}")
    print(f"Final POI rows: {len(final_rows)}")
    print(f"CSV: {CSV_OUTPUT}")
    print(f"JSON: {JSON_OUTPUT}")
    print(f"GeoJSON: {GEOJSON_OUTPUT}")


if __name__ == "__main__":
    main()
