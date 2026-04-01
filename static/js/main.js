  // ===== Analytics tracking =====
  (function () {
    const trackEvent = (eventName, params = {}) => {
      if (window.kayaAnalytics && typeof window.kayaAnalytics.track === 'function') {
        window.kayaAnalytics.track(eventName, {
          page_path: window.location.pathname,
          ...params,
        });
      }
    };

    const normalizeText = (value) => {
      return String(value || '')
        .replace(/\s+/g, ' ')
        .trim()
        .slice(0, 100);
    };

    const attrNameToParamKey = (attrName) => {
      return attrName
        .replace(/^data-analytics-param-/, '')
        .replace(/-/g, '_');
    };

    const extractAnalyticsParams = (element) => {
      if (!(element instanceof Element)) return {};
      const params = {};
      element.getAttributeNames().forEach((name) => {
        if (!name.startsWith('data-analytics-param-')) return;
        const value = element.getAttribute(name);
        if (value === null || value === '') return;
        params[attrNameToParamKey(name)] = value;
      });
      return params;
    };

    const findTripContext = (element) => {
      const scoped = element instanceof Element ? element.closest('[data-trip-context]') : null;
      const fallback = document.querySelector('[data-trip-context]');
      const source = scoped || fallback;
      if (!(source instanceof HTMLElement)) return {};
      const params = {};
      if (source.dataset.tripSlug) {
        params.trip_slug = source.dataset.tripSlug;
      }
      if (source.dataset.tripTitle) {
        params.trip_title = source.dataset.tripTitle;
      }
      if (source.dataset.tripId) {
        params.trip_id = source.dataset.tripId;
      }
      return params;
    };

    const buildParams = (element, extra = {}) => {
      return {
        ...findTripContext(element),
        ...extractAnalyticsParams(element),
        ...extra,
      };
    };

    const successNode = document.querySelector('[data-booking-success-analytics]');
    if (successNode instanceof HTMLElement) {
      const successParams = buildParams(successNode, {
        bookings_count: successNode.dataset.bookingsCount || '0',
        booking_status: successNode.dataset.bookingStatus || '',
        currency: successNode.dataset.currency || '',
        total_value: successNode.dataset.totalValue || '',
      });
      trackEvent('booking_success_view', successParams);
      trackEvent('generate_lead', {
        ...successParams,
        lead_type: 'booking_success',
      });
    }

    document.addEventListener(
      'click',
      (event) => {
        const target = event.target instanceof Element ? event.target : null;
        if (!target) return;

        const analyticsTarget = target.closest('[data-analytics-event]');
        if (analyticsTarget instanceof HTMLElement) {
          const eventName = analyticsTarget.dataset.analyticsEvent || '';
          if (eventName) {
            trackEvent(
              eventName,
              buildParams(analyticsTarget, {
                link_text: normalizeText(
                  analyticsTarget.getAttribute('aria-label') || analyticsTarget.textContent
                ),
              })
            );
          }
        }

        const link = target.closest('a[href]');
        if (!(link instanceof HTMLAnchorElement)) return;

        const href = link.getAttribute('href') || '';
        const linkText = normalizeText(
          link.dataset.analyticsLabel ||
            link.getAttribute('aria-label') ||
            link.textContent
        );
        const linkArea = normalizeText(
          link.dataset.analyticsArea ||
            link.closest('footer')?.getAttribute('aria-labelledby') ||
            link.closest('footer')?.getAttribute('aria-label') ||
            link.closest('main')?.id ||
            link.className
        );
        const baseParams = buildParams(link, {
          link_text: linkText,
          link_area: linkArea,
        });

        if (href.includes('wa.me/')) {
          trackEvent('whatsapp_click', baseParams);
        } else if (href.startsWith('tel:')) {
          trackEvent('phone_click', {
            ...baseParams,
            phone_number: href.replace(/^tel:/, ''),
          });
        } else if (href.startsWith('mailto:')) {
          trackEvent('email_click', {
            ...baseParams,
            email_address: href.replace(/^mailto:/, ''),
          });
        }
      },
      true
    );

    document.addEventListener(
      'submit',
      (event) => {
        const form = event.target;
        if (!(form instanceof HTMLFormElement)) return;

        if (form.matches('[data-cart-toggle]')) {
          const toggleButton =
            form.querySelector('[data-cart-toggle-button]') ||
            event.submitter;
          const isRemoval =
            form.dataset.cartAction === 'remove' ||
            (toggleButton instanceof HTMLElement &&
              toggleButton.getAttribute('data-cart-state') === 'added');
          trackEvent(isRemoval ? 'booking_list_remove' : 'booking_list_add', {
            ...buildParams(form),
            ui_source: form.dataset.cartSource || 'cart_toggle',
          });
        }

        if (form.id === 'cart-checkout-form') {
          const cartCount = document.querySelectorAll('[data-entry][data-entry-id]').length;
          trackEvent('booking_checkout_submit', {
            cart_count: cartCount,
          });
          trackEvent('generate_lead', {
            lead_type: 'booking_checkout',
            cart_count: cartCount,
          });
        }
      },
      true
    );
  })();

  // ===== Sync nav offset with actual header height =====
  (function () {
    const root = document.documentElement;
    const header = document.querySelector('header.nav');
    if (!root || !header) return;

    const applyOffset = () => {
      const height = header.getBoundingClientRect().height;
      if (!height || !Number.isFinite(height)) return;
      root.style.setProperty('--nav-sticky-offset', `${Math.round(height)}px`);
    };

    applyOffset();

    if (typeof ResizeObserver === 'function') {
      const observer = new ResizeObserver(() => applyOffset());
      observer.observe(header);
      window.addEventListener('beforeunload', () => observer.disconnect());
    } else {
      window.addEventListener('resize', applyOffset);
    }
  })();

  (function () {
    const el = document.getElementById('countdown');
    if (!el) return;
    const target = new Date(Date.now() + 26 * 60 * 60 * 1000);
    const pad = (n) => String(n).padStart(2, '0');
    const tick = () => {
      const diff = Math.max(0, target - new Date());
      const s = Math.floor(diff / 1000);
      const d = Math.floor(s / 86400);
      const h = Math.floor((s % 86400) / 3600);
      const m = Math.floor((s % 3600) / 60);
      const sec = s % 60;
      el.textContent = `${d} day ${pad(h)} hours ${pad(m)} minutes ${pad(sec)} seconds`;
    };
    tick(); setInterval(tick, 1000);
  })();

  // ===== Hero video: poster-first, single-source loading =====
  (function () {
    const hero = document.getElementById('hero');
    const video = hero?.querySelector('[data-hero-video]');
    if (!hero || !video) return;

    const desktopSrc = video.dataset.videoDesktopSrc || '';
    const desktopType = video.dataset.videoDesktopType || 'video/mp4';
    const mobileSrc = video.dataset.videoMobileSrc || '';
    const mobileType = video.dataset.videoMobileType || 'video/mp4';
    const mobileQuery = window.matchMedia('(max-width: 767px)');

    const pickSource = () => {
      if (mobileQuery.matches) {
        return {
          src: mobileSrc || desktopSrc,
          type: mobileSrc ? mobileType : desktopType,
        };
      }
      return {
        src: desktopSrc || mobileSrc,
        type: desktopSrc ? desktopType : mobileType,
      };
    };

    const revealVideo = () => {
      hero.classList.add('is-video-ready');
    };

    const loadVideo = () => {
      if (video.dataset.videoLoaded === 'true') return;
      const chosen = pickSource();
      if (!chosen.src) return;

      const source = document.createElement('source');
      source.src = chosen.src;
      source.type = chosen.type || 'video/mp4';
      video.appendChild(source);
      video.dataset.videoLoaded = 'true';
      video.load();

      const playPromise = video.play();
      if (playPromise && typeof playPromise.then === 'function') {
        playPromise.catch(() => {});
      }
    };

    video.addEventListener('loadeddata', revealVideo, { once: true });
    video.addEventListener('canplay', revealVideo, { once: true });

    const startWhenReady = () => {
      if ('requestIdleCallback' in window) {
        window.requestIdleCallback(loadVideo, { timeout: 1500 });
      } else {
        window.setTimeout(loadVideo, 250);
      }
    };

    if (document.readyState === 'complete') {
      startWhenReady();
    } else {
      window.addEventListener('load', startWhenReady, { once: true });
    }
  })();

  // ===== Hero mini-frame auto rotation =====
  (function () {
    const container = document.querySelector('[data-hero-overlays]');
    if (!container) return;
    const frames = container.querySelectorAll('[data-hero-overlay]');
    if (frames.length <= 1) return;

    let index = 0;
    const minInterval = 2000;
    const attr = parseInt(container.getAttribute('data-hero-overlay-interval') || '', 10);
    const interval = Number.isNaN(attr) ? 6000 : Math.max(attr, minInterval);
    let timerId = null;

    const setActive = (nextIndex) => {
      frames.forEach((frame, i) => {
        frame.classList.toggle('is-active', i === nextIndex);
      });
      index = nextIndex;
    };

    const tick = () => {
      const next = (index + 1) % frames.length;
      setActive(next);
    };

    const start = () => {
      stop();
      timerId = window.setInterval(tick, interval);
    };

    const stop = () => {
      if (timerId !== null) {
        window.clearInterval(timerId);
        timerId = null;
      }
    };

    container.addEventListener('mouseenter', stop);
    container.addEventListener('mouseleave', start);
    container.addEventListener('focusin', stop);
    container.addEventListener('focusout', start);

    start();
  })();

  // ===== Navigation Cart interactions =====
  (function() {
    const cart = document.querySelector('[data-navcart]');
    if (!cart) return;

    const trigger   = cart.querySelector('[data-cart-trigger]');
    const panel     = cart.querySelector('[data-cart-panel]');
    const toast     = cart.querySelector('[data-cart-toast]');
    const toastMsg  = cart.querySelector('[data-cart-toast-message]');
    const toastIcon = cart.querySelector('[data-cart-toast-icon]');
    const focusableSelector = [
      'a[href]',
      'button:not([disabled])',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
    ].join(', ');

    if (trigger && panel?.id) {
      trigger.setAttribute('aria-controls', panel.id);
    }

    const getFocusable = () => {
      if (!panel) return [];
      return Array.from(panel.querySelectorAll(focusableSelector)).filter((node) => {
        if (!(node instanceof HTMLElement)) return false;
        return !node.hasAttribute('disabled') && node.tabIndex !== -1;
      });
    };

    const setPanelA11y = (isOpen) => {
      if (!panel) return;
      panel.setAttribute('aria-hidden', isOpen ? 'false' : 'true');
    };

    const open  = () => {
      cart.dataset.open = 'true';
      trigger?.setAttribute('aria-expanded', 'true');
      setPanelA11y(true);
      window.requestAnimationFrame(() => {
        const focusable = getFocusable();
        const firstTarget = focusable.length ? focusable[0] : panel;
        if (firstTarget && typeof firstTarget.focus === 'function') {
          firstTarget.focus({ preventScroll: true });
        }
      });
    };
    const close = () => {
      cart.dataset.open = 'false';
      trigger?.setAttribute('aria-expanded', 'false');
      setPanelA11y(false);
    };

    setPanelA11y(false);

    trigger?.addEventListener('click', (e) => {
      e.stopPropagation();
      cart.dataset.open === 'true' ? close() : open();
    });

    document.addEventListener('click', (e) => {
      if (!cart.contains(e.target)) close();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') close();
    });

    panel?.addEventListener('keydown', (e) => {
      if (e.key !== 'Tab' || cart.dataset.open !== 'true') return;
      const focusable = getFocusable();
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) {
        e.preventDefault();
        last.focus();
      } else if (!e.shiftKey && document.activeElement === last) {
        e.preventDefault();
        first.focus();
      }
    });

    const getTokens = (button, attr) => {
      const value = button?.getAttribute(attr);
      if (!value) return [];
      return value
        .split(/\s+/)
        .map((token) => token.trim())
        .filter(Boolean);
    };

    const applyButtonState = (button, inCart) => {
      if (!button) return;
      const addedTokens = getTokens(button, 'data-cart-class-added');
      const removedTokens = getTokens(button, 'data-cart-class-removed');
      const allTokens = [...addedTokens, ...removedTokens];
      allTokens.forEach((token) => token && button.classList.remove(token));
      const targetTokens = inCart ? addedTokens : removedTokens;
      targetTokens.forEach((token) => token && button.classList.add(token));
      const addedLabel = button.getAttribute('data-cart-label-added') || 'Remove from booking list';
      const removedLabel = button.getAttribute('data-cart-label-removed') || 'Add to booking list';
      button.textContent = inCart ? addedLabel : removedLabel;
      button.setAttribute('data-cart-state', inCart ? 'added' : 'removed');
      button.setAttribute('aria-expanded', 'false');
    };

    const broadcastCartUpdate = (payload) => {
      if (typeof window === 'undefined' || !payload) return;
      window.dispatchEvent(new CustomEvent('booking:cart-update', { detail: payload }));
    };

    const syncCartToggleButtons = (payload) => {
      if (!payload) return;
      const buttons = document.querySelectorAll('[data-cart-toggle-button][data-trip-id]');
      if (!buttons.length) return;

      const entryIds = new Set();
      if (payload.cart_summary && Array.isArray(payload.cart_summary.entries)) {
        payload.cart_summary.entries.forEach((entry) => {
          const tripId = Number(entry?.trip_id);
          if (!Number.isNaN(tripId) && tripId > 0) {
            entryIds.add(tripId);
          }
        });
      }

      const applyBySet = entryIds.size > 0;
      const targetTripId = Number(payload.trip_id);

      buttons.forEach((button) => {
        const tripIdAttr = Number(button.getAttribute('data-trip-id'));
        if (Number.isNaN(tripIdAttr) || tripIdAttr <= 0) {
          return;
        }
        if (applyBySet) {
          applyButtonState(button, entryIds.has(tripIdAttr));
        } else if (!Number.isNaN(targetTripId) && tripIdAttr === targetTripId) {
          applyButtonState(button, !!payload.in_cart);
        }
      });
    };

    const updateCartUI = (payload) => {
      if (!payload) return;

      const count = typeof payload.cart_count === 'number' ? payload.cart_count : 0;
      const label = payload.cart_label || '';
      const panelHtml = payload.panel_html || '';

      const countBadge = cart.querySelector('[data-cart-count-badge]');
      if (countBadge) {
        countBadge.textContent = String(count);
        countBadge.classList.toggle('hidden', count <= 0);
      }

      const labelText = cart.querySelector('[data-cart-label-text]');
      if (labelText) {
        labelText.textContent = label;
      }

      if (trigger) {
        trigger.classList.toggle('has-items', count > 0);
      }

      const panel = cart.querySelector('[data-cart-panel]');
      if (panel && typeof panelHtml === 'string') {
        panel.innerHTML = panelHtml;
      }

      syncCartToggleButtons(payload);
      broadcastCartUpdate(payload);
    };

    const showToast = (message, icon = '✓', state = 'added') => {
      if (!toast || !toastMsg) return;
      toastMsg.textContent = message || 'Updated your list';
      if (toastIcon) {
        toastIcon.textContent = icon || '';
      }
      cart.dataset.toast = 'show';
      toast.dataset.state = state === 'removed' ? 'removed' : 'added';
      window.setTimeout(() => {
        cart.dataset.toast = '';
        toast.dataset.state = '';
        if (toastIcon) {
          toastIcon.textContent = '';
        }
      }, 1600);
    };

    const sendCartToggleRequest = async (form) => {
      const formData = new FormData(form);
      const csrfToken = formData.get('csrfmiddlewaretoken');

      try {
        const response = await fetch(form.action, {
          method: 'POST',
          headers: {
            'X-Requested-With': 'XMLHttpRequest',
            Accept: 'application/json',
            ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
          },
          body: formData,
        });

        if (!response.ok) {
          throw new Error(`Request failed with ${response.status}`);
        }

        const payload = await response.json();
        updateCartUI(payload);
        const message = payload.toast_message || (payload.in_cart ? 'Added to your list' : 'Removed from your list');
        const toastState = payload.in_cart ? 'added' : 'removed';
        showToast(message, payload.in_cart ? '✓' : '−', toastState);
      } catch (error) {
        console.error('Failed to update cart:', error);
        form.submit();
      }
    };

    cart.addEventListener('submit', (e) => {
      const form = e.target;
      if (form && form.matches('[data-cart-toggle]')) {
        e.preventDefault();
        sendCartToggleRequest(form);
      }
    });
  })();

  // ===== Trip listing card navigation =====
  (function () {
    const cards = document.querySelectorAll('[data-trip-card-href]');
    if (!cards.length) return;

    const INTERACTIVE_SELECTOR = [
      'a',
      'button',
      'input',
      'select',
      'textarea',
      '[data-cart-toggle-button]',
      '[data-quick-add-container]',
      '[data-quick-add-popover]',
      '[data-quick-add-trigger]',
      '[data-quick-add-step]',
      '[data-quick-add-input]',
      '[data-quick-add-date]',
      '[data-quick-add-confirm]',
      '[data-quick-add-cancel]',
    ].join(', ');

    const shouldIgnore = (target) => {
      if (!target) return false;
      return Boolean(target.closest(INTERACTIVE_SELECTOR));
    };

    cards.forEach((card) => {
      const href = card.getAttribute('data-trip-card-href');
      if (!href) return;

      card.addEventListener('click', (event) => {
        if (event.defaultPrevented) return;
        if (card.classList.contains('quick-add-active')) return;
        if (shouldIgnore(event.target)) return;
        if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button === 1) {
          window.open(href, '_blank');
          return;
        }
        window.location.href = href;
      });

      card.addEventListener('keydown', (event) => {
        if (event.defaultPrevented) return;
        if (card.classList.contains('quick-add-active')) return;
        if (event.key !== 'Enter' && event.key !== ' ') return;
        if (document.activeElement !== card) return;
        event.preventDefault();
        window.location.href = href;
      });
    });
  })();

  // ===== Testimonials carousel (manual navigation) =====
  (function () {
    const carousels = document.querySelectorAll('[data-testimonials]');
    if (!carousels.length) return;

    const debounce = (fn, delay = 150) => {
      let handle = null;
      return (...args) => {
        if (handle) window.clearTimeout(handle);
        handle = window.setTimeout(() => fn(...args), delay);
      };
    };

    const setupCarousel = (root) => {
      const track = root.querySelector('[data-testimonial-track]');
      const slides = Array.from(track?.querySelectorAll('[data-testimonial]') || []);
      if (!track || slides.length <= 1) return;

      const dots = Array.from(root.querySelectorAll('[data-testimonial-dot]'));

      let activeIndex = 0;
      let positions = [];

      const setAriaForSlide = (slide, isActive) => {
        slide.setAttribute('aria-hidden', String(!isActive));
        slide.classList.toggle('is-active', isActive);
        if (isActive) {
          slide.setAttribute('tabindex', '0');
        } else {
          slide.setAttribute('tabindex', '-1');
        }
      };

      const updateDotState = () => {
        dots.forEach((dot, idx) => {
          const isActive = idx === activeIndex;
          dot.classList.toggle('is-active', isActive);
          dot.setAttribute('aria-selected', String(isActive));
          dot.setAttribute('tabindex', isActive ? '0' : '-1');
        });
      };

      const applyTransform = (targetIndex, { animate = true } = {}) => {
        const base = positions[targetIndex] || 0;
        if (!animate) {
          track.style.transition = 'none';
        } else {
          track.style.transition = 'transform 450ms cubic-bezier(0.33, 1, 0.68, 1)';
        }
        track.style.transform = `translateX(-${base}px)`;
      };

      const normalizeIndex = (index) => {
        if (index < 0) return slides.length - 1;
        if (index >= slides.length) return 0;
        return index;
      };

      const goTo = (index, { animate = true } = {}) => {
        const target = normalizeIndex(index);
        activeIndex = target;
        slides.forEach((slide, idx) => setAriaForSlide(slide, idx === target));
        updateDotState();
        applyTransform(target, { animate });
      };

      const next = () => goTo(activeIndex + 1);
      const prev = () => goTo(activeIndex - 1);

      const recomputePositions = () => {
        const prevTransition = track.style.transition;
        const prevTransform = track.style.transform;
        track.style.transition = 'none';
        track.style.transform = 'translateX(0px)';
        positions = slides.map((slide) => slide.offsetLeft);
        track.style.transition = prevTransition;
        track.style.transform = prevTransform;
        goTo(activeIndex, { animate: false });
      };

      recomputePositions();
      goTo(0, { animate: false });
      updateDotState();

      dots.forEach((dot, idx) => {
        dot.addEventListener('click', (event) => {
          event.preventDefault();
          goTo(idx);
        });
        dot.addEventListener('keydown', (event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            goTo(idx);
          }
        });
      });

      const bindButton = (button, handler) => {
        if (!button) return;
        button.addEventListener('click', (event) => {
          event.preventDefault();
          handler();
        });
        button.addEventListener('keydown', (event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            handler();
          }
        });
      };

      bindButton(root.querySelector('[data-testimonial-prev]'), prev);
      bindButton(root.querySelector('[data-testimonial-next]'), next);

      const controls = root.querySelector('[data-testimonial-controls]');
      if (controls) {
        controls.addEventListener('keydown', (event) => {
          if (event.key === 'ArrowLeft') {
            event.preventDefault();
            prev();
          } else if (event.key === 'ArrowRight') {
            event.preventDefault();
            next();
          }
        });
      }

      window.addEventListener('resize', debounce(recomputePositions, 150));
    };

    carousels.forEach(setupCarousel);
  })();
