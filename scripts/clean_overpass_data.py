import csv
import json
import math
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "raw" / "overpass_raw_combined.json"
OUTPUT_DIR = BASE_DIR / "data" / "clean"
CSV_OUTPUT_PATH = OUTPUT_DIR / "poi_osm_clean.csv"
JSON_OUTPUT_PATH = OUTPUT_DIR / "poi_osm_clean.json"
GEOJSON_OUTPUT_PATH = OUTPUT_DIR / "poi_osm_clean.geojson"
DEDUP_DISTANCE_METERS = 30

OUTPUT_COLUMNS = [
    "poi_id",
    "osm_type",
    "osm_id",
    "name",
    "name_clean",
    "category",
    "subcategory",
    "zone",
    "latitude",
    "longitude",
    "amenity",
    "tourism",
    "shop",
    "cuisine",
    "opening_hours",
    "phone",
    "website",
    "source",
    "source_url",
    "extracted_at",
    "raw_tags",
    "is_direct_competitor",
    "is_food_alternative",
    "is_demand_point",
    "is_supporting_facility",
]


def load_combined_payload() -> dict:
    with INPUT_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def normalize_name(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"\s+", " ", value)
    return value


def get_coordinates(element: dict) -> tuple[str, str]:
    if "lat" in element and "lon" in element:
        return str(element["lat"]), str(element["lon"])

    center = element.get("center") or {}
    if "lat" in center and "lon" in center:
        return str(center["lat"]), str(center["lon"])

    return "", ""


def determine_category(tags: dict) -> tuple[str, str]:
    name_text = str(tags.get("name", "")).lower()
    cuisine_text = str(tags.get("cuisine", "")).lower()
    combined_text = f"{name_text} {cuisine_text}"

    if any(keyword in combined_text for keyword in ("kebab", "kabab", "kebap", "shawarma")):
        return "direct_kebab_competitor", "keyword_match"

    amenity = tags.get("amenity", "")
    tourism = tags.get("tourism", "")
    shop = tags.get("shop", "")

    amenity_map = {
        "fast_food": "fast_food",
        "restaurant": "restaurant",
        "cafe": "cafe",
        "food_court": "food_court",
        "university": "university",
        "college": "college",
        "school": "school",
        "marketplace": "marketplace",
    }
    if amenity in amenity_map:
        return amenity_map[amenity], f"amenity:{amenity}"

    tourism_map = {
        "hotel": "hotel",
        "guest_house": "guest_house",
        "hostel": "hostel",
    }
    if tourism in tourism_map:
        return tourism_map[tourism], f"tourism:{tourism}"

    if shop in {"convenience", "supermarket", "mall"}:
        return "retail", f"shop:{shop}"

    return "other", "unmapped"


def derive_flags(category: str) -> dict:
    return {
        "is_direct_competitor": "true" if category == "direct_kebab_competitor" else "false",
        "is_food_alternative": "true" if category in {"fast_food", "restaurant", "cafe", "food_court", "direct_kebab_competitor"} else "false",
        "is_demand_point": "true" if category in {"university", "college", "school"} else "false",
        "is_supporting_facility": "true" if category in {"hotel", "guest_house", "hostel", "retail", "marketplace"} else "false",
    }


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    return 2 * radius * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def dedupe_by_osm_id(records: list[dict]) -> list[dict]:
    grouped = {}
    for record in records:
        key = (record["osm_type"], record["osm_id"])
        grouped.setdefault(key, []).append(record)

    deduped = []
    for group in grouped.values():
        primary = dict(group[0])
        zones = sorted({item["zone"] for item in group if item["zone"]})
        if zones:
            primary["zone"] = "/".join(zones)
        extracted_times = sorted({item["extracted_at"] for item in group if item["extracted_at"]})
        if extracted_times:
            primary["extracted_at"] = extracted_times[-1]
        deduped.append(primary)
    return deduped


