import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
POI_INPUT = BASE_DIR / "data" / "clean" / "poi_final.csv"
BASELINE_INPUT = BASE_DIR / "zone_summary.csv"
OUTPUT_PATH = BASE_DIR / "data" / "clean" / "zone_summary_final.csv"

TARGET_ZONES = ["Depok", "Mlati", "Gamping", "Ngaglik Selatan"]

OUTPUT_COLUMNS = [
    "zone",
    "population",
    "density_per_km2",
    "school_note",
    "data_year",
    "baseline_confidence",
    "baseline_notes",
    "direct_kebab_competitor_count",
    "fast_food_count",
    "restaurant_count",
    "cafe_count",
    "food_court_count",
    "culinary_activity_count",
    "university_count",
    "college_count",
    "school_count",
    "education_count",
    "hotel_count",
    "guest_house_count",
    "hostel_count",
    "accommodation_count",
    "retail_count",
    "marketplace_count",
    "total_poi_count",
    "zone_counting_method",
]


def load_csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_zone_memberships(zone_value: str) -> list[str]:
    parts = [part.strip() for part in (zone_value or "").split("/") if part.strip()]
    normalized = [part for part in parts if part in TARGET_ZONES]
    if normalized:
        return normalized[:1]
    return []


def count_zone_metrics(poi_rows: list[dict]) -> dict:
    zone_metrics = {
        zone: {
            "direct_kebab_competitor_count": 0,
            "fast_food_count": 0,
            "restaurant_count": 0,
            "cafe_count": 0,
            "food_court_count": 0,
            "university_count": 0,
            "college_count": 0,
            "school_count": 0,
            "hotel_count": 0,
            "guest_house_count": 0,
            "hostel_count": 0,
            "retail_count": 0,
            "marketplace_count": 0,
            "total_poi_count": 0,
        }
        for zone in TARGET_ZONES
    }

    tracked_categories = {
        "direct_kebab_competitor": "direct_kebab_competitor_count",
        "fast_food": "fast_food_count",
        "restaurant": "restaurant_count",
        "cafe": "cafe_count",
        "food_court": "food_court_count",
        "university": "university_count",
        "college": "college_count",
        "school": "school_count",
        "hotel": "hotel_count",
        "guest_house": "guest_house_count",
        "hostel": "hostel_count",
        "retail": "retail_count",
        "marketplace": "marketplace_count",
    }

    for row in poi_rows:
        zones = parse_zone_memberships(row.get("zone", ""))
        if not zones:
            continue

        category = row.get("category", "")
        for zone in zones:
            zone_metrics[zone]["total_poi_count"] += 1
            if category in tracked_categories:
                zone_metrics[zone][tracked_categories[category]] += 1

    for zone in TARGET_ZONES:
        metrics = zone_metrics[zone]
        metrics["culinary_activity_count"] = (
            metrics["fast_food_count"]
            + metrics["restaurant_count"]
            + metrics["cafe_count"]
            + metrics["food_court_count"]
        )
        metrics["education_count"] = (
            metrics["university_count"]
            + metrics["college_count"]
            + metrics["school_count"]
        )
        metrics["accommodation_count"] = (
            metrics["hotel_count"]
            + metrics["guest_house_count"]
            + metrics["hostel_count"]
        )

    return zone_metrics


def merge_with_baseline(baseline_rows: list[dict], zone_metrics: dict) -> list[dict]:
    baseline_by_zone = {row["zone"]: row for row in baseline_rows}
    final_rows = []

    for zone in TARGET_ZONES:
        baseline = baseline_by_zone.get(zone, {})
        metrics = zone_metrics[zone]
        final_rows.append(
            {
                "zone": zone,
                "population": baseline.get("population", ""),
                "density_per_km2": baseline.get("density_per_km2", ""),
                "school_note": baseline.get("school_note", ""),
                "data_year": baseline.get("data_year", ""),
                "baseline_confidence": baseline.get("confidence", ""),
                "baseline_notes": baseline.get("notes", ""),
                **metrics,
                "zone_counting_method": "POI counted by single primary zone from poi_final.csv",
            }
        )

    return final_rows


def write_output(rows: list[dict]) -> None:
    # Write to clean path
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in OUTPUT_COLUMNS})
            
    # Also write to root directory path
    root_path = BASE_DIR / "zone_summary.csv"
    with root_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in OUTPUT_COLUMNS})


def main() -> None:
    poi_rows = load_csv_rows(POI_INPUT)
    baseline_rows = load_csv_rows(BASELINE_INPUT)
    zone_metrics = count_zone_metrics(poi_rows)
    final_rows = merge_with_baseline(baseline_rows, zone_metrics)
    write_output(final_rows)

    print("Generate zone summary selesai.")
    print(f"Input POI rows: {len(poi_rows)}")
    print(f"Output zones: {len(final_rows)}")
    print(f"CSV: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
