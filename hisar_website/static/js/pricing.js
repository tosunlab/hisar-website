function setBillingPeriod(toggle, period) {
  for (const periodButton of toggle.querySelectorAll("[data-billing-period]")) {
    periodButton.setAttribute("aria-pressed", String(periodButton.dataset.billingPeriod === period));
  }
  for (const option of document.querySelectorAll("[data-billing-option]")) {
    option.hidden = option.dataset.billingOption !== period;
  }
}

function setUpBillingToggle() {
  const toggle = document.querySelector("[data-billing-toggle]");
  if (!toggle) {
    return;
  }
  toggle.hidden = false;
  for (const periodButton of toggle.querySelectorAll("[data-billing-period]")) {
    periodButton.addEventListener("click", () => setBillingPeriod(toggle, periodButton.dataset.billingPeriod));
  }
}

document.addEventListener("DOMContentLoaded", setUpBillingToggle);
