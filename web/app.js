const categoryPalette = {
  direct_kebab_competitor: { label: "Kompetitor Kebab", color: "#B64419", icon: "⚔️" },
  fast_food: { label: "Fast Food", color: "#E06C2A", icon: "🍔" },
  restaurant: { label: "Restaurant", color: "#D97706", icon: "🍛" },
  cafe: { label: "Cafe", color: "#B45309", icon: "☕" },
  food_court: { label: "Food Court", color: "#8A4B14", icon: "🍽️" },
  university: { label: "University", color: "#2563EB", icon: "🎓" },
  college: { label: "College", color: "#4F46E5", icon: "🏫" },
  school: { label: "School", color: "#0284C7", icon: "✏️" },
  hotel: { label: "Hotel", color: "#7C3AED", icon: "🏨" },
  guest_house: { label: "Guest House", color: "#8B5CF6", icon: "🏠" },
  hostel: { label: "Hostel", color: "#A855F7", icon: "🛌" },
  retail: { label: "Retail", color: "#059669", icon: "🛒" },
  marketplace: { label: "Marketplace", color: "#0D9488", icon: "🎪" },
  other: { label: "Other", color: "#64748B", icon: "📍" },
  "mall/titik_keramaian": { label: "Mall / Keramaian", color: "#0F766E", icon: "🏢" },
  "transport/titik_keramaian": { label: "Transport / Keramaian", color: "#0369A1", icon: "🚉" },
  brand_reference: { label: "Brand Reference", color: "#92400E", icon: "⭐" },
};

// Bounding boxes coordinates from overpass_queries.json
const zoneBboxConfig = {
  "Depok": { bounds: [[-7.805, 110.355], [-7.715, 110.47]], name: "Kecamatan Depok" },
  "Mlati": { bounds: [[-7.795, 110.315], [-7.69, 110.39]], name: "Kecamatan Mlati" },
  "Gamping": { bounds: [[-7.84, 110.27], [-7.735, 110.35]], name: "Kecamatan Gamping" },
  "Ngaglik Selatan": { bounds: [[-7.745, 110.355], [-7.675, 110.435]], name: "Kecamatan Ngaglik Selatan" }
};

let mapInstance = null;
let mapLayerGroup = null;
let bboxLayerGroup = null;
let rankingChartInstance = null;
let comparisonChartInstance = null;

let allPois = [];
let activeCategories = new Set(["direct_kebab_competitor", "university", "college", "mall/titik_keramaian"]);

// Global Interactive State
let selectedZone = null;
let selectedPoi = null;
let highlightedPoiId = null;
let bestZoneGlobal = null;
let globalDashboardData = null;
const zoneRectangleLayers = {};
const poiMarkersMap = new Map();

document.addEventListener("DOMContentLoaded", async () => {
  try {
    const data = await loadLandingData();
    allPois = data.poi_map || [];
    globalDashboardData = data;
    renderDashboard(data);
  } catch (error) {
    console.error(error);
    renderError(error);
  }
});

async function loadLandingData() {
  const response = await fetch("./data/landing_page_data.json");
  if (!response.ok) {
    throw new Error("Gagal memuat web/data/landing_page_data.json");
  }
  return response.json();
}

function renderDashboard(data) {
  document.title = data.project_title;
  const recommendation = getRecommendationModel(data.zone_rankings);
  bestZoneGlobal = recommendation.entryZone || data.summary_cards.best_zone;
  
  renderHero(data);
  renderSummaryCards(data.summary_cards, recommendation);
  renderRankingChart(data.zone_rankings);
  renderRankingInsights(data.zone_rankings, recommendation);
  
  // Initialize map structure and interactions
  initMapStructure(bestZoneGlobal);
  renderZoneQuickSelectors();
  initDetailPanel();
  updateDetailPanel();
  renderMapLegend();
  updateMapMarkers();

  // Render Charts & Tables
  renderMetricsComparisonChart(data.zone_summary);
  renderZoneMetricsSummary(data.zone_summary);
  renderZoneSummary(data.zone_summary);
  renderMenuTable(data.mbak_kebab_menu);
  renderCompetitorTable(data.competitors);
  renderSwot(data.swot);
}

function renderHero(data) {
  const heroBadges = document.getElementById("hero-badges");
  const bestZoneLabel = document.getElementById("best-zone-label");
  const bestZoneInsight = document.getElementById("best-zone-insight");
  const highestThreatLabel = document.getElementById("highest-threat-label");
  const lastUpdatedLabel = document.getElementById("last-updated-label");

  const bestZone = data.summary_cards.best_zone;
  const highestThreatZone = data.summary_cards.highest_threat_zone;
  const bestZoneData = data.zone_rankings.find((row) => row.zone === bestZone);
  const recommendation = getRecommendationModel(data.zone_rankings);
  const lastUpdated = new Date(data.last_updated);

  heroBadges.innerHTML = [
    `${data.summary_cards.total_zones} zona analisis`,
    `${formatNumber(data.summary_cards.total_poi)} titik POI final`,
    `${data.summary_cards.total_kebab_competitors} kompetitor kebab`,
    "Data publik + OSM Overpass",
  ]
    .map(
      (text) => `
        <span class="tag-pill inline-flex items-center rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-clay bg-mist/60 border border-clay/10 shadow-sm">
          ${text}
        </span>
      `,
    )
    .join("");

  bestZoneLabel.textContent = bestZone || "-";
  bestZoneInsight.textContent = recommendation.heroInsight || bestZoneData?.insight || "Insight zona terbaik belum tersedia.";
  highestThreatLabel.textContent = highestThreatZone || "-";
  lastUpdatedLabel.textContent = lastUpdated.toLocaleString("id-ID", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function renderSummaryCards(summaryCards, recommendation) {
  const container = document.getElementById("summary-cards");
  const cards = [
    {
      label: "Total Zona",
      value: summaryCards.total_zones,
      note: "Wilayah analisis yang dibaca di dashboard",
    },
    {
      label: "Total POI",
      value: formatNumber(summaryCards.total_poi),
      note: "Hasil merge final baseline dan OSM",
    },
    {
      label: "Kompetitor Kebab",
      value: summaryCards.total_kebab_competitors,
      note: "Titik kompetitor kebab pada dataset final",
    },
    {
      label: "Overall Leader",
      value: summaryCards.best_zone,
      note: "Skor total tertinggi, tapi tekanannya juga besar",
    },
    {
      label: "Entry Candidate",
      value: recommendation.entryZone,
      note: "Kandidat masuk paling seimbang untuk ekspansi awal",
    },
  ];

  container.innerHTML = cards
    .map(
      (card) => `
        <article class="summary-card rounded-[1.6rem] border border-white/70 bg-paper p-5 shadow-soft">
          <p class="text-[11px] font-semibold uppercase tracking-[0.22em] text-smoke">${card.label}</p>
          <p class="mt-3 font-display text-3xl text-clay font-black">${card.value}</p>
          <p class="mt-3 text-xs leading-5 text-smoke">${card.note}</p>
        </article>
      `,
    )
    .join("");
}

function renderRankingChart(zoneRankings, selectedZone = null) {
  const ctx = document.getElementById("zoneRankingChart").getContext("2d");
  
  if (rankingChartInstance) {
    rankingChartInstance.destroy();
  }

  // Sort rankings by business potential score (descending)
  const sortedRankings = [...zoneRankings].sort((a, b) => b.business_potential_score - a.business_potential_score);
  const labels = sortedRankings.map(row => row.zone);
  const scores = sortedRankings.map(row => row.business_potential_score);

  const baseColors = [
    "#7b341e", // Clay for Rank 1
    "#dd5d21", // Ember
    "#6b635b", // Smoke
    "#f0b34a"  // Brass
  ];

  const backgroundColors = sortedRankings.map((row, index) => {
    const color = baseColors[index % baseColors.length];
    if (!selectedZone || row.zone === selectedZone) {
      return color;
    }
    return color + "26"; // ~15% opacity
  });

  rankingChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [{
        label: "Business Potential Score",
        data: scores,
        backgroundColor: backgroundColors,
        borderRadius: 8,
        borderWidth: 0,
        barThickness: 24
      }]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      onHover: (event, chartElement) => {
        event.native.target.style.cursor = chartElement[0] ? "pointer" : "default";
      },
      onClick: (event, elements) => {
        if (elements && elements.length > 0) {
          const clickedIndex = elements[0].index;
          const clickedZone = labels[clickedIndex];
          selectZone(clickedZone === selectedZone ? null : clickedZone);
        }
      },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#12100e",
          titleFont: { family: "Manrope", size: 12, weight: "bold" },
          bodyFont: { family: "Manrope", size: 11 },
          padding: 10,
          cornerRadius: 8,
          displayColors: false
        }
      },
      scales: {
        x: {
          max: 100,
          grid: { color: "rgba(18, 16, 14, 0.05)" },
          ticks: {
            font: { family: "Manrope", size: 10 },
            color: "#6b635b"
          }
        },
        y: {
          grid: { display: false },
          ticks: {
            font: { family: "Manrope", size: 11, weight: "bold" },
            color: "#12100e"
          }
        }
      }
    }
  });
}

