document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector(".login-form");
  if (!form) return;

  form.addEventListener("submit", (event) => {
    const email = document.getElementById("email")?.value.trim();
    const password = document.getElementById("password")?.value;

    let errorMessage = "";

    if (!email || !password) {
      errorMessage = "Please enter both email and password.";
    }

    if (errorMessage) {
      event.preventDefault();
      showLoginFormError(errorMessage);
    }
  });
});

function showLoginFormError(message) {
  let errorBox = document.getElementById("loginFormErrorBox");

  if (!errorBox) {
    errorBox = document.createElement("div");
    errorBox.id = "loginFormErrorBox";
    errorBox.className = "form-error";

    const form = document.querySelector(".login-form");
    form.parentNode.insertBefore(errorBox, form);
  }

  errorBox.textContent = "* " + message;
}