(function () {
  const section = document.querySelector('[data-review-section]');
  if (!section) return;

  const form = section.querySelector('[data-review-form]');
  if (!form) return;

  const toggleButton = section.querySelector('[data-review-toggle]');
  const emptyCta = section.querySelector('[data-review-empty-cta]');
  const cancelButton = form.querySelector('[data-review-cancel]');
  const submitButton = form.querySelector('[data-review-submit]');
  const summaryEl = section.querySelector('[data-review-summary]');
  const listEl = section.querySelector('[data-review-list]');
  const emptyState = section.querySelector('[data-review-empty]');
  const errorBanner = form.querySelector('[data-form-error]');
  const successBanner = form.querySelector('[data-form-success]');
  const submitLabel = submitButton ? submitButton.querySelector('[data-submit-label]') : null;
  const submitSpinner = submitButton ? submitButton.querySelector('[data-submit-spinner]') : null;

  const fieldErrors = new Map();
  form.querySelectorAll('[data-field-error]').forEach((node) => {
    const key = node.getAttribute('data-field-error');
    if (key) {
      fieldErrors.set(key, node);
    }
  });

  const defaultToggleLabel = toggleButton?.getAttribute('data-review-toggle-label') || 'Write a review';
  const activeToggleLabel = toggleButton?.getAttribute('data-review-toggle-active-label') || 'Close review form';
  let successTimerId = null;

  const getCsrfToken = () => {
    const name = 'csrftoken=';
    const decodedCookies = decodeURIComponent(document.cookie || '');
    if (decodedCookies) {
      const parts = decodedCookies.split(';');
      for (const part of parts) {
        const trimmed = part.trim();
        if (trimmed.startsWith(name)) {
          return trimmed.substring(name.length);
        }
      }
    }
    const input = form.querySelector('input[name="csrfmiddlewaretoken"]');
    return input ? input.value : '';
  };

  const setLoading = (isLoading) => {
    if (!submitButton) return;
    submitButton.disabled = isLoading;
    submitButton.setAttribute('aria-busy', isLoading ? 'true' : 'false');
    if (submitLabel) {
      submitLabel.classList.toggle('hidden', isLoading);
    }
    if (submitSpinner) {
      submitSpinner.classList.toggle('hidden', !isLoading);
    }
  };

  const clearFieldErrors = () => {
    fieldErrors.forEach((node) => {
      node.textContent = '';
      node.classList.add('hidden');
    });
  };

  const clearBanners = () => {
    if (errorBanner) {
      errorBanner.textContent = '';
      errorBanner.classList.add('hidden');
    }
    if (successBanner) {
      successBanner.classList.add('hidden');
    }
    if (successTimerId !== null) {
      window.clearTimeout(successTimerId);
      successTimerId = null;
    }
  };

  const showErrorBanner = (message) => {
    if (!errorBanner) return;
    errorBanner.textContent = message || 'We could not submit your review. Please try again.';
    errorBanner.classList.remove('hidden');
  };

  const showSuccessBanner = () => {
    if (!successBanner) return;
    successBanner.classList.remove('hidden');
    if (successTimerId !== null) {
      window.clearTimeout(successTimerId);
    }
    successTimerId = window.setTimeout(() => {
      successBanner.classList.add('hidden');
      successTimerId = null;
    }, 5000);
  };

  const updateToggleLabel = () => {
    if (!toggleButton) return;
    const isHidden = form.classList.contains('hidden');
    toggleButton.textContent = isHidden ? defaultToggleLabel : activeToggleLabel;
    toggleButton.setAttribute('aria-expanded', (!isHidden).toString());
  };

  const openForm = () => {
    form.classList.remove('hidden');
    form.dataset.state = 'open';
    clearFieldErrors();
    clearBanners();
    updateToggleLabel();
    window.requestAnimationFrame(() => {
      const yOffset = typeof window.scrollY === 'number' ? window.scrollY : window.pageYOffset;
      const formRect = form.getBoundingClientRect();
      const targetY = formRect.top + yOffset - 80;
      window.scrollTo({ top: targetY, behavior: 'smooth' });
      const firstField = form.querySelector('textarea, input');
      if (firstField) {
        firstField.focus({ preventScroll: true });
      }
    });
  };

  const closeForm = () => {
    form.classList.add('hidden');
    form.dataset.state = 'closed';
    updateToggleLabel();
  };

  const handleToggleClick = () => {
    if (form.classList.contains('hidden')) {
      openForm();
    } else {
      closeForm();
    }
  };

  const handleCancel = () => {
    form.reset();
    clearFieldErrors();
    clearBanners();
    closeForm();
  };

  const applyFieldErrors = (errors) => {
    if (!errors) return;
    Object.entries(errors).forEach(([field, messages]) => {
      const node = fieldErrors.get(field);
      if (!node) return;
      const text = Array.isArray(messages) ? messages.join(' ') : String(messages);
      node.textContent = text;
      node.classList.remove('hidden');
    });
  };

  const updateSummary = (data) => {
    if (!summaryEl) return;
    if (data && typeof data.summary === 'string' && data.summary.trim()) {
      summaryEl.textContent = data.summary;
      return;
    }
    const count = Number(data?.count || section.dataset.reviewCount || 0);
    if (count > 0) {
      const label = count === 1 ? 'review' : 'reviews';
      summaryEl.textContent = `${count} ${label} posted`;
    } else {
      summaryEl.textContent = 'New — be the first to review';
    }
  };

  const ensureListVisibility = (count) => {
    if (!emptyState || !listEl) return;
    if (Number(count) > 0) {
      emptyState.classList.add('hidden');
      listEl.classList.remove('hidden');
    } else {
      listEl.classList.add('hidden');
      emptyState.classList.remove('hidden');
    }
  };

  const insertReview = (html) => {
    if (!listEl || !html) return;
    listEl.classList.remove('hidden');
    listEl.insertAdjacentHTML('afterbegin', html);
    const first = listEl.firstElementChild;
    if (first) {
      first.classList.add('ring-2', 'ring-primary/40');
      window.setTimeout(() => {
        first.classList.remove('ring-2', 'ring-primary/40');
      }, 2400);
    }
  };

  const submitReview = async (event) => {
    event.preventDefault();
    clearFieldErrors();
    clearBanners();
    setLoading(true);

    const formData = new FormData(form);
    const csrfToken = getCsrfToken();

    try {
      const response = await fetch(form.getAttribute('action'), {
        method: 'POST',
        headers: {
          Accept: 'application/json',
          ...(csrfToken ? { 'X-CSRFToken': csrfToken } : {}),
        },
        body: formData,
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok || !data || data.ok === false) {
        const fieldErrorsData = data?.errors || {};
        applyFieldErrors(fieldErrorsData);

        const message = Array.isArray(data?.non_field_errors) && data.non_field_errors.length
          ? data.non_field_errors.join(' ')
          : Array.isArray(fieldErrorsData.__all__) && fieldErrorsData.__all__.length
            ? fieldErrorsData.__all__.join(' ')
            : 'We could not submit your review. Please double-check your booking details.';
        showErrorBanner(message);
        return;
      }

  insertReview(data.review?.html || '');
  ensureListVisibility(data.count);
  updateSummary(data);
  section.dataset.reviewCount = data.count != null ? String(data.count) : '';

      form.reset();
      showSuccessBanner();
    } catch (error) {
      console.error('Review submission failed', error);
      showErrorBanner('Something went wrong. Please try again in a moment.');
    } finally {
      setLoading(false);
    }
  };

  if (toggleButton) {
    toggleButton.addEventListener('click', handleToggleClick);
  }
  if (emptyCta) {
    emptyCta.addEventListener('click', () => {
      if (form.classList.contains('hidden')) {
        openForm();
      } else {
        const yOffset = typeof window.scrollY === 'number' ? window.scrollY : window.pageYOffset;
        const formRect = form.getBoundingClientRect();
        const targetY = formRect.top + yOffset - 80;
        window.scrollTo({ top: targetY, behavior: 'smooth' });
      }
    });
  }
  if (cancelButton) {
    cancelButton.addEventListener('click', handleCancel);
  }

  form.addEventListener('submit', submitReview);
  updateToggleLabel();
})();
