import csv
import json
import re
from pathlib import Path


BASE = Path(__file__).resolve().parent
RAW_PATTERN = "overpass_raw_*.json"
BASELINE_FILE = BASE / "poi_baseline.csv"
RAW_OUTPUT = BASE / "poi_raw.csv"
CLEAN_OUTPUT = BASE / "poi_clean.csv"
COMBINED_OUTPUT = BASE / "overpass_raw_combined.json"

RAW_FIELDNAMES = [
    "poi_id",
    "name",
    "category",
    "zone",
    "latitude",
    "longitude",
    "address",
    "source",
    "confidence",
    "notes",
    "record_origin",
    "osm_type",
    "osm_id",
    "osm_primary_key",
    "osm_primary_value",
    "zone_matches",
    "matched_baseline_poi_id",
]

CLEAN_FIELDNAMES = [
    "poi_id",
    "name",
    "category",
    "zone",
    "latitude",
    "longitude",
    "address",
    "source",
    "confidence",
    "notes",
]


def normalize_name(value: str) -> str:
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def choose_primary_tag(tags: dict) -> tuple[str, str]:
    for key in ("amenity", "shop", "tourism", "cuisine"):
        if tags.get(key):
            return key, tags[key]
    return "unknown", ""


def map_category(tags: dict) -> str:
    haystack = " ".join(str(v) for v in tags.values()).lower()
    if any(token in haystack for token in ("kebab", "kabab", "kebap", "shawarma")):
        return "direct_kebab_competitor"

    amenity = tags.get("amenity", "")
    shop = tags.get("shop", "")
    tourism = tags.get("tourism", "")

    amenity_mapping = {
        "university": "university",
        "college": "college",
        "school": "school",
        "fast_food": "fast_food",
        "restaurant": "restaurant",
        "cafe": "cafe",
        "food_court": "food_court",
        "marketplace": "marketplace",
    }
    if amenity in amenity_mapping:
        return amenity_mapping[amenity]

    shop_mapping = {
        "convenience": "minimarket",
        "supermarket": "minimarket",
        "mall": "mall/titik_keramaian",
    }
    if shop in shop_mapping:
        return shop_mapping[shop]

    tourism_mapping = {
        "hotel": "lodging",
        "guest_house": "lodging",
        "hostel": "lodging",
    }
    if tourism in tourism_mapping:
        return tourism_mapping[tourism]

    return "osm_other"


def get_lat_lon(element: dict) -> tuple[str, str]:
    if "lat" in element and "lon" in element:
        return str(element["lat"]), str(element["lon"])

    center = element.get("center") or {}
    if "lat" in center and "lon" in center:
        return str(center["lat"]), str(center["lon"])

    return "", ""


def build_address(tags: dict) -> str:
    if tags.get("addr:full"):
        return tags["addr:full"]

    parts = []
    for key in ("addr:street", "addr:housenumber", "addr:suburb", "addr:city"):
        if tags.get(key):
            parts.append(str(tags[key]))
    return ", ".join(parts)


def build_notes(tags: dict, primary_key: str, primary_value: str, zone_matches: str) -> str:
    tag_bits = []
    for key in ("brand", "cuisine", "opening_hours", "operator"):
        if tags.get(key):
            tag_bits.append(f"{key}={tags[key]}")

    note = f"OSM {primary_key}={primary_value}; zone query match: {zone_matches}."
    if tag_bits:
        note += " " + "; ".join(tag_bits)
    return note


def confidence_from_record(name: str, category: str) -> str:
    if category == "direct_kebab_competitor" and name:
        return "medium-high"
    if name:
        return "medium"
    return "low"


def load_osm_records() -> list[dict]:
    records_by_key = {}

    for path in sorted(BASE.glob(RAW_PATTERN)):
        if path.name == COMBINED_OUTPUT.name:
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for element in payload.get("elements", []):
            key = f"{element.get('type')}:{element.get('id')}"
            tags = element.get("tags") or {}
            zone_name = element.get("zone_name_query") or path.stem.replace("overpass_raw_", "").replace("_", " ").title()
            zone_name = zone_name.replace("Ngaglik Selatan", "Ngaglik Selatan")

            current = records_by_key.setdefault(
                key,
                {
                    "element": element,
                    "tags": tags,
                    "zone_names": set(),
                },
            )
            current["zone_names"].add(zone_name)

    normalized = []
    for index, (key, item) in enumerate(sorted(records_by_key.items()), start=1):
        element = item["element"]
        tags = item["tags"]
        name = tags.get("name", "").strip()
        category = map_category(tags)
        lat, lon = get_lat_lon(element)
        primary_key, primary_value = choose_primary_tag(tags)
        zones = sorted(item["zone_names"])
        zone_label = "/".join(zones)
        record = {
            "poi_id": f"OSM-{index:04d}",
            "name": name,
            "category": category,
            "zone": zone_label,
            "latitude": lat,
            "longitude": lon,
            "address": build_address(tags),
            "source": "OpenStreetMap Overpass",
            "confidence": confidence_from_record(name, category),
            "notes": build_notes(tags, primary_key, primary_value, zone_label),
            "record_origin": "osm",
            "osm_type": element.get("type", ""),
            "osm_id": str(element.get("id", "")),
            "osm_primary_key": primary_key,
            "osm_primary_value": primary_value,
            "zone_matches": zone_label,
            "matched_baseline_poi_id": "",
        }
        normalized.append(record)

    combined = {"elements": []}
    for item in sorted(records_by_key.values(), key=lambda entry: (entry["element"].get("type", ""), entry["element"].get("id", 0))):
        element = dict(item["element"])
        element["zone_name_query"] = sorted(item["zone_names"])
        combined["elements"].append(element)
    COMBINED_OUTPUT.write_text(json.dumps(combined, ensure_ascii=False, indent=2), encoding="utf-8")

    return normalized


