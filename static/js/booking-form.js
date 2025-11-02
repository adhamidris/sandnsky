

(function () {
    const form = document.querySelector('[data-module="booking-form"]');
    if (!form) return;
  
    const root = form.closest('[data-booking-root]') || form;
  
    const adultPrice = parseFloat(form.dataset.adultPrice || form.dataset.basePrice || '0');
    const childPrice = parseFloat(form.dataset.childPrice || form.dataset.adultPrice || form.dataset.basePrice || '0');
    const currencySymbol = form.dataset.currencySymbol || '';

    const baseOutputs = root.querySelectorAll('[data-booking-base]');
    const adultOutputs = root.querySelectorAll('[data-booking-adult]');
    const childOutputs = root.querySelectorAll('[data-booking-child]');
    const adultCountOutputs = root.querySelectorAll('[data-booking-adult-count]');
    const childCountOutputs = root.querySelectorAll('[data-booking-child-count]');
    const childRows = root.querySelectorAll('[data-booking-child-row]');
    const extrasOutputs = root.querySelectorAll('[data-booking-extras]');
    const totalOutputs = root.querySelectorAll('[data-booking-total]');
    const travelerSummaries = root.querySelectorAll('[data-traveler-summary]');

    const normalizedAdultPrice = Number.isFinite(adultPrice) ? Math.max(adultPrice, 0) : 0;
    const normalizedChildPrice = Number.isFinite(childPrice) ? Math.max(childPrice, 0) : normalizedAdultPrice;
    const adultPriceCents = Math.round(normalizedAdultPrice * 100);
    const childPriceCents = Math.round(normalizedChildPrice * 100);
  
    function formatCurrency(amount) {
      return `${currencySymbol}${amount.toLocaleString(undefined, {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`;
    }
  
    function formatCurrencyFromCents(cents) {
      return formatCurrency(cents / 100);
    }
  
    function setCurrency(nodes, cents) {
      const label = formatCurrencyFromCents(cents);
      nodes.forEach((node) => {
        node.textContent = label;
      });
    }
  
    function setTravelerSummary(summary) {
      const message = summary ? `Estimate · ${summary}` : 'Estimate';
      travelerSummaries.forEach((node) => {
        node.textContent = message;
      });
    }
  
    function clampValue(input) {
      if (!input) return 0;
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
      const infantsInput = form.querySelector('input[data-traveler-type="infants"]');
  
      const adults = Math.max(clampValue(adultsInput), 1);
      const children = childrenInput ? clampValue(childrenInput) : 0;
      const infants = infantsInput ? clampValue(infantsInput) : 0;
  
      const billedTravelerCount = Math.max(adults + children, 1);
      const adultTotalCents = adultPriceCents * adults;
      const childTotalCents = childPriceCents * children;
      const baseTotalCents = adultTotalCents + childTotalCents;

      let extrasTotalCents = 0;
      form.querySelectorAll('input[name="extras"]:checked').forEach((checkbox) => {
        const price = parseFloat(checkbox.dataset.extraPrice || '0');
        extrasTotalCents += Math.max(Math.round(price * 100), 0);
      });
  
      const grandTotalCents = baseTotalCents + extrasTotalCents;
      const summaryParts = [];
      const pushPart = (count, label) => {
        if (count > 0) {
          summaryParts.push(`${count} ${label}${count === 1 ? '' : 's'}`);
        }
      };
  
      pushPart(adults, 'adult');
      pushPart(children, 'child');
      pushPart(infants, 'infant');
  
      if (!summaryParts.length) {
        summaryParts.push('0 travelers');
      }
  
      const summary = summaryParts.join(' · ');
  
      setCurrency(baseOutputs, baseTotalCents);
      setCurrency(adultOutputs, adultTotalCents);
      setCurrency(childOutputs, childTotalCents);
      setCurrency(extrasOutputs, extrasTotalCents);
      setCurrency(totalOutputs, grandTotalCents);

      adultCountOutputs.forEach((node) => {
        node.textContent = String(adults);
      });
      childCountOutputs.forEach((node) => {
        node.textContent = String(children);
      });
      childRows.forEach((row) => {
        if (!(row instanceof HTMLElement)) return;
        row.classList.toggle('hidden', children === 0);
      });
      if (travelerSummaries.length) {
        setTravelerSummary(summary);
      }
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
  
      ['change', 'blur', 'input'].forEach((eventName) => {
        input.addEventListener(eventName, recalculate);
      });
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
    if (!floater) return;
    stopFloaterObserver();
    setFloaterVisibility(true);
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
  
