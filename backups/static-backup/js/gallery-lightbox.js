(function () {
  const KEY = {
    LEFT: 'ArrowLeft',
    RIGHT: 'ArrowRight',
    ESC: 'Escape',
  };

  const state = {
    galleries: [],
    activeGallery: null,
    activeIndex: -1,
    overlay: null,
    keydownBound: false,
  };

  function bootstrap() {
    state.galleries = [];
    document.querySelectorAll('[data-gallery]').forEach((galleryEl, galleryIndex) => {
      const items = Array.from(galleryEl.querySelectorAll('[data-gallery-item]'));
      if (items.length === 0) {
        return;
      }

      const gallery = {
        root: galleryEl,
        items,
        index: galleryIndex,
      };

      items.forEach((item, itemIndex) => {
        const trigger = item.querySelector('[data-gallery-trigger]');
        if (!trigger) {
          return;
        }
        trigger.addEventListener('click', () => open(gallery, itemIndex));
        trigger.addEventListener('keydown', (event) => {
          if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            open(gallery, itemIndex);
          }
        });
      });

      state.galleries.push(gallery);
    });

    setupOverlay();
  }

  function setupOverlay() {
    const overlay = document.querySelector('[data-gallery-overlay]');
    if (!overlay) {
      state.overlay = null;
      if (state.keydownBound) {
        document.removeEventListener('keydown', onKeydown);
        state.keydownBound = false;
      }
      return;
    }

    state.overlay = overlay;
    state.backdrop = overlay.querySelector('[data-gallery-close]');
    state.dialog = overlay.querySelector('.gallery-lightbox__dialog');
    state.imageEl = overlay.querySelector('[data-gallery-active-image]');
    state.captionEl = overlay.querySelector('[data-gallery-active-caption]');
    state.prevBtn = overlay.querySelector('[data-gallery-prev]');
    state.nextBtn = overlay.querySelector('[data-gallery-next]');
    state.closeButtons = overlay.querySelectorAll('[data-gallery-close]');

    state.closeButtons.forEach((button) => {
      button.addEventListener('click', close);
    });

    state.prevBtn?.addEventListener('click', () => step(-1));
    state.nextBtn?.addEventListener('click', () => step(1));

    overlay.addEventListener('wheel', (event) => {
      if (state.overlay.hidden) return;
      event.preventDefault();
      if (event.deltaY > 0) {
        step(1);
      } else if (event.deltaY < 0) {
        step(-1);
      }
    }, { passive: false });

    overlay.addEventListener('touchstart', onTouchStart, { passive: true });
    overlay.addEventListener('touchend', onTouchEnd, { passive: true });

    if (state.keydownBound) {
      document.removeEventListener('keydown', onKeydown);
    }
    document.addEventListener('keydown', onKeydown);
    state.keydownBound = true;
  }

  let touchStartX = null;
  function onTouchStart(event) {
    if (event.touches.length === 1) {
      touchStartX = event.touches[0].clientX;
    }
  }

  function onTouchEnd(event) {
    if (touchStartX === null || event.changedTouches.length === 0) {
      return;
    }
    const deltaX = event.changedTouches[0].clientX - touchStartX;
    const threshold = 40;
    if (deltaX > threshold) {
      step(-1);
    } else if (deltaX < -threshold) {
      step(1);
    }
    touchStartX = null;
  }

  function onKeydown(event) {
    if (!state.overlay || state.overlay.hidden) return;
    switch (event.key) {
      case KEY.LEFT:
        step(-1);
        break;
      case KEY.RIGHT:
        step(1);
        break;
      case KEY.ESC:
        close();
        break;
      default:
        break;
    }
  }

  function open(gallery, index) {
    if (!state.overlay) return;

    state.previouslyFocused = document.activeElement;
    state.activeGallery = gallery;
    state.activeIndex = index;

    updateSlide();
    state.overlay.hidden = false;
    document.body.classList.add('gallery-lightbox--open');
    state.dialog?.focus({ preventScroll: true });
  }

  function close() {
    if (!state.overlay) return;
    state.overlay.hidden = true;
    document.body.classList.remove('gallery-lightbox--open');
    state.activeGallery = null;
    state.activeIndex = -1;
    if (state.previouslyFocused && typeof state.previouslyFocused.focus === 'function') {
      state.previouslyFocused.focus({ preventScroll: true });
    }
    state.previouslyFocused = null;
  }

  function step(direction) {
    if (!state.activeGallery) return;
    const { items } = state.activeGallery;
    const total = items.length;
    state.activeIndex = (state.activeIndex + direction + total) % total;
    updateSlide();
  }

  function updateSlide() {
    if (!state.activeGallery || !state.imageEl) return;
    const item = state.activeGallery.items[state.activeIndex];
    if (!item) return;

    const imageSrc = item.getAttribute('data-gallery-full');
    const caption = item.getAttribute('data-gallery-caption') || '';
    const inlineImg = item.querySelector('img');
    const altText = inlineImg ? inlineImg.getAttribute('alt') : 'Expanded gallery image';
    const total = state.activeGallery.items.length;

    state.imageEl.src = imageSrc;
    state.imageEl.alt = altText;
    if (state.captionEl) {
      state.captionEl.textContent = caption;
      state.captionEl.style.display = caption ? 'block' : 'none';
    }
    const showNav = total > 1;
    if (state.prevBtn) {
      state.prevBtn.style.visibility = showNav ? 'visible' : 'hidden';
    }
    if (state.nextBtn) {
      state.nextBtn.style.visibility = showNav ? 'visible' : 'hidden';
    }
  }

  window.initGalleryLightbox = bootstrap;

  if (document.readyState !== 'loading') {
    bootstrap();
  } else {
    document.addEventListener('DOMContentLoaded', bootstrap);
  }
})();
