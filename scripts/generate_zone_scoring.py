import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "clean" / "zone_summary_final.csv"
OUTPUT_PATH = BASE_DIR / "data" / "clean" / "zone_scoring_final.csv"

NUMERIC_COLUMNS = [
    "population",
    "education_count",
    "retail_count",
    "culinary_activity_count",
    "direct_kebab_competitor_count",
    "accommodation_count",
    "marketplace_count",
    "total_poi_count",
]

OUTPUT_COLUMNS = [
    "zone",
    "target_market_score",
    "culinary_activity_score",
    "low_competition_score",
    "supporting_area_score",
    "opportunity_score",
    "threat_score",
    "business_potential_score",
    "rank",
    "insight",
]


def load_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def to_float(value: str) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def power_ratio_score(value: float, all_values: list[float], exponent: float = 0.65) -> float:
    maximum = max(all_values) if all_values else 0.0
    if maximum <= 0:
        return 0.0
    return round((value / maximum) ** exponent * 100, 2)


def inverse_power_ratio_score(value: float, all_values: list[float], exponent: float = 0.7) -> float:
    maximum = max(all_values) if all_values else 0.0
    if maximum <= 0:
        return 100.0
    ratio = clamp(1 - (value / maximum), 0.0, 1.0)
    return round((ratio ** exponent) * 100, 2)


def build_metric_vectors(rows: list[dict]) -> dict:
    vectors = {column: [] for column in NUMERIC_COLUMNS}
    vectors["poi_intensity_per_10k"] = []
    vectors["culinary_share"] = []
    vectors["competitor_share"] = []

    for row in rows:
        population = to_float(row.get("population", ""))
        total_poi = to_float(row.get("total_poi_count", ""))
        culinary = to_float(row.get("culinary_activity_count", ""))
        competitors = to_float(row.get("direct_kebab_competitor_count", ""))

        for column in NUMERIC_COLUMNS:
            vectors[column].append(to_float(row.get(column, "")))

        poi_intensity = (total_poi / population * 10000) if population > 0 else 0.0
        culinary_share = (culinary / total_poi) if total_poi > 0 else 0.0
        competitor_share = (competitors / culinary) if culinary > 0 else competitors

        vectors["poi_intensity_per_10k"].append(poi_intensity)
        vectors["culinary_share"].append(culinary_share)
        vectors["competitor_share"].append(competitor_share)

    return vectors


def build_insight(
    target_score: float,
    threat_score: float,
    low_competition_score: float,
    support_score: float,
    business_score: float,
) -> str:
    if business_score >= 70 and threat_score <= 45:
        return "Zona sangat siap untuk ekspansi karena intensity pasar tinggi, area pendukung kuat, dan tekanan kompetisi masih terkendali."
    if business_score >= 65 and threat_score > 45:
        return "Zona kuat untuk ekspansi, tetapi perlu diferensiasi harga, menu, dan lokasi mikro karena tekanan pasar juga tinggi."
    if low_competition_score >= 75 and support_score >= 45:
        return "Zona menarik untuk uji pasar bertahap karena kompetitor relatif ringan dan fasilitas pendukung sudah cukup terbentuk."
    if target_score >= 55 and threat_score >= 60:
        return "Pasarnya aktif, namun ancaman kompetisi dan saturasi kuliner cukup tinggi sehingga masuknya harus lebih selektif."
    return "Zona layak dipantau, namun masih butuh validasi lapangan atau eksperimen penjualan ringan sebelum dijadikan prioritas utama."


