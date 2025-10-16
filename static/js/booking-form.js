(function () {
  const form = document.querySelector('[data-module="booking-form"]');
  if (!form) return;

  const basePrice = parseFloat(form.dataset.basePrice || '0');
  const currencySymbol = form.dataset.currencySymbol || '';

  const baseOutput = form.querySelector('[data-booking-base]');
  const extrasOutput = form.querySelector('[data-booking-extras]');
  const totalOutput = form.querySelector('[data-booking-total]');

  function formatCurrency(amount) {
    return `${currencySymbol}${amount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }

  function clampValue(input) {
    const min = parseInt(input.getAttribute('min') || '0', 10);
    const value = parseInt(input.value || input.defaultValue || '0', 10);
    if (Number.isNaN(value) || value < min) {
      input.value = min;
      return min;
    }
    return value;
  }

  function recalculate() {
    const adultsInput = form.querySelector('input[data-traveler-type="adults"]');
    const childrenInput = form.querySelector('input[data-traveler-type="children"]');

    const adults = Math.max(clampValue(adultsInput), 1);
    const children = clampValue(childrenInput);

    const travelerCount = Math.max(adults + children, 1);
    const baseTotal = basePrice * travelerCount;

    let extrasTotal = 0;
    form.querySelectorAll('input[name="extras"]:checked').forEach((checkbox) => {
      const price = parseFloat(checkbox.dataset.extraPrice || '0');
      extrasTotal += price;
    });

    if (baseOutput) baseOutput.textContent = formatCurrency(baseTotal);
    if (extrasOutput) extrasOutput.textContent = formatCurrency(extrasTotal);
    if (totalOutput) totalOutput.textContent = formatCurrency(baseTotal + extrasTotal);
  }

  form.querySelectorAll('[data-counter]').forEach((counter) => {
    const input = counter.querySelector('input[type="number"]');
    if (!input) return;

    counter.addEventListener('click', (event) => {
      const button = event.target.closest('button[data-counter-inc], button[data-counter-dec]');
      if (!button) return;
      event.preventDefault();

      const step = button.hasAttribute('data-counter-inc') ? 1 : -1;
      const current = clampValue(input);
      const min = parseInt(input.getAttribute('min') || '0', 10);
      const next = Math.max(current + step, min);
      input.value = next;
      input.dispatchEvent(new Event('change', { bubbles: true }));
    });

    input.addEventListener('change', recalculate);
    input.addEventListener('blur', recalculate);
  });

  form.querySelectorAll('input[name="extras"]').forEach((checkbox) => {
    checkbox.addEventListener('change', recalculate);
  });

  recalculate();
})();

(function () {
  const itineraryToggle = document.querySelector('[data-expand-itinerary]');
  if (itineraryToggle) {
    itineraryToggle.addEventListener('click', () => {
      const detailsNodes = document.querySelectorAll('#itinerary details');
      const allOpen = Array.from(detailsNodes).every((node) => node.open);
      detailsNodes.forEach((node) => {
        node.open = !allOpen;
      });
    });
  }

  const faqToggle = document.querySelector('[data-expand-faq]');
  if (faqToggle) {
    faqToggle.addEventListener('click', () => {
      const detailsNodes = document.querySelectorAll('#faqs details');
      const allOpen = Array.from(detailsNodes).every((node) => node.open);
      detailsNodes.forEach((node) => {
        node.open = !allOpen;
      });
    });
  }
})();
