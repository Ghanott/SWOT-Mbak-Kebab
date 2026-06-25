# Paket Data Analisis SWOT Mbak Kebab di Sleman Selatan

## Ringkasan
Paket ini berisi dataset awal untuk studi kasus **Analisis Potensi Bisnis Mbak Kebab di Area Sleman Selatan**. Data dibagi menjadi data internal publik Mbak Kebab, data menu/harga yang berhasil diinferensikan dari sumber publik, data kompetitor, data pendukung wilayah, scoring zona, dan mapping SWOT evidence.

## Zona Analisis
- Depok
- Mlati
- Gamping
- Ngaglik Selatan

## File Utama
- `mbak_kebab_internal_baseline.csv`: profil internal publik brand.
- `mbak_kebab_menu.csv`: menu, harga, dan ukuran yang berhasil dikumpulkan dari sumber publik.
- `competitor_menu_price.csv`: kompetitor kebab dan harga/menu jika tersedia.
- `zone_summary.csv`: data pendukung wilayah per zona.
- `zone_scoring.csv`: skor peluang dan ancaman per zona.
- `swot_evidence.csv`: evidence untuk SWOT.
- `landing_page_data.json`: file siap konsumsi untuk web/landing page.
- `poi_clean.csv` dan `poi_manual.geojson`: data POI manual/awal untuk map.
- `overpass_queries.json`: query untuk mengambil POI OSM/Overpass asli.
- `methods_code_snippets.py`: script untuk menjalankan query Overpass di IDE.

## Catatan Kualitas Data
1. Data Instagram tidak di-scrape otomatis. Data berasal dari tampilan publik/snippet dan perlu diverifikasi manual melalui screenshot atau owner.
2. Harga/menu Mbak Kebab masih bersifat baseline publik, bukan katalog resmi terbaru.
3. File `overpass_raw_*.json` masih placeholder. Jalankan `methods_code_snippets.py` untuk mengambil raw OSM asli.
4. Sebagian koordinat POI merupakan centroid/manual estimate sehingga belum ideal untuk analisis jarak presisi.
5. Data BPS/UMKM bercampur dari publikasi dan portal publik; bila ingin akademik lebih rapi, samakan tahun data sebelum final.

## Rekomendasi Penggunaan
Untuk web, gunakan `landing_page_data.json`.
Untuk analisis Python, mulai dari:
- `zone_summary.csv`
- `zone_scoring.csv`
- `swot_evidence.csv`
- `mbak_kebab_menu.csv`
- `competitor_menu_price.csv`

## Formula Scoring
Opportunity Score = 0.40 × Demand Score + 0.35 × Commercial Score + 0.25 × Low Competition Score

Business Potential Score = Opportunity Score - 0.15 × Threat Score

## Kesimpulan Awal
Depok paling kuat dari sisi demand, tetapi juga memiliki ancaman kompetisi tinggi. Mlati kuat sebagai koridor traffic dan retail. Gamping menarik sebagai opsi alternatif dengan tekanan kompetisi langsung yang relatif lebih ringan. Ngaglik Selatan bisa dipakai sebagai zona tambahan, namun masih membutuhkan data spasial yang lebih presisi.