def generate_scores(rows: list[dict]) -> list[dict]:
    vectors = build_metric_vectors(rows)
    scored_rows = []

    for index, row in enumerate(rows):
        population = to_float(row.get("population", ""))
        education = to_float(row.get("education_count", ""))
        retail = to_float(row.get("retail_count", ""))
        culinary = to_float(row.get("culinary_activity_count", ""))
        competitors = to_float(row.get("direct_kebab_competitor_count", ""))
        accommodation = to_float(row.get("accommodation_count", ""))
        marketplace = to_float(row.get("marketplace_count", ""))
        total_poi = to_float(row.get("total_poi_count", ""))

        poi_intensity = vectors["poi_intensity_per_10k"][index]
        culinary_share = vectors["culinary_share"][index]
        competitor_share = vectors["competitor_share"][index]

        population_score = power_ratio_score(population, vectors["population"])
        education_score = power_ratio_score(education, vectors["education_count"])
        retail_score = power_ratio_score(retail, vectors["retail_count"])
        poi_intensity_score = power_ratio_score(poi_intensity, vectors["poi_intensity_per_10k"])
        target_market_score = round(
            (population_score * 0.30)
            + (education_score * 0.30)
            + (retail_score * 0.15)
            + (poi_intensity_score * 0.25),
            2,
        )

        culinary_count_score = power_ratio_score(culinary, vectors["culinary_activity_count"])
        culinary_share_score = power_ratio_score(culinary_share, vectors["culinary_share"])
        culinary_activity_score = round((culinary_count_score * 0.75) + (culinary_share_score * 0.25), 2)

        competitor_count_inverse = inverse_power_ratio_score(competitors, vectors["direct_kebab_competitor_count"])
        competitor_share_inverse = inverse_power_ratio_score(competitor_share, vectors["competitor_share"])
        low_competition_score = round((competitor_count_inverse * 0.55) + (competitor_share_inverse * 0.45), 2)

        accommodation_score = power_ratio_score(accommodation, vectors["accommodation_count"])
        marketplace_score = power_ratio_score(marketplace, vectors["marketplace_count"])
        support_activity_score = power_ratio_score(total_poi, vectors["total_poi_count"])
        supporting_area_score = round(
            (retail_score * 0.30)
            + (accommodation_score * 0.25)
            + (marketplace_score * 0.15)
            + (support_activity_score * 0.30),
            2,
        )

        opportunity_score = round(
            (target_market_score * 0.36)
            + (culinary_activity_score * 0.20)
            + (supporting_area_score * 0.22)
            + (low_competition_score * 0.22),
            2,
        )

        direct_competitor_pressure = power_ratio_score(competitors, vectors["direct_kebab_competitor_count"])
        competitor_share_pressure = power_ratio_score(competitor_share, vectors["competitor_share"])
        culinary_pressure = power_ratio_score(culinary, vectors["culinary_activity_count"])
        threat_score = round(
            (direct_competitor_pressure * 0.55)
            + (competitor_share_pressure * 0.25)
            + (culinary_pressure * 0.20),
            2,
        )

        business_potential_score = round(
            clamp(
                opportunity_score
                - (threat_score * 0.18)
                + (poi_intensity_score * 0.08)
            ),
            2,
        )

        scored_rows.append(
            {
                "zone": row["zone"],
                "target_market_score": target_market_score,
                "culinary_activity_score": culinary_activity_score,
                "low_competition_score": low_competition_score,
                "supporting_area_score": supporting_area_score,
                "opportunity_score": opportunity_score,
                "threat_score": threat_score,
                "business_potential_score": business_potential_score,
                "rank": 0,
                "insight": build_insight(
                    target_market_score,
                    threat_score,
                    low_competition_score,
                    supporting_area_score,
                    business_potential_score,
                ),
            }
        )

    scored_rows.sort(key=lambda item: item["business_potential_score"], reverse=True)
    for rank, row in enumerate(scored_rows, start=1):
        row["rank"] = rank

    return scored_rows


def write_rows(rows: list[dict]) -> None:
    # Write to clean path
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in OUTPUT_COLUMNS})
            
    # Also write to root directory path
    root_path = BASE_DIR / "zone_scoring.csv"
    with root_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in OUTPUT_COLUMNS})


def main() -> None:
    rows = load_rows(INPUT_PATH)
    scored_rows = generate_scores(rows)
    write_rows(scored_rows)

    print("Generate zone scoring selesai.")
    print(f"Input rows: {len(rows)}")
    print(f"Output rows: {len(scored_rows)}")
    print(f"CSV: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
