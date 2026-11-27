document.querySelectorAll("[data-toggle]").forEach((button) => {
  button.addEventListener("click", () => {
    const input = document.getElementById(button.dataset.toggle);
    if (!input) return;
    const showing = input.type === "text";
    input.type = showing ? "password" : "text";
    button.textContent = showing ? "Show" : "Hide";
  });
});

document.querySelectorAll(".otp-input").forEach((input) => {
  input.addEventListener("input", () => {
    input.value = input.value.replace(/[^0-9 ]/g, "").slice(0, 8);
  });
});

document.querySelectorAll(".flash").forEach((message) => {
  window.setTimeout(() => {
    message.classList.add("fade-out");
    window.setTimeout(() => message.remove(), 350);
  }, 4500);
});
