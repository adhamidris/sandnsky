(function () {
  var marquees = document.querySelectorAll('[data-marquee]');
  if (!marquees.length) {
    return;
  }

  marquees.forEach(function (marquee) {
    if (marquee.dataset.marqueeInitialized === 'true') {
      return;
    }

    var wrapper = marquee.querySelector('[data-marquee-wrapper]');
    var tracks = marquee.querySelectorAll('[data-marquee-track]');
    if (!wrapper || tracks.length === 0) {
      return;
    }

    var primaryTrack = tracks[0];
    var primaryItems = primaryTrack.querySelectorAll('[data-marquee-card]');
    if (!primaryItems.length) {
      return;
    }

    function duplicateContent(track, times) {
      var fragment = document.createDocumentFragment();
      for (var i = 0; i < times; i += 1) {
        primaryItems.forEach(function (item) {
          fragment.appendChild(item.cloneNode(true));
        });
      }
      track.appendChild(fragment);
    }

    var clonesNeeded = 2;
    duplicateContent(primaryTrack, clonesNeeded);

    for (var i = 1; i < tracks.length; i += 1) {
      var track = tracks[i];
      track.innerHTML = '';
      duplicateContent(track, clonesNeeded + 1);
      track.classList.add('marquee-track--delay');
    }

    var totalWidth = 0;
    var elementCount = 0;
    primaryTrack.childNodes.forEach(function (node) {
      if (node.nodeType === 1) {
        var rect = node.getBoundingClientRect();
        totalWidth += rect.width;
        elementCount += 1;
      }
    });

    var gap = 32;
    totalWidth += gap * Math.max(0, elementCount - 1);

    if (totalWidth === 0) {
      totalWidth = primaryTrack.scrollWidth;
    }

    if (totalWidth > 0) {
      wrapper.style.minWidth = totalWidth + 'px';
      marquee.style.setProperty('--marquee-duration', Math.max(40, Math.min(90, totalWidth / 4)) + 's');
    }

    var modal = document.querySelector('[data-gallery-modal]');
    var modalImage = modal ? modal.querySelector('[data-gallery-modal-image]') : null;
    var modalCaption = modal ? modal.querySelector('[data-gallery-modal-caption]') : null;
    var closeButton = modal ? modal.querySelector('[data-gallery-close]') : null;
    var activeAnimationState = null;

    function pauseTracks() {
      tracks.forEach(function (track) {
        track.style.animationPlayState = 'paused';
      });
    }

    function resumeTracks() {
      tracks.forEach(function (track) {
        track.style.animationPlayState = 'running';
      });
    }

    wrapper.addEventListener('mouseenter', pauseTracks);
    wrapper.addEventListener('mouseleave', resumeTracks);

    function openModal(src, alt, caption) {
      if (!modal || !modalImage) {
        return;
      }
      modalImage.src = src;
      modalImage.alt = alt || '';
      if (modalCaption) {
        modalCaption.textContent = caption || '';
      }
      modal.classList.remove('hidden');
      modal.classList.add('flex');
      modal.setAttribute('aria-hidden', 'false');
      activeAnimationState = tracks[0].style.animationPlayState;
      pauseTracks();
      closeButton && closeButton.focus();
    }

    function closeModal() {
      if (!modal) {
        return;
      }
      modal.classList.remove('flex');
      modal.classList.add('hidden');
      modal.setAttribute('aria-hidden', 'true');
      modalImage && (modalImage.src = '');
      resumeTracks();
    }

    if (modal && closeButton) {
      closeButton.addEventListener('click', closeModal);
      modal.addEventListener('click', function (event) {
        if (event.target === modal) {
          closeModal();
        }
      });
      document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape' && modal.classList.contains('flex')) {
          closeModal();
        }
      });
    }

    wrapper.addEventListener('click', function (event) {
      var button = event.target.closest('[data-gallery-open]');
      if (!button) {
        return;
      }
      var src = button.getAttribute('data-gallery-src');
      var alt = button.getAttribute('data-gallery-alt');
      var caption = button.getAttribute('data-gallery-caption');
      openModal(src, alt, caption);
    });

    marquee.dataset.marqueeInitialized = 'true';
  });
})();
