(function () {
  const form = document.querySelector('[data-module="booking-form"]');
  if (!form) return;

  const travelerField = form.querySelector('input[name="travelers"]');
  if (travelerField) {
    travelerField.addEventListener('input', () => {
      if (travelerField.value < 1) {
        travelerField.value = 1;
      }
    });
  }
})();
