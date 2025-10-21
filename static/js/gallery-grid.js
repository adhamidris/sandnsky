(function () {
  var grid = document.querySelector('[data-gallery-grid]');
  if (!grid) {
    return;
  }

  var cards = Array.prototype.slice.call(grid.querySelectorAll('[data-gallery-card]'));
  if (!cards.length) {
    return;
  }

  var searchInput = document.querySelector('[data-gallery-search]');
  var filterButtons = Array.prototype.slice.call(document.querySelectorAll('[data-gallery-filter]'));
  var countRegion = document.querySelector('[data-gallery-count]');
  var mapToggle = document.querySelector('[data-gallery-map-toggle]');
  var mapPlaceholder = document.querySelector('[data-gallery-map]');
  var gridWrapper = document.querySelector('[data-gallery-grid-wrapper]');

  var lightbox = document.querySelector('[data-gallery-dialog]');
  var lightboxOverlay = lightbox ? lightbox.querySelector('[data-gallery-overlay]') : null;
  var lightboxImage = lightbox ? lightbox.querySelector('[data-gallery-modal-image]') : null;
  var lightboxCaption = lightbox ? lightbox.querySelector('[data-gallery-modal-caption]') : null;
  var lightboxLocation = lightbox ? lightbox.querySelector('[data-gallery-modal-location]') : null;
  var lightboxClose = lightbox ? lightbox.querySelector('[data-gallery-close]') : null;
  var lightboxPrev = lightbox ? lightbox.querySelector('[data-gallery-prev]') : null;
  var lightboxNext = lightbox ? lightbox.querySelector('[data-gallery-next]') : null;

  var activeFilter = 'all';
  var searchQuery = '';
  var activeIndex = -1;
  var lastFocusedElement = null;

  var reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (reducedMotion) {
    grid.classList.add('is-reduced-motion');
  }

  function normalise(value) {
    return (value || '').toString().toLowerCase();
  }

  function getVisibleCards() {
    return cards.filter(function (card) {
      return !card.hasAttribute('hidden');
    });
  }

  function announceCount(count) {
    if (!countRegion) {
      return;
    }
    var label = count === 1 ? 'photo' : 'photos';
    countRegion.textContent = count + ' ' + label;
  }

  function applyFilters() {
    var normalisedQuery = normalise(searchQuery);

    var visibleCount = 0;
    cards.forEach(function (card) {
      var destination = card.getAttribute('data-destination') || '';
      var destinationLabel = card.getAttribute('data-destination-label') || '';
      var title = card.getAttribute('data-title') || '';
      var matchesFilter = activeFilter === 'all' || destination === activeFilter;
      var matchesQuery = !normalisedQuery;
      if (!matchesQuery) {
        var composite = normalise(destinationLabel + ' ' + title);
        matchesQuery = composite.indexOf(normalisedQuery) !== -1;
      }

      if (matchesFilter && matchesQuery) {
        card.removeAttribute('hidden');
        card.setAttribute('aria-hidden', 'false');
        visibleCount += 1;
      } else {
        card.setAttribute('hidden', '');
        card.setAttribute('aria-hidden', 'true');
      }
    });

    announceCount(visibleCount);
  }

  function setActiveFilter(value) {
    activeFilter = value;
    filterButtons.forEach(function (button) {
      var buttonValue = button.getAttribute('data-gallery-filter');
      var isActive = buttonValue === activeFilter;
      button.classList.toggle('is-active', isActive);
      button.setAttribute('aria-pressed', isActive ? 'true' : 'false');
    });
    applyFilters();
  }

  if (filterButtons.length) {
    filterButtons.forEach(function (button) {
      button.addEventListener('click', function () {
        var value = button.getAttribute('data-gallery-filter');
        setActiveFilter(value);
      });
    });
  }

  if (searchInput) {
    searchInput.addEventListener('input', function (event) {
      searchQuery = event.target.value || '';
      applyFilters();
    });
  }

  function toggleMapView(forceState) {
    if (!mapToggle || !mapPlaceholder) {
      return;
    }
    var shouldShow = typeof forceState === 'boolean' ? forceState : mapToggle.getAttribute('aria-pressed') !== 'true';
    mapToggle.setAttribute('aria-pressed', shouldShow ? 'true' : 'false');
    if (shouldShow) {
      mapPlaceholder.hidden = false;
      grid.setAttribute('hidden', '');
    } else {
      mapPlaceholder.hidden = true;
      grid.removeAttribute('hidden');
    }
  }

  if (mapToggle) {
    mapToggle.addEventListener('click', function () {
      toggleMapView();
    });
  }

  function getCardData(card) {
    if (!card) {
      return null;
    }
    var button = card.querySelector('[data-gallery-open]');
    if (!button) {
      return null;
    }
    return {
      src: button.getAttribute('data-gallery-src'),
      alt: button.getAttribute('data-gallery-alt'),
      caption: button.getAttribute('data-gallery-caption'),
      location: button.getAttribute('data-gallery-location'),
      index: parseInt(card.getAttribute('data-index'), 10) || 0,
    };
  }

  function preloadImage(src) {
    if (!src) {
      return;
    }
    var img = new Image();
    img.decoding = 'async';
    img.src = src;
  }

  function renderLightbox(card) {
    if (!lightbox || !lightboxImage) {
      return;
    }
    var data = getCardData(card);
    if (!data) {
      return;
    }

    activeIndex = cards.indexOf(card);
    lightboxImage.src = data.src;
    lightboxImage.alt = data.alt || '';
    if (lightboxLocation) {
      lightboxLocation.textContent = data.location || '';
    }
    if (lightboxCaption) {
      lightboxCaption.textContent = data.caption || '';
    }

    var visibleCards = getVisibleCards();
    var currentVisibleIndex = visibleCards.indexOf(card);
    if (currentVisibleIndex !== -1) {
      var nextCard = visibleCards[currentVisibleIndex + 1];
      var prevCard = visibleCards[currentVisibleIndex - 1];
      if (nextCard) {
        var nextData = getCardData(nextCard);
        preloadImage(nextData && nextData.src);
      }
      if (prevCard) {
        var prevData = getCardData(prevCard);
        preloadImage(prevData && prevData.src);
      }
    }
  }

  function openLightbox(card) {
    if (!lightbox) {
      return;
    }
    lightbox.classList.add('is-open');
    lightbox.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    lastFocusedElement = document.activeElement;
    renderLightbox(card);
    if (lightboxClose) {
      lightboxClose.focus();
    }
  }

  function closeLightbox() {
    if (!lightbox) {
      return;
    }
    lightbox.classList.remove('is-open');
    lightbox.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {
      lastFocusedElement.focus();
    }
  }

  function navigateLightbox(direction) {
    var visibleCards = getVisibleCards();
    if (!visibleCards.length) {
      return;
    }
    var currentCard = cards[activeIndex];
    var currentVisibleIndex = visibleCards.indexOf(currentCard);
    if (currentVisibleIndex === -1) {
      return;
    }
    var nextIndex = currentVisibleIndex + direction;
    if (nextIndex < 0) {
      nextIndex = visibleCards.length - 1;
    }
    if (nextIndex >= visibleCards.length) {
      nextIndex = 0;
    }
    var targetCard = visibleCards[nextIndex];
    renderLightbox(targetCard);
  }

  grid.addEventListener('click', function (event) {
    var trigger = event.target.closest('[data-gallery-open]');
    if (!trigger) {
      return;
    }
    var card = trigger.closest('[data-gallery-card]');
    if (!card) {
      return;
    }
    openLightbox(card);
  });

  if (lightboxOverlay) {
    lightboxOverlay.addEventListener('click', closeLightbox);
  }
  if (lightboxClose) {
    lightboxClose.addEventListener('click', closeLightbox);
  }
  if (lightboxPrev) {
    lightboxPrev.addEventListener('click', function () {
      navigateLightbox(-1);
    });
  }
  if (lightboxNext) {
    lightboxNext.addEventListener('click', function () {
      navigateLightbox(1);
    });
  }

  document.addEventListener('keydown', function (event) {
    if (!lightbox || !lightbox.classList.contains('is-open')) {
      return;
    }
    if (event.key === 'Escape') {
      event.preventDefault();
      closeLightbox();
      return;
    }
    if (event.key === 'ArrowRight') {
      event.preventDefault();
      navigateLightbox(1);
      return;
    }
    if (event.key === 'ArrowLeft') {
      event.preventDefault();
      navigateLightbox(-1);
    }
  });

  var touchStartX = null;
  if (lightbox) {
    lightbox.addEventListener('touchstart', function (event) {
      if (event.touches && event.touches.length === 1) {
        touchStartX = event.touches[0].clientX;
      }
    });
    lightbox.addEventListener('touchend', function (event) {
      if (touchStartX === null || !event.changedTouches || !event.changedTouches.length) {
        return;
      }
      var deltaX = event.changedTouches[0].clientX - touchStartX;
      var threshold = 60;
      if (deltaX > threshold) {
        navigateLightbox(-1);
      } else if (deltaX < -threshold) {
        navigateLightbox(1);
      }
      touchStartX = null;
    });
  }

  if (gridWrapper) {
    gridWrapper.addEventListener('keydown', function (event) {
      if (event.key !== 'Tab' || !lightbox || !lightbox.classList.contains('is-open')) {
        return;
      }
      var focusable = Array.prototype.slice.call(lightbox.querySelectorAll('button'));
      if (!focusable.length) {
        return;
      }
      var first = focusable[0];
      var last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    });
  }

  toggleMapView(false);
  applyFilters();
})();
