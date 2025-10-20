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
    var track = marquee.querySelector('[data-marquee-track]');
    if (!wrapper || !track) {
      return;
    }

    var originalItems = Array.from(track.querySelectorAll('[data-marquee-card]'));
    if (!originalItems.length) {
      return;
    }

    var marqueeWidth = marquee.getBoundingClientRect().width || wrapper.getBoundingClientRect().width || window.innerWidth;
    var direction = marquee.dataset.marqueeDirection === 'reverse' ? 'reverse' : 'forward';
    var speed = parseFloat(marquee.dataset.marqueeSpeed || '45');
    if (Number.isNaN(speed) || speed <= 0) {
      speed = 45;
    }

    var baseHTML = originalItems
      .map(function (item) {
        return item.outerHTML;
      })
      .join('');

    var cycleHTML = baseHTML;
    track.innerHTML = cycleHTML;

    var cycleWidth = track.scrollWidth || track.getBoundingClientRect().width;
    var loopCount = 1;
    var maxLoops = 8;
    while (cycleWidth < marqueeWidth && loopCount < maxLoops) {
      cycleHTML += baseHTML;
      track.innerHTML = cycleHTML;
      cycleWidth = track.scrollWidth || track.getBoundingClientRect().width;
      loopCount += 1;
    }

    track.innerHTML = cycleHTML + cycleHTML;
    cycleWidth = track.scrollWidth ? track.scrollWidth / 2 : (track.getBoundingClientRect().width / 2);

    if (cycleWidth <= 0) {
      return;
    }

    var offset = direction === 'reverse' ? -cycleWidth : 0;
    track.style.transform = 'translateX(' + offset + 'px)';

    var running = true;
    var lastTime = null;

    function step(timestamp) {
      if (!running) {
        lastTime = timestamp;
        requestAnimationFrame(step);
        return;
      }

      if (lastTime !== null) {
        var delta = (timestamp - lastTime) / 1000;
        var distance = speed * delta;

        if (direction === 'reverse') {
          offset += distance;
          if (offset >= 0) {
            offset -= cycleWidth;
          }
        } else {
          offset -= distance;
          if (offset <= -cycleWidth) {
            offset += cycleWidth;
          }
        }

        track.style.transform = 'translateX(' + offset + 'px)';
      }

      lastTime = timestamp;
      requestAnimationFrame(step);
    }

    requestAnimationFrame(step);

    function pauseMarquee() {
      running = false;
    }

    function resumeMarquee() {
      if (!running) {
        running = true;
        lastTime = null;
      }
    }

    wrapper.addEventListener('mouseenter', pauseMarquee);
    wrapper.addEventListener('mouseleave', resumeMarquee);

    var modal = document.querySelector('[data-gallery-modal]');
    var modalImage = modal ? modal.querySelector('[data-gallery-modal-image]') : null;
    var modalCaption = modal ? modal.querySelector('[data-gallery-modal-caption]') : null;
    var closeButton = modal ? modal.querySelector('[data-gallery-close]') : null;

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
      pauseMarquee();
      closeButton && closeButton.focus();
    }

    function closeModal() {
      if (!modal) {
        return;
      }
      modal.classList.remove('flex');
      modal.classList.add('hidden');
      modal.setAttribute('aria-hidden', 'true');
      if (modalImage) {
        modalImage.src = '';
      }
      resumeMarquee();
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
