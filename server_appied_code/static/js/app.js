document.addEventListener("DOMContentLoaded", async () => {
  setupAccountDropdown();
  initialiseFavouritesPage();

  const mapElement = document.getElementById("map");
  if (mapElement && window.google && google.maps) {
    initialiseMapPage();
  }

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
let markers = [];
let bikeStations = [];
let currentWeather = null;
let forecastWeather = [];
let selectedStation = null;
let favouriteStationNumbers = new Set();
let userCurrentLocation = null;
let selectedFromPlace = null;
let selectedToPlace = null;
let userLocationMarker = null;
let userAccuracyCircle = null;
let fromPlaceMarker = null;
let toPlaceMarker = null;
let directionsService = null;

let walkingPolyline1 = null;
let cyclingPolyline = null;
let walkingPolyline2 = null;

let routeStepMarkers = [];

/* ----------------------
  INITIALISE PAGES
----------------------- */

function setupFavouritesPageControls() {
  const searchInput = document.getElementById("favouritesSearch");
  const sortSelect = document.getElementById("favouritesSort");

  if (searchInput) {
    searchInput.addEventListener("input", () => {
      renderFavouritesPage();
    });
  }

  if (sortSelect) {
    sortSelect.addEventListener("change", () => {
      renderFavouritesPage();
    });
  }
}

async function initialiseMapPage() {
  const mapElement = document.getElementById("map");
  if (!mapElement) return;

  try {
    setupGoogleMap();

    await getUserCurrentLocation();

    await loadAllData();

    if (window.IS_LOGGED_IN) {
      await loadUserFavourites();
    }

    renderStationMarkers(bikeStations);
    setupSearchAndFilters();
    setupJourneyAutocomplete();
    setupJourneyClearButton();
    setupStationSearchAutocomplete();
    setupFavouriteToggle();
    setupChatForm();
    setupChatToggle();
    setupUseCurrentLocationButton();
    setupJourneyPlanner();

    const defaultStation = bikeStations.find(
      (station) => Number(station.number) === 31
    );

    if (defaultStation) {
      selectStation(defaultStation);
    } else if (bikeStations.length > 0) {
      selectStation(bikeStations[0]);
    }

    if (userCurrentLocation) {
      renderUserLocation(userCurrentLocation);
    }
  } catch (error) {
    console.error("Error initialising map page:", error);
  }
  await getUserCurrentLocation();
  console.log("initial userCurrentLocation:", userCurrentLocation);
}

function initialiseFavouritesPage() {
  const favouritesGrid = document.getElementById("favouritesGrid");
  if (!favouritesGrid) return;

  setupFavouritesPageControls();
  renderFavouritesPage();
}

async function fetchUserFavourites() {
  const response = await fetch("/api/favourites");

  if (!response.ok) {
    if (response.status === 401) {
      window.location.href = "/login";
      return [];
    }
    throw new Error("Failed to load favourites.");
  }

  const data = await response.json();

  if (!data.success || !Array.isArray(data.favourites)) {
    return [];
  }

  return data.favourites;
}

/* ----------------------
  DATA LOADING
----------------------- */

async function fetchJson(url) {
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error(`Request failed: ${url} (${response.status})`);
  }

  return await response.json();
}

async function loadAllData() {
  const [bikeData, currentWeatherData, forecastWeatherData] = await Promise.all([
    fetchJson("/api/bike_stations_latest"),
    fetchJson("/api/current_weather"),
    fetchJson("/api/hourly_forecast")
  ]);

  bikeStations = Array.isArray(bikeData) ? bikeData : [];
  currentWeather = currentWeatherData || null;
  forecastWeather = Array.isArray(forecastWeatherData) ? forecastWeatherData : [];
}

/* ----------------------
  MAP SETUP
----------------------- */

function setupGoogleMap() {
  if (map) return;

  map = new google.maps.Map(document.getElementById("map"), {
    center: { lat: 53.3498, lng: -6.2603 },
    zoom: 13,
    mapId: window.GOOGLE_MAPS_MAP_ID
  });

  directionsService = new google.maps.DirectionsService();
}

function renderStationMarkers(stations) {
  // delete old marker
  markers.forEach(marker => marker.map = null);
  markers = [];

  stations.forEach((station) => {
    const lat = Number(station.position?.lat);
    const lng = Number(station.position?.lng);

    if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

    const marker = new google.maps.marker.AdvancedMarkerElement({
      map,
      position: { lat, lng },
      content: createMarkerHTML(station),
    });

    marker.addListener("click", () => {
      selectStation(station);
    });

    // save
    markers.push(marker);
  });
}

function createMarkerHTML(station) {
  const bikes = station.available_bikes ?? 0;
  const color = getMarkerColour(station);

  const container = document.createElement("div");

  container.style.display = "flex";
  container.style.alignItems = "center";
  container.style.justifyContent = "center";

  container.style.width = "32px";
  container.style.height = "32px";
  container.style.borderRadius = "50%";

  container.style.background = color;
  container.style.color = "white";
  container.style.fontSize = "12px";
  container.style.fontWeight = "bold";

  container.style.border = "2px solid white";
  container.style.boxShadow = "0 2px 6px rgba(0,0,0,0.3)";
  container.style.cursor = "pointer";

  // 👉 show bike number
  container.textContent = bikes;

  return container;
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

  const lat = Number(station.position?.lat);
  const lng = Number(station.position?.lng);

  if (Number.isFinite(lat) && Number.isFinite(lng) && map) {
    map.panTo({ lat, lng });

    const currentZoom = map.getZoom();
    if (currentZoom < 15) {
      window.setTimeout(() => {
        map.setZoom(15);
      }, 250);
    }
  }

  updateFavouriteButtonState();
  loadPredictionForStation(station);
}

function updateStationMetaBlock(station) {
  const metaContainer = document.querySelector(".topbar-right .station-meta");
  if (!metaContainer) return;

  const bikes = station.available_bikes ?? 0;

  let statusText = "Moderate availability";
  if (bikes >= 15) statusText = "High bike availability";
  else if (bikes < 5) statusText = "Low bike availability";

  metaContainer.innerHTML = `
    <p><strong>Status:</strong> ${statusText}</p>
  `;
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

function setupStationSearchAutocomplete() {
  const stationSearch = document.getElementById("stationSearch");
  const stationSuggestions = document.getElementById("stationSuggestions");

  if (!stationSearch || !stationSuggestions) return;

  setupAutocompleteForInput(stationSearch, stationSuggestions, {
    onSelect: (station) => {
      stationSearch.value = formatStationName(station.name);
      selectStation(station);
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

/* ----------------------
  CHAT PLACEHOLDER
----------------------- */

function setupChatForm() {
  const chatForm = document.querySelector(".chat-input-row");
  const chatInput = document.getElementById("chatInput");
  const chatMessages = document.querySelector(".chat-messages");

  if (!chatForm || !chatInput || !chatMessages) return;

  chatForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const message = chatInput.value.trim();
    if (!message) return;

    appendChatBubble(message, "user", chatMessages);
    chatInput.value = "";

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          message: message,
          user_lat: userCurrentLocation?.lat ?? null,
          user_lng: userCurrentLocation?.lng ?? null,
          selected_station_id: selectedStation?.number ?? null
        })
      });

      const data = await response.json();

      appendChatBubble(
        data.reply || "Sorry, I couldn't get a response.",
        "bot",
        chatMessages
      );
    } catch (error) {
      console.error("Chat error:", error);
      appendChatBubble(
        "Sorry, something went wrong.",
        "bot",
        chatMessages
      );
    }
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

        <button
          class="favourite-icon-btn active remove-favourite-heart-btn"
          type="button"
          data-station-number="${station.number}"
          aria-label="Remove favourite"
          title="Remove favourite"
        >
          <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 21s-6.5-4.2-9-7A5 5 0 0 1 12 6a5 5 0 0 1 9 8c-2.5 2.8-9 7-9 7z" />
          </svg>
        </button>
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
        <a href="/map?station=${station.number}" class="btn btn-primary">View on Map</a>
      </div>
    </article>
  `;
}

async function removeFavouriteFromDatabase(stationNumber) {
  const response = await fetch("/api/favourites/remove", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      station_number: Number(stationNumber)
    })
  });

  const data = await response.json();

  if (!response.ok || !data.success) {
    throw new Error(data.message || "Failed to remove favourite.");
  }

  return true;
}

function setupFavouriteCardNavigation() {
  const cards = document.querySelectorAll(".favourite-card");

  cards.forEach((card) => {
    card.addEventListener("click", (event) => {
      const clickedHeart = event.target.closest(".remove-favourite-heart-btn");
      const clickedButton = event.target.closest("button");
      const clickedLink = event.target.closest("a");

      if (clickedHeart || clickedButton || clickedLink) {
        return;
      }

      const stationNumber = card.dataset.stationNumber;
      if (!stationNumber) return;

      window.location.href = `/map?station=${stationNumber}`;
    });
  });
}

function setupFavouriteRemoval() {
  const removeButtons = document.querySelectorAll(".remove-favourite-heart-btn");

  removeButtons.forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.preventDefault();
      event.stopPropagation();

      const stationNumber = button.dataset.stationNumber;
      if (!stationNumber) return;

      try {
        await removeFavouriteFromDatabase(stationNumber);
        await renderFavouritesPage();
      } catch (error) {
        console.error("Error removing favourite:", error);
        alert("Could not remove favourite. Please try again.");
      }
    });
  });
}

async function renderFavouritesPage() {
  const favouritesGrid = document.getElementById("favouritesGrid");
  const emptyState = document.getElementById("emptyState");
  const searchInput = document.getElementById("favouritesSearch");
  const sortSelect = document.getElementById("favouritesSort");

  if (!favouritesGrid) return;

  let favourites = [];
  let allSaved = [];

  try {
    allSaved = await fetchUserFavourites();
    favourites = [...allSaved];
  } catch (error) {
    console.error("Error loading favourites page:", error);
    favouritesGrid.innerHTML = "";
    if (emptyState) emptyState.style.display = "block";
    return;
  }

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
          <img src="/static/icons/star.svg" alt="Star icon" />
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

  setupFavouriteCardNavigation();
  setupFavouriteRemoval();
}

async function loadUserFavourites() {
  try {
    const response = await fetch("/api/favourites");

    if (!response.ok) {
      favouriteStationNumbers = new Set();
      return;
    }

    const data = await response.json();

    if (data.success && Array.isArray(data.favourites)) {
      favouriteStationNumbers = new Set(
        data.favourites.map((station) => Number(station.number))
      );
    } else {
      favouriteStationNumbers = new Set();
    }
  } catch (error) {
    console.error("Error loading favourites:", error);
    favouriteStationNumbers = new Set();
  }
}

function isStationFavourite(station) {
  if (!station) return false;
  return favouriteStationNumbers.has(Number(station.number));
}

function updateFavouriteButtonState() {
  const favouriteBtn = document.getElementById("favouriteToggleBtn");
  if (!favouriteBtn) return;

  if (!selectedStation || !window.IS_LOGGED_IN) {
    favouriteBtn.classList.remove("active");
    return;
  }

  favouriteBtn.classList.toggle("active", isStationFavourite(selectedStation));
}

function setupFavouriteToggle() {
  const favouriteBtn = document.getElementById("favouriteToggleBtn");
  if (!favouriteBtn) return;

  favouriteBtn.addEventListener("click", async () => {
    if (!selectedStation) return;

    // no login, redirect to login page
    if (!window.IS_LOGGED_IN) {
      window.location.href = "/login";
      return;
    }

    const stationNumber = Number(selectedStation.number);

    try {
      if (isStationFavourite(selectedStation)) {
        const response = await fetch("/api/favourites/remove", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            station_number: stationNumber
          })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
          throw new Error(data.message || "Failed to remove favourite.");
        }

        favouriteStationNumbers.delete(stationNumber);
      } else {
        const response = await fetch("/api/favourites/add", {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            station_number: stationNumber
          })
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
          throw new Error(data.message || "Failed to add favourite.");
        }

        favouriteStationNumbers.add(stationNumber);
      }

      updateFavouriteButtonState();
    } catch (error) {
      console.error("Favourite toggle error:", error);
      alert("Could not update favourite. Please try again.");
    }
  });
}


/* ----------------------
  Route Planning
----------------------- */
function moveMapToLocation(lat, lng, zoom = 15) {
  if (!map) return;
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

  map.panTo({ lat, lng });

  const currentZoom = map.getZoom();
  if (currentZoom < zoom) {
    window.setTimeout(() => {
      map.setZoom(zoom);
    }, 250);
  }
}

function setupJourneyAutocomplete() {
  const fromInput = document.getElementById("fromInput");
  const toInput = document.getElementById("toInput");

  if (!fromInput || !toInput || !window.google || !google.maps || !google.maps.places) {
    return;
  }

  const options = {
    fields: ["place_id", "geometry", "formatted_address", "name"],
    componentRestrictions: { country: "ie" }
  };

  const fromAutocomplete = new google.maps.places.Autocomplete(fromInput, options);
  const toAutocomplete = new google.maps.places.Autocomplete(toInput, options);

  if (map) {
    fromAutocomplete.bindTo("bounds", map);
    toAutocomplete.bindTo("bounds", map);
  }

  if (userCurrentLocation) {
    const locationCircle = new google.maps.Circle({
      center: userCurrentLocation,
      radius: 5000
    });

    fromAutocomplete.setBounds(locationCircle.getBounds());
    toAutocomplete.setBounds(locationCircle.getBounds());
  }

  fromAutocomplete.addListener("place_changed", () => {
    const place = fromAutocomplete.getPlace();

    if (!place.geometry || !place.geometry.location) {
      selectedFromPlace = null;
      return;
    }

    selectedFromPlace = {
      placeId: place.place_id,
      name: place.name || "",
      address: place.formatted_address || fromInput.value,
      lat: place.geometry.location.lat(),
      lng: place.geometry.location.lng()
    };

    fromInput.value = selectedFromPlace.address;

    moveMapToLocation(selectedFromPlace.lat, selectedFromPlace.lng);
    setTemporaryPlaceMarker("from", selectedFromPlace.lat, selectedFromPlace.lng);
  });

  toAutocomplete.addListener("place_changed", () => {
    const place = toAutocomplete.getPlace();

    if (!place.geometry || !place.geometry.location) {
      selectedToPlace = null;
      return;
    }

    selectedToPlace = {
      placeId: place.place_id,
      name: place.name || "",
      address: place.formatted_address || toInput.value,
      lat: place.geometry.location.lat(),
      lng: place.geometry.location.lng()
    };

    toInput.value = selectedToPlace.address;

    moveMapToLocation(selectedToPlace.lat, selectedToPlace.lng);
    setTemporaryPlaceMarker("to", selectedToPlace.lat, selectedToPlace.lng);
  });
}

function getUserCurrentLocation() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        userCurrentLocation = {
          lat: position.coords.latitude,
          lng: position.coords.longitude,
          accuracy: position.coords.accuracy
        };
        resolve(userCurrentLocation);
      },
      (error) => {
        console.warn("Could not get current location:", error);
        resolve(null);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 300000
      }
    );
  });
}

function setupUseCurrentLocationButton() {
  const btn = document.getElementById("useCurrentLocationBtn");
  const fromInput = document.getElementById("fromInput");

  if (!btn || !fromInput) return;

  btn.addEventListener("click", async () => {
    if (!userCurrentLocation) {
      await getUserCurrentLocation();
    }

    if (!userCurrentLocation) {
      alert("Could not get your current location.");
      return;
    }

    selectedFromPlace = {
      placeId: null,
      name: "Current location",
      address: "My current location",
      lat: userCurrentLocation.lat,
      lng: userCurrentLocation.lng
    };

    fromInput.value = "My current location";

    setTemporaryPlaceMarker("from", userCurrentLocation.lat, userCurrentLocation.lng);

    if (map) {
      moveMapToLocation(userCurrentLocation.lat, userCurrentLocation.lng);
      renderUserLocation(userCurrentLocation);
    }
  });
}

function renderUserLocation(location) {
  if (!map || !location) return;

  const { lat, lng, accuracy } = location;

  if (userLocationMarker) userLocationMarker.map = null;
  if (userAccuracyCircle) userAccuracyCircle.setMap(null);

  // 🔵 
  userLocationMarker = new google.maps.marker.AdvancedMarkerElement({
    map,
    position: { lat, lng },
    content: createUserLocationDot()
  });

  // 🟦 blue range
  userAccuracyCircle = new google.maps.Circle({
    map,
    center: { lat, lng },
    radius: accuracy || 50,
    strokeColor: "#4285F4",
    strokeOpacity: 0.3,
    strokeWeight: 1,
    fillColor: "#4285F4",
    fillOpacity: 0.15
  });
}

function createUserLocationDot() {
  const container = document.createElement("div");

  container.style.width = "16px";
  container.style.height = "16px";
  container.style.borderRadius = "50%";

  container.style.background = "#4285F4"; // Google blue
  container.style.border = "3px solid white";
  container.style.boxShadow = "0 0 6px rgba(0,0,0,0.3)";

  return container;
}

function createRoutePlaceMarker(label, color) {
  const container = document.createElement("div");

  container.innerHTML = `
    <svg width="36" height="48" viewBox="0 0 36 48">
      <!-- shape -->
      <path
        d="M18 0C9 0 2 7 2 16c0 12 16 32 16 32s16-20 16-32C34 7 27 0 18 0z"
        fill="${color}"
        stroke="white"
        stroke-width="2"
      />
      
      <!-- white center -->
      <circle cx="18" cy="16" r="8" fill="white" />

      <!--  A / B -->
      <text
        x="18"
        y="20"
        text-anchor="middle"
        font-size="10"
        font-weight="bold"
        fill="${color}"
      >
        ${label}
      </text>
    </svg>
  `;

  return container;
}

function setTemporaryPlaceMarker(type, lat, lng) {
  if (!map) return;
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

  if (type === "from") {
    if (fromPlaceMarker) {
      fromPlaceMarker.map = null;
    }

    fromPlaceMarker = new google.maps.marker.AdvancedMarkerElement({
      map,
      position: { lat, lng },
      content: createRoutePlaceMarker("A", "#24cee1")
    });
  }

  if (type === "to") {
    if (toPlaceMarker) {
      toPlaceMarker.map = null;
    }

    toPlaceMarker = new google.maps.marker.AdvancedMarkerElement({
      map,
      position: { lat, lng },
      content: createRoutePlaceMarker("B", "#32cbe6")
    });
  }
}

function clearTemporaryRouteMarkers() {
  if (fromPlaceMarker) {
    fromPlaceMarker.map = null;
    fromPlaceMarker = null;
  }

  if (toPlaceMarker) {
    toPlaceMarker.map = null;
    toPlaceMarker = null;
  }

  selectedFromPlace = null;
  selectedToPlace = null;

  const fromInput = document.getElementById("fromInput");
  const toInput = document.getElementById("toInput");

  if (fromInput) fromInput.value = "";
  if (toInput) toInput.value = "";
}

function setupJourneyClearButton() {
  const routeForm = document.querySelector(".route-form");
  const clearBtn = routeForm?.querySelector('button[type="reset"]');
  const routeResults = document.getElementById("routeResults");

  if (!clearBtn) return;

  clearBtn.addEventListener("click", (event) => {
    event.preventDefault();

    clearPlannedRoute();
    clearTemporaryRouteMarkers();

    if (routeResults) {
      routeResults.innerHTML = `<p>Choose a start and destination station to preview a route.</p>`;
    }
  });
}

/* ----------------------
  Route Planning Main
----------------------- */
function calculateDistanceKm(lat1, lng1, lat2, lng2) {
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

function findNearestStation(lat, lng, options = {}) {
  const {
    requireAvailableBikes = false,
    requireAvailableStands = false
  } = options;

  let nearestStation = null;
  let minDistance = Infinity;

  for (const station of bikeStations) {
    const stationLat = Number(station.position?.lat);
    const stationLng = Number(station.position?.lng);

    if (!Number.isFinite(stationLat) || !Number.isFinite(stationLng)) {
      continue;
    }

    if (requireAvailableBikes && (station.available_bikes ?? 0) <= 0) {
      continue;
    }

    if (requireAvailableStands && (station.available_bike_stands ?? 0) <= 0) {
      continue;
    }

    const distance = calculateDistanceKm(lat, lng, stationLat, stationLng);

    if (distance < minDistance) {
      minDistance = distance;
      nearestStation = station;
    }
  }

  return nearestStation;
}

async function requestRouteSegment(origin, destination, travelMode) {
  if (!directionsService) {
    throw new Error("DirectionsService is not initialized.");
  }

  const result = await directionsService.route({
    origin,
    destination,
    travelMode,
    unitSystem: google.maps.UnitSystem.METRIC
  });

  return result;
}

function drawRoutePolylineFromDirectionsResult(result, options = {}) {
  const route = result.routes?.[0];
  if (!route) return null;

  const overviewPath = route.overview_path;
  if (!overviewPath || !overviewPath.length) return null;

  return new google.maps.Polyline({
    map,
    path: overviewPath,
    geodesic: true,
    strokeColor: options.strokeColor || "#1a9632",
    strokeOpacity: options.strokeOpacity ?? 1,
    strokeWeight: options.strokeWeight ?? 5,
    icons: options.icons || undefined
  });
}

function getWalkingPolylineOptions() {
  return {
    strokeColor: "#6c757d",
    strokeOpacity: 0.9,
    strokeWeight: 4,
    icons: [
      {
        icon: {
          path: "M 0,-1 0,1",
          strokeOpacity: 1,
          scale: 4
        },
        offset: "0",
        repeat: "12px"
      }
    ]
  };
}

function getCyclingPolylineOptions() {
  return {
    strokeColor: "#1a9632",
    strokeOpacity: 0.95,
    strokeWeight: 5
  };
}

function addRouteStationMarker(station, label, color) {
  const lat = Number(station.position?.lat);
  const lng = Number(station.position?.lng);

  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

  const marker = new google.maps.marker.AdvancedMarkerElement({
    map,
    position: { lat, lng },
    content: createRoutePlaceMarker(label, color)
  });

  routeStepMarkers.push(marker);
}

function setupJourneyPlanner() {
  const planRouteBtn = document.getElementById("planRouteBtn");
  const routeResults = document.getElementById("routeResults");

  if (!planRouteBtn) return;

  planRouteBtn.addEventListener("click", async () => {
    try {
      if (!selectedFromPlace || !selectedToPlace) {
        if (routeResults) {
          routeResults.innerHTML = `<p>Please choose both a start and destination.</p>`;
        }
        return;
      }

      clearPlannedRoute();

      const startStation = findNearestStation(
        selectedFromPlace.lat,
        selectedFromPlace.lng,
        { requireAvailableBikes: true }
      );

      const endStation = findNearestStation(
        selectedToPlace.lat,
        selectedToPlace.lng,
        { requireAvailableStands: true }
      );

      if (!startStation || !endStation) {
        if (routeResults) {
          routeResults.innerHTML = `<p>Could not find suitable bike stations for this journey.</p>`;
        }
        return;
      }

      const startStationLatLng = {
        lat: Number(startStation.position.lat),
        lng: Number(startStation.position.lng)
      };

      const endStationLatLng = {
        lat: Number(endStation.position.lat),
        lng: Number(endStation.position.lng)
      };

      const walkingResult1 = await requestRouteSegment(
        { lat: selectedFromPlace.lat, lng: selectedFromPlace.lng },
        startStationLatLng,
        google.maps.TravelMode.WALKING
      );

      const cyclingResult = await requestRouteSegment(
        startStationLatLng,
        endStationLatLng,
        google.maps.TravelMode.BICYCLING
      );

      const walkingResult2 = await requestRouteSegment(
        endStationLatLng,
        { lat: selectedToPlace.lat, lng: selectedToPlace.lng },
        google.maps.TravelMode.WALKING
      );

      walkingPolyline1 = drawRoutePolylineFromDirectionsResult(
        walkingResult1,
        getWalkingPolylineOptions()
      );

      cyclingPolyline = drawRoutePolylineFromDirectionsResult(
        cyclingResult,
        getCyclingPolylineOptions()
      );

      walkingPolyline2 = drawRoutePolylineFromDirectionsResult(
        walkingResult2,
        getWalkingPolylineOptions()
      );

      addRouteStationMarker(startStation, "A", "#1a9632");
      addRouteStationMarker(endStation, "B", "#d9534f");

      fitMapToWholeJourney(
        selectedFromPlace,
        startStation,
        endStation,
        selectedToPlace
      );

      updateRouteSummary(
        routeResults,
        walkingResult1,
        cyclingResult,
        walkingResult2,
        startStation,
        endStation
      );
    } catch (error) {
      console.error("Route planning failed:", error);

      if (routeResults) {
        routeResults.innerHTML = `<p>Could not plan the route. Please try again.</p>`;
      }
    }
  });
}

function fitMapToWholeJourney(fromPlace, startStation, endStation, toPlace) {
  if (!map) return;

  const bounds = new google.maps.LatLngBounds();

  bounds.extend({ lat: fromPlace.lat, lng: fromPlace.lng });
  bounds.extend({
    lat: Number(startStation.position.lat),
    lng: Number(startStation.position.lng)
  });
  bounds.extend({
    lat: Number(endStation.position.lat),
    lng: Number(endStation.position.lng)
  });
  bounds.extend({ lat: toPlace.lat, lng: toPlace.lng });

  map.fitBounds(bounds);
}

function getLegDistanceAndDuration(result) {
  const leg = result.routes?.[0]?.legs?.[0];
  return {
    distanceText: leg?.distance?.text || "--",
    durationText: leg?.duration?.text || "--"
  };
}

function updateRouteSummary(routeResults, walking1, cycling, walking2, startStation, endStation) {
  if (!routeResults) return;

  const walk1 = getLegDistanceAndDuration(walking1);
  const bike = getLegDistanceAndDuration(cycling);
  const walk2 = getLegDistanceAndDuration(walking2);

  routeResults.innerHTML = `
    <div class="route-summary-card">
      <div class="route-summary-item">
        <span class="route-summary-label">Walk to station</span>
        <strong>${walk1.durationText}</strong>
        <small>${walk1.distanceText}</small>
      </div>

      <div class="route-summary-divider"></div>

      <div class="route-summary-item">
        <span class="route-summary-label">Cycle</span>
        <strong>${bike.durationText}</strong>
        <small>${bike.distanceText}</small>
      </div>

      <div class="route-summary-divider"></div>

      <div class="route-summary-item">
        <span class="route-summary-label">Walk to destination</span>
        <strong>${walk2.durationText}</strong>
        <small>${walk2.distanceText}</small>
      </div>
    </div>

    <div class="route-station-summary">
      <p><strong>Pickup:</strong> ${formatStationName(startStation.name)}</p>
      <p><strong>Dropoff:</strong> ${formatStationName(endStation.name)}</p>
    </div>
  `;
}

function clearPlannedRoute() {
  if (walkingPolyline1) {
    walkingPolyline1.setMap(null);
    walkingPolyline1 = null;
  }

  if (cyclingPolyline) {
    cyclingPolyline.setMap(null);
    cyclingPolyline = null;
  }

  if (walkingPolyline2) {
    walkingPolyline2.setMap(null);
    walkingPolyline2 = null;
  }

  routeStepMarkers.forEach((marker) => {
    marker.map = null;
  });
  routeStepMarkers = [];
}

/* ----------------------
  ML
----------------------- */
async function fetchPrediction(stationId) {
  try {
    const res = await fetch(`/api/prediction?station_id=${stationId}`);
    if (!res.ok) throw new Error("Prediction failed");

    return await res.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}

function renderPredictionChart(predictions, currentBikes) {
  const container = document.querySelector(".chart-placeholder");
  if (!container) return;

  container.innerHTML = "";

  if (!predictions || predictions.length === 0) {
    container.innerHTML = '<p class="prediction-empty">No prediction data</p>';
    return;
  }

  const allData = [
    {
      dt_txt: "Now",
      predicted_bikes: currentBikes ?? 0,
      isCurrent: true
    },
    ...predictions.map((p) => ({
      ...p,
      isCurrent: false
    }))
  ];

  const displayData = allData.slice(0, 12);
  const maxValue = Math.max(...displayData.map((p) => Number(p.predicted_bikes) || 0), 1);

  displayData.forEach((p) => {
    const value = Number(p.predicted_bikes) || 0;
    const heightPercent = (value / maxValue) * 100;

    const item = document.createElement("div");
    item.className = "prediction-bar-item";

    const label = document.createElement("div");
    label.className = "prediction-value-label";
    label.textContent = value;

    const barArea = document.createElement("div");
    barArea.className = "prediction-bar-area";

    const bar = document.createElement("div");
    bar.className = "chart-bar";
    bar.style.height = `${Math.max(heightPercent, 8)}%`;

    if (p.isCurrent) {
      bar.classList.add("current-bar");
    } else {
      bar.classList.add("forecast-bar");
    }

    bar.title = `${p.dt_txt} → ${value} bikes`;

    barArea.appendChild(bar);
    item.appendChild(label);
    item.appendChild(barArea);
    container.appendChild(item);
  });
}

async function loadPredictionForStation(station) {
  if (!station) return;

  const stationId = station.number;

  const data = await fetchPrediction(stationId);

  if (!data || !data.predictions) {
    console.error("No prediction data");
    return;
  }

  renderPredictionChart(data.predictions, station.available_bikes ?? 0);
}
