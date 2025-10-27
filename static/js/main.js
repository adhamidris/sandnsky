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

    // Optional: demo toast on add/remove without page refresh
    cart.addEventListener('submit', (e) => {
      const form = e.target;
      if (form && form.matches('[data-cart-toggle]')) {
        e.preventDefault();
        if (toast && toastMsg) {
          toastMsg.textContent = 'Updated your list';
          toast.dataset.state = 'added';
          if (toastIcon) {
            toastIcon.textContent = '✓';
          }
          cart.dataset.toast = 'show';
          setTimeout(() => {
            cart.dataset.toast = '';
            toast.dataset.state = '';
            if (toastIcon) {
              toastIcon.textContent = '';
            }
          }, 1400);
        }
      }
    });
  })();
