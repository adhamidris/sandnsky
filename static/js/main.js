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

    const open  = () => { cart.dataset.open = 'true';  trigger?.setAttribute('aria-expanded', 'true'); };
    const close = () => { cart.dataset.open = 'false'; trigger?.setAttribute('aria-expanded', 'false'); };

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

    const updateCartUI = (payload) => {
      if (!payload) return;

      const count = typeof payload.cart_count === 'number' ? payload.cart_count : 0;
      const label = payload.cart_label || '';
      const panelHtml = payload.panel_html || '';

      const countBadge = cart.querySelector('[data-cart-count-badge]');
      if (countBadge) {
        if (count > 0) {
          countBadge.textContent = count;
          countBadge.classList.remove('hidden');
        } else {
          countBadge.textContent = '';
          countBadge.classList.add('hidden');
        }
      }

      const labelText = cart.querySelector('[data-cart-label-text]');
      if (labelText) {
        labelText.textContent = label;
      }

      if (trigger) {
        trigger.classList.toggle('has-items', count > 0);
      }

      const panel = cart.querySelector('[data-cart-panel]');
      if (panel && panelHtml) {
        panel.innerHTML = panelHtml;
      }
    };

    const showToast = (message, icon = '✓') => {
      if (!toast || !toastMsg) return;
      toastMsg.textContent = message || 'Updated your list';
      if (toastIcon) {
        toastIcon.textContent = icon || '';
      }
      cart.dataset.toast = 'show';
      toast.dataset.state = 'added';
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
        showToast(message, payload.in_cart ? '✓' : '−');
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

  // ===== Testimonials carousel (swipe + auto-rotate) =====
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
      const intervalAttr = parseInt(root.getAttribute('data-interval') || '', 10);
      const rotateInterval = Number.isNaN(intervalAttr) ? 6500 : Math.max(intervalAttr, 4000);

      let activeIndex = 0;
      let positions = [];
      let timerId = null;
      let isDragging = false;
      let startX = 0;
      let deltaX = 0;

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

      const applyTransform = (targetIndex, { animate = true, offset = 0 } = {}) => {
        const base = positions[targetIndex] || 0;
        if (!animate) {
          track.style.transition = 'none';
        } else {
          track.style.transition = 'transform 450ms cubic-bezier(0.33, 1, 0.68, 1)';
        }
        track.style.transform = `translateX(${-(base + offset)}px)`;
      };

      const goTo = (index, { animate = true } = {}) => {
        const target = Math.max(0, Math.min(slides.length - 1, index));
        activeIndex = target;
        slides.forEach((slide, idx) => setAriaForSlide(slide, idx === target));
        updateDotState();
        applyTransform(target, { animate });
      };

      const next = () => goTo(activeIndex + 1);
      const prev = () => goTo(activeIndex - 1);

      const stopAuto = () => {
        if (timerId) {
          window.clearInterval(timerId);
          timerId = null;
        }
      };

      const startAuto = () => {
        stopAuto();
        timerId = window.setInterval(() => {
          const nextIndex = activeIndex + 1 >= slides.length ? 0 : activeIndex + 1;
          goTo(nextIndex);
        }, rotateInterval);
      };

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

      const onPointerDown = (event) => {
        isDragging = true;
        deltaX = 0;
        startX = event.type.startsWith('touch')
          ? event.touches[0].clientX
          : event.clientX;
        if (event.pointerId != null && track.setPointerCapture) {
          try { track.setPointerCapture(event.pointerId); } catch (error) { /* no-op */ }
        }
        track.style.transition = 'none';
        stopAuto();
      };

      const onPointerMove = (event) => {
        if (!isDragging) return;
        const currentX = event.type.startsWith('touch')
          ? event.touches[0].clientX
          : event.clientX;
        deltaX = currentX - startX;
        applyTransform(activeIndex, { animate: false, offset: deltaX });
        if (event.type === 'touchmove' && Math.abs(deltaX) > 6) {
          event.preventDefault();
        }
      };

      const releaseCapture = (event) => {
        if (event.pointerId != null && track.releasePointerCapture) {
          try { track.releasePointerCapture(event.pointerId); } catch (error) { /* no-op */ }
        }
      };

      const onPointerUp = (event) => {
        if (!isDragging) return;
        isDragging = false;
        const threshold = Math.min(90, (slides[activeIndex].offsetWidth || 0) * 0.25);
        if (deltaX <= -threshold && activeIndex < slides.length - 1) {
          goTo(activeIndex + 1);
        } else if (deltaX >= threshold && activeIndex > 0) {
          goTo(activeIndex - 1);
        } else {
          goTo(activeIndex);
        }
        deltaX = 0;
        releaseCapture(event);
        startAuto();
      };

      const onPointerCancel = (event) => {
        if (!isDragging) return;
        isDragging = false;
        deltaX = 0;
        goTo(activeIndex);
        releaseCapture(event);
        startAuto();
      };

      recomputePositions();
      goTo(0, { animate: false });
      updateDotState();
      startAuto();

      dots.forEach((dot, idx) => {
        dot.addEventListener('click', (event) => {
          event.preventDefault();
          goTo(idx);
          startAuto();
        });
        dot.addEventListener('keydown', (event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            goTo(idx);
            startAuto();
          }
        });
      });

      const pointerOptions = { passive: false };
      track.addEventListener('pointerdown', onPointerDown, pointerOptions);
      track.addEventListener('pointermove', onPointerMove, pointerOptions);
      track.addEventListener('pointerup', onPointerUp, pointerOptions);
      track.addEventListener('pointercancel', onPointerCancel, pointerOptions);
      track.addEventListener('pointerleave', onPointerUp, pointerOptions);

      // Support older touch events if PointerEvent isn't available
      if (!window.PointerEvent) {
        track.addEventListener('touchstart', onPointerDown, pointerOptions);
        track.addEventListener('touchmove', onPointerMove, pointerOptions);
        track.addEventListener('touchend', onPointerUp, pointerOptions);
        track.addEventListener('touchcancel', onPointerCancel, pointerOptions);
      }

      root.addEventListener('mouseenter', stopAuto);
      root.addEventListener('mouseleave', startAuto);
      root.addEventListener('focusin', stopAuto);
      root.addEventListener('focusout', startAuto);

      window.addEventListener('resize', debounce(recomputePositions, 150));
    };

    carousels.forEach(setupCarousel);
  })();