function renderRankingInsights(zoneRankings, recommendation) {
  const container = document.getElementById("ranking-insights");
  container.innerHTML = zoneRankings
    .map(
      (row) => `
        <div class="rounded-[1.4rem] border border-white/10 bg-white/5 p-5">
          <div class="flex items-center justify-between gap-4">
            <p class="font-display text-2xl text-cream">${row.zone}</p>
            <span class="rounded-full border border-brass/20 bg-brass/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.22em] text-brass">${zoneBadge(row, recommendation)}</span>
          </div>
          <p class="mt-3 text-xs leading-6 text-white/80">${row.insight}</p>
        </div>
      `,
    )
    .join("");
}

function getRecommendationModel(zoneRankings) {
  const sorted = [...(zoneRankings || [])].sort(
    (a, b) => Number(a.rank || 999) - Number(b.rank || 999)
  );
  const overallLeader = sorted[0]?.zone || "-";

  const balancedCandidates = sorted
    .filter((row) => Number(row.business_potential_score || 0) >= 50)
    .sort((a, b) => {
      const scoreA = Number(a.business_potential_score || 0) - Number(a.threat_score || 0) * 0.22;
      const scoreB = Number(b.business_potential_score || 0) - Number(b.threat_score || 0) * 0.22;
      return scoreB - scoreA;
    });

  const entryZone = balancedCandidates[0]?.zone || overallLeader;
  const heroInsight =
    entryZone && entryZone !== overallLeader
      ? `${overallLeader} memimpin skor total, tetapi ${entryZone} terlihat paling seimbang untuk ekspansi awal karena ancamannya lebih rendah.`
      : sorted[0]?.insight || "";

  return {
    overallLeader,
    entryZone,
    heroInsight,
  };
}

function zoneBadge(row, recommendation) {
  if (row.zone === recommendation.overallLeader && row.zone === recommendation.entryZone) {
    return `Rank ${row.rank}`;
  }
  if (row.zone === recommendation.overallLeader) {
    return "Overall Leader";
  }
  if (row.zone === recommendation.entryZone) {
    return "Entry Candidate";
  }
  return `Rank ${row.rank}`;
}

async function initMapStructure(bestZone) {
  if (mapInstance) return;

  // Center on Sleman Selatan (Yogyakarta-Sleman border area)
  mapInstance = L.map("poi-map", { 
    scrollWheelZoom: true,
    zoomControl: true,
    zoomSnap: 0.5,
    zoomDelta: 0.5,
    wheelPxPerZoomLevel: 120
  }).setView([-7.758, 110.378], 12);

  // Add custom zoom control position
  mapInstance.zoomControl.setPosition('bottomright');
  
  // Use CartoDB Positron basemap
  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    attribution: '&copy; OpenStreetMap &copy; CARTO',
    maxZoom: 19,
  }).addTo(mapInstance);

  mapLayerGroup = L.layerGroup().addTo(mapInstance);
  bboxLayerGroup = L.layerGroup().addTo(mapInstance);

  try {
    const response = await fetch("./data/zone_boundaries.geojson");
    if (!response.ok) throw new Error("Gagal memuat zone_boundaries.geojson");
    const geojsonData = await response.json();

    L.geoJSON(geojsonData, {
      style: (feature) => {
        const zoneKey = feature.properties.name;
        const isRecommended = zoneKey === bestZone;
        
        return {
          color: isRecommended ? "#7b341e" : "#6b635b",
          weight: isRecommended ? 3.5 : 1.5,
          dashArray: isRecommended ? "6, 4" : "4, 6",
          opacity: isRecommended ? 0.95 : 0.4,
          fillColor: isRecommended ? "#dd5d21" : "#64748B",
          fillOpacity: isRecommended ? 0.06 : 0.01
        };
      },
      onEachFeature: (feature, layer) => {
        const zoneKey = feature.properties.name;
        const isRecommended = zoneKey === bestZone;
        const config = zoneBboxConfig[zoneKey];
        const dispName = config ? config.name : zoneKey;

        const tooltipText = isRecommended 
          ? `<b>${dispName}</b><br><span class="text-clay font-bold text-[10px]">REKOMENDASI UTAMA</span>`
          : `<b>${dispName}</b>`;

        layer.bindTooltip(tooltipText, {
          sticky: true,
          className: isRecommended ? "border-clay text-xs font-semibold" : "text-xs text-smoke"
        });

        // Interactive behaviors
        layer.on("click", () => {
          selectZone(zoneKey);
        });

        layer.on("mouseover", (e) => {
          const pathEl = e.target.getElement();
          if (pathEl) {
            pathEl.style.cursor = "pointer";
          }
        });

        layer.addTo(bboxLayerGroup);
        zoneRectangleLayers[zoneKey] = layer;
      }
    });
  } catch (err) {
    console.error("Fallback ke bounding box rectangle karena:", err);
    // Draw bounding boxes for all 4 zones as fallback
    Object.entries(zoneBboxConfig).forEach(([zoneKey, config]) => {
      const isRecommended = zoneKey === bestZone;
      const borderWeight = isRecommended ? 3.5 : 1.5;
      const borderDash = isRecommended ? "6, 4" : "4, 6";
      const borderOpacity = isRecommended ? 0.95 : 0.4;
      const fillColor = isRecommended ? "#dd5d21" : "#64748B";
      const fillOpacity = isRecommended ? 0.06 : 0.01;
      const borderColor = isRecommended ? "#7b341e" : "#6b635b";

      const rectangle = L.rectangle(config.bounds, {
        color: borderColor,
        weight: borderWeight,
        dashArray: borderDash,
        opacity: borderOpacity,
        fillColor: fillColor,
        fillOpacity: fillOpacity
      });

      const tooltipText = isRecommended 
        ? `<b>${config.name}</b><br><span class="text-clay font-bold text-[10px]">REKOMENDASI UTAMA</span>`
        : `<b>${config.name}</b>`;

      rectangle.bindTooltip(tooltipText, {
        sticky: true,
        className: isRecommended ? "border-clay text-xs font-semibold" : "text-xs text-smoke"
      });

      rectangle.on("click", () => {
        selectZone(zoneKey);
      });

      rectangle.on("mouseover", (e) => {
        const pathEl = e.target.getElement();
        if (pathEl) {
          pathEl.style.cursor = "pointer";
        }
      });

      rectangle.addTo(bboxLayerGroup);
      zoneRectangleLayers[zoneKey] = rectangle;
    });
  }
}

