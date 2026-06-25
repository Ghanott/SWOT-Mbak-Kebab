Kamu adalah AI Agent Fullstack Developer dan Data Analyst. Saya sedang membuat project:

“Analisis Potensi Bisnis Mbak Kebab di Area Sleman Selatan Berbasis Data Scraping, Visualisasi Web, dan SWOT Analysis.”

Saya sudah memiliki paket data awal berisi file:

* `mbak_kebab_internal_baseline.csv`
* `mbak_kebab_menu.csv`
* `competitor_menu_price.csv`
* `poi_raw.csv`
* `poi_clean.csv`
* `poi_manual.geojson`
* `zone_summary.csv`
* `zone_scoring.csv`
* `swot_evidence.csv`
* `landing_page_data.json`
* `overpass_queries.json`
* `methods_code_snippets.py`
* `analysis_report.md`
* `data_dictionary.csv`
* `evidence_sources.csv`

Tugas kamu adalah membantu saya menyelesaikan project ini dari data sampai visualisasi web.

==================================================
A. TUJUAN PROJECT
=================

Buat workflow lengkap:

1. Validasi data awal.
2. Jalankan scraping OpenStreetMap/Overpass.
3. Cleaning data hasil scraping.
4. Gabungkan data hasil scraping dengan data baseline.
5. Hitung ulang ringkasan per zona.
6. Hitung ulang skor potensi bisnis per zona.
7. Buat SWOT evidence final.
8. Export JSON final untuk web.
9. Buat dashboard web visualisasi menggunakan React + Vite.
10. Tampilkan hasil analisis dalam bentuk landing page/dashboard.

Project ini digunakan untuk presentasi challenge magang. Jadi hasilnya harus rapi, mudah dipahami, dan bisa dijelaskan sebagai alur:

Scraping Data → Cleaning Data → Analisis Zona → SWOT Evidence → Visualisasi Web → Rekomendasi Bisnis

==================================================
B. BATASAN DAN ETIKA DATA
=========================

Ikuti aturan berikut:

1. Jangan scraping Instagram secara otomatis.
2. Jangan bypass login, captcha, atau proteksi platform.
3. Data Instagram Mbak Kebab hanya digunakan sebagai baseline manual/publik.
4. Scraping utama hanya dari OpenStreetMap melalui Overpass API.
5. Jika memakai Google Places, hanya gunakan API resmi jika API key tersedia.
6. Jangan hardcode API key.
7. Jangan mengambil data personal pelanggan.
8. Semua output harus menyimpan sumber data dan timestamp.

==================================================
C. STRUKTUR PROJECT YANG DIHARAPKAN
===================================

Rapikan project menjadi seperti ini:

project/
├── data/
│   ├── raw/
│   │   ├── overpass_raw_depok.json
│   │   ├── overpass_raw_mlati.json
│   │   ├── overpass_raw_gamping.json
│   │   ├── overpass_raw_ngaglik_selatan.json
│   │   └── overpass_raw_combined.json
│   ├── baseline/
│   │   ├── mbak_kebab_internal_baseline.csv
│   │   ├── mbak_kebab_menu.csv
│   │   ├── competitor_menu_price.csv
│   │   ├── zone_summary.csv
│   │   ├── zone_scoring.csv
│   │   └── swot_evidence.csv
│   ├── clean/
│   │   ├── poi_osm_clean.csv
│   │   ├── poi_final.csv
│   │   ├── zone_summary_final.csv
│   │   ├── zone_scoring_final.csv
│   │   └── swot_evidence_final.csv
│   └── final/
│       └── landing_page_data_final.json
├── scripts/
│   ├── cek_data.py
│   ├── scrape_overpass.py
│   ├── clean_overpass_data.py
│   ├── merge_data.py
│   ├── generate_zone_summary.py
│   ├── generate_zone_scoring.py
│   ├── generate_swot.py
│   └── export_landing_json.py
├── web/
│   └── React/Vite dashboard
├── README.md
└── requirements.txt

