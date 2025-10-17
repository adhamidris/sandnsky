
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
  const container = document.querySelector('[data-mobile-sheet-container]') || null;
  const sheet = container ? container.querySelector('[data-mobile-sheet]') : document.querySelector('[data-mobile-sheet]');
  if (!sheet) return;

  const overlay = container ? container.querySelector('[data-mobile-sheet-overlay]') : document.querySelector('[data-mobile-sheet-overlay]');
  const openButtons = document.querySelectorAll('[data-mobile-sheet-open]');
  const closeButton = sheet.querySelector('[data-mobile-sheet-close]');
  const mediaQuery = window.matchMedia('(min-width: 1024px)');
  const floater = document.querySelector('[data-booking-floater]');
  const summaryCard = document.querySelector('[data-trip-summary]');
  const focusableSelector = 'a[href], button:not([disabled]), textarea, input, select, [tabindex]:not([tabindex="-1"])';
  const scrollContainer = sheet.querySelector('[data-booking-scroll]');
  const submitSection = sheet.querySelector('[data-booking-submit]');
  const fullNameField = sheet.querySelector('input[name="name"], input[name="full_name"]');
  let lastFocusedElement = null;
  let isOpen = false;
  let floaterObserver = null;

  const setAriaExpanded = (value) => {
    openButtons.forEach((button) => button.setAttribute('aria-expanded', value ? 'true' : 'false'));
  };

  const setScrollLock = (locked) => {
    document.body.style.overflow = locked ? 'hidden' : '';
  };

  const trapFocus = (event) => {
    if (!isOpen || event.key !== 'Tab') return;

    const focusable = Array.from(sheet.querySelectorAll(focusableSelector)).filter((node) => {
      if (!(node instanceof HTMLElement)) return false;
      if (node.hasAttribute('disabled')) return false;
      if (node.getAttribute('tabindex') === '-1') return false;
      if (node.getAttribute('aria-hidden') === 'true') return false;
      const isVisible = node.offsetParent !== null || node.getClientRects().length > 0;
      return isVisible;
    });

    if (!focusable.length) return;

    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const isShift = event.shiftKey;
    const active = document.activeElement;

    if (!isShift && active === last) {
      event.preventDefault();
      first.focus();
    } else if (isShift && active === first) {
      event.preventDefault();
      last.focus();
    }
  };

  const setFloaterVisibility = (visible) => {
    if (!floater) return;
    floater.setAttribute('aria-hidden', visible ? 'false' : 'true');
  };

  const stopFloaterObserver = () => {
    if (floaterObserver) {
      floaterObserver.disconnect();
      floaterObserver = null;
    }
  };

  const startFloaterObserver = () => {
    if (!floater || !summaryCard) return;
    stopFloaterObserver();
    floaterObserver = new IntersectionObserver((entries) => {
      const entry = entries[0];
      const summaryVisible = entry ? entry.isIntersecting : false;
      setFloaterVisibility(!summaryVisible);
    }, {
      root: null,
      threshold: 0,
      rootMargin: '0px 0px -20% 0px',
    });
    floaterObserver.observe(summaryCard);
  };

  const updateFloaterForViewport = () => {
    if (!floater) return;
    if (mediaQuery.matches) {
      if (summaryCard) {
        startFloaterObserver();
      } else {
        stopFloaterObserver();
        setFloaterVisibility(true);
      }
    } else {
      stopFloaterObserver();
      setFloaterVisibility(false);
    }
  };

  const openSheet = () => {
    if (isOpen) return;
    lastFocusedElement = document.activeElement instanceof HTMLElement ? document.activeElement : null;

    if (container) {
      container.classList.add('is-open');
      container.setAttribute('aria-hidden', 'false');
    }

    sheet.classList.add('is-open');
    sheet.setAttribute('aria-hidden', 'false');

    if (overlay) {
      overlay.classList.add('is-visible');
      overlay.setAttribute('aria-hidden', 'false');
    }

    setScrollLock(true);
    setAriaExpanded(true);
    isOpen = true;

    const initialFocus = closeButton || sheet.querySelector(focusableSelector);
    if (initialFocus instanceof HTMLElement) {
      initialFocus.focus();
    }
  };

  const closeSheet = (restoreFocus = true) => {
    if (!isOpen) return;

    sheet.classList.remove('is-open');
    sheet.setAttribute('aria-hidden', 'true');

    if (container) {
      container.classList.remove('is-open');
      container.setAttribute('aria-hidden', 'true');
    }

    if (overlay) {
      overlay.classList.remove('is-visible');
      overlay.setAttribute('aria-hidden', 'true');
    }

    setScrollLock(false);
    setAriaExpanded(false);
    isOpen = false;

    if (restoreFocus && lastFocusedElement instanceof HTMLElement) {
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
    if (!isOpen) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      closeSheet();
      return;
    }
  });

  sheet.addEventListener('keydown', trapFocus);

  const handleBreakpointChange = () => {
    setAriaExpanded(false);
    isOpen = false;

    if (container) {
      container.classList.remove('is-open');
      container.setAttribute('aria-hidden', 'true');
    }

    sheet.classList.remove('is-open');
    sheet.setAttribute('aria-hidden', 'true');

    if (overlay) {
      overlay.classList.remove('is-visible');
      overlay.setAttribute('aria-hidden', 'true');
    }

    setScrollLock(false);
    updateFloaterForViewport();
  };

  mediaQuery.addEventListener('change', handleBreakpointChange);
  handleBreakpointChange();

  if (floater && !summaryCard) {
    setFloaterVisibility(mediaQuery.matches);
  }

  if (fullNameField) {
    fullNameField.addEventListener('focus', () => {
      const target = submitSection || sheet.querySelector('[data-contact-section]') || sheet;
      window.requestAnimationFrame(() => {
        if (scrollContainer) {
          const targetRect = target.getBoundingClientRect();
          const containerRect = scrollContainer.getBoundingClientRect();
          const offset = targetRect.top - containerRect.top - 24;
          scrollContainer.scrollTo({ top: scrollContainer.scrollTop + offset, behavior: 'smooth' });
        } else {
          target.scrollIntoView({ block: 'start', behavior: 'smooth' });
        }
      });
    });
  }
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
