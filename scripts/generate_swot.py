import csv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
INTERNAL_INPUT = BASE_DIR / "mbak_kebab_internal_baseline.csv"
MENU_INPUT = BASE_DIR / "mbak_kebab_menu.csv"
COMPETITOR_INPUT = BASE_DIR / "competitor_menu_price.csv"
ZONE_SUMMARY_INPUT = BASE_DIR / "data" / "clean" / "zone_summary_final.csv"
ZONE_SCORING_INPUT = BASE_DIR / "data" / "clean" / "zone_scoring_final.csv"
OUTPUT_PATH = BASE_DIR / "data" / "clean" / "swot_evidence_final.csv"

OUTPUT_COLUMNS = [
    "swot_type",
    "factor_code",
    "factor_title",
    "evidence",
    "source_dataset",
    "related_metric",
    "zone",
    "confidence",
    "recommendation",
]


def load_csv_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def find_internal_value(rows: list[dict], item: str) -> dict:
    for row in rows:
        if row.get("item") == item:
            return row
    return {}


def parse_price_range(menu_rows: list[dict]) -> tuple[str, str]:
    min_prices = []
    max_prices = []
    for row in menu_rows:
        if row.get("price_min_idr"):
            min_prices.append(int(row["price_min_idr"]))
        if row.get("price_max_idr"):
            max_prices.append(int(row["price_max_idr"]))

    if not min_prices or not max_prices:
        return "", ""
    return str(min(min_prices)), str(max(max_prices))


def build_strengths(internal_rows: list[dict], menu_rows: list[dict]) -> list[dict]:
    positioning = find_internal_value(internal_rows, "brand_positioning")
    product_claim = find_internal_value(internal_rows, "product_claim")
    price_min, price_max = parse_price_range(menu_rows)
    menu_count = len(menu_rows)

    strengths = [
        {
            "swot_type": "Strength",
            "factor_code": "S1",
            "factor_title": "Positioning rasa lokal sudah terlihat",
            "evidence": positioning.get("value", "Positioning brand belum terdokumentasi penuh tetapi ada indikasi rasa khas nusantara pada jejak publik."),
            "source_dataset": "mbak_kebab_internal_baseline.csv",
            "related_metric": "brand_positioning",
            "zone": "All",
            "confidence": positioning.get("evidence_strength", "medium"),
            "recommendation": "Pertahankan pesan diferensiasi citarasa nusantara sebagai pembeda utama dibanding kebab generik.",
        },
        {
            "swot_type": "Strength",
            "factor_code": "S2",
            "factor_title": "Produk cocok untuk fast food dan take-away",
            "evidence": "Bentuk produk kebab dan variasi paket menunjukkan model yang cocok untuk pembelian cepat, take-away, dan penjualan di area mahasiswa atau traffic tinggi.",
            "source_dataset": "mbak_kebab_menu.csv",
            "related_metric": "menu_count",
            "zone": "All",
            "confidence": "medium",
            "recommendation": "Gunakan format penjualan cepat, bundling, dan promosi delivery sebagai kekuatan operasional.",
        },
        {
            "swot_type": "Strength",
            "factor_code": "S3",
            "factor_title": "Ada indikasi harga historis terjangkau",
            "evidence": f"Jejak publik menunjukkan kisaran harga historis sekitar Rp{price_min} sampai Rp{price_max} untuk beberapa menu yang terdeteksi." if price_min and price_max else "Jejak publik menunjukkan ada indikasi harga terjangkau, tetapi detail kisaran belum lengkap.",
            "source_dataset": "mbak_kebab_menu.csv",
            "related_metric": "historical_price_range",
            "zone": "All",
            "confidence": "low",
            "recommendation": "Jika harga masih kompetitif, jadikan paket hemat dan entry price sebagai alat penetrasi pasar.",
        },
        {
            "swot_type": "Strength",
            "factor_code": "S4",
            "factor_title": "Narasi bahan fresh dan halal mendukung kepercayaan awal",
            "evidence": product_claim.get("value", "Klaim bahan fresh dan halal belum lengkap tetapi muncul pada jejak publik brand."),
            "source_dataset": "mbak_kebab_internal_baseline.csv",
            "related_metric": "product_claim",
            "zone": "All",
            "confidence": product_claim.get("evidence_strength", "medium"),
            "recommendation": "Jadikan klaim bahan fresh dan halal sebagai pendukung trust, tetapi tetap siapkan validasi jika dipakai di materi resmi.",
        },
    ]

    return strengths


