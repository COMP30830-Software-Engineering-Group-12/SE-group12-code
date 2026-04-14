document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector(".signup-form");

  if (!form) return;

  form.addEventListener("submit", (event) => {
    // get value
    const fullName = document.getElementById("fullName")?.value.trim();
    const email = document.getElementById("signupEmail")?.value.trim();
    const password = document.getElementById("signupPassword")?.value;
    const confirmPassword = document.getElementById("confirmPassword")?.value;

    let errorMessage = "";

    // 1. check if all sessions are not empty
    if (!fullName || !email || !password || !confirmPassword) {
      errorMessage = "All fields are required.";
    }

    // 2. Length of password validation
    else if (password.length < 8) {
      errorMessage = "Password must be at least 8 characters.";
    }

    // 3. if confirm password is the same
    else if (password !== confirmPassword) {
      errorMessage = "Passwords do not match.";
    }

    // ❌ if incorrect - stop submitting
    if (errorMessage) {
      event.preventDefault();
      showFormError(errorMessage);
    }
  });
});

function showFormError(message) {
  let errorBox = document.getElementById("formErrorBox");

  if (!errorBox) {
    errorBox = document.createElement("div");
    errorBox.id = "formErrorBox";
    errorBox.className = "form-error";

    const form = document.querySelector(".signup-form");
    form.parentNode.insertBefore(errorBox, form);
  }

  errorBox.textContent = "* " + message;
}