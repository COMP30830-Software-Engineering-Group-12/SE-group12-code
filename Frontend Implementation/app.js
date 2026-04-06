document.addEventListener("DOMContentLoaded", async () => {
  setupAccountDropdown();
  initialiseFavouritesPage();
  initialiseMapPage();

  const isHomePage = document.querySelector(".weather-summary");

  if (isHomePage) {
    try {
      await loadAllData();
      updateHomeWeather();
    } catch (error) {
      console.error("Error loading home weather:", error);
    }
  }
});

let map;
let markersLayer;
let bikeStations = [];
let currentWeather = null;
let forecastWeather = null;
let selectedStation = null;

/* ----------------------
  INITIALISE PAGES
----------------------- */

async function initialiseMapPage() {
  const mapElement = document.getElementById("map");
  if (!mapElement) return;

  try {
    await loadAllData();
    setupLeafletMap();
    renderStationMarkers(bikeStations);
    updateWeatherStrip();
    setupSearchAndFilters();
    setupJourneyAutocomplete();
    setupStationSearchAutocomplete();
    setupJourneyPlanner();
    setupFavouriteToggle();
    setupReserveButton();
    setupChatForm();
    setupChatToggle();

    const stationFromUrl = getStationNumberFromUrl();

    if (stationFromUrl !== null) {
      const matchedStation = bikeStations.find(
        (station) => station.number === stationFromUrl
      );

      if (matchedStation) {
        selectStation(matchedStation);
      } else if (bikeStations.length > 0) {
        selectStation(bikeStations[0]);
      }
    } else if (bikeStations.length > 0) {
      selectStation(bikeStations[0]);
    }
  } catch (error) {
    console.error("Error initialising map page:", error);
  }
}

function initialiseFavouritesPage() {
  const favouritesGrid = document.getElementById("favouritesGrid");
  if (!favouritesGrid) return;

  setupFavouritesPageControls();
  renderFavouritesPage();
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
  if (!markersLayer) return;

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
      <strong>${formatStationName(station.name)}</strong><br>
      ${station.address || "No address available"}<br>
      Bikes: ${station.available_bikes ?? "--"}<br>
      Stands: ${station.available_bike_stands ?? "--"}
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

  if (typeof lat === "number" && typeof lng === "number" && map) {
    map.setView([lat, lng], 15);
  }

  updateFavouriteButtonState();
  updateReserveButtonState();
}

function updateStationMetaBlock(station) {
  const metaContainer = document.querySelector(".station-overlay .station-meta");
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
    const eveningForecast = forecastWeather.list.find((item) =>
      item.dt_txt?.includes("18:00:00")
    );

    const eveningTemp = kelvinToCelsius(eveningForecast?.main?.temp);
    pillValues[2].textContent = eveningTemp !== null ? `${eveningTemp}°C` : "--";
  }
}

function updateHomeWeather() {
  if (!currentWeather) return;

  const temp = kelvinToCelsius(currentWeather.main?.temp);
  const high = kelvinToCelsius(currentWeather.main?.temp_max);
  const low = kelvinToCelsius(currentWeather.main?.temp_min);
  const description = currentWeather.weather?.[0]?.description ?? "Unavailable";
  const wind = currentWeather.wind?.speed;

  const eveningForecast = forecastWeather?.list?.find((item) =>
    item.dt_txt?.includes("18:00:00")
  );

  const eveningTemp = kelvinToCelsius(eveningForecast?.main?.temp);

  const currentTempEl = document.getElementById("homeCurrentTemp");
  const currentDescEl = document.getElementById("homeCurrentDesc");

  const highLowTempEl = document.getElementById("homeHighLowTemp");
  const highLowDescEl = document.getElementById("homeHighLowDesc");

  const windEl = document.getElementById("homeWindSpeed");
  const windDescEl = document.getElementById("homeWindDesc");

  const tonightTempEl = document.getElementById("homeTonightTemp");
  const tonightDescEl = document.getElementById("homeTonightDesc");

  if (currentTempEl && temp !== null) {
    currentTempEl.textContent = `${temp}°C`;
  }

  if (currentDescEl) {
    currentDescEl.textContent = capitalise(description);
  }

  if (highLowTempEl && high !== null && low !== null) {
    highLowTempEl.textContent = `${high}°C / ${low}°C`;
  }

  if (highLowDescEl) {
    highLowDescEl.textContent = "Today's range";
  }

  if (windEl && typeof wind === "number") {
    windEl.textContent = `${msToKmh(wind)} km/h`;
  }

  if (windDescEl) {
    windDescEl.textContent = "Wind conditions";
  }

  if (tonightTempEl && eveningTemp !== null) {
    tonightTempEl.textContent = `${eveningTemp}°C`;
  }

  if (tonightDescEl) {
    tonightDescEl.textContent = "Evening forecast";
  }
}

