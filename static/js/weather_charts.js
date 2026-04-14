document.addEventListener("DOMContentLoaded", () => {
  const hourlyForecast = window.hourlyForecastData || [];

  if (!Array.isArray(hourlyForecast) || hourlyForecast.length === 0) {
    return;
  }

  renderTemperatureChart(hourlyForecast);
  renderRainChart(hourlyForecast);
});

function renderTemperatureChart(hourlyForecast) {
  const canvas = document.getElementById("temperatureChart");
  if (!canvas) return;

  const labels = hourlyForecast.map((item, index) => {
    if (!item.dt_txt) return index === 0 ? "Now" : "--:--";
    return index === 0 ? "Now" : item.dt_txt.slice(11, 16);
  });

  const temperatures = hourlyForecast.map((item) => {
    return item.temp != null ? Math.round(item.temp) : null;
  });

  new Chart(canvas, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Temperature (°C)",
          data: temperatures,
          tension: 0.3,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.parsed.y}°C`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: false,
          ticks: {
            callback: function(value) {
              return value + "°C";
            }
          }
        }
      }
    }
  });
}

function renderRainChart(hourlyForecast) {
  const canvas = document.getElementById("rainChart");
  if (!canvas) return;

  const labels = hourlyForecast.map((item, index) => {
    if (!item.dt_txt) return index === 0 ? "Now" : "--:--";
    return index === 0 ? "Now" : item.dt_txt.slice(11, 16);
  });

  const rainProbability = hourlyForecast.map((item) => {
    const value = item.prob != null ? item.prob : 0;
    return Math.round(value * 100);
  });

  new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Rain Probability (%)",
          data: rainProbability
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          callbacks: {
            label: function(context) {
              return `${context.parsed.y}%`;
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          ticks: {
            callback: function(value) {
              return value + "%";
            }
          }
        }
      }
    }
  });
}