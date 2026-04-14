document.addEventListener("DOMContentLoaded", () => {
  let seconds = 5;
  const countdownEl = document.getElementById("countdown");

  const interval = setInterval(() => {
    seconds -= 1;

    if (countdownEl) {
      countdownEl.textContent = seconds;
    }

    if (seconds <= 0) {
      clearInterval(interval);
      window.location.href = "/login";
    }
  }, 1000);
});