def build_weaknesses(internal_rows: list[dict], menu_rows: list[dict]) -> list[dict]:
    sleman_presence = find_internal_value(internal_rows, "sleman_presence")
    current_price_missing = sum(1 for row in menu_rows if not row.get("price_current_idr"))
    size_unknown_count = sum(1 for row in menu_rows if "unknown" in (row.get("size") or "").lower())

    weaknesses = [
        {
            "swot_type": "Weakness",
            "factor_code": "W1",
            "factor_title": "Outlet Sleman Selatan belum terverifikasi",
            "evidence": sleman_presence.get("value", "Belum ada bukti kuat bahwa outlet aktif di Sleman Selatan sudah terverifikasi."),
            "source_dataset": "mbak_kebab_internal_baseline.csv",
            "related_metric": "sleman_presence",
            "zone": "Sleman Selatan",
            "confidence": sleman_presence.get("evidence_strength", "medium"),
            "recommendation": "Posisikan studi ini sebagai analisis ekspansi, bukan evaluasi outlet aktif yang sudah mapan.",
        },
        {
            "swot_type": "Weakness",
            "factor_code": "W2",
            "factor_title": "Harga terbaru belum lengkap",
            "evidence": f"{current_price_missing} dari {len(menu_rows)} item menu belum memiliki harga current yang terverifikasi pada dataset publik.",
            "source_dataset": "mbak_kebab_menu.csv",
            "related_metric": "missing_current_price_count",
            "zone": "All",
            "confidence": "high",
            "recommendation": "Sebelum presentasi final, lengkapi harga aktif, margin, dan produk prioritas untuk menguatkan analisis komersial.",
        },
        {
            "swot_type": "Weakness",
            "factor_code": "W3",
            "factor_title": "Spesifikasi ukuran dan detail produk belum stabil",
            "evidence": f"{size_unknown_count} item menu masih memakai penanda ukuran atau detail produk yang belum pasti.",
            "source_dataset": "mbak_kebab_menu.csv",
            "related_metric": "unknown_size_count",
            "zone": "All",
            "confidence": "medium",
            "recommendation": "Rapikan ukuran produk, komposisi, dan best seller agar materi penjualan dan pricing lebih kuat.",
        },
        {
            "swot_type": "Weakness",
            "factor_code": "W4",
            "factor_title": "Bukti awareness lokal Sleman masih terbatas",
            "evidence": "Jejak brand publik lebih mengarah ke Ponorogo dan Jawa Timur, sementara bukti penetrasi brand di pasar Sleman belum terlihat kuat.",
            "source_dataset": "mbak_kebab_internal_baseline.csv",
            "related_metric": "known_operational_area",
            "zone": "Sleman Selatan",
            "confidence": "medium",
            "recommendation": "Jika masuk Sleman, siapkan strategi awareness lokal seperti tester, booth event, atau reseller area kampus.",
        },
    ]

    return weaknesses


def build_opportunities(zone_summary_rows: list[dict], zone_scoring_rows: list[dict]) -> list[dict]:
    best_zone = zone_scoring_rows[0]
    highest_competition_gap = max(zone_summary_rows, key=lambda row: int(row["retail_count"]) + int(row["education_count"]))
    lowest_competition_zone = max(zone_scoring_rows, key=lambda row: float(row["low_competition_score"]))

    opportunities = [
        {
            "swot_type": "Opportunity",
            "factor_code": "O1",
            "factor_title": f"{best_zone['zone']} menjadi kandidat zona utama",
            "evidence": f"{best_zone['zone']} memiliki business potential score {best_zone['business_potential_score']} dan memimpin ranking zona saat ini.",
            "source_dataset": "data/clean/zone_scoring_final.csv",
            "related_metric": "business_potential_score",
            "zone": best_zone["zone"],
            "confidence": "medium",
            "recommendation": f"Jadikan {best_zone['zone']} sebagai fokus eksplorasi lokasi, khususnya untuk uji pasar atau validasi titik jual.",
        },
        {
            "swot_type": "Opportunity",
            "factor_code": "O2",
            "factor_title": "Titik pendidikan dan retail memberi peluang traffic konsumen",
            "evidence": f"{highest_competition_gap['zone']} memiliki education_count {highest_competition_gap['education_count']} dan retail_count {highest_competition_gap['retail_count']} yang menunjukkan potensi pergerakan target pasar.",
            "source_dataset": "data/clean/zone_summary_final.csv",
            "related_metric": "education_count + retail_count",
            "zone": highest_competition_gap["zone"],
            "confidence": "medium",
            "recommendation": "Gunakan area kampus, sekolah, dan retail sebagai orientasi pencarian titik penjualan atau promosi.",
        },
        {
            "swot_type": "Opportunity",
            "factor_code": "O3",
            "factor_title": "Zona dengan kompetitor kebab lebih rendah cocok untuk uji pasar",
            "evidence": f"{lowest_competition_zone['zone']} memiliki low_competition_score {lowest_competition_zone['low_competition_score']} yang paling tinggi di antara zona yang dianalisis.",
            "source_dataset": "data/clean/zone_scoring_final.csv",
            "related_metric": "low_competition_score",
            "zone": lowest_competition_zone["zone"],
            "confidence": "medium",
            "recommendation": f"Pertimbangkan {lowest_competition_zone['zone']} untuk model soft opening, booth, atau reseller sebelum ekspansi lebih besar.",
        },
        {
            "swot_type": "Opportunity",
            "factor_code": "O4",
            "factor_title": "Aktivitas kuliner tinggi membuka peluang demand yang sudah terbentuk",
            "evidence": f"Zona dengan aktivitas kuliner tinggi seperti {best_zone['zone']} menunjukkan pasar sudah aktif, sehingga produk baru tidak perlu membangun demand dari nol.",
            "source_dataset": "data/clean/zone_summary_final.csv",
            "related_metric": "culinary_activity_count",
            "zone": best_zone["zone"],
            "confidence": "medium",
            "recommendation": "Masuk dengan diferensiasi yang jelas agar bisa menumpang arus demand yang sudah ada.",
        },
    ]

    return opportunities