function renderMapLegend() {
  const legend = document.getElementById("map-legend");
  
  legend.innerHTML = Object.entries(categoryPalette)
    .map(([catKey, value]) => {
      const count = allPois.filter((poi) => poi.category === catKey).length;
      const isActive = activeCategories.has(catKey);
      
      return `
        <button 
          onclick="toggleMapCategory('${catKey}')"
          class="map-filter-button transition duration-150 flex items-center gap-2 cursor-pointer ${isActive ? "" : "is-inactive"}"
          id="legend-pill-${catKey}"
        >
          <span class="marker-dot" style="background:${value.color}"></span>
          <span>${value.label}</span>
          <span class="font-mono text-[9px] bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded-full">${count}</span>
        </button>
      `;
    })
    .join("");
}

window.toggleMapCategory = function(catKey) {
  if (activeCategories.has(catKey)) {
    if (activeCategories.size > 1) {
      activeCategories.delete(catKey);
    }
  } else {
    activeCategories.add(catKey);
  }
  renderMapLegend();
  updateMapMarkers();
};

function updateMapMarkers() {
  if (!mapInstance || !mapLayerGroup) return;

  mapLayerGroup.clearLayers();
  poiMarkersMap.clear();

  const filteredPois = allPois.filter((poi) => {
    const isCategoryActive = activeCategories.has(poi.category);
    const isZoneMatch = !selectedZone || poi.zone === selectedZone;
    return isCategoryActive && isZoneMatch;
  });

  filteredPois.forEach((poi) => {
    const lat = Number(poi.latitude);
    const lon = Number(poi.longitude);
    if (Number.isNaN(lat) || Number.isNaN(lon)) return;

    const categoryStyle = categoryPalette[poi.category] || categoryPalette.other;
    const isDirectCompetitor = poi.category === "direct_kebab_competitor";
    const isSelected = highlightedPoiId === poi.poi_id;

    const marker = L.circleMarker([lat, lon], {
      radius: isSelected ? (isDirectCompetitor ? 12 : 9) : (isDirectCompetitor ? 8 : 4.5),
      color: isSelected ? "#dd5d21" : "#ffffff",
      weight: isSelected ? 3.5 : (isDirectCompetitor ? 2.5 : 1),
      fillColor: isSelected ? "#f0b34a" : categoryStyle.color,
      fillOpacity: isSelected ? 1.0 : 0.85,
    });

    marker.bindPopup(`
      <div class="max-w-[220px] text-xs font-sans">
        <div class="flex items-center gap-1.5">
          <span class="text-xs">${categoryStyle.icon || "📍"}</span>
          <span class="text-[9px] font-bold uppercase tracking-wider" style="color:${categoryStyle.color}">
            ${categoryStyle.label}
          </span>
        </div>
        <p class="mt-1.5 text-sm font-bold text-slate-900">${poi.name || "Tanpa nama"}</p>
        <p class="mt-1 text-[11px] leading-relaxed text-slate-600">${poi.address || "Alamat tidak tersedia."}</p>
        <div class="mt-2 border-t border-slate-100 pt-1.5 text-[10px] text-slate-500 space-y-0.5">
          <div><b>Zona:</b> ${poi.zone || "-"}</div>
          <div><b>Sumber:</b> ${poi.source || "-"}</div>
          <div><b>Catatan:</b> ${poi.notes || "-"}</div>
        </div>
      </div>
    `);

    marker.on("click", () => {
      selectPoi(poi);
    });

    marker.addTo(mapLayerGroup);
    if (isSelected) {
      marker.bringToFront();
    }
    poiMarkersMap.set(poi.poi_id, marker);
  });
}

function highlightMarker(poiId) {
  // Restore previously highlighted marker style
  if (highlightedPoiId) {
    const prevMarker = poiMarkersMap.get(highlightedPoiId);
    if (prevMarker) {
      const prevPoi = allPois.find(p => p.poi_id === highlightedPoiId);
      if (prevPoi) {
        const categoryStyle = categoryPalette[prevPoi.category] || categoryPalette.other;
        const isDirectCompetitor = prevPoi.category === "direct_kebab_competitor";
        prevMarker.setStyle({
          radius: isDirectCompetitor ? 8 : 4.5,
          color: "#ffffff",
          weight: isDirectCompetitor ? 2.5 : 1,
          fillColor: categoryStyle.color,
          fillOpacity: 0.85
        });
      }
    }
  }

  // Highlight new marker style
  highlightedPoiId = poiId;
  if (poiId) {
    const marker = poiMarkersMap.get(poiId);
    if (marker) {
      const poi = allPois.find(p => p.poi_id === poiId);
      const isDirectCompetitor = poi && poi.category === "direct_kebab_competitor";
      marker.setStyle({
        radius: isDirectCompetitor ? 12 : 9,
        color: "#dd5d21",
        weight: 3.5,
        fillColor: "#f0b34a",
        fillOpacity: 1.0
      });
      marker.bringToFront();
    }
  }
}

function renderMetricsComparisonChart(zoneSummary, selectedZone = null) {
  const ctx = document.getElementById("zoneMetricsComparisonChart").getContext("2d");

  if (comparisonChartInstance) {
    comparisonChartInstance.destroy();
  }

  const labels = zoneSummary.map(z => z.zone);
  const kebabCounts = zoneSummary.map(z => z.direct_kebab_competitor_count);
  const culinaryCounts = zoneSummary.map(z => z.culinary_activity_count);
  const educationCounts = zoneSummary.map(z => z.education_count);
  const retailCounts = zoneSummary.map(z => z.retail_count);

  const getColors = (baseColor) => {
    return zoneSummary.map(z => {
      if (!selectedZone || z.zone === selectedZone) {
        return baseColor;
      }
      return baseColor + "22"; // Dimmed (13% opacity)
    });
  };

  comparisonChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Pesaing Kebab",
          data: kebabCounts,
          backgroundColor: getColors("#B64419"),
          borderRadius: 4
        },
        {
          label: "Kuliner",
          data: culinaryCounts,
          backgroundColor: getColors("#dd5d21"),
          borderRadius: 4
        },
        {
          label: "Pendidikan",
          data: educationCounts,
          backgroundColor: getColors("#2563EB"),
          borderRadius: 4
        },
        {
          label: "Ritel",
          data: retailCounts,
          backgroundColor: getColors("#059669"),
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      onHover: (event, chartElement) => {
        event.native.target.style.cursor = chartElement[0] ? "pointer" : "default";
      },
      onClick: (event, elements) => {
        if (elements && elements.length > 0) {
          const clickedIndex = elements[0].index;
          const clickedZone = labels[clickedIndex];
          selectZone(clickedZone === selectedZone ? null : clickedZone);
        }
      },
      plugins: {
        legend: {
          position: "top",
          labels: {
            font: { family: "Manrope", size: 9 },
            boxWidth: 8,
            padding: 6
          }
        },
        tooltip: {
          backgroundColor: "#12100e",
          titleFont: { family: "Manrope", size: 11, weight: "bold" },
          bodyFont: { family: "Manrope", size: 10 },
          padding: 8,
          cornerRadius: 6
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { family: "Manrope", size: 9 },
            color: "#6b635b"
          }
        },
        y: {
          grid: { color: "rgba(18, 16, 14, 0.05)" },
          ticks: {
            font: { family: "Manrope", size: 9 },
            color: "#6b635b"
          }
        }
      }
    }
  });
}

