const API_BASE_URL = "http://127.0.0.1:5000/api/dvf";
const GEOJSON_SOURCES = [
  "./data/paris-arrondissements.geojson",
  "https://opendata.paris.fr/explore/dataset/arrondissements/download/?format=geojson&lang=fr",
  "https://raw.githubusercontent.com/flother/paris-geojson/master/data/arrondissements.geojson",
];
const CHOROPLETH_COLORS = ["#fff5eb", "#fdc38d", "#fc8d59", "#e34a33", "#b30000", "#7f0000"];

const state = {
  map: null,
  geojsonLayer: null,
  geojsonData: null,
  legendControl: null,
  arrondissementByCode: new Map(),
  colorScale: null,
};

const yearSelect = document.getElementById("yearSelect");
const statusElement = document.getElementById("status");

bootstrap().catch((error) => {
  console.error(error);
  setStatus(`Erreur inattendue : ${error.message}`, "error");
});

async function bootstrap() {
  setStatus("Initialisation du dashboard…");
  initMap();
  state.geojsonData = await loadGeojson();
  const years = await fetchAvailableYears();
  if (!years.length) {
    setStatus("Aucune année disponible. Vérifiez la couche gold.", "error");
    return;
  }
  populateYearSelect(years);
  const initialYear = years[years.length - 1];
  yearSelect.value = initialYear;
  yearSelect.addEventListener("change", (event) => {
    const selectedYear = Number(event.target.value);
    updateChoropleth(selectedYear);
  });
  await updateChoropleth(initialYear);
}

function initMap() {
  state.map = L.map("map", {
    zoomControl: false,
  }).setView([48.8566, 2.3522], 12.4);

  L.tileLayer("https://{s}.tile.openstreetmap.fr/osmfr/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap France",
  }).addTo(state.map);

  L.control
    .zoom({
      position: "bottomright",
    })
    .addTo(state.map);
}

function populateYearSelect(years) {
  yearSelect.innerHTML = "";
  years.forEach((year) => {
    const option = document.createElement("option");
    option.value = year;
    option.textContent = year;
    yearSelect.appendChild(option);
  });
}

async function fetchAvailableYears() {
  const response = await fetch(`${API_BASE_URL}/years`);
  if (!response.ok) {
    throw new Error("Impossible de récupérer la liste des années.");
  }
  return (await response.json()).map((year) => Number(year));
}

async function fetchArrondissementData(year) {
  const params = new URLSearchParams();
  if (Number.isFinite(year)) {
    params.set("year", String(year));
  }
  const response = await fetch(`${API_BASE_URL}/arrondissements?${params.toString()}`);
  if (!response.ok) {
    throw new Error("Impossible de récupérer les agrégations DVF.");
  }
  const payload = await response.json();
  return payload.items ?? [];
}

async function loadGeojson() {
  for (const source of GEOJSON_SOURCES) {
    try {
      const response = await fetch(source);
      if (!response.ok) {
        throw new Error(`Status ${response.status}`);
      }
      const data = await response.json();
      const normalized = normalizeGeojson(data);
      if (normalized.features.length) {
        setStatus(`Géométrie chargée via ${source}`);
        return normalized;
      }
    } catch (error) {
      console.warn(`Impossible de charger ${source}`, error);
    }
  }
  setStatus("Chargement GeoJSON impossible, utilisation d'une grille simplifiée.", "warning");
  return buildFallbackGeojson();
}

function normalizeGeojson(data) {
  if (!data || !data.features) {
    return { type: "FeatureCollection", features: [] };
  }
  const features = data.features
    .map((feature) => {
      const code = deriveFeatureCode(feature);
      if (!code) {
        return null;
      }
      feature.properties = feature.properties || {};
      feature.properties.__arrCode = code;
      feature.properties.__label =
        feature.properties.l_aroff ||
        feature.properties.l_ar ||
        feature.properties.nom ||
        `${parseInt(code.slice(-2), 10)}e arrondissement`;
      return feature;
    })
    .filter(Boolean);

  return { type: "FeatureCollection", features };
}

function deriveFeatureCode(feature) {
  if (!feature || !feature.properties) {
    return null;
  }
  const props = feature.properties;
  const candidates = [
    props.c_quinsee,
    props.c_ar_quinsee,
    props.c_ar,
    props.c_arinsee,
    props.code,
    props.CODE,
    props.CODE_INSEE,
    props.code_insee,
    props.INSEE_COM,
    props.insee,
  ];
  for (const value of candidates) {
    const normalized = normalizeArrCode(value);
    if (normalized) {
      return normalized;
    }
  }
  return null;
}

function normalizeArrCode(value) {
  if (value === null || value === undefined) {
    return null;
  }
  const raw = String(value).trim();
  if (!raw) {
    return null;
  }
  if (/^75\d{3}$/.test(raw)) {
    return raw;
  }
  if (/^\d{1,2}$/.test(raw)) {
    return `751${raw.padStart(2, "0")}`;
  }
  return null;
}

async function updateChoropleth(year) {
  try {
    setStatus("Chargement des données DVF…");
    const items = await fetchArrondissementData(year);
    state.arrondissementByCode = new Map(items.map((item) => [String(item.code_commune), item]));
    const values = items.map((item) => Number(item.prix_m2_med)).filter((value) => Number.isFinite(value));
    state.colorScale = buildColorScale(values);
    renderGeojsonLayer();
    updateLegend();
    setStatus(`Carte mise à jour pour ${year}`);
  } catch (error) {
    console.error(error);
    setStatus(error.message, "error");
  }
}

