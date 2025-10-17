
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
  const sheet = document.querySelector('[data-mobile-sheet]');
  if (!sheet) return;

  const overlay = document.querySelector('[data-mobile-sheet-overlay]');
  const openButtons = document.querySelectorAll('[data-mobile-sheet-open]');
  const closeButton = sheet.querySelector('[data-mobile-sheet-close]');
  const mediaQuery = window.matchMedia('(min-width: 1024px)');
  let lastFocusedElement = null;
  let isOpen = false;

  const setAriaExpanded = (value) => {
    openButtons.forEach((button) => button.setAttribute('aria-expanded', value ? 'true' : 'false'));
  };

  const openSheet = () => {
    if (mediaQuery.matches) return;
    lastFocusedElement = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    sheet.classList.add('is-open');
    sheet.setAttribute('aria-hidden', 'false');
    if (overlay) {
      overlay.classList.add('is-visible');
      overlay.setAttribute('aria-hidden', 'false');
    }
    document.body.style.overflow = 'hidden';
    setAriaExpanded(true);
    isOpen = true;
    if (closeButton) {
      closeButton.focus();
    }
  };

  const closeSheet = (restoreFocus = true) => {
    sheet.classList.remove('is-open');
    sheet.setAttribute('aria-hidden', 'true');
    if (overlay) {
      overlay.classList.remove('is-visible');
      overlay.setAttribute('aria-hidden', 'true');
    }
    document.body.style.overflow = '';
    setAriaExpanded(false);
    isOpen = false;
    if (restoreFocus && lastFocusedElement) {
      lastFocusedElement.focus();
    }
  };

  openButtons.forEach((button) => {
    button.addEventListener('click', () => {
      if (isOpen) {
        closeSheet();
      } else {
        openSheet();
      }
    });
  });

  if (closeButton) {
    closeButton.addEventListener('click', () => {
      closeSheet();
    });
  }

  if (overlay) {
    overlay.addEventListener('click', () => {
      closeSheet();
    });
  }

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && isOpen && !mediaQuery.matches) {
      closeSheet();
    }
  });

  const handleBreakpointChange = () => {
    if (mediaQuery.matches) {
      sheet.classList.remove('is-open');
      document.body.style.overflow = '';
      if (overlay) {
        overlay.classList.remove('is-visible');
        overlay.setAttribute('aria-hidden', 'true');
      }
      setAriaExpanded(false);
      isOpen = false;
      sheet.removeAttribute('role');
      sheet.removeAttribute('aria-modal');
      sheet.removeAttribute('aria-hidden');
    } else {
      sheet.classList.remove('is-open');
      if (overlay) {
        overlay.classList.remove('is-visible');
        overlay.setAttribute('aria-hidden', 'true');
      }
      setAriaExpanded(false);
      isOpen = false;
      sheet.setAttribute('role', 'dialog');
      sheet.setAttribute('aria-modal', 'true');
      sheet.setAttribute('aria-hidden', 'true');
    }
  };

  mediaQuery.addEventListener('change', handleBreakpointChange);
  handleBreakpointChange();
})();

(function () {
  function setupExpandToggle(buttonSelector, detailsSelector) {
    const button = document.querySelector(buttonSelector);
    if (!button) return;

    const detailsNodes = document.querySelectorAll(detailsSelector);
    if (!detailsNodes.length) return;

    const labelNode = button.querySelector('span');
    const collapsedLabel = labelNode ? labelNode.textContent.trim() : button.textContent.trim();
    const expandedLabel = button.dataset.expandedLabel || 'Collapse all';

    const updateButton = () => {
      const allOpen = Array.from(detailsNodes).every((node) => node.open);
      button.setAttribute('aria-pressed', allOpen ? 'true' : 'false');
      if (labelNode) {
        labelNode.textContent = allOpen ? expandedLabel : collapsedLabel;
      } else {
        button.textContent = allOpen ? expandedLabel : collapsedLabel;
      }
    };

    button.addEventListener('click', () => {
      const allOpen = Array.from(detailsNodes).every((node) => node.open);
      detailsNodes.forEach((node) => {
        node.open = !allOpen;
      });
      updateButton();
    });

    detailsNodes.forEach((node) => {
      node.addEventListener('toggle', updateButton);
    });

    updateButton();
  }

  setupExpandToggle('[data-expand-itinerary]', '#itinerary details');
  setupExpandToggle('[data-expand-faq]', '#faqs details');
})();