function renderZoneSummary(zoneSummary) {
  const tbody = document.getElementById("zone-summary-table");
  tbody.innerHTML = zoneSummary
    .map(
      (row) => {
        const isHighlighted = selectedZone === row.zone;
        return `
          <tr 
            onclick="selectZone('${row.zone}' === selectedZone ? null : '${row.zone}')"
            class="hover:bg-white/70 border-b border-black/5 cursor-pointer transition ${isHighlighted ? 'table-row-highlight' : ''}"
          >
            <td class="px-4 py-3.5 font-semibold text-cocoa">${row.zone}</td>
            <td class="px-4 py-3.5 font-mono">${row.direct_kebab_competitor_count}</td>
            <td class="px-4 py-3.5 font-mono">${row.culinary_activity_count}</td>
            <td class="px-4 py-3.5 font-mono">${row.education_count}</td>
            <td class="px-4 py-3.5 font-mono">${row.accommodation_count}</td>
            <td class="px-4 py-3.5 font-mono">${row.retail_count}</td>
            <td class="px-4 py-3.5 font-semibold text-clay font-mono">${formatNumber(row.total_poi_count)}</td>
          </tr>
        `;
      }
    )
    .join("");
}

function renderMenuTable(menuRows) {
  const tbody = document.getElementById("menu-table");
  tbody.innerHTML = menuRows
    .map(
      (row) => `
        <tr class="hover:bg-white/70 border-b border-black/5">
          <td class="px-4 py-3.5">
            <p class="font-semibold text-cocoa">${row.menu_name}</p>
            <p class="mt-1 text-xs text-smoke font-light">${row.notes || "-"}</p>
          </td>
          <td class="px-4 py-3.5 capitalize text-smoke">${row.category || "-"}</td>
          <td class="px-4 py-3.5 text-smoke">${row.variant || "-"}</td>
          <td class="px-4 py-3.5 font-semibold text-clay font-mono">${formatPrice(row)}</td>
          <td class="px-4 py-3.5">
            <span class="${confidenceBadgeClass(row.confidence)}">${row.confidence || "-"}</span>
          </td>
        </tr>
      `,
    )
    .join("");
}