Jika folder belum ada, buat otomatis.

==================================================
D. STEP 1 — VALIDASI DATA AWAL
==============================

Buat script:

`scripts/cek_data.py`

Tugas:

1. Membaca file CSV dan JSON awal.
2. Menampilkan jumlah baris.
3. Menampilkan kolom masing-masing file.
4. Menampilkan 5 data teratas.
5. Memberi warning jika file kosong, tidak ditemukan, atau kolom penting hilang.

File yang dicek:

* `mbak_kebab_internal_baseline.csv`
* `mbak_kebab_menu.csv`
* `competitor_menu_price.csv`
* `zone_summary.csv`
* `zone_scoring.csv`
* `swot_evidence.csv`
* `landing_page_data.json`

Command:

python scripts/cek_data.py

==================================================
E. STEP 2 — SCRAPING OPENSTREETMAP / OVERPASS
=============================================

Buat script:

`scripts/scrape_overpass.py`

Input:

* `overpass_queries.json`

Tugas:

1. Baca query dari `overpass_queries.json`.
2. Jalankan request ke Overpass API.
3. Simpan hasil per zona ke:

   * `data/raw/overpass_raw_depok.json`
   * `data/raw/overpass_raw_mlati.json`
   * `data/raw/overpass_raw_gamping.json`
   * `data/raw/overpass_raw_ngaglik_selatan.json`
4. Gabungkan semua hasil ke:

   * `data/raw/overpass_raw_combined.json`
5. Tambahkan delay antar request minimal 3 detik.
6. Tambahkan error handling jika timeout.
7. Jika endpoint utama gagal, sediakan opsi endpoint cadangan:

   * https://overpass-api.de/api/interpreter
   * https://overpass.kumi.systems/api/interpreter

Kategori data yang harus diambil:

* kompetitor kebab
* fast food
* restaurant
* cafe
* food court
* university
* college
* school
* hotel
* guest house
* hostel
* convenience store
* supermarket
* mall
* marketplace

Zona:

* Depok
* Mlati
* Gamping
* Ngaglik Selatan

Command:

python scripts/scrape_overpass.py

==================================================
F. STEP 3 — CLEANING DATA OVERPASS
==================================

Buat script:

`scripts/clean_overpass_data.py`

Input:

* `data/raw/overpass_raw_combined.json`

Output:

* `data/clean/poi_osm_clean.csv`
* `data/clean/poi_osm_clean.json`
* `data/clean/poi_osm_clean.geojson`

Kolom output minimal:

* `poi_id`
* `osm_type`
* `osm_id`
* `name`
* `name_clean`
* `category`
* `subcategory`
* `zone`
* `latitude`
* `longitude`
* `amenity`
* `tourism`
* `shop`
* `cuisine`
* `opening_hours`
* `phone`
* `website`
* `source`
* `source_url`
* `extracted_at`
* `raw_tags`

Aturan cleaning:

1. Ambil koordinat:

   * Jika node, gunakan `lat` dan `lon`.
   * Jika way/relation, gunakan `center.lat` dan `center.lon`.

2. Hapus data tanpa koordinat.

3. Normalisasi nama:

   * lowercase
   * strip whitespace
   * hapus spasi ganda

4. Kategori:

   * jika name/cuisine mengandung `kebab`, `kabab`, `kebap`, `shawarma` → `direct_kebab_competitor`
   * amenity=fast_food → `fast_food`
   * amenity=restaurant → `restaurant`
   * amenity=cafe → `cafe`
   * amenity=food_court → `food_court`
   * amenity=university → `university`
   * amenity=college → `college`
   * amenity=school → `school`
   * tourism=hotel → `hotel`
   * tourism=guest_house → `guest_house`
   * tourism=hostel → `hostel`
   * shop=convenience/supermarket/mall → `retail`
   * amenity=marketplace → `marketplace`
   * lainnya → `other`

5. Tambahkan flag:

   * `is_direct_competitor`
   * `is_food_alternative`
   * `is_demand_point`
   * `is_supporting_facility`

