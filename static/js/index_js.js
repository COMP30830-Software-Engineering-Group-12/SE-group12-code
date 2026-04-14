async function updateCurrentWeather() {
    const res = await fetch("/api/current_weather");
    const data = await res.json();

    document.getElementById("current-temp").textContent =
        (data.temp ?? "N/A") + " °C";
}

setInterval(updateCurrentWeather, 30000);