/* ----------------------
  SEARCH AND FILTERS
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
      station.name?.toLowerCase().includes(searchValue) ||
      station.address?.toLowerCase().includes(searchValue)
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
  AUTOCOMPLETE
---------------------------- */

function setupJourneyAutocomplete() {
  const fromInput = document.getElementById("fromInput");
  const toInput = document.getElementById("toInput");
  const fromSuggestions = document.getElementById("fromSuggestions");
  const toSuggestions = document.getElementById("toSuggestions");

  if (!fromInput || !toInput || !fromSuggestions || !toSuggestions) return;

  setupAutocompleteForInput(fromInput, fromSuggestions, {
    onSelect: (station) => {
      fromInput.value = formatStationName(station.name);
    }
  });

  setupAutocompleteForInput(toInput, toSuggestions, {
    onSelect: (station) => {
      toInput.value = formatStationName(station.name);
    }
  });

  document.addEventListener("click", (event) => {
    if (!fromSuggestions.contains(event.target) && event.target !== fromInput) {
      hideSuggestions(fromSuggestions);
    }

    if (!toSuggestions.contains(event.target) && event.target !== toInput) {
      hideSuggestions(toSuggestions);
    }
  });
}

function setupStationSearchAutocomplete() {
  const stationSearch = document.getElementById("stationSearch");
  const stationSuggestions = document.getElementById("stationSuggestions");

  if (!stationSearch || !stationSuggestions) return;

  setupAutocompleteForInput(stationSearch, stationSuggestions, {
    onSelect: (station) => {
      stationSearch.value = formatStationName(station.name);
      selectStation(station);

      if (map && station.position?.lat && station.position?.lng) {
        map.setView([station.position.lat, station.position.lng], 15);
      }

      renderStationMarkers([station]);
    }
  });

  document.addEventListener("click", (event) => {
    if (
      !stationSuggestions.contains(event.target) &&
      event.target !== stationSearch
    ) {
      hideSuggestions(stationSuggestions);
    }
  });
}

function setupAutocompleteForInput(inputElement, suggestionsElement, options = {}) {
  const { onSelect } = options;

  const getMatches = () => {
    const query = inputElement.value.trim().toLowerCase();

    if (!query) {
      hideSuggestions(suggestionsElement);
      return [];
    }

    return bikeStations
      .filter((station) =>
        station.name?.toLowerCase().includes(query) ||
        station.address?.toLowerCase().includes(query)
      )
      .slice(0, 6);
  };

  inputElement.addEventListener("input", () => {
    const matches = getMatches();
    renderSuggestions(matches, inputElement, suggestionsElement, onSelect);
  });

  inputElement.addEventListener("focus", () => {
    const matches = getMatches();
    renderSuggestions(matches, inputElement, suggestionsElement, onSelect);
  });
}

function renderSuggestions(matches, inputElement, suggestionsElement, onSelect) {
  suggestionsElement.innerHTML = "";

  if (!matches.length) {
    hideSuggestions(suggestionsElement);
    return;
  }

  matches.forEach((station) => {
    const item = document.createElement("div");
    item.className = "autocomplete-item";
    item.textContent = formatStationName(station.name);

    item.addEventListener("click", () => {
      inputElement.value = formatStationName(station.name);
      hideSuggestions(suggestionsElement);

      if (typeof onSelect === "function") {
        onSelect(station);
      } else {
        selectStation(station);
      }
    });

    suggestionsElement.appendChild(item);
  });

  suggestionsElement.classList.add("show");
}

function hideSuggestions(suggestionsElement) {
  suggestionsElement.classList.remove("show");
  suggestionsElement.innerHTML = "";
}

/* ---------------------------
  JOURNEY PLANNER
---------------------------- */

function setupJourneyPlanner() {
  const planRouteBtn = document.getElementById("planRouteBtn");
  const routeForm = document.querySelector(".route-form");
  const clearBtn = routeForm?.querySelector('button[type="reset"]');
  const fromInput = document.getElementById("fromInput");
  const toInput = document.getElementById("toInput");
  const startJourneyBtn = document.getElementById("startJourneyBtn");

  if (planRouteBtn) {
    planRouteBtn.addEventListener("click", handlePlanRoute);
  }

  if (clearBtn) {
    clearBtn.addEventListener("click", () => {
      window.setTimeout(() => {
        clearRouteResults();
      }, 0);
    });
  }

  if (startJourneyBtn) {
    startJourneyBtn.addEventListener("click", () => {
      alert("Journey start placeholder: backend navigation can be connected here later.");
    });
  }

  if (fromInput) {
    fromInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        handlePlanRoute();
      }
    });
  }

  if (toInput) {
    toInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        handlePlanRoute();
      }
    });
  }
}