function renderCompetitorTable(rows) {
  const tbody = document.getElementById("competitor-table");
  
  // Filter by selected zone
  const filteredRows = selectedZone ? rows.filter(r => r.zone === selectedZone) : rows;

  if (filteredRows.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="px-4 py-8 text-center text-smoke italic">
          Tidak ada data kompetitor untuk zona ${selectedZone}.
        </td>
      </tr>
    `;
    return;
  }

  tbody.innerHTML = filteredRows
    .map(
      (row) => {
        // Find if this competitor has spatial representation on our POI map
        const poi = allPois.find(p => 
          p.category === "direct_kebab_competitor" && 
          p.name && 
          row.competitor_name && 
          (p.name.toLowerCase().includes(row.competitor_name.toLowerCase()) || 
           row.competitor_name.toLowerCase().includes(p.name.toLowerCase()))
        );

        const clickableAttr = poi ? `onclick="selectPoiById('${poi.poi_id}')"` : '';
        const cursorClass = poi ? 'cursor-pointer hover:bg-brass/5' : '';

        return `
          <tr ${clickableAttr} class="border-b border-black/5 transition ${cursorClass}">
            <td class="px-4 py-3.5">
              <div class="flex items-center gap-1">
                <p class="font-semibold text-cocoa">${row.competitor_name}</p>
                ${poi ? `<span class="inline-block text-[10px] text-ember animate-pulse" title="Klik untuk lihat di peta">📍</span>` : ''}
              </div>
              <p class="mt-1 text-xs text-smoke font-light max-w-[180px] truncate" title="${row.area_detail || ""}">${row.area_detail || "-"}</p>
            </td>
            <td class="px-4 py-3.5 text-smoke">${row.zone || "-"}</td>
            <td class="px-4 py-3.5 text-smoke">${row.menu_name || "-"}</td>
            <td class="px-4 py-3.5">
              <p class="font-semibold text-clay font-mono">${row.price_idr ? `Rp${formatNumber(row.price_idr)}` : "-"}</p>
              ${priceValidationHint(row.price_validation_level)}
            </td>
            <td class="px-4 py-3.5 text-center">
              <span class="${confidenceBadgeClass(row.confidence)}">${row.confidence || "-"}</span>
            </td>
          </tr>
        `;
      }
    )
    .join("");
}

function renderSwot(swot) {
  const grid = document.getElementById("swot-grid");
  const cards = [
    { key: "strengths", title: "Strength", tone: "border-emerald-200 bg-emerald-50/20 text-emerald-950", icon: "💪" },
    { key: "weaknesses", title: "Weakness", tone: "border-rose-200 bg-rose-50/20 text-rose-950", icon: "⚠️" },
    { key: "opportunities", title: "Opportunity", tone: "border-sky-200 bg-sky-50/20 text-sky-950", icon: "📈" },
    { key: "threats", title: "Threat", tone: "border-amber-200 bg-amber-50/20 text-amber-950", icon: "⚡" },
  ];

  grid.innerHTML = cards
    .map((card) => {
      const items = swot[card.key] || [];
      
      // Filter SWOT items based on active selected zone
      const filteredItems = items.filter(item => {
        if (!selectedZone) return true;
        const itemZone = item.zone ? item.zone.toLowerCase() : "";
        const targetZone = selectedZone.toLowerCase();
        return itemZone === targetZone || itemZone === "all" || itemZone === "sleman selatan";
      });

      return `
        <article class="swot-card rounded-[1.6rem] border ${card.tone} p-4 flex flex-col justify-between">
          <div>
            <h3 class="font-display text-xl text-cocoa flex items-center gap-1.5 border-b border-black/5 pb-2 mb-3">
              <span>${card.icon}</span> ${card.title}
            </h3>
            <div class="space-y-3">
              ${filteredItems
                .map(
                  (item) => {
                    const isZoneSpecific = selectedZone && item.zone && item.zone.toLowerCase() === selectedZone.toLowerCase();
                    const cardHighlightClass = isZoneSpecific 
                      ? 'border-ember shadow-sm ring-1 ring-ember/35 bg-white scale-[1.01]' 
                      : 'border-black/5 bg-white';
                    
                    return `
                      <div class="rounded-xl border p-3 space-y-1 transition duration-150 ${cardHighlightClass}">
                        <div class="flex items-center gap-2">
                          <span class="rounded bg-slate-900 px-1.5 py-0.5 text-[9px] font-bold text-white font-mono">${item.factor_code}</span>
                          <p class="font-bold text-xs text-cocoa leading-tight">${item.factor_title}</p>
                        </div>
                        <p class="text-[10px] text-smoke leading-normal">${item.evidence}</p>
                        <div class="rounded bg-slate-50 border border-slate-100 p-1.5 text-[9px] text-cocoa mt-1.5">
                          <span class="font-semibold text-paprika">💡 Aksi:</span> ${item.recommendation}
                        </div>
                      </div>
                    `;
                  }
                )
                .join("")}
              ${filteredItems.length === 0 ? '<p class="text-xs text-smoke italic">Tidak ada data untuk zona ini.</p>' : ''}
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderError(error) {
  document.body.innerHTML = `
    <main class="min-h-screen bg-sand p-8 text-cocoa">
      <div class="mx-auto max-w-2xl rounded-[2rem] border border-rose-200 bg-white p-8 shadow-panel">
        <p class="text-xs font-semibold uppercase tracking-[0.24em] text-rose-700">Dashboard Error</p>
        <h1 class="mt-4 font-display text-4xl">Gagal memuat data dashboard</h1>
        <p class="mt-4 text-xs leading-5 text-smoke">
          Pastikan file <code>web/data/landing_page_data.json</code> tersedia dan dibuka melalui server lokal.
        </p>
        <pre class="mt-6 overflow-auto rounded-2xl bg-rose-50 p-4 text-[10px] text-rose-800 font-mono">${error.message}</pre>
      </div>
    </main>
  `;
}

function confidenceBadgeClass(confidence) {
  if (confidence === "high") {
    return "inline-flex rounded border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-emerald-700";
  }
  if (confidence === "medium") {
    return "inline-flex rounded border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-amber-700";
  }
  return "inline-flex rounded border border-rose-200 bg-rose-50 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.12em] text-rose-700";
}

function priceValidationHint(level) {
  if (level === "outlet_specific") {
    return '<p class="mt-1 text-[10px] font-medium uppercase tracking-[0.08em] text-smoke">outlet</p>';
  }
  if (level === "benchmark_brand_level") {
    return '<p class="mt-1 text-[10px] font-medium uppercase tracking-[0.08em] text-smoke">brand</p>';
  }
  return "";
}

function formatPrice(row) {
  const current = Number(row.price_current_idr || 0);
  const min = Number(row.price_min_idr || 0);
  const max = Number(row.price_max_idr || 0);

  if (current) {
    return `Rp${formatNumber(current)}`;
  }
  if (min && max && min === max) {
    return `Rp${formatNumber(min)}`;
  }
  if (min && max) {
    return `Rp${formatNumber(min)} - Rp${formatNumber(max)}`;
  }
  return "-";
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString("id-ID");
}

function formatScore(value) {
  return Number(value || 0).toFixed(2).replace(/\.00$/, "");
}

// ==========================================
// INTERACTIVE MAP & DASHBOARD FUNCTIONS
// ==========================================

window.selectZone = function(zoneName) {
  selectedZone = zoneName;
  selectedPoi = null;

  // Show the floating panel if it was collapsed
  const detailPanel = document.getElementById("map-detail-panel");
  if (detailPanel && zoneName) {
    detailPanel.classList.remove("is-collapsed");
  }

  // 1. Update quick selectors UI
  document.querySelectorAll(".zone-selector-btn").forEach(btn => {
    const isAll = zoneName === null && btn.getAttribute("data-zone") === "all";
    const isTarget = btn.getAttribute("data-zone") === zoneName;
    if (isAll || isTarget) {
      btn.classList.add("is-active");
    } else {
      btn.classList.remove("is-active");
    }
  });

  // 2. Adjust map view
  if (!zoneName) {
    mapInstance.setView([-7.758, 110.378], 12);
  } else {
    const config = zoneBboxConfig[zoneName];
    if (config) {
      mapInstance.fitBounds(config.bounds, { padding: [30, 30] });
    }
  }

  // 3. Highlight bounding box rectangles
  Object.entries(zoneRectangleLayers).forEach(([zKey, rect]) => {
    const isSelected = selectedZone === zKey;
    const isNoneSelected = !selectedZone;
    const isBest = zKey === bestZoneGlobal;
    
    let opacity = 0.4;
    let fillOpacity = 0.01;
    let weight = 1.5;
    let dashArray = "4, 6";
    let color = "#6b635b";
    
    if (isSelected) {
      opacity = 0.95;
      fillOpacity = 0.07;
      weight = 4;
      dashArray = null;
      color = "#dd5d21";
    } else if (!isNoneSelected) {
      opacity = 0.08;
      fillOpacity = 0.005;
      weight = 0.5;
      color = "#6b635b";
    } else if (isBest) {
      opacity = 0.95;
      fillOpacity = 0.06;
      weight = 3.5;
      dashArray = "6, 4";
      color = "#7b341e";
    }
    
    rect.setStyle({
      color: color,
      weight: weight,
      dashArray: dashArray,
      opacity: opacity,
      fillOpacity: fillOpacity
    });
  });

  // 4. Update dynamic dashboard content
  const data = globalDashboardData;
  if (data) {
    renderRankingChart(data.zone_rankings, selectedZone);
    renderMetricsComparisonChart(data.zone_summary, selectedZone);
    renderZoneSummary(data.zone_summary);
    renderCompetitorTable(data.competitors);
    renderSwot(data.swot);
  }

  // Filter map markers by active zone
  updateMapMarkers();

  // 5. Update detail panel
  updateDetailPanel();
  
  // 6. Clear search input text
  const searchInput = document.getElementById("map-search-input");
  if (searchInput) {
    searchInput.value = "";
    const clearBtn = document.getElementById("search-clear-btn");
    if (clearBtn) clearBtn.classList.add("hidden");
  }
};

window.selectPoi = function(poi) {
  selectedPoi = poi;
  
  // Show the floating panel if it was collapsed
  const detailPanel = document.getElementById("map-detail-panel");
  if (detailPanel) {
    detailPanel.classList.remove("is-collapsed");
  }
  // Ensure its category is enabled
  if (!activeCategories.has(poi.category)) {
    activeCategories.add(poi.category);
    renderMapLegend();
    updateMapMarkers();
  }

  // Highlight marker on map
  highlightMarker(poi.poi_id);

  // Update input text with POI name
  const searchInput = document.getElementById("map-search-input");
  if (searchInput) {
    searchInput.value = poi.name || "";
    const clearBtn = document.getElementById("search-clear-btn");
    if (clearBtn) clearBtn.classList.remove("hidden");
  }

  updateDetailPanel();
};

window.selectPoiById = function(poiId) {
  const poi = allPois.find(p => p.poi_id === poiId);
  if (!poi) return;

  // Zoom to marker coordinate
  const lat = Number(poi.latitude);
  const lon = Number(poi.longitude);
  if (!Number.isNaN(lat) && !Number.isNaN(lon)) {
    mapInstance.flyTo([lat, lon], 16, { animate: true, duration: 1.2 });
  }

  selectPoi(poi);

  // Open leaflet popup after panning completes
  setTimeout(() => {
    const marker = poiMarkersMap.get(poiId);
    if (marker) {
      marker.openPopup();
    }
  }, 350);
};

window.renderZoneQuickSelectors = function() {
  const selector = document.getElementById("zone-quick-selector");
  if (!selector) return;

  const zones = ["Depok", "Mlati", "Ngaglik Selatan", "Gamping"];
  
  let html = `
    <button 
      onclick="selectZone(null)" 
      data-zone="all" 
      class="zone-selector-btn is-active"
    >
      Semua
    </button>
  `;

  zones.forEach(zone => {
    html += `
      <button 
        onclick="selectZone('${zone}')" 
        data-zone="${zone}" 
        class="zone-selector-btn"
      >
        ${zone}
      </button>
    `;
  });

  selector.innerHTML = html;
};

window.initDetailPanel = function() {
  const panel = document.getElementById("map-detail-panel");
  if (!panel) return;

  panel.innerHTML = `
    <button class="panel-close-btn" onclick="toggleDetailPanel()" title="Tutup panel">
      <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
      </svg>
    </button>
    <div class="search-container mb-4 mt-1">
      <div class="relative">
        <input 
          type="text" 
          id="map-search-input" 
          placeholder="Cari tempat / kompetitor..." 
          class="w-full rounded-full border border-black/10 px-4 py-2.5 pl-9 text-xs focus:outline-none focus:border-ember focus:ring-1 focus:ring-ember bg-white text-ink shadow-sm"
          oninput="handleSearchInput(this.value)"
        >
        <span class="absolute left-3.5 top-3 text-smoke text-xs">
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
          </svg>
        </span>
        <button id="search-clear-btn" class="absolute right-3 top-3 text-smoke hover:text-ink hidden cursor-pointer" onclick="clearSearch(event)">
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
          </svg>
        </button>
      </div>
      <div id="map-search-suggestions" class="autocomplete-suggestions hidden"></div>
    </div>
    
    <div id="map-detail-content" class="flex-grow overflow-y-auto pr-1">
      <!-- Dynamic detailed content -->
    </div>
  `;
};

// Toggle floating detail panel visibility
window.toggleDetailPanel = function() {
  const panel = document.getElementById("map-detail-panel");
  if (!panel) return;
  panel.classList.toggle("is-collapsed");
  
  // If panel is closed/collapsed, reset selection state
  if (panel.classList.contains("is-collapsed")) {
    selectedPoi = null;
    highlightMarker(null);
    
    // Clear search input text
    const searchInput = document.getElementById("map-search-input");
    if (searchInput) {
      searchInput.value = "";
      const clearBtn = document.getElementById("search-clear-btn");
      if (clearBtn) clearBtn.classList.add("hidden");
    }

    if (selectedZone) {
      selectZone(null);
    } else {
      clearPoiSelection();
    }
  }

  // Invalidate map size when panel toggles
  setTimeout(() => { if (mapInstance) mapInstance.invalidateSize(); }, 400);
};

// Toggle map legend visibility
window.toggleMapLegend = function() {
  const legend = document.getElementById("map-legend");
  const toggleText = document.getElementById("legend-toggle-text");
  if (!legend) return;
  legend.classList.toggle("is-hidden");
  if (toggleText) {
    toggleText.textContent = legend.classList.contains("is-hidden") ? "Tampilkan" : "Sembunyikan";
  }
};

// Toggle map fullscreen mode
window.toggleMapFullscreen = function() {
  const wrapper = document.getElementById("map-wrapper");
  const label = document.getElementById("fullscreen-label");
  if (!wrapper) return;
  
  wrapper.classList.toggle("is-fullscreen");
  const isFs = wrapper.classList.contains("is-fullscreen");
  
  if (label) {
    label.textContent = isFs ? "Keluar" : "Perbesar";
  }
  
  // Prevent body scroll when fullscreen
  document.body.style.overflow = isFs ? "hidden" : "";
  
  // Invalidate map size after transition
  setTimeout(() => { 
    if (mapInstance) mapInstance.invalidateSize();
  }, 100);
};

// Handle Escape key to exit fullscreen
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    const wrapper = document.getElementById("map-wrapper");
    if (wrapper && wrapper.classList.contains("is-fullscreen")) {
      toggleMapFullscreen();
    }
  }
});