def dedupe_nearby(records: list[dict]) -> list[dict]:
    kept = []
    for record in records:
        if not record["name_clean"]:
            kept.append(record)
            continue

        is_duplicate = False
        for existing in kept:
            if record["name_clean"] != existing["name_clean"]:
                continue
            if record["category"] != existing["category"]:
                continue
            if not record["latitude"] or not existing["latitude"]:
                continue

            distance = haversine_meters(
                float(record["latitude"]),
                float(record["longitude"]),
                float(existing["latitude"]),
                float(existing["longitude"]),
            )
            if distance <= DEDUP_DISTANCE_METERS:
                is_duplicate = True
                break

        if not is_duplicate:
            kept.append(record)
    return kept


def build_clean_records(payload: dict) -> tuple[list[dict], dict]:
    raw_elements = payload.get("elements", [])
    without_coordinates = 0
    prepared_records = []

    for element in raw_elements:
        latitude, longitude = get_coordinates(element)
        if not latitude or not longitude:
            without_coordinates += 1
            continue

        tags = element.get("tags") or {}
        category, subcategory = determine_category(tags)
        flags = derive_flags(category)
        record = {
            "poi_id": "",
            "osm_type": element.get("type", ""),
            "osm_id": str(element.get("id", "")),
            "name": tags.get("name", "").strip(),
            "name_clean": normalize_name(tags.get("name", "")),
            "category": category,
            "subcategory": subcategory,
            "zone": element.get("zone_name_query", ""),
            "latitude": latitude,
            "longitude": longitude,
            "amenity": tags.get("amenity", ""),
            "tourism": tags.get("tourism", ""),
            "shop": tags.get("shop", ""),
            "cuisine": tags.get("cuisine", ""),
            "opening_hours": tags.get("opening_hours", ""),
            "phone": tags.get("phone", "") or tags.get("contact:phone", ""),
            "website": tags.get("website", "") or tags.get("contact:website", ""),
            "source": element.get("source", payload.get("source", "OpenStreetMap Overpass")),
            "source_url": element.get("source_url", ""),
            "extracted_at": element.get("extracted_at", payload.get("extracted_at", "")),
            "raw_tags": json.dumps(tags, ensure_ascii=False, sort_keys=True),
            **flags,
        }
        prepared_records.append(record)

    deduped_by_id = dedupe_by_osm_id(prepared_records)
    final_records = dedupe_nearby(deduped_by_id)

    for index, record in enumerate(final_records, start=1):
        record["poi_id"] = f"OSM-{index:04d}"

    summary = {
        "raw_elements": len(raw_elements),
        "dropped_without_coordinates": without_coordinates,
        "after_osm_id_dedup": len(deduped_by_id),
        "final_records": len(final_records),
    }
    return final_records, summary


def write_csv(records: list[dict]) -> None:
    with CSV_OUTPUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for record in records:
            writer.writerow({column: record.get(column, "") for column in OUTPUT_COLUMNS})


def write_json(records: list[dict], summary: dict) -> None:
    payload = {
        "source": "OpenStreetMap Overpass",
        "generated_from": str(INPUT_PATH.relative_to(BASE_DIR)),
        "summary": summary,
        "records": records,
    }
    JSON_OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def write_geojson(records: list[dict]) -> None:
    features = []
    for record in records:
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [float(record["longitude"]), float(record["latitude"])],
            },
            "properties": {column: record.get(column, "") for column in OUTPUT_COLUMNS if column not in {"latitude", "longitude"}},
        }
        features.append(feature)

    geojson = {"type": "FeatureCollection", "features": features}
    GEOJSON_OUTPUT_PATH.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = load_combined_payload()
    records, summary = build_clean_records(payload)
    write_csv(records)
    write_json(records, summary)
    write_geojson(records)

    print("Cleaning Overpass selesai.")
    print(f"Raw elements: {summary['raw_elements']}")
    print(f"Dropped without coordinates: {summary['dropped_without_coordinates']}")
    print(f"After OSM ID dedup: {summary['after_osm_id_dedup']}")
    print(f"Final clean records: {summary['final_records']}")
    print(f"CSV: {CSV_OUTPUT_PATH}")
    print(f"JSON: {JSON_OUTPUT_PATH}")
    print(f"GeoJSON: {GEOJSON_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