function handlePlanRoute() {
  const fromInput = document.getElementById("fromInput");
  const toInput = document.getElementById("toInput");
  const routeResults = document.getElementById("routeResults");

  if (!fromInput || !toInput || !routeResults) return;

  const fromValue = fromInput.value.trim();
  const toValue = toInput.value.trim();

  if (!fromValue || !toValue) {
    routeResults.innerHTML = `<p>Please enter both a start and destination station.</p>`;
    return;
  }

  routeResults.innerHTML = `
    <div class="route-meta">
      5 min <span>1.2 km</span>
    </div>

    <p><strong>From:</strong> ${fromValue}</p>
    <p><strong>To:</strong> ${toValue}</p>

    <ol class="route-steps">
      <li>Walk to <strong>${fromValue}</strong>.</li>
      <li>Collect a bike and begin your journey.</li>
      <li>Cycle toward <strong>${toValue}</strong>.</li>
      <li>Dock at the destination station.</li>
    </ol>

    <p><em>Route planning preview only. Live routing will be provided by the backend.</em></p>
  `;
}

function clearRouteResults() {
  const routeResults = document.getElementById("routeResults");
  if (!routeResults) return;

  routeResults.innerHTML = `
    <p>Choose a start and destination station to preview a route.</p>
  `;

  renderStationMarkers(bikeStations);
}

function findStationByNameOrAddress(query) {
  const normalisedQuery = query.trim().toLowerCase();

  return bikeStations.find((station) => {
    const stationName = station.name?.toLowerCase() || "";
    const stationAddress = station.address?.toLowerCase() || "";

    return (
      stationName === normalisedQuery ||
      stationAddress === normalisedQuery ||
      formatStationName(station.name).toLowerCase() === normalisedQuery
    );
  });
}

function calculateDistanceKm(lat1, lng1, lat2, lng2) {
  if (
    typeof lat1 !== "number" ||
    typeof lng1 !== "number" ||
    typeof lat2 !== "number" ||
    typeof lng2 !== "number"
  ) {
    return 0;
  }

  const toRadians = (degrees) => (degrees * Math.PI) / 180;
  const earthRadiusKm = 6371;

  const dLat = toRadians(lat2 - lat1);
  const dLng = toRadians(lng2 - lng1);

  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(lat1)) *
      Math.cos(toRadians(lat2)) *
      Math.sin(dLng / 2) ** 2;

  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return earthRadiusKm * c;
}

function highlightRouteStations(fromStation, toStation) {
  if (!map) return;

  renderStationMarkers(bikeStations);

  const fromLat = fromStation.position?.lat;
  const fromLng = fromStation.position?.lng;
  const toLat = toStation.position?.lat;
  const toLng = toStation.position?.lng;

  if (
    typeof fromLat !== "number" ||
    typeof fromLng !== "number" ||
    typeof toLat !== "number" ||
    typeof toLng !== "number"
  ) {
    return;
  }

  const routeBounds = L.latLngBounds([
    [fromLat, fromLng],
    [toLat, toLng]
  ]);

  L.circleMarker([fromLat, fromLng], {
    radius: 10,
    color: "#1a9632",
    fillColor: "#1a9632",
    fillOpacity: 1,
    weight: 3
  })
    .bindPopup(`<strong>Start:</strong> ${formatStationName(fromStation.name)}`)
    .addTo(markersLayer);

  L.circleMarker([toLat, toLng], {
    radius: 10,
    color: "#0e5c1d",
    fillColor: "#ffffff",
    fillOpacity: 1,
    weight: 3
  })
    .bindPopup(`<strong>Destination:</strong> ${formatStationName(toStation.name)}`)
    .addTo(markersLayer);

  L.polyline(
    [
      [fromLat, fromLng],
      [toLat, toLng]
    ],
    {
      color: "#1a9632",
      weight: 4,
      opacity: 0.75,
      dashArray: "8 8"
    }
  ).addTo(markersLayer);

  map.fitBounds(routeBounds, { padding: [50, 50] });
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
  const chatCloseBtn = document.getElementById("chatCloseBtn");

  if (!chatToggleBtn || !chatWidget) return;

  chatToggleBtn.addEventListener("click", () => {
    chatWidget.classList.toggle("collapsed");
  });

  if (chatCloseBtn) {
    chatCloseBtn.addEventListener("click", () => {
      chatWidget.classList.add("collapsed");
    });
  }
}