// Render zone metrics summary in the dark card below map
function renderZoneMetricsSummary(zoneSummary) {
  const container = document.getElementById("zone-metrics-summary");
  if (!container || !zoneSummary) return;

  container.innerHTML = zoneSummary.map(zone => {
    const isBest = zone.zone === bestZoneGlobal;
    return `
      <div class="zone-metric-row" onclick="selectZone('${zone.zone}')" style="cursor:pointer">
        <div class="flex items-center gap-2.5">
          <span class="h-6 w-6 rounded-full flex items-center justify-center text-[10px] font-bold ${isBest ? 'bg-brass text-ink' : 'bg-white/10 text-white/60'}">
            ${isBest ? '⭐' : '📍'}
          </span>
          <div>
            <span class="font-bold text-sm block">${zone.zone}</span>
            <span class="text-[10px] text-white/50 uppercase">${zone.total_poi_count} POI</span>
          </div>
        </div>
        <div class="flex items-center gap-3 text-[11px]">
          <span class="font-mono" title="Kompetitor Kebab">⚔️ ${zone.direct_kebab_competitor_count}</span>
          <span class="font-mono" title="Kuliner">🍜 ${zone.culinary_activity_count}</span>
          <span class="font-mono" title="Pendidikan">🎓 ${zone.education_count}</span>
          <span class="text-white/30">→</span>
        </div>
      </div>
    `;
  }).join("");
}

