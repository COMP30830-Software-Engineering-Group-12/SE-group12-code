document.addEventListener("DOMContentLoaded", () => {
  initialiseMapPage();
});

let map;
let markersLayer;
let bikeStations = [];
let currentWeather = null;
let forecastWeather = null;
let selectedStation = null;

async function initialiseMapPage() {
  const mapElement = document.getElementById("map");
  if (!mapElement) return;

  try {
    await loadAllData();
    setupLeafletMap();
    renderStationMarkers(bikeStations);
    updateWeatherStrip();
    setupSearchAndFilters();
    setupRoutePlanner();
    setupChatForm();
    setupChatToggle();

    if (bikeStations.length > 0) {
      selectStation(bikeStations[0]);
    }
  } catch (error) {
    console.error("Error initialising map page:", error);
  }
}

/* ----------------------
   DATA LOADING
  ----------------------- */

async function loadAllData() {
  const [bikeData, currentWeatherData, forecastWeatherData] = await Promise.all([
    loadJsonFromTextFile("bike_data.txt"),
    loadJsonFromTextFile("weather_current_data.txt"),
    loadJsonFromTextFile("weather_forecast_data.txt")
  ]);

  bikeStations = Array.isArray(bikeData) ? bikeData : [];
  currentWeather = currentWeatherData;
  forecastWeather = forecastWeatherData;
}

async function loadJsonFromTextFile(filePath) {
  const response = await fetch(filePath);

  if (!response.ok) {
    throw new Error(`Could not load ${filePath}`);
  }

  const text = await response.text();
  return JSON.parse(text);
}

/* ----------------------
   MAP SETUP
----------------------- */

