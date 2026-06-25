import csv
import json
from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
ZONE_SUMMARY_INPUT = BASE_DIR / "data" / "clean" / "zone_summary_final.csv"
ZONE_SCORING_INPUT = BASE_DIR / "data" / "clean" / "zone_scoring_final.csv"
SWOT_INPUT = BASE_DIR / "data" / "clean" / "swot_evidence_final.csv"
POI_INPUT = BASE_DIR / "data" / "clean" / "poi_final.csv"
MENU_INPUT = BASE_DIR / "mbak_kebab_menu.csv"
COMPETITOR_INPUT = BASE_DIR / "competitor_menu_price.csv"
OUTPUT_PATH = BASE_DIR / "data" / "final" / "landing_page_data_final.json"


def load_csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def to_number(value: str):
    if value is None or value == "":
        return ""
    try:
        if "." in str(value):
            return float(value)
        return int(value)
    except ValueError:
        return value


def convert_row_types(row: dict) -> dict:
    converted = {}
    for key, value in row.items():
        converted[key] = to_number(value)
    return converted


def build_swot_groups(rows: list[dict]) -> dict:
    grouped = {
        "strengths": [],
        "weaknesses": [],
        "opportunities": [],
        "threats": [],
    }

    key_map = {
        "Strength": "strengths",
        "Weakness": "weaknesses",
        "Opportunity": "opportunities",
        "Threat": "threats",
    }

    for row in rows:
        bucket = key_map.get(row.get("swot_type", ""))
        if bucket:
            grouped[bucket].append(row)

    return grouped


def build_strategies(swot_groups: dict, zone_rankings: list[dict]) -> dict:
    best_zone = zone_rankings[0]["zone"] if zone_rankings else "zona utama"
    lower_competition_zone = next(
        (row["zone"] for row in zone_rankings if float(row.get("low_competition_score", 0) or 0) >= 80),
        best_zone,
    )

    so = [
        f"Gunakan positioning rasa lokal dan narasi bahan fresh untuk memperkuat penetrasi awal di {best_zone}.",
        "Padukan format fast food, bundling, dan promosi delivery untuk memanfaatkan demand yang sudah aktif.",
    ]
    wo = [
        "Lengkapi harga aktif, ukuran produk, dan best seller agar kelemahan data internal tidak mengganggu eksekusi komersial.",
        f"Mulai dari uji pasar ringan di {lower_competition_zone} jika ingin menekan risiko masuk pasar terlalu cepat.",
    ]
    st = [
        f"Masuk ke {best_zone} dengan diferensiasi yang tajam agar tidak bertabrakan langsung dengan pemain kebab yang sudah ada.",
        "Gunakan paket hemat, rasa khas, dan titik jual yang dekat demand point sebagai cara melawan tekanan kompetisi.",
    ]
    wt = [
        "Hindari keputusan outlet permanen sebelum validasi lokasi mikro dan validasi harga terbaru selesai.",
        "Gunakan model booth, pop-up, atau reseller jika ancaman kompetisi terasa lebih tinggi daripada kesiapan data internal.",
    ]

    return {"SO": so, "WO": wo, "ST": st, "WT": wt}


def main() -> None:
    zone_summary_rows = [convert_row_types(row) for row in load_csv_rows(ZONE_SUMMARY_INPUT)]
    zone_scoring_rows = [convert_row_types(row) for row in load_csv_rows(ZONE_SCORING_INPUT)]
    swot_rows = [convert_row_types(row) for row in load_csv_rows(SWOT_INPUT)]
    poi_rows = [convert_row_types(row) for row in load_csv_rows(POI_INPUT)]
    menu_rows = [convert_row_types(row) for row in load_csv_rows(MENU_INPUT)]
    competitor_rows = [convert_row_types(row) for row in load_csv_rows(COMPETITOR_INPUT)]

    zone_rankings = sorted(zone_scoring_rows, key=lambda row: float(row.get("rank", 9999)))
    swot_groups = build_swot_groups(swot_rows)
    best_zone = zone_rankings[0]["zone"] if zone_rankings else ""
    highest_threat_zone = max(zone_rankings, key=lambda row: float(row.get("threat_score", 0)))["zone"] if zone_rankings else ""

    payload = {
        "project_title": "Analisis Potensi Bisnis Mbak Kebab di Area Sleman Selatan",
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "summary_cards": {
            "total_zones": len(zone_summary_rows),
            "total_poi": len(poi_rows),
            "total_kebab_competitors": sum(1 for row in poi_rows if row.get("category") == "direct_kebab_competitor"),
            "best_zone": best_zone,
            "highest_threat_zone": highest_threat_zone,
        },
        "zone_rankings": zone_rankings,
        "zone_summary": zone_summary_rows,
        "poi_map": poi_rows,
        "mbak_kebab_menu": menu_rows,
        "competitors": competitor_rows,
        "swot": swot_groups,
        "strategies": build_strategies(swot_groups, zone_rankings),
    }

    # Write to final clean path
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Also write to root directory path
    root_json_path = BASE_DIR / "landing_page_data.json"
    root_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    # Also write to web data path
    web_json_path = BASE_DIR / "web" / "data" / "landing_page_data.json"
    web_json_path.parent.mkdir(parents=True, exist_ok=True)
    web_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Export landing JSON selesai.")
    print(f"Zone rankings: {len(zone_rankings)}")
    print(f"POI rows: {len(poi_rows)}")
    print(f"SWOT rows: {len(swot_rows)}")
    print(f"JSON: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