/* ----------------------
  ACCOUNT DROPDOWN
----------------------- */

function setupAccountDropdown() {
  const accountBtn = document.querySelector(".account-btn");
  const dropdownMenu = document.querySelector(".dropdown-menu");

  if (!accountBtn || !dropdownMenu) return;

  accountBtn.addEventListener("click", (event) => {
    event.stopPropagation();
    dropdownMenu.classList.toggle("show");
    accountBtn.classList.toggle("active");
  });

  dropdownMenu.addEventListener("click", (event) => {
    event.stopPropagation();
  });

  document.addEventListener("click", () => {
    dropdownMenu.classList.remove("show");
    accountBtn.classList.remove("active");
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
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function getStationNumberFromUrl() {
  const params = new URLSearchParams(window.location.search);
  const stationNumber = params.get("station");
  return stationNumber ? Number(stationNumber) : null;
}

/* ----------------------
  FAVOURITE STATIONS
----------------------- */

function getFavouriteStations() {
  const stored = localStorage.getItem("favouriteStations");

  try {
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error("Could not parse favourite stations:", error);
    return [];
  }
}

function saveFavouriteStations(favourites) {
  localStorage.setItem("favouriteStations", JSON.stringify(favourites));
}

function isStationFavourite(station) {
  if (!station) return false;

  const favourites = getFavouriteStations();
  return favourites.some((fav) => fav.number === station.number);
}

function toggleFavouriteStation(station) {
  if (!station) return;

  const favourites = getFavouriteStations();
  const existingIndex = favourites.findIndex((fav) => fav.number === station.number);

  if (existingIndex >= 0) {
    favourites.splice(existingIndex, 1);
  } else {
    favourites.push({
      number: station.number,
      name: station.name,
      address: station.address,
      available_bikes: station.available_bikes,
      available_bike_stands: station.available_bike_stands,
      bike_stands: station.bike_stands,
      status: station.status,
      position: station.position
    });
  }

  saveFavouriteStations(favourites);
}

function updateFavouriteButtonState() {
  const favouriteBtn = document.getElementById("favouriteToggleBtn");
  if (!favouriteBtn) return;

  if (!selectedStation) {
    favouriteBtn.classList.remove("active");
    return;
  }

  favouriteBtn.classList.toggle("active", isStationFavourite(selectedStation));
}

function setupFavouriteToggle() {
  const favouriteBtn = document.getElementById("favouriteToggleBtn");
  if (!favouriteBtn) return;

  favouriteBtn.addEventListener("click", () => {
    if (!selectedStation) return;

    toggleFavouriteStation(selectedStation);
    updateFavouriteButtonState();
  });
}

/* ----------------------
  FAVOURITES PAGE
----------------------- */

function getAvailabilityLabel(station) {
  const bikes = station?.available_bikes ?? 0;

  if (bikes >= 15) return "High bike availability";
  if (bikes >= 5) return "Moderate availability";
  return "Low bike availability";
}

function createFavouriteCard(station) {
  return `
    <article class="favourite-card" data-station-number="${station.number}">
      <div class="card-top">
        <div>
          <p class="station-area">Saved Station</p>
          <h3>${formatStationName(station.name)}</h3>
          <p class="station-address">${station.address || "No address available"}</p>
        </div>
        <span class="station-badge">Saved</span>
      </div>

      <div class="station-stats">
        <div class="stat-box">
          <span class="stat-label">Bikes</span>
          <span class="stat-value">${station.available_bikes ?? "--"}</span>
        </div>
        <div class="stat-box">
          <span class="stat-label">Stands</span>
          <span class="stat-value">${station.available_bike_stands ?? "--"}</span>
        </div>
      </div>

      <div class="station-meta">
        <p><strong>Status:</strong> ${getAvailabilityLabel(station)}</p>
      </div>

      <div class="card-actions">
        <a href="map.html?station=${station.number}" class="btn btn-primary">View on Map</a>
        <button
          class="btn btn-outline remove-favourite-btn"
          type="button"
          data-station-number="${station.number}"
        >
          Remove
        </button>
      </div>
    </article>
  `;
}

function renderFavouritesPage() {
  const favouritesGrid = document.getElementById("favouritesGrid");
  const emptyState = document.getElementById("emptyState");
  const searchInput = document.getElementById("favouritesSearch");
  const sortSelect = document.getElementById("favouritesSort");

  if (!favouritesGrid) return;

  let favourites = getFavouriteStations();
  const allSaved = getFavouriteStations();

  const searchTerm = searchInput?.value.trim().toLowerCase() || "";
  const sortValue = sortSelect?.value || "";

  if (searchTerm) {
    favourites = favourites.filter((station) =>
      station.name?.toLowerCase().includes(searchTerm) ||
      station.address?.toLowerCase().includes(searchTerm)
    );
  }

  if (sortValue === "name") {
    favourites.sort((a, b) =>
      formatStationName(a.name).localeCompare(formatStationName(b.name))
    );
  } else if (sortValue === "bikes") {
    favourites.sort((a, b) => (b.available_bikes ?? 0) - (a.available_bikes ?? 0));
  } else if (sortValue === "stands") {
    favourites.sort((a, b) => (b.available_bike_stands ?? 0) - (a.available_bike_stands ?? 0));
  }

  if (allSaved.length === 0) {
    favouritesGrid.innerHTML = "";
    if (emptyState) emptyState.style.display = "block";
    return;
  }

  if (favourites.length === 0) {
    favouritesGrid.innerHTML = `
      <div class="empty-box">
        <div class="feature-icon">
          <img src="icons/star.svg" alt="Star icon" />
        </div>
        <h2>No matching favourites</h2>
        <p>Try a different search term or sort option.</p>
      </div>
    `;
    if (emptyState) emptyState.style.display = "none";
    return;
  }

  favouritesGrid.innerHTML = favourites.map(createFavouriteCard).join("");
  if (emptyState) emptyState.style.display = "none";

  setupFavouriteRemoval();
}

function removeFavouriteStation(stationNumber) {
  const favourites = getFavouriteStations().filter(
    (station) => station.number !== Number(stationNumber)
  );

  saveFavouriteStations(favourites);
}

function setupFavouriteRemoval() {
  const removeButtons = document.querySelectorAll(".remove-favourite-btn");

  removeButtons.forEach((button) => {
    button.addEventListener("click", () => {
      const stationNumber = button.dataset.stationNumber;
      removeFavouriteStation(stationNumber);
      renderFavouritesPage();
    });
  });
}

function setupFavouritesPageControls() {
  const searchInput = document.getElementById("favouritesSearch");
  const sortSelect = document.getElementById("favouritesSort");

  if (searchInput) {
    searchInput.addEventListener("input", renderFavouritesPage);
  }

  if (sortSelect) {
    sortSelect.addEventListener("change", renderFavouritesPage);
  }
}

/* ----------------------
  RESERVE BIKES
----------------------- */

function getReservedStations() {
  const stored = localStorage.getItem("reservedStations");

  try {
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.error("Could not parse reserved stations:", error);
    return [];
  }
}

function saveReservedStations(reservations) {
  localStorage.setItem("reservedStations", JSON.stringify(reservations));
}

function isStationReserved(station) {
  if (!station) return false;

  const reservations = getReservedStations();
  return reservations.some((reserved) => reserved.number === station.number);
}

function reserveStation(station) {
  if (!station) return;

  const reservations = getReservedStations();

  if (reservations.some((reserved) => reserved.number === station.number)) {
    return;
  }

  reservations.push({
    number: station.number,
    name: station.name,
    address: station.address,
    available_bikes: station.available_bikes,
    available_bike_stands: station.available_bike_stands,
    bike_stands: station.bike_stands,
    status: station.status,
    position: station.position,
    reservedAt: new Date().toISOString()
  });

  saveReservedStations(reservations);
}

function cancelReservation(station) {
  if (!station) return;

  const reservations = getReservedStations().filter(
    (reserved) => reserved.number !== station.number
  );

  saveReservedStations(reservations);
}

function updateReserveButtonState() {
  const reserveBtn = document.getElementById("reserveBtn");
  if (!reserveBtn) return;

  if (!selectedStation) {
    reserveBtn.textContent = "Reserve";
    reserveBtn.disabled = true;
    reserveBtn.classList.remove("reserved");
    return;
  }

  reserveBtn.disabled = false;

  if (isStationReserved(selectedStation)) {
    reserveBtn.textContent = "Reserved";
    reserveBtn.classList.add("reserved");
  } else {
    reserveBtn.textContent = "Reserve";
    reserveBtn.classList.remove("reserved");
  }
}

function setupReserveButton() {
  const reserveBtn = document.getElementById("reserveBtn");
  if (!reserveBtn) return;

  reserveBtn.addEventListener("click", () => {
    if (!selectedStation) return;

    if (isStationReserved(selectedStation)) {
      cancelReservation(selectedStation);
    } else {
      reserveStation(selectedStation);
    }

    updateReserveButtonState();
  });
}