window.updateDetailPanel = function() {
  const content = document.getElementById("map-detail-content");
  if (!content) return;

  if (selectedPoi) {
    const style = categoryPalette[selectedPoi.category] || categoryPalette.other;
    const notesStr = selectedPoi.notes || "-";
    const addressStr = selectedPoi.address || "Alamat tidak dicatat secara spesifik.";
    const isCompetitor = selectedPoi.category === "direct_kebab_competitor";

    let competitorBenchmarkLink = "";
    if (isCompetitor && globalDashboardData) {
      const compRow = globalDashboardData.competitors.find(c => 
        c.competitor_name.toLowerCase().includes(selectedPoi.name.toLowerCase()) ||
        selectedPoi.name.toLowerCase().includes(c.competitor_name.toLowerCase())
      );
      if (compRow) {
        competitorBenchmarkLink = `
          <div class="mt-4 border-t border-black/5 pt-3">
            <p class="text-[9px] font-bold uppercase tracking-wider text-smoke">Data Benchmark Harga</p>
            <div class="mt-2 grid grid-cols-2 gap-2 text-xs bg-mist/40 p-2.5 rounded-xl border border-black/5">
              <div>
                <span class="text-smoke block text-[9px] uppercase">Menu Utama</span>
                <span class="font-bold text-ink truncate block max-w-[120px]" title="${compRow.menu_name || '-'}">${compRow.menu_name || "-"}</span>
              </div>
              <div>
                <span class="text-smoke block text-[9px] uppercase">Harga</span>
                <span class="font-semibold text-clay font-mono">${compRow.price_idr ? `Rp${formatNumber(compRow.price_idr)}` : "-"}</span>
              </div>
            </div>
          </div>
        `;
      }
    }

    content.innerHTML = `
      <div class="space-y-4 animate-[fadeIn_200ms_ease]">
        <div class="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[9px] font-extrabold uppercase tracking-wider text-white" style="background:${style.color}">
          <span>${style.icon}</span>
          <span>${style.label}</span>
        </div>
        
        <div>
          <h4 class="font-display text-lg text-ink leading-snug">${selectedPoi.name || "Tanpa Nama"}</h4>
          <p class="mt-2 text-xs text-smoke leading-relaxed font-light">${addressStr}</p>
        </div>

        <div class="space-y-2 border-t border-black/5 pt-3">
          <div class="flex justify-between text-xs">
            <span class="text-smoke">Zona Wilayah</span>
            <span class="font-bold text-ink hover:text-clay cursor-pointer" onclick="selectZone('${selectedPoi.zone}')">${selectedPoi.zone || "-"} &rarr;</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-smoke">Validitas Data</span>
            <span class="${confidenceBadgeClass(selectedPoi.confidence || 'medium')}">${selectedPoi.confidence || 'verified'}</span>
          </div>
          <div class="flex justify-between text-xs">
            <span class="text-smoke">Sumber</span>
            <span class="font-medium text-ink truncate max-w-[150px]" title="${selectedPoi.source}">${selectedPoi.source || "-"}</span>
          </div>
        </div>

        <div class="bg-mist/30 border border-black/5 p-3 rounded-xl">
          <p class="text-[9px] font-bold uppercase tracking-wider text-smoke mb-1">Catatan Lapangan</p>
          <p class="text-xs text-smoke leading-relaxed italic">${notesStr}</p>
        </div>

        ${competitorBenchmarkLink}

        <div class="pt-2">
          <button onclick="clearPoiSelection()" class="w-full rounded-full border border-black/10 py-2 text-center text-xs font-bold text-smoke hover:bg-black/5 transition cursor-pointer">
            Kembali ke Ikhtisar
          </button>
        </div>
      </div>
    `;
  } else if (selectedZone) {
    const zConfig = zoneBboxConfig[selectedZone];
    const data = globalDashboardData;
    const rankingData = data ? data.zone_rankings.find(r => r.zone === selectedZone) : null;
    const summaryData = data ? data.zone_summary.find(s => s.zone === selectedZone) : null;

    let statsHtml = "";
    if (summaryData) {
      statsHtml = `
        <div class="grid grid-cols-2 gap-2 mt-3">
          <div class="map-card-stat">
            <span class="block text-[22px]">⚔️</span>
            <span class="block text-lg font-bold font-mono text-clay mt-1">${summaryData.direct_kebab_competitor_count}</span>
            <span class="text-[9px] text-smoke uppercase font-semibold">Pesaing Kebab</span>
          </div>
          <div class="map-card-stat">
            <span class="block text-[22px]">🍜</span>
            <span class="block text-lg font-bold font-mono text-clay mt-1">${summaryData.culinary_activity_count}</span>
            <span class="text-[9px] text-smoke uppercase font-semibold">Usaha Kuliner</span>
          </div>
          <div class="map-card-stat">
            <span class="block text-[22px]">🎓</span>
            <span class="block text-lg font-bold font-mono text-clay mt-1">${summaryData.education_count}</span>
            <span class="text-[9px] text-smoke uppercase font-semibold">Institusi Pend.</span>
          </div>
          <div class="map-card-stat">
            <span class="block text-[22px]">🛒</span>
            <span class="block text-lg font-bold font-mono text-clay mt-1">${summaryData.retail_count}</span>
            <span class="text-[9px] text-smoke uppercase font-semibold">Fasilitas Ritel</span>
          </div>
        </div>
      `;
    }

    // Calculate Price Comparison
    let priceComparisonHtml = "";
    if (data) {
      // Average Mbak Kebab price
      const mbakKebabPrices = data.mbak_kebab_menu
        .map(m => Number(m.price_current_idr || m.price_min_idr || 0))
        .filter(p => p > 0);
      const mbakKebabAvg = mbakKebabPrices.reduce((a, b) => a + b, 0) / mbakKebabPrices.length;

      // Average Competitor price in active zone
      const competitorPrices = data.competitors
        .filter(c => c.zone === selectedZone && c.price_idr)
        .map(c => Number(c.price_idr));
      
      const competitorAvg = competitorPrices.length > 0
        ? competitorPrices.reduce((a, b) => a + b, 0) / competitorPrices.length
        : 0;

      if (competitorAvg > 0 && mbakKebabAvg > 0) {
        const gapPercent = Math.round(((competitorAvg - mbakKebabAvg) / competitorAvg) * 100);
        const gapText = gapPercent > 0 
          ? `<span class="text-emerald-700 font-extrabold">${gapPercent}% lebih murah</span> dibanding kompetitor`
          : `<span class="text-clay font-extrabold">${Math.abs(gapPercent)}% lebih premium</span> dibanding kompetitor`;

        priceComparisonHtml = `
          <div class="mt-4 border-t border-black/5 pt-3.5">
            <p class="text-[10px] font-bold uppercase tracking-wider text-smoke mb-2">Benchmark Harga Wilayah</p>
            <div class="bg-mist/30 p-3 rounded-xl border border-black/5 text-xs space-y-1.5">
              <div class="flex justify-between">
                <span class="text-smoke">Rata-rata Pasar:</span>
                <span class="font-semibold text-cocoa font-mono">Rp${formatNumber(Math.round(competitorAvg))}</span>
              </div>
              <div class="flex justify-between">
                <span class="text-smoke">Mbak Kebab:</span>
                <span class="font-bold text-clay font-mono">Rp${formatNumber(Math.round(mbakKebabAvg))}</span>
              </div>
              <div class="border-t border-black/5 pt-1.5 text-[11px] text-cocoa text-center">
                💡 ${gapText}!
              </div>
            </div>
          </div>
        `;
      }
    }

    let radarChartContainerHtml = "";
    if (rankingData) {
      radarChartContainerHtml = `
        <div class="mt-4 border-t border-black/5 pt-3.5">
          <p class="text-[10px] font-bold uppercase tracking-wider text-smoke mb-2">Komposisi Potensi Wilayah</p>
          <div class="h-[180px] w-full bg-paper rounded-xl p-1 relative flex items-center justify-center">
            <canvas id="zoneScoreRadarChart"></canvas>
          </div>
        </div>
      `;
    }

    content.innerHTML = `
      <div class="space-y-4 animate-[fadeIn_200ms_ease]">
        <div class="flex items-center justify-between">
          <div class="inline-flex items-center gap-1.5 rounded-full bg-clay/10 border border-clay/20 px-3 py-1 text-[10px] font-bold text-clay uppercase tracking-wider">
            📍 Zona Aktif
          </div>
          ${rankingData ? `
            <span class="text-xs font-bold text-ember">
              Skor Potensi: ${formatScore(rankingData.business_potential_score)}/100
            </span>
          ` : ""}
        </div>

        ${rankingData ? `
          <div class="w-full bg-slate-100 rounded-full h-2 overflow-hidden shadow-inner -mt-1.5">
            <div class="bg-gradient-to-r from-brass via-ember to-clay h-full rounded-full" style="width: ${rankingData.business_potential_score}%"></div>
          </div>
        ` : ""}

        <div>
          <h4 class="font-display text-2xl text-ink leading-tight">${zConfig?.name || selectedZone}</h4>
          ${rankingData ? `
            <p class="mt-1 text-xs font-bold text-brass uppercase tracking-wider">
              Peringkat Bisnis #${rankingData.rank} dari 4 Zona
            </p>
          ` : ""}
        </div>

        ${rankingData ? `
          <div class="bg-amber-50/20 border border-amber-200/50 p-3 rounded-2xl">
            <p class="text-[9px] font-bold uppercase tracking-wider text-amber-800 mb-1">Analisis Potensi Singkat</p>
            <p class="text-xs text-cocoa leading-relaxed font-light">${rankingData.insight}</p>
          </div>
        ` : ""}

        ${statsHtml}
        ${priceComparisonHtml}
        ${radarChartContainerHtml}

        <div class="pt-2">
          <button onclick="selectZone(null)" class="w-full rounded-full bg-ember hover:bg-clay text-white py-2.5 text-center text-xs font-bold transition shadow-sm cursor-pointer">
            Tampilkan Semua Zona
          </button>
        </div>
      </div>
    `;

    // Render the radar chart after HTML is injected
    if (rankingData) {
      setTimeout(() => {
        const radarCtx = document.getElementById("zoneScoreRadarChart").getContext("2d");
        
        if (window.activeRadarChartInstance) {
          window.activeRadarChartInstance.destroy();
        }

        window.activeRadarChartInstance = new Chart(radarCtx, {
          type: "radar",
          data: {
            labels: ["Pasar", "Kuliner", "Kompetisi", "Pendukung", "Peluang"],
            datasets: [{
              data: [
                rankingData.target_market_score,
                rankingData.culinary_activity_score,
                rankingData.low_competition_score,
                rankingData.supporting_area_score,
                rankingData.opportunity_score
              ],
              backgroundColor: "rgba(221, 93, 33, 0.15)",
              borderColor: "#dd5d21",
              pointBackgroundColor: "#7b341e",
              pointBorderColor: "#fff",
              pointHoverBackgroundColor: "#fff",
              pointHoverBorderColor: "#dd5d21",
              borderWidth: 1.5,
              pointRadius: 2.5
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
              legend: { display: false },
              tooltip: {
                callbacks: {
                  label: function(context) {
                    return `${context.label}: ${context.raw.toFixed(1)}/100`;
                  }
                }
              }
            },
            scales: {
              r: {
                min: 0,
                max: 100,
                ticks: { display: false, stepSize: 20 },
                grid: { color: "rgba(18, 16, 14, 0.06)" },
                angleLines: { color: "rgba(18, 16, 14, 0.06)" },
                pointLabels: {
                  font: { family: "Manrope", size: 8, weight: "bold" },
                  color: "#6b635b"
                }
              }
            }
          }
        });
      }, 50);
    }
  } else {
    const rankingRows = globalDashboardData ? globalDashboardData.zone_rankings : [];
    let rankingItemsHtml = "";

    if (rankingRows.length > 0) {
      const sorted = [...rankingRows].sort((a,b) => a.rank - b.rank);
      rankingItemsHtml = sorted.map(row => {
        const isBest = row.zone === bestZoneGlobal;
        return `
          <div 
            onclick="selectZone('${row.zone}')"
            class="flex items-center justify-between p-3 rounded-xl border border-black/5 hover:border-ember bg-white cursor-pointer hover:shadow-soft transition duration-150"
          >
            <div class="flex items-center gap-3">
              <span class="h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold ${isBest ? 'bg-ember text-white' : 'bg-mist text-smoke'}">
                ${row.rank}
              </span>
              <div>
                <span class="font-bold text-sm text-cocoa block">${row.zone}</span>
                <span class="text-[10px] text-smoke uppercase">Skor: ${formatScore(row.business_potential_score)}</span>
              </div>
            </div>
            <span class="text-xs text-smoke hover:text-ember transition">&rarr;</span>
          </div>
        `;
      }).join("");
    }

    content.innerHTML = `
      <div class="space-y-4 animate-[fadeIn_200ms_ease]">
        <div>
          <h4 class="font-display text-xl text-ink leading-tight font-black">Sleman Selatan</h4>
          <p class="mt-2 text-xs text-smoke leading-relaxed font-light">
            Gunakan kotak pencarian di atas untuk mencari POI, atau klik langsung pada zona peta untuk melihat rekapitulasi data.
          </p>
        </div>

        <div class="border-t border-black/5 pt-3">
          <p class="text-[10px] font-bold uppercase tracking-wider text-smoke mb-3">Peringkat Potensi Bisnis</p>
          <div class="space-y-2">
            ${rankingItemsHtml}
          </div>
        </div>
      </div>
    `;
  }
};

window.handleSearchInput = function(query) {
  const suggestionsBox = document.getElementById("map-search-suggestions");
  const clearBtn = document.getElementById("search-clear-btn");
  if (!suggestionsBox) return;

  if (!query || query.trim().length < 2) {
    suggestionsBox.innerHTML = "";
    suggestionsBox.classList.add("hidden");
    if (clearBtn) clearBtn.classList.add("hidden");
    return;
  }

  if (clearBtn) clearBtn.classList.remove("hidden");

  const cleanQuery = query.toLowerCase().trim();
  
  const matches = allPois
    .filter(poi => {
      const nameMatch = poi.name && poi.name.toLowerCase().includes(cleanQuery);
      const addrMatch = poi.address && poi.address.toLowerCase().includes(cleanQuery);
      const catStyle = categoryPalette[poi.category];
      const catMatch = catStyle && catStyle.label.toLowerCase().includes(cleanQuery);
      return nameMatch || addrMatch || catMatch;
    })
    .slice(0, 7);

  if (matches.length === 0) {
    suggestionsBox.innerHTML = `
      <div class="p-3 text-xs text-smoke italic text-center">
        Tidak menemukan hasil yang cocok.
      </div>
    `;
    suggestionsBox.classList.remove("hidden");
    return;
  }

  suggestionsBox.innerHTML = matches.map(poi => {
    const style = categoryPalette[poi.category] || categoryPalette.other;
    return `
      <div 
        onclick="selectSearchSuggestion('${poi.poi_id}')"
        class="suggestion-item hover:bg-mist/50 transition"
      >
        <div class="font-bold text-slate-800 text-[12px] truncate">${poi.name || "Tanpa Nama"}</div>
        <div class="flex items-center gap-1.5 mt-0.5">
          <span class="text-[10px]">${style.icon}</span>
          <span class="suggestion-category" style="color:${style.color}">
            ${style.label} ${poi.zone ? `• ${poi.zone}` : ''}
          </span>
        </div>
      </div>
    `;
  }).join("");

  suggestionsBox.classList.remove("hidden");
};

window.selectSearchSuggestion = function(poiId) {
  const suggestionsBox = document.getElementById("map-search-suggestions");
  if (suggestionsBox) {
    suggestionsBox.classList.add("hidden");
    suggestionsBox.innerHTML = "";
  }
  selectPoiById(poiId);
};

window.clearSearch = function(event) {
  if (event) {
    event.stopPropagation();
    event.preventDefault();
  }
  const searchInput = document.getElementById("map-search-input");
  if (searchInput) {
    searchInput.value = "";
  }
  const suggestionsBox = document.getElementById("map-search-suggestions");
  if (suggestionsBox) {
    suggestionsBox.innerHTML = "";
    suggestionsBox.classList.add("hidden");
  }
  const clearBtn = document.getElementById("search-clear-btn");
  if (clearBtn) {
    clearBtn.classList.add("hidden");
  }
  clearPoiSelection();
};

window.clearPoiSelection = function() {
  selectedPoi = null;
  highlightMarker(null);
  mapInstance.closePopup();
  updateDetailPanel();
  
  if (selectedZone) {
    selectZone(selectedZone);
  } else {
    mapInstance.setView([-7.758, 110.378], 12);
    updateMapMarkers();
  }
};