function setupLeafletMap() {
  map = L.map("map").setView([53.3498, -6.2603], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  markersLayer = L.layerGroup().addTo(map);
}

function renderStationMarkers(stations) {
  markersLayer.clearLayers();

  stations.forEach((station) => {
    const lat = station.position?.lat;
    const lng = station.position?.lng;

    if (typeof lat !== "number" || typeof lng !== "number") return;

    const marker = L.circleMarker([lat, lng], {
      radius: 8,
      weight: 2,
      opacity: 1,
      fillOpacity: 0.85,
      color: getMarkerColour(station),
      fillColor: getMarkerColour(station)
    });

    marker.bindPopup(`
      <strong>${station.name}</strong><br>
      ${station.address}<br>
      Bikes: ${station.available_bikes}<br>
      Stands: ${station.available_bike_stands}
    `);

    marker.on("click", () => {
      selectStation(station);
    });

    marker.addTo(markersLayer);
  });
}

function getMarkerColour(station) {
  const bikes = station.available_bikes ?? 0;

  if (bikes >= 15) return "#1a9632";
  if (bikes >= 5) return "#f0ad4e";
  return "#d9534f";
}

/* ----------------------
   STATION PANEL
----------------------- */

function selectStation(station) {
  selectedStation = station;

  const stationTitle = document.getElementById("stationTitle");
  const stationMeta = document.getElementById("stationMeta");
  const bikesAvail = document.getElementById("bikesAvail");
  const standsAvail = document.getElementById("standsAvail");

  if (stationTitle) stationTitle.textContent = formatStationName(station.name);
  if (stationMeta) stationMeta.textContent = station.address || "No address available";
  if (bikesAvail) bikesAvail.textContent = station.available_bikes ?? "--";
  if (standsAvail) standsAvail.textContent = station.available_bike_stands ?? "--";

  updateStationMetaBlock(station);

  const lat = station.position?.lat;
  const lng = station.position?.lng;

  if (map && typeof lat === "number" && typeof lng === "number") {
    map.flyTo([lat, lng], 15, { duration: 0.8 });
  }
}

function updateStationMetaBlock(station) {
  const metaContainer = document.querySelector(".station-card .station-meta");
  if (!metaContainer) return;

  const bikes = station.available_bikes ?? 0;
  const stands = station.available_bike_stands ?? 0;

  let statusText = "Moderate availability";
  if (bikes >= 15) statusText = "High bike availability";
  else if (bikes < 5) statusText = "Low bike availability";

  const weatherDescription =
    currentWeather?.weather?.[0]?.description ?? "Weather unavailable";

  const tempC = kelvinToCelsius(currentWeather?.main?.temp);

  metaContainer.innerHTML = `
    <p><strong>Status:</strong> ${statusText}</p>
    <p><strong>Weather:</strong> ${tempC !== null ? `${tempC}°C` : "--"}${weatherDescription ? `, ${capitalise(weatherDescription)}` : ""}</p>
    <p><strong>Total Stands:</strong> ${station.bike_stands ?? bikes + stands}</p>
  `;
}

/* ----------------------
   WEATHER
----------------------- */

function updateWeatherStrip() {
  if (!currentWeather) return;

  const temp = kelvinToCelsius(currentWeather.main?.temp);
  const high = kelvinToCelsius(currentWeather.main?.temp_max);
  const low = kelvinToCelsius(currentWeather.main?.temp_min);
  const description = currentWeather.weather?.[0]?.description ?? "Unavailable";
  const wind = currentWeather.wind?.speed;

  const weatherMainTemp = document.querySelector(".weather-main h2");
  const weatherMainDesc = document.querySelector(".weather-main p:last-child");

  const pillValues = document.querySelectorAll(".pill-value");

  if (weatherMainTemp && temp !== null) {
    weatherMainTemp.textContent = `${temp}°C`;
  }

  if (weatherMainDesc) {
    weatherMainDesc.textContent = `${capitalise(description)} in Dublin`;
  }

  if (pillValues[0] && high !== null && low !== null) {
    pillValues[0].textContent = `${high}°C / ${low}°C`;
  }

  if (pillValues[1] && typeof wind === "number") {
    pillValues[1].textContent = `${msToKmh(wind)} km/h`;
  }

  if (pillValues[2] && forecastWeather?.list?.length) {
    const eveningForecast = forecastWeather.list.find(item =>
      item.dt_txt?.includes("18:00:00")
    );

    const eveningTemp = kelvinToCelsius(eveningForecast?.main?.temp);
    pillValues[2].textContent = eveningTemp !== null ? `${eveningTemp}°C` : "--";
  }
}

/* ----------------------
   SEARCH + FILTERS
----------------------- */

function setupSearchAndFilters() {
  const searchInput = document.getElementById("stationSearch");
  const availabilityFilter = document.getElementById("availabilityFilter");

  if (searchInput) {
    searchInput.addEventListener("input", applyFilters);
  }

  if (availabilityFilter) {
    availabilityFilter.addEventListener("change", applyFilters);
  }
}

function applyFilters() {
  const searchValue =
    document.getElementById("stationSearch")?.value.trim().toLowerCase() || "";

  const availabilityValue =
    document.getElementById("availabilityFilter")?.value || "";

  let filteredStations = [...bikeStations];

  if (searchValue) {
    filteredStations = filteredStations.filter((station) =>
      station.name.toLowerCase().includes(searchValue) ||
      station.address.toLowerCase().includes(searchValue)
    );
  }

  if (availabilityValue) {
    filteredStations = filteredStations.filter((station) => {
      const bikes = station.available_bikes ?? 0;

      if (availabilityValue === "high") return bikes >= 15;
      if (availabilityValue === "medium") return bikes >= 5 && bikes < 15;
      if (availabilityValue === "low") return bikes < 5;
      return true;
    });
  }

  renderStationMarkers(filteredStations);
}

/* ---------------------------
   ROUTE PLANNER PLACEHOLDER
---------------------------- */

function setupRoutePlanner() {
  const planButton = document.getElementById("planRouteBtn");
  const routeResults = document.getElementById("routeResults");

  if (!planButton || !routeResults) return;

  planButton.addEventListener("click", () => {
    const fromValue = document.getElementById("fromInput")?.value.trim();
    const toValue = document.getElementById("toInput")?.value.trim();

    if (!fromValue || !toValue) {
      routeResults.innerHTML = `<p>Please enter both a starting point and a destination.</p>`;
      return;
    }

    routeResults.innerHTML = `
      <p><strong>Route planned:</strong> ${fromValue} → ${toValue}</p>
      <ul class="route-steps">
        <li>Walk to the nearest station</li>
        <li>Unlock a Dublin Bike</li>
        <li>Cycle toward your destination</li>
        <li>Dock the bike at the nearest station</li>
      </ul>
    `;
  });
}

/* ----------------------
   CHAT PLACEHOLDER
----------------------- */

function setupChatForm() {
  const chatForm = document.querySelector(".chat-input-row");
  const chatInput = document.getElementById("chatInput");
  const chatMessages = document.querySelector(".chat-messages");

  if (!chatForm || !chatInput || !chatMessages) return;

  chatForm.addEventListener("submit", (event) => {
    event.preventDefault();

    const message = chatInput.value.trim();
    if (!message) return;

    appendChatBubble(message, "user", chatMessages);

    let reply = "I can help with station availability, routes, and map exploration.";
    if (selectedStation && message.toLowerCase().includes("station")) {
      reply = `${formatStationName(selectedStation.name)} currently has ${selectedStation.available_bikes} bikes and ${selectedStation.available_bike_stands} free stands.`;
    } else if (message.toLowerCase().includes("weather")) {
      const desc = currentWeather?.weather?.[0]?.description ?? "unavailable";
      const temp = kelvinToCelsius(currentWeather?.main?.temp);
      reply = `Current Dublin weather is ${temp !== null ? `${temp}°C` : "--"} with ${desc}.`;
    }

    appendChatBubble(reply, "bot", chatMessages);
    chatInput.value = "";
  });
}

function appendChatBubble(text, type, container) {
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${type}`;
  bubble.textContent = text;
  container.appendChild(bubble);
  container.scrollTop = container.scrollHeight;
}

function setupChatToggle() {
  const chatToggleBtn = document.getElementById("chatToggleBtn");
  const chatWidget = document.getElementById("chatWidget");

  if (!chatToggleBtn || !chatWidget) return;

  chatToggleBtn.addEventListener("click", () => {
    chatWidget.classList.toggle("collapsed");
  });
}

/* ----------------------
   HELPERS
----------------------- */

function kelvinToCelsius(value) {
  if (typeof value !== "number") return null;
  return Math.round(value - 273.15);
}

function msToKmh(value) {
  if (typeof value !== "number") return "--";
  return Math.round(value * 3.6);
}

function capitalise(text) {
  if (!text) return "";
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function formatStationName(name) {
  if (!name) return "Unknown Station";
  return name
    .toLowerCase()
    .split(" ")
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}