function renderGeojsonLayer() {
  if (!state.geojsonLayer) {
    state.geojsonLayer = L.geoJSON(state.geojsonData, {
      style: styleFeature,
      onEachFeature,
    }).addTo(state.map);
  } else {
    state.geojsonLayer.setStyle(styleFeature);
    state.geojsonLayer.eachLayer(refreshTooltip);
  }
}

function styleFeature(feature) {
  const code = feature.properties.__arrCode;
  const payload = code ? state.arrondissementByCode.get(code) : undefined;
  const color = colorForValue(payload?.prix_m2_med);
  return {
    color: "#f5f3f1",
    weight: 1,
    fillColor: color,
    fillOpacity: payload ? 0.85 : 0.3,
  };
}

function onEachFeature(feature, layer) {
  layer.on({
    mouseover: (event) => highlightFeature(event.target),
    mouseout: (event) => resetHighlight(event.target),
  });
  refreshTooltip(layer);
}

function refreshTooltip(layer) {
  const code = layer.feature.properties.__arrCode;
  const payload = code ? state.arrondissementByCode.get(code) : undefined;
  const arrondissementLabel = payload?.label || layer.feature.properties.__label || "Arrondissement inconnu";
  const message = payload
    ? `<strong>${arrondissementLabel}</strong><br>Prix médian&nbsp;: ${formatEuro(payload.prix_m2_med)} / m²<br>Transactions&nbsp;: ${formatNumber(
        payload.nb_ventes
      )}`
    : `<strong>${arrondissementLabel}</strong><br>Donnée indisponible pour l'année sélectionnée`;
  layer.bindTooltip(message, { sticky: true, direction: "top" });
}

function highlightFeature(layer) {
  layer.setStyle({
    weight: 3,
    color: "#0f172a",
    fillOpacity: 0.95,
  });
  if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
    layer.bringToFront();
  }
}

function resetHighlight(layer) {
  if (state.geojsonLayer) {
    state.geojsonLayer.resetStyle(layer);
    layer.bringToFront();
  }
}

function buildColorScale(values) {
  if (!values.length) {
    return null;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    return null;
  }
  if (min === max) {
    return {
      thresholds: Array.from({ length: CHOROPLETH_COLORS.length - 1 }, () => max),
      min,
      max,
    };
  }
  const steps = CHOROPLETH_COLORS.length - 1;
  const interval = (max - min) / steps;
  const thresholds = Array.from({ length: steps }, (_, index) => Number(min + interval * (index + 1)));
  return { thresholds, min, max };
}

function colorForValue(value) {
  if (!state.colorScale || !Number.isFinite(value)) {
    return "#d9d9d9";
  }
  const thresholds = state.colorScale.thresholds;
  for (let idx = 0; idx < thresholds.length; idx += 1) {
    if (value <= thresholds[idx]) {
      return CHOROPLETH_COLORS[idx];
    }
  }
  return CHOROPLETH_COLORS[thresholds.length];
}

function updateLegend() {
  if (!state.legendControl) {
    state.legendControl = L.control({ position: "bottomleft" });
    state.legendControl.onAdd = function onAdd() {
      this._div = L.DomUtil.create("div", "legend");
      return this._div;
    };
    state.legendControl.addTo(state.map);
  }
  const container = state.legendControl._div;
  if (!container) {
    return;
  }
  if (!state.colorScale) {
    container.innerHTML = "<p>Aucune donnée</p>";
    return;
  }
  const { thresholds, min } = state.colorScale;
  let from = min;
  container.innerHTML = "<strong>Prix médian (€/m²)</strong><br>";
  thresholds.forEach((to, index) => {
    const color = CHOROPLETH_COLORS[index];
    container.innerHTML += legendRow(color, from, to);
    from = to;
  });
  container.innerHTML += legendRow(CHOROPLETH_COLORS[thresholds.length], from, state.colorScale.max);
}

function legendRow(color, from, to) {
  const formatter = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });
  const rangeLabel = `${formatter.format(Math.round(from))} – ${formatter.format(Math.round(to))}`;
  return `<span><i style="background:${color}"></i>${rangeLabel}</span>`;
}

function formatEuro(value) {
  const formatter = new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    maximumFractionDigits: 0,
  });
  return formatter.format(Number(value) || 0);
}

function formatNumber(value) {
  return new Intl.NumberFormat("fr-FR").format(Number(value) || 0);
}

function setStatus(message, variant = "info") {
  if (!statusElement) {
    return;
  }
  statusElement.textContent = message || "";
  statusElement.dataset.variant = variant;
}

function buildFallbackGeojson() {
  const features = [];
  const baseLat = 48.82;
  const baseLon = 2.28;
  const latStep = 0.012;
  const lonStep = 0.015;
  const rectLat = 0.007;
  const rectLon = 0.01;
  for (let index = 0; index < 20; index += 1) {
    const arrNumber = index + 1;
    const row = Math.floor(index / 4);
    const col = index % 4;
    const centerLat = baseLat + row * latStep;
    const centerLon = baseLon + col * lonStep;
    const code = `751${String(arrNumber).padStart(2, "0")}`;
    features.push({
      type: "Feature",
      properties: {
        __arrCode: code,
        __label: `${arrNumber}e arrondissement (approx.)`,
      },
      geometry: {
        type: "Polygon",
        coordinates: [
          [
            [centerLon - rectLon, centerLat - rectLat],
            [centerLon + rectLon, centerLat - rectLat],
            [centerLon + rectLon, centerLat + rectLat],
            [centerLon - rectLon, centerLat + rectLat],
            [centerLon - rectLon, centerLat - rectLat],
          ],
        ],
      },
    });
  }
  return { type: "FeatureCollection", features };
}