6. Hapus duplikasi:

   * berdasarkan `osm_type + osm_id`
   * jika nama sama dan jarak koordinat sangat dekat, simpan satu saja

Command:

python scripts/clean_overpass_data.py

==================================================
G. STEP 4 — MERGE DATA
======================

Buat script:

`scripts/merge_data.py`

Input:

* `poi_clean.csv` dari baseline jika ada
* `data/clean/poi_osm_clean.csv`

Output:

* `data/clean/poi_final.csv`
* `data/clean/poi_final.json`
* `data/clean/poi_final.geojson`

Tugas:

1. Gabungkan data baseline POI dengan hasil OSM.
2. Samakan nama kolom.
3. Hapus duplikasi.
4. Pastikan setiap data punya kategori dan zona.
5. Simpan hasil final.

Command:

python scripts/merge_data.py

==================================================
H. STEP 5 — GENERATE ZONE SUMMARY
=================================

Buat script:

`scripts/generate_zone_summary.py`

Input:

* `data/clean/poi_final.csv`
* `zone_summary.csv` baseline jika tersedia

Output:

* `data/clean/zone_summary_final.csv`

Hitung per zona:

* `direct_kebab_competitor_count`
* `fast_food_count`
* `restaurant_count`
* `cafe_count`
* `food_court_count`
* `culinary_activity_count`
* `university_count`
* `college_count`
* `school_count`
* `education_count`
* `hotel_count`
* `guest_house_count`
* `hostel_count`
* `accommodation_count`
* `retail_count`
* `marketplace_count`
* `total_poi_count`

Zona:

* Depok
* Mlati
* Gamping
* Ngaglik Selatan

Command:

python scripts/generate_zone_summary.py

==================================================
I. STEP 6 — GENERATE ZONE SCORING
=================================

Buat script:

`scripts/generate_zone_scoring.py`

Input:

* `data/clean/zone_summary_final.csv`

Output:

* `data/clean/zone_scoring_final.csv`

Rumus:

Target Market Score:

* berdasarkan `education_count`, `retail_count`, dan jika tersedia `population`

Culinary Activity Score:

* berdasarkan `fast_food_count + restaurant_count + cafe_count + food_court_count`

Low Competition Score:

* berdasarkan kebalikan dari `direct_kebab_competitor_count`
* semakin sedikit kompetitor kebab, semakin tinggi skor

Supporting Area Score:

* berdasarkan `accommodation_count + retail_count + marketplace_count`

Threat Score:

* berdasarkan `direct_kebab_competitor_count + culinary_activity_count`

Business Potential Score:

Business Potential Score =
0.35 × Target Market Score

* 0.25 × Culinary Activity Score
* 0.25 × Low Competition Score
* 0.15 × Supporting Area Score

Tambahkan kolom:

* `zone`
* `target_market_score`
* `culinary_activity_score`
* `low_competition_score`
* `supporting_area_score`
* `opportunity_score`
* `threat_score`
* `business_potential_score`
* `rank`
* `insight`

Buat insight otomatis:

* Jika skor tinggi dan threat rendah, tulis zona sangat potensial.
* Jika skor tinggi dan threat tinggi, tulis zona potensial tetapi kompetitif.
* Jika kompetitor rendah tetapi demand sedang, tulis cocok untuk uji pasar.
* Jika skor rendah, tulis perlu validasi tambahan.

Command:

python scripts/generate_zone_scoring.py

==================================================
J. STEP 7 — GENERATE SWOT EVIDENCE
==================================

Buat script:

`scripts/generate_swot.py`

Input:

* `mbak_kebab_internal_baseline.csv`
* `mbak_kebab_menu.csv`
* `competitor_menu_price.csv`
* `data/clean/zone_summary_final.csv`
* `data/clean/zone_scoring_final.csv`

Output:

* `data/clean/swot_evidence_final.csv`

Kolom output:

* `swot_type`
* `factor_code`
* `factor_title`
* `evidence`
* `source_dataset`
* `related_metric`
* `zone`
* `confidence`
* `recommendation`

Aturan SWOT:

Strength:

* berasal dari data internal Mbak Kebab
* contoh:

  * positioning citarasa khas nusantara
  * harga historis terjangkau
  * produk praktis/take-away
  * varian menu
  * bahan fresh/halal jika valid

Weakness:

* berasal dari data internal yang belum kuat
* contoh:

  * outlet Sleman belum terverifikasi
  * harga/menu terbaru belum lengkap
  * ukuran produk belum terukur
  * data penjualan belum tersedia
  * brand awareness Sleman belum terbukti

Opportunity:

* berasal dari data eksternal
* contoh:

  * banyak kampus/sekolah
  * banyak retail/minimarket
  * banyak hotel/penginapan
  * zona aktivitas kuliner tinggi
  * kompetitor kebab masih rendah

Threat:

* berasal dari data eksternal
* contoh:

  * kompetitor kebab banyak
  * fast food/cafe/restoran banyak
  * harga kompetitor agresif
  * kompetitor punya lokasi lebih dekat kampus
  * area kuliner padat memicu perang harga

Command:

python scripts/generate_swot.py

==================================================
K. STEP 8 — EXPORT JSON FINAL UNTUK WEB
=======================================

Buat script:

`scripts/export_landing_json.py`

Input:

* `data/clean/zone_summary_final.csv`
* `data/clean/zone_scoring_final.csv`
* `data/clean/swot_evidence_final.csv`
* `data/clean/poi_final.csv`
* `mbak_kebab_menu.csv`
* `competitor_menu_price.csv`

Output:

* `data/final/landing_page_data_final.json`

Struktur JSON:

{
"project_title": "Analisis Potensi Bisnis Mbak Kebab di Area Sleman Selatan",
"last_updated": "",
"summary_cards": {
"total_zones": 0,
"total_poi": 0,
"total_kebab_competitors": 0,
"best_zone": "",
"highest_threat_zone": ""
},
"zone_rankings": [],
"zone_summary": [],
"poi_map": [],
"mbak_kebab_menu": [],
"competitors": [],
"swot": {
"strengths": [],
"weaknesses": [],
"opportunities": [],
"threats": []
},
"strategies": {
"SO": [],
"WO": [],
"ST": [],
"WT": []
}
}

Command:

python scripts/export_landing_json.py

==================================================
L. STEP 9 — BUAT WEB DASHBOARD
==============================

Buat folder:

`web/`

Di dalamnya buat project React + Vite.

Command:

npm create vite@latest web

Pilih:

* React
* JavaScript

Masuk ke folder web:

cd web

Install dependency:

npm install
npm install recharts leaflet react-leaflet lucide-react

Copy file:

`data/final/landing_page_data_final.json`

ke:

`web/public/data/landing_page_data.json`

==================================================
M. STRUKTUR WEB
===============

Buat struktur:

web/
├── public/
│   └── data/
│       └── landing_page_data.json
├── src/
│   ├── App.jsx
│   ├── main.jsx
│   ├── index.css
│   ├── utils/
│   │   └── getLandingData.js
│   └── components/
│       ├── SummaryCards.jsx
│       ├── ZoneRankingChart.jsx
│       ├── ZoneSummaryTable.jsx
│       ├── PoiMap.jsx
│       ├── SwotMatrix.jsx
│       ├── StrategySection.jsx
│       ├── MenuTable.jsx
│       └── CompetitorTable.jsx

==================================================
N. KOMPONEN WEB YANG HARUS DIBUAT
=================================

1. Hero Section
   Judul:
   “Analisis Potensi Bisnis Mbak Kebab di Area Sleman Selatan”

Subjudul:
“Berbasis data kompetitor, titik keramaian, potensi pasar, dan SWOT analysis.”

2. SummaryCards.jsx
   Tampilkan:

* total zona
* total POI
* total kompetitor kebab
* zona terbaik
* zona ancaman tertinggi

3. ZoneRankingChart.jsx
   Gunakan Recharts.
   Tampilkan bar chart:

* `business_potential_score` per zona

4. ZoneSummaryTable.jsx
   Tampilkan tabel:

* zona
* jumlah kompetitor kebab
* culinary activity
* education
* accommodation
* retail
* total POI

5. PoiMap.jsx
   Gunakan Leaflet.
   Tampilkan marker:

* kompetitor kebab
* fast food/restoran/cafe
* kampus/sekolah
* hotel/penginapan
* retail

Popup marker menampilkan:

* nama tempat
* kategori
* zona
* sumber

6. SwotMatrix.jsx
   Tampilkan 4 card:

* Strength
* Weakness
* Opportunity
* Threat

Data dari:

* `swot.strengths`
* `swot.weaknesses`
* `swot.opportunities`
* `swot.threats`

7. StrategySection.jsx
   Tampilkan:

* SO Strategy
* WO Strategy
* ST Strategy
* WT Strategy

8. MenuTable.jsx
   Tampilkan:

* menu Mbak Kebab
* kategori
* varian
* ukuran
* harga
* confidence
* notes

9. CompetitorTable.jsx
   Tampilkan:

* nama kompetitor
* zona
* menu
* harga
* source
* confidence

==================================================
O. DESAIN WEB
=============

Gunakan tampilan modern, rapi, dan mudah dipresentasikan.

Style:

* background terang
* card rounded
* shadow halus
* layout responsive
* warna utama boleh merah/oranye/coklat karena cocok dengan brand kuliner
* gunakan font sans-serif
* jangan terlalu ramai

Urutan halaman:

1. Hero
2. Summary Cards
3. Ranking Zona
4. Peta POI
5. Ringkasan Zona
6. Data Menu Mbak Kebab
7. Data Kompetitor
8. SWOT Matrix
9. Strategi Rekomendasi
10. Footer sumber data

==================================================
P. COMMAND YANG HARUS BISA DIJALANKAN
=====================================

Bagian Python:

python scripts/cek_data.py
python scripts/scrape_overpass.py
python scripts/clean_overpass_data.py
python scripts/merge_data.py
python scripts/generate_zone_summary.py
python scripts/generate_zone_scoring.py
python scripts/generate_swot.py
python scripts/export_landing_json.py

Bagian web:

cd web
npm install
npm run dev

==================================================
Q. README
=========

Buat README.md yang menjelaskan:

1. Judul project.
2. Latar belakang.
3. Data sources.
4. Alur data.
5. Cara menjalankan Python pipeline.
6. Cara menjalankan web.
7. Penjelasan file output.
8. Penjelasan scoring.
9. Penjelasan SWOT.
10. Catatan keterbatasan data.

==================================================
R. OUTPUT AKHIR
===============

Pastikan hasil akhir memiliki:

1. Dataset bersih:

   * `poi_final.csv`
   * `zone_summary_final.csv`
   * `zone_scoring_final.csv`
   * `swot_evidence_final.csv`

2. JSON web:

   * `landing_page_data_final.json`

3. Dashboard web:

   * summary cards
   * chart ranking zona
   * map POI
   * table zona
   * table menu
   * table kompetitor
   * SWOT matrix
   * strategi rekomendasi

4. README lengkap.

==================================================
S. CARA KERJA
=============

Jangan hanya memberi penjelasan. Buat file dan kode yang benar-benar bisa dijalankan.

Kerjakan bertahap:

1. Rapikan struktur folder.
2. Buat semua script Python.
3. Jalankan validasi data.
4. Siapkan pipeline scraping dan cleaning.
5. Buat export JSON final.
6. Buat dashboard React.
7. Pastikan tidak ada error import.
8. Beri instruksi command final untuk menjalankan project.

Jika ada data yang belum lengkap, jangan mengarang. Isi dengan null/kosong dan beri catatan pada kolom `notes` atau `confidence`.