def load_baseline_records() -> list[dict]:
    with BASELINE_FILE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def enrich_baseline(baseline_rows: list[dict], osm_rows: list[dict]) -> tuple[list[dict], set[str]]:
    osm_by_name = {}
    for row in osm_rows:
        key = normalize_name(row["name"])
        if key:
            osm_by_name.setdefault(key, []).append(row)

    used_osm_keys = set()
    enriched = []

    for row in baseline_rows:
        merged = dict(row)
        merged["record_origin"] = "baseline"
        merged["matched_baseline_poi_id"] = row["poi_id"]
        key = normalize_name(row["name"])
        matches = osm_by_name.get(key, [])

        best_match = None
        for candidate in matches:
            if candidate["category"] == row["category"] or row["category"] in candidate["category"] or candidate["category"] in row["category"]:
                best_match = candidate
                break
        if best_match is None and matches:
            best_match = matches[0]

        if best_match:
            osm_key = f"{best_match['osm_type']}:{best_match['osm_id']}"
            used_osm_keys.add(osm_key)
            if best_match["latitude"] and best_match["longitude"]:
                merged["latitude"] = best_match["latitude"]
                merged["longitude"] = best_match["longitude"]
            if not merged.get("address") and best_match["address"]:
                merged["address"] = best_match["address"]
            merged["source"] = f"{row['source']} + {best_match['source']}"
            merged["confidence"] = "medium" if row["confidence"] == "low" else row["confidence"]
            merged["notes"] = f"{row['notes']} | Matched OSM {best_match['osm_type']}:{best_match['osm_id']}."

        enriched.append(merged)

    return enriched, used_osm_keys


def row_has_useful_name(row: dict) -> bool:
    return bool(normalize_name(row["name"]))


def row_is_clean_candidate(row: dict) -> bool:
    if row["record_origin"] == "baseline":
        return True
    if row["category"] == "osm_other":
        return False
    return row_has_useful_name(row)


def dedupe_clean_rows(rows: list[dict]) -> list[dict]:
    deduped = {}
    for row in rows:
        key = (
            normalize_name(row["name"]),
            row["category"],
            row["zone"],
            round(float(row["latitude"]), 6) if row["latitude"] else "",
            round(float(row["longitude"]), 6) if row["longitude"] else "",
        )
        deduped.setdefault(key, row)
    return list(deduped.values())


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def main():
    osm_rows = load_osm_records()
    baseline_rows = load_baseline_records()
    enriched_baseline, used_osm_keys = enrich_baseline(baseline_rows, osm_rows)

    raw_rows = []
    for row in enriched_baseline:
        raw_rows.append({**row, "osm_type": "", "osm_id": "", "osm_primary_key": "", "osm_primary_value": "", "zone_matches": row["zone"]})

    for row in osm_rows:
        osm_key = f"{row['osm_type']}:{row['osm_id']}"
        row_copy = dict(row)
        if osm_key in used_osm_keys:
            row_copy["matched_baseline_poi_id"] = next(
                (baseline["poi_id"] for baseline in baseline_rows if normalize_name(baseline["name"]) == normalize_name(row["name"])),
                "",
            )
        raw_rows.append(row_copy)

    clean_rows = list(enriched_baseline)
    for row in osm_rows:
        osm_key = f"{row['osm_type']}:{row['osm_id']}"
        if osm_key in used_osm_keys:
            continue
        if row_is_clean_candidate(row):
            clean_rows.append(
                {
                    "poi_id": row["poi_id"],
                    "name": row["name"],
                    "category": row["category"],
                    "zone": row["zone"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "address": row["address"],
                    "source": row["source"],
                    "confidence": row["confidence"],
                    "notes": row["notes"],
                }
            )

    clean_rows = dedupe_clean_rows(clean_rows)

    write_csv(RAW_OUTPUT, RAW_FIELDNAMES, raw_rows)
    write_csv(CLEAN_OUTPUT, CLEAN_FIELDNAMES, clean_rows)

    print(f"OSM normalized rows: {len(osm_rows)}")
    print(f"Baseline rows: {len(baseline_rows)}")
    print(f"poi_raw.csv rows written: {len(raw_rows)}")
    print(f"poi_clean.csv rows written: {len(clean_rows)}")


if __name__ == "__main__":
    main()