def build_threats(competitor_rows: list[dict], zone_summary_rows: list[dict], zone_scoring_rows: list[dict]) -> list[dict]:
    best_zone = zone_scoring_rows[0]
    highest_threat_zone = max(zone_scoring_rows, key=lambda row: float(row["threat_score"]))
    price_points = [int(row["price_idr"]) for row in competitor_rows if row.get("price_idr", "").isdigit()]
    min_price = min(price_points) if price_points else None
    depok_competitors = [row["competitor_name"] for row in competitor_rows if row.get("zone") == "Depok"][:5]
    depok_summary = next(row for row in zone_summary_rows if row["zone"] == "Depok")

    threats = [
        {
            "swot_type": "Threat",
            "factor_code": "T1",
            "factor_title": f"Kompetisi tertinggi terkonsentrasi di {highest_threat_zone['zone']}",
            "evidence": f"{highest_threat_zone['zone']} memiliki threat_score {highest_threat_zone['threat_score']} dan direct competitor count yang relatif paling tinggi.",
            "source_dataset": "data/clean/zone_scoring_final.csv",
            "related_metric": "threat_score",
            "zone": highest_threat_zone["zone"],
            "confidence": "medium",
            "recommendation": "Masuk ke zona ini harus disertai diferensiasi rasa, harga, dan lokasi mikro yang lebih cermat.",
        },
        {
            "swot_type": "Threat",
            "factor_code": "T2",
            "factor_title": "Pilihan kuliner alternatif sangat padat",
            "evidence": f"{depok_summary['zone']} memiliki culinary_activity_count {depok_summary['culinary_activity_count']} yang menunjukkan konsumen punya banyak pilihan makanan cepat saji dan kuliner lain.",
            "source_dataset": "data/clean/zone_summary_final.csv",
            "related_metric": "culinary_activity_count",
            "zone": depok_summary["zone"],
            "confidence": "medium",
            "recommendation": "Hindari positioning kebab generik; tonjolkan nilai unik dan alasan beli yang spesifik.",
        },
        {
            "swot_type": "Threat",
            "factor_code": "T3",
            "factor_title": "Harga kompetitor bisa menekan ruang bermain",
            "evidence": f"Data publik kompetitor menunjukkan price point mulai sekitar Rp{min_price} pada item yang berhasil terdeteksi." if min_price else "Data kompetitor menunjukkan ada variasi harga yang dapat menekan ruang bermain, walau tidak semua price point tersedia.",
            "source_dataset": "competitor_menu_price.csv",
            "related_metric": "price_idr",
            "zone": "All",
            "confidence": "medium" if min_price else "low",
            "recommendation": "Siapkan strategi paket, porsi, dan value proposition agar tidak terjebak perang harga murni.",
        },
        {
            "swot_type": "Threat",
            "factor_code": "T4",
            "factor_title": "Pemain yang sudah dekat koridor mahasiswa lebih dulu hadir",
            "evidence": f"Nama kompetitor seperti {', '.join(depok_competitors)} menunjukkan beberapa pemain sudah menempel pada koridor aktif mahasiswa dan kuliner." if depok_competitors else "Beberapa kompetitor sudah lebih dekat ke koridor mahasiswa dan area kuliner aktif.",
            "source_dataset": "competitor_menu_price.csv",
            "related_metric": "competitor_name",
            "zone": best_zone["zone"],
            "confidence": "medium",
            "recommendation": "Cari titik jual yang tidak terlalu berhimpitan atau gunakan strategi mobile/pop-up untuk mengurangi benturan langsung.",
        },
    ]

    return threats


def write_output(rows: list[dict]) -> None:
    # Write to clean path
    with OUTPUT_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in OUTPUT_COLUMNS})

    # Also write to root directory path
    root_path = BASE_DIR / "swot_evidence.csv"
    with root_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in OUTPUT_COLUMNS})


def main() -> None:
    internal_rows = load_csv_rows(INTERNAL_INPUT)
    menu_rows = load_csv_rows(MENU_INPUT)
    competitor_rows = load_csv_rows(COMPETITOR_INPUT)
    zone_summary_rows = load_csv_rows(ZONE_SUMMARY_INPUT)
    zone_scoring_rows = load_csv_rows(ZONE_SCORING_INPUT)

    final_rows = []
    final_rows.extend(build_strengths(internal_rows, menu_rows))
    final_rows.extend(build_weaknesses(internal_rows, menu_rows))
    final_rows.extend(build_opportunities(zone_summary_rows, zone_scoring_rows))
    final_rows.extend(build_threats(competitor_rows, zone_summary_rows, zone_scoring_rows))

    write_output(final_rows)

    print("Generate SWOT selesai.")
    print(f"Output rows: {len(final_rows)}")
    print(f"CSV: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
