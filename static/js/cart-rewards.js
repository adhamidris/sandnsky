(function () {
  const root = document.querySelector("[data-cart-rewards-root]");
  if (!root) return;

  const summaryScript = document.getElementById("cart-summary-state");
  let currentSummary = null;

  try {
    currentSummary = summaryScript ? JSON.parse(summaryScript.textContent) : null;
  } catch (error) {
    currentSummary = null;
    console.warn("Unable to parse initial cart summary payload.", error);
  }

  if (!currentSummary) return;

  const entriesContainer = document.querySelector("[data-cart-entries]");
  const emptyStateEl = document.querySelector("[data-empty-cart-state]");
  const quickAddRoot = document.querySelector("[data-quick-add-root]");
  const quickAddUrlTemplate = quickAddRoot?.dataset.quickAddUrlTemplate || "";
  const tripUrlTemplate = quickAddRoot?.dataset.tripUrlTemplate || "";
  const checkoutUrl = quickAddRoot?.dataset.checkoutUrl || "";
  const progressContainer = root.querySelector("[data-reward-progress-container]");
  const phaseList = root.querySelector("[data-reward-phase-list]");
  const alertBox = root.querySelector("[data-rewards-alert]");
  const badgeEl = root.querySelector("[data-reward-badge]");
  const mobileSummary = document.querySelector("[data-mobile-reward-summary]");
  const mobileProgressContainer = document.querySelector("[data-mobile-progress]");
  const mobileCountEl = document.querySelector("[data-mobile-reward-count]");
  const mobileToggle = document.querySelector("[data-mobile-reward-toggle]");
  const mobileDetails = document.querySelector("[data-mobile-reward-details]");
  const mobilePhaseList = document.querySelector("[data-mobile-phase-list]");
  const mobileAlertBox = document.querySelector("[data-mobile-rewards-alert]");

  const summaryCountEl = document.querySelector("[data-summary-count]");
  const summaryPreEl = document.querySelector("[data-summary-pre-discount]");
  const summaryDiscountEl = document.querySelector("[data-summary-discount]");
  const summaryTotalEl = document.querySelector("[data-summary-total]");

  const APPLY_CLASS = "inline-flex items-center gap-1 rounded-full border border-primary/40 bg-background px-3 py-1 text-xs font-semibold text-primary transition hover:bg-primary/10";
  const LOCKED_CLASS = "inline-flex items-center gap-1 rounded-full border border-dashed border-muted px-3 py-1 text-xs font-semibold text-muted-foreground";
  const REMOVE_CLASS = "inline-flex items-center gap-1 rounded-full border border-destructive/40 px-3 py-1 text-xs font-semibold text-destructive transition hover:bg-destructive/10";
  let activeQuickAddContainer = null;

  function isoLocalDateString(date) {
    if (!(date instanceof Date) || isNaN(date.getTime())) {
      return "";
    }
    const offset = date.getTimezoneOffset() * 60000;
    const local = new Date(date.getTime() - offset);
    return local.toISOString().slice(0, 10);
  }

  function todayIsoDate() {
    return isoLocalDateString(new Date());
  }

  function clampTravelerCount(value, minValue, maxValue) {
    const min = typeof minValue === "number" && !Number.isNaN(minValue) ? minValue : 1;
    const max = typeof maxValue === "number" && !Number.isNaN(maxValue) ? maxValue : null;
    let parsed = parseInt(value, 10);
    if (Number.isNaN(parsed)) {
      parsed = min;
    }
    if (parsed < min) {
      parsed = min;
    }
    if (max !== null && parsed > max) {
      parsed = max;
    }
    return parsed;
  }

  function getQuickAddElements(container) {
    if (!container) {
      return {
        container: null,
        trigger: null,
        popover: null,
        dateInput: null,
        countInput: null,
      };
    }
    return {
      container,
      trigger: container.querySelector("[data-quick-add-trigger]"),
      popover: container.querySelector("[data-quick-add-popover]"),
      dateInput: container.querySelector("[data-quick-add-date]"),
      countInput: container.querySelector("[data-quick-add-count]"),
    };
  }

  function ensureQuickAddDefaults(container) {
    const { dateInput, countInput } = getQuickAddElements(container);
    if (dateInput) {
      const today = todayIsoDate();
      if (dateInput.min !== today) {
        dateInput.min = today;
      }
      if (!dateInput.value || dateInput.value < today) {
        dateInput.value = today;
      }
    }
    if (countInput) {
      const min = parseInt(countInput.getAttribute("min"), 10);
      const max = parseInt(countInput.getAttribute("max"), 10);
      const clamped = clampTravelerCount(countInput.value, min, max);
      countInput.value = String(clamped);
    }
  }

  function closeQuickAddPopover(container) {
    const { popover, trigger } = getQuickAddElements(container);
    if (!popover || popover.dataset.state !== "open") {
      return;
    }
    popover.classList.add("hidden");
    popover.dataset.state = "closed";
    if (trigger) {
      trigger.setAttribute("aria-expanded", "false");
    }
    if (container) {
      container.classList.remove("quick-add-open");
    }
    if (activeQuickAddContainer === container) {
      activeQuickAddContainer = null;
    }
  }

  function closeAllQuickAddPopovers(exceptContainer) {
    const openPopovers = document.querySelectorAll("[data-quick-add-popover][data-state='open']");
    openPopovers.forEach((popover) => {
      const host = popover.closest("[data-quick-add-container]");
      if (host && host !== exceptContainer) {
        closeQuickAddPopover(host);
      }
    });
  }

  function openQuickAddPopover(container) {
    const { popover, trigger } = getQuickAddElements(container);
    if (!popover) {
      return;
    }
    if (popover.dataset.state === "open") {
      return;
    }
    closeAllQuickAddPopovers(container);
    ensureQuickAddDefaults(container);
    popover.classList.remove("hidden");
    popover.dataset.state = "open";
    if (trigger) {
      trigger.setAttribute("aria-expanded", "true");
    }
    if (container) {
      container.classList.add("quick-add-open");
    }
    activeQuickAddContainer = container;
    const { dateInput } = getQuickAddElements(container);
    if (dateInput) {
      window.requestAnimationFrame(() => {
        dateInput.focus();
      });
    }
  }

  function stepTravelerCount(container, direction) {
    const { countInput } = getQuickAddElements(container);
    if (!countInput) {
      return;
    }
    const min = parseInt(countInput.getAttribute("min"), 10);
    const max = parseInt(countInput.getAttribute("max"), 10);
    const current = clampTravelerCount(countInput.value, min, max);
    const next = clampTravelerCount(current + direction, min, max);
    countInput.value = String(next);
  }

  function extractQuickAddValues(container) {
    ensureQuickAddDefaults(container);
    const { dateInput, countInput } = getQuickAddElements(container);
    const values = { date: "", adults: "" };
    if (dateInput) {
      values.date = dateInput.value || "";
    }
    if (countInput) {
      const min = parseInt(countInput.getAttribute("min"), 10);
      const max = parseInt(countInput.getAttribute("max"), 10);
      const clamped = clampTravelerCount(countInput.value, min, max);
      countInput.value = String(clamped);
      values.adults = String(clamped);
    }
    return values;
  }

  function fillSlug(template, slug) {
    if (!template || !slug) return "";
    return template.replace("__slug__", encodeURIComponent(slug));
  }

  function buildTripUrl(template, slug, suffix = "") {
    if (!template || !slug) return "";
    return `${fillSlug(template, slug)}${suffix}`;
  }

  function escapeHtml(value) {
    if (value === null || value === undefined) return "";
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function setText(el, value) {
    if (!el) return;
    el.textContent = value;
  }

  function setMobileExpanded(expanded) {
    if (!mobileDetails) return;
    const isExpanded = !!expanded;
    mobileDetails.dataset.mobileExpanded = isExpanded ? "true" : "false";
    mobileDetails.classList.toggle("hidden", !isExpanded);
    mobileDetails.classList.toggle("block", isExpanded);
    if (mobileToggle) {
      mobileToggle.textContent = isExpanded ? "Hide rewards" : "Redeem here";
      mobileToggle.setAttribute("aria-expanded", isExpanded ? "true" : "false");
    }
  }

  function updateSummaryScript(summary) {
    if (!summaryScript) return;
    try {
      summaryScript.textContent = JSON.stringify(summary);
    } catch (error) {
      // no-op
    }
  }

  function getCsrfToken() {
    const cookies = document.cookie ? document.cookie.split(";") : [];
    for (let i = 0; i < cookies.length; i += 1) {
      const cookie = cookies[i].trim();
      if (cookie.startsWith("csrftoken=")) {
        return decodeURIComponent(cookie.substring("csrftoken=".length));
      }
    }
    const csrfInput = document.querySelector("input[name=csrfmiddlewaretoken]");
    return csrfInput ? csrfInput.value : "";
  }

  function applyAlertState(box, message, isError) {
    if (!box) return;
    box.textContent = message;
    box.classList.toggle("hidden", false);
    box.classList.toggle("border-destructive/40", !!isError);
    box.classList.toggle("bg-destructive/10", !!isError);
    box.classList.toggle("text-destructive", !!isError);
    box.classList.toggle("border-primary/40", !isError);
    box.classList.toggle("bg-primary/10", !isError);
    box.classList.toggle("text-primary", !isError);
  }

  function resetAlert(box) {
    if (!box) return;
    box.textContent = "";
    box.classList.add("hidden");
    box.classList.remove("border-primary/40", "bg-primary/10", "text-primary");
    box.classList.add("border-destructive/40", "bg-destructive/10", "text-destructive");
  }

  function showAlert(message, isError = true) {
    applyAlertState(alertBox, message, isError);
    applyAlertState(mobileAlertBox, message, isError);
  }

  function clearAlert() {
    resetAlert(alertBox);
    resetAlert(mobileAlertBox);
  }

  function getScrollContainers(element) {
    const containers = [];
    const seen = new Set();
    if (phaseList && phaseList.scrollHeight > phaseList.clientHeight + 1) {
      containers.push(phaseList);
      seen.add(phaseList);
    }
    if (mobilePhaseList && mobilePhaseList.scrollHeight > mobilePhaseList.clientHeight + 1) {
      containers.push(mobilePhaseList);
      seen.add(mobilePhaseList);
    }
    let current = element?.parentElement || null;
    while (current && current !== document.body) {
      if (!seen.has(current) && current.scrollHeight > current.clientHeight + 1) {
        containers.push(current);
        seen.add(current);
      }
      current = current.parentElement;
    }
    if (root && root.scrollHeight > root.clientHeight + 1 && !seen.has(root)) {
      containers.push(root);
      seen.add(root);
    }
    return containers;
  }

  function scrollWithin(container, target) {
    if (!container) return false;
    if (container.scrollHeight <= container.clientHeight + 1) return false;
    const containerRect = container.getBoundingClientRect();
    const targetRect = target.getBoundingClientRect();
    if (
      targetRect.bottom <= containerRect.bottom &&
      targetRect.top >= containerRect.top
    ) {
      return true;
    }
    let delta = 0;
    if (targetRect.bottom > containerRect.bottom) {
      delta = targetRect.bottom - containerRect.bottom + 12;
    } else if (targetRect.top < containerRect.top) {
      delta = targetRect.top - containerRect.top - 12;
    }
    if (delta !== 0) {
      container.scrollBy({ top: delta, behavior: "smooth" });
      return true;
    }
    return false;
  }

  function ensureVisibleWithinPanel(element) {
    if (!element) return;
    const containers = getScrollContainers(element);
    for (let i = 0; i < containers.length; i += 1) {
      if (scrollWithin(containers[i], element)) {
        return;
      }
    }
    element.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }

  if (mobileDetails) {
    setMobileExpanded(mobileDetails.dataset.mobileExpanded === "true");
  }
  if (mobileToggle && mobileDetails) {
    mobileToggle.addEventListener("click", () => {
      const expanded = mobileDetails.dataset.mobileExpanded === "true";
      setMobileExpanded(!expanded);
      if (!expanded) {
        ensureVisibleWithinPanel(mobileDetails);
      }
    });
  }

  function renderProgressCard(rewards) {
    const phases = Array.isArray(rewards?.phases) ? rewards.phases : [];
    const progress = rewards?.progress || {};
    const totalCents = Number(progress.total_cents || 0);
    const unlockedIds = Array.isArray(progress.unlocked_phase_ids) ? progress.unlocked_phase_ids : [];
    const nextPhaseId = progress.next_phase_id;
    const unlockedIdSet = new Set(
      unlockedIds.map((id) => {
        if (id === null || id === undefined) return "";
        return String(id);
      })
    );
    const nextPhaseIdStr =
      nextPhaseId === null || nextPhaseId === undefined ? null : String(nextPhaseId);
    const remainingDisplay = progress.remaining_to_next_display || "";
    const currency = progress.currency || currentSummary.currency || root.dataset.currency || "";
    const totalDisplay = progress.total_display || "0.00";

    if (!phases.length) {
      return `
        <div class="rounded-2xl border border-dashed border-border p-4 text-sm text-muted-foreground" data-reward-progress-empty>
          Configure reward phases in the admin to surface checkout incentives here.
        </div>
      `;
    }

    const thresholds = phases.map((phase) => Number(phase.threshold_amount_cents || 0));
    const maxThreshold = Math.max(1, ...thresholds, 1);
    const rawProgressPercent = (totalCents / maxThreshold) * 100;
    const progressPercent = Math.min(100, Math.max(0, rawProgressPercent));
    const progressPercentStr = Number(progressPercent.toFixed(3)).toString();

    const markerHtml = phases
      .map((phase) => {
        const percent = Math.min(
          100,
          Math.max(0, ((Number(phase.threshold_amount_cents || 0) / maxThreshold) * 100))
        );
        const percentStr = Number(percent.toFixed(3)).toString();
        const unlocked = phase.unlocked;
        const phaseIdStr = phase?.id === undefined || phase?.id === null ? "" : String(phase.id);
        const hasApplied =
          Array.isArray(phase?.applied_entry_ids) && phase.applied_entry_ids.length > 0;
        const phaseStatus = hasApplied
          ? "redeemed"
          : unlocked
          ? "unlocked"
          : nextPhaseIdStr && nextPhaseIdStr === phaseIdStr
          ? "active"
          : "locked";
        return `
          <div class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2"
               style="left: ${percentStr}%;"
               data-reward-progress-marker
               data-phase-id="${escapeHtml(phase.id)}"
               data-phase-status="${escapeHtml(phaseStatus)}">
            <span class="block h-2.5 w-2.5 rounded-full border-2 ${unlocked ? "border-primary bg-primary" : "border-muted bg-background"}"></span>
          </div>
        `;
      })
      .join("");

    const labelHtml = phases
      .map((phase, index) => {
        const percent = Math.min(
          100,
          Math.max(0, ((Number(phase.threshold_amount_cents || 0) / maxThreshold) * 100))
        );
        const percentStr = Number(percent.toFixed(3)).toString();
        const phaseIdStr = phase?.id === undefined || phase?.id === null ? "" : String(phase.id);
        const hasApplied =
          Array.isArray(phase?.applied_entry_ids) && phase.applied_entry_ids.length > 0;
        const phaseStatus = hasApplied
          ? "redeemed"
          : unlockedIdSet.has(phaseIdStr)
          ? "unlocked"
          : nextPhaseIdStr && nextPhaseIdStr === phaseIdStr
          ? "active"
          : "locked";
        return `
          <span class="rewards-phase-pill flex-1 text-left ${
            index === 0 ? "" : index === phases.length - 1 ? "text-right" : "text-center"
          }"
                data-phase-id="${escapeHtml(phase.id)}"
                data-phase-status="${escapeHtml(phaseStatus)}">
            Phase ${escapeHtml(index + 1)}
          </span>
        `;
      })
      .join("");

    let nextPhaseMessage = "You've unlocked every available reward. Nice work!";
    if (nextPhaseId && remainingDisplay) {
      const nextPhase = phases.find((phase) => phase.id === nextPhaseId);
      if (nextPhase) {
        nextPhaseMessage = `You're ${escapeHtml(remainingDisplay)} away from unlocking <span class="font-medium text-foreground">${escapeHtml(
          nextPhase.name || "the next phase"
        )}</span>.`;
      }
    } else if (!nextPhaseId && !unlockedIds.length) {
      nextPhaseMessage = "Add a little more to begin unlocking 50% off rewards.";
    }

    const unlockedCount = unlockedIds.length;
    const unlockedSummary = `${escapeHtml(unlockedCount)} of ${escapeHtml(phases.length)} reward${phases.length === 1 ? "" : "s"} unlocked.`;

    return `
      <div class="rounded-2xl border border-border bg-background/80 p-4 space-y-3" data-reward-progress-block>
        <div class="flex flex-col gap-1 text-sm text-muted-foreground">
          <span class="text-sm font-semibold text-foreground" data-reward-total>${escapeHtml(currency)} ${escapeHtml(totalDisplay)}</span>
          <span data-reward-next>${nextPhaseMessage}</span>
        </div>
        <div class="relative">
          <div class="relative h-2 w-full overflow-hidden rounded-full bg-muted"
               data-reward-progress-track
               data-total-cents="${escapeHtml(totalCents)}"
               data-max-threshold="${escapeHtml(maxThreshold)}">
            <div class="absolute left-0 top-0 h-full rounded-full bg-primary transition-all"
                 style="width: ${progressPercentStr}%;"
                 data-reward-progress-fill></div>
            ${markerHtml}
          </div>
          <div class="mt-3 flex flex-wrap items-center justify-between gap-2 text-[0.65rem] text-muted-foreground" data-reward-progress-labels>
            ${labelHtml}
          </div>
        </div>
        <p class="text-xs text-muted-foreground">${unlockedSummary}</p>
      </div>
    `;
  }

  function renderPhaseCards(rewards, entries) {
    const phases = Array.isArray(rewards?.phases) ? rewards.phases : [];
    const entriesById = new Map();
    (entries || []).forEach((entry) => {
      if (entry && entry.id !== undefined) {
        entriesById.set(String(entry.id), entry);
      }
    });

    const globalRedeemedTrips = new Set(
      Array.isArray(rewards?.redeemed_trip_ids) ? rewards.redeemed_trip_ids : []
    );
    const hasGlobalRedeemed = globalRedeemedTrips.size > 0;

    return phases
      .map((phase, index) => {
        const unlocked = !!phase.unlocked;
        const appliedEntries = Array.isArray(phase.applied_entry_ids)
          ? phase.applied_entry_ids
              .map((entryId) => entriesById.get(String(entryId)))
              .filter(Boolean)
          : [];
        const isOpen = appliedEntries.length > 0;
        const phaseStatus = !unlocked ? "locked" : appliedEntries.length > 0 ? "redeemed" : "unlocked";
        const tripsHtml = Array.isArray(phase.trip_options)
          ? phase.trip_options
              .map((trip) => {
                const image = trip.card_image_url
                  ? `<img src="${escapeHtml(trip.card_image_url)}" alt="" class="h-12 w-16 rounded-lg object-cover" />`
                  : "";
                const comparison = trip.comparison || {};
                const travelerLabel = comparison.traveler_label || "";
                const fullPrice = comparison.full_price_display || "";
                const rewardPrice = comparison.reward_price_display || "";
                const discountDisplay = comparison.discount_display || "";
                const perPersonFull = trip.base_price_per_person_display || "";
                const perPersonReward = comparison.reward_price_per_person_display || "";
                const showComparison = travelerLabel && fullPrice && rewardPrice;
                const discountPercentValue = Number(phase.discount_percent || 0);
                const discountPercentLabel = Number.isFinite(discountPercentValue)
                  ? `${discountPercentValue % 1 === 0 ? discountPercentValue.toFixed(0) : discountPercentValue.toFixed(2)}%`
                  : "";
                const isRedeemed = !!trip.is_redeemed;
                const cardState = !unlocked
                  ? "locked"
                  : isRedeemed
                  ? "redeemed"
                  : hasGlobalRedeemed
                  ? "replace"
                  : "available";
                const quickAddState = cardState;
                const comparisonLines = showComparison
                  ? `
                      <p class="text-[0.65rem] text-muted-foreground">
                        <span class="font-medium text-foreground">${escapeHtml(travelerLabel)}</span>
                        · ${escapeHtml(fullPrice)} → <span class="font-semibold text-primary">${escapeHtml(rewardPrice)}</span>
                        ${discountDisplay ? `· Save ${escapeHtml(discountDisplay)}` : ""}
                      </p>
                      ${
                        perPersonFull && perPersonReward
                          ? `<p class="text-[0.65rem] text-muted-foreground">
                               Per traveler: ${escapeHtml(perPersonFull)} → <span class="font-semibold text-primary">${escapeHtml(perPersonReward)}</span>
                             </p>`
                          : ""
                      }
                    `
                  : perPersonFull
                  ? `<p class="text-[0.65rem] text-muted-foreground">From ${escapeHtml(perPersonFull)} per traveler</p>`
                  : "";
                let statusLine = "";
                if (!unlocked) {
                  statusLine = discountPercentLabel
                    ? `<p class="text-[0.65rem] text-muted-foreground">Unlock this phase to activate ${escapeHtml(discountPercentLabel)} savings.</p>`
                    : `<p class="text-[0.65rem] text-muted-foreground">Unlock this phase to redeem rewards.</p>`;
                } else if (isRedeemed) {
                  statusLine = `<p class="text-[0.65rem] font-semibold text-primary">Reward redeemed for your list.</p>`;
                } else if (hasGlobalRedeemed) {
                  statusLine = `<p class="text-[0.65rem] text-muted-foreground">Redeem this trip instead to switch rewards.</p>`;
                }
                const cardClasses = [
                  "rounded-xl",
                  "border",
                  isRedeemed ? "border-primary" : "border-border",
                  isRedeemed ? "bg-primary/10" : "bg-background",
                  "px-3",
                  "py-2",
                ];
                if (!unlocked) {
                  cardClasses.push("opacity-50");
                }
                const plusIcon = `
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4">
                    <path fill-rule="evenodd" d="M10 3.5a.75.75 0 0 1 .75.75v5h5a.75.75 0 0 1 0 1.5h-5v5a.75.75 0 0 1-1.5 0v-5h-5a.75.75 0 0 1 0-1.5h5v-5A.75.75 0 0 1 10 3.5Z" clip-rule="evenodd" />
                  </svg>
                `;
                const checkIcon = `
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4">
                    <path fill-rule="evenodd" d="M16.704 5.29a1 1 0 0 1 0 1.414l-6.764 6.764a1 1 0 0 1-1.414 0l-3.53-3.53a1 1 0 0 1 1.414-1.414l2.823 2.823 6.057-6.057a1 1 0 0 1 1.414 0Z" clip-rule="evenodd" />
                  </svg>
                `;
                const minusIcon = `
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4">
                    <path fill-rule="evenodd" d="M4 10a1 1 0 0 1 .883-.993L5 9h10a1 1 0 0 1 .117 1.993L15 11H5a1 1 0 0 1-1-1Z" clip-rule="evenodd" />
                  </svg>
                `;
                const lockIcon = `
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4">
                    <path d="M10 2a5 5 0 0 1 5 5v2h1a1 1 0 0 1 0 2h-1v4a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V11H4a1 1 0 1 1 0-2h1V7a5 5 0 0 1 5-5Zm-3 7h6V7a3 3 0 1 0-6 0v2Z" />
                  </svg>
                `;
                const arrowIcon = `
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-3.5 w-3.5">
                    <path fill-rule="evenodd" d="M5 10a.75.75 0 0 1 .75-.75h6.19l-2.22-2.22a.75.75 0 1 1 1.06-1.06l3.5 3.5a.75.75 0 0 1 0 1.06l-3.5 3.5a.75.75 0 1 1-1.06-1.06l2.22-2.22H5.75A.75.75 0 0 1 5 10Z" clip-rule="evenodd" />
                  </svg>
                `;
                const tripUrl = tripUrlTemplate ? buildTripUrl(tripUrlTemplate, trip.slug || "") : "";
                let quickAddLabel = "Redeem this trip";
                let quickAddIcon = plusIcon;
                let quickAddClasses =
                  "inline-flex items-center gap-1 rounded-full bg-primary px-3 py-1 text-xs font-semibold text-primary-foreground transition hover:bg-primary/90";
                let quickAddAttributes = `data-reward-trip-action data-trip-state="${escapeHtml(quickAddState)}"`;
                if (quickAddState === "redeemed") {
                  quickAddLabel = "Remove reward";
                  quickAddIcon = minusIcon;
                } else if (quickAddState === "replace") {
                  quickAddLabel = "Redeem instead";
                  quickAddIcon = checkIcon;
                } else if (quickAddState === "locked") {
                  quickAddLabel = "Locked";
                  quickAddIcon = lockIcon;
                  quickAddClasses =
                    "inline-flex items-center gap-1 rounded-full bg-muted px-3 py-1 text-xs font-semibold text-muted-foreground cursor-not-allowed";
                  quickAddAttributes += " disabled";
                }
                if (quickAddState !== "locked") {
                  quickAddAttributes += ` data-quick-add-trigger data-trip-slug="${escapeHtml(trip.slug || "")}"`;
                }
                const viewControl = tripUrl
                  ? `<a href="${escapeHtml(tripUrl)}"
                        class="inline-flex items-center gap-1 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary transition hover:bg-primary/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary">
                       View trip
                       ${arrowIcon}
                     </a>`
                  : trip.slug
                  ? `<button type="button"
                            class="inline-flex items-center gap-1 rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold text-primary transition hover:bg-primary/20 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                            data-action="view-trip"
                            data-trip-slug="${escapeHtml(trip.slug || "")}">
                       View trip
                       ${arrowIcon}
                     </button>`
                  : "";
                return `
                  <div class="${cardClasses.join(" ")}"
                       data-reward-trip-card
                       data-trip-state="${escapeHtml(cardState)}">
                    <button type="button"
                            class="flex w-full items-center justify-between gap-3 text-left text-xs font-semibold text-foreground transition focus:outline-none focus:ring-2 focus:ring-primary"
                            data-reward-trip
                            data-phase-id="${escapeHtml(phase.id)}"
                            data-trip-id="${escapeHtml(trip.trip_id)}"${unlocked ? "" : " disabled"}>
                      <div class="flex-1">
                        <p class="text-xs font-semibold text-foreground">${escapeHtml(trip.title || "")}</p>
                        ${comparisonLines}
                        ${statusLine}
                      </div>
                      ${image}
                    </button>
                    <div class="mt-2 flex flex-wrap items-center justify-between gap-2 text-[0.65rem]">
                      <span class="text-muted-foreground">
                        ${discountPercentLabel ? `${escapeHtml(discountPercentLabel)} off reward` : "Reward savings"}
                      </span>
                      <div class="flex flex-wrap items-center gap-2">
                        ${viewControl}
                        <button type="button"
                                class="${quickAddClasses}"
                                ${quickAddAttributes}>
                          ${quickAddIcon}
                          ${escapeHtml(quickAddLabel)}
                        </button>
                      </div>
                    </div>
                  </div>
                `;
              })
              .join("")
          : "";

        const description = phase.headline
          ? `<p class="mb-3 text-sm font-medium text-foreground">${escapeHtml(phase.headline)}</p>`
          : phase.description
          ? `<p class="mb-3 text-sm text-muted-foreground">${escapeHtml(phase.description)}</p>`
          : "";

        const appliedBlock = appliedEntries.length
          ? `
            <div class="mt-3 rounded-xl bg-primary/10 p-3 text-xs text-primary" data-phase-applied-target>
              <p class="font-semibold">Applied to:</p>
              <ul class="mt-1 space-y-1">
                ${appliedEntries
                  .map((entry) => `<li>${escapeHtml(entry.trip_title || "")}</li>`)
                  .join("")}
              </ul>
            </div>
          `
          : "";

        let statusBadge = `
          <span class="inline-flex items-center gap-1 rounded-full bg-muted px-2.5 py-1 text-muted-foreground">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-3.5 w-3.5">
              <path d="M10 2a5 5 0 0 1 5 5v2h1a1 1 0 0 1 0 2h-1v4a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V11H4a1 1 0 1 1 0-2h1V7a5 5 0 0 1 5-5Zm-3 7h6V7a3 3 0 1 0-6 0v2Z" />
            </svg>
            Locked
          </span>
        `;
        if (phaseStatus === "unlocked") {
          statusBadge = `
            <span class="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-1 text-primary">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-3.5 w-3.5">
                <path fill-rule="evenodd" d="M16.704 5.29a1 1 0 0 1 0 1.414l-6.764 6.764a1 1 0 0 1-1.414 0l-3.53-3.53a1 1 0 0 1 1.414-1.414l2.823 2.823 6.057-6.057a1 1 0 0 1 1.414 0Z" clip-rule="evenodd" />
              </svg>
              Unlocked
            </span>
          `;
        } else if (phaseStatus === "redeemed") {
          statusBadge = `
            <span class="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-1 text-primary">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-3.5 w-3.5">
                <path fill-rule="evenodd" d="M16.704 5.29a1 1 0 0 1 0 1.414l-6.764 6.764a1 1 0 0 1-1.414 0l-3.53-3.53a1 1 0 0 1 1.414-1.414l2.823 2.823 6.057-6.057a1 1 0 0 1 1.414 0Z" clip-rule="evenodd" />
              </svg>
              Redeemed
            </span>
          `;
        }

        const bodyClasses = ["border-t", "border-border/60", "px-4", "pb-4", "pt-3", "text-xs", "text-muted-foreground"];
        if (!isOpen) {
          bodyClasses.push("hidden");
        }

        return `
          <article class="rounded-2xl border border-border bg-background/70"
                   data-reward-phase
                   data-phase-id="${escapeHtml(phase.id)}"
                   data-phase-unlocked="${unlocked ? "true" : "false"}"
                   data-phase-status="${escapeHtml(phaseStatus)}"
                   data-open="${isOpen ? "true" : "false"}">
            <button type="button"
                    class="flex w-full items-center justify-between gap-3 px-4 py-3 text-left"
                    data-reward-phase-toggle>
              <div>
                <p class="text-xs uppercase tracking-wide text-muted-foreground">Phase ${escapeHtml(index + 1)}</p>
                <p class="text-sm font-semibold text-foreground">${escapeHtml(phase.name || "")}</p>
                <p class="text-xs text-muted-foreground">
                  Unlock at ${escapeHtml(phase.currency || "")} ${escapeHtml(phase.threshold_amount_display || "")} &middot; ${escapeHtml(Number(phase.discount_percent || 0).toFixed(0))}% off
                </p>
              </div>
              <div class="flex items-center gap-2 text-xs font-semibold">
                ${statusBadge}
                <svg xmlns="http://www.w3.org/2000/svg"
                     viewBox="0 0 20 20"
                     fill="currentColor"
                     class="h-4 w-4 transition-transform ${isOpen ? "rotate-180" : ""}"
                     data-chevron>
                  <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 0 1 1.06.02L10 11.042l3.71-3.81a.75.75 0 1 1 1.08 1.04l-4.24 4.36a.75.75 0 0 1-1.08 0l-4.24-4.36a.75.75 0 0 1 .02-1.06Z" clip-rule="evenodd" />
                </svg>
              </div>
            </button>
            <div class="${bodyClasses.join(" ")}" data-reward-phase-body>
              ${description}
              <p class="font-semibold text-foreground">Eligible trips</p>
              <div class="mt-2 grid grid-cols-1 gap-2" data-reward-phase-trips>
                ${tripsHtml || '<span class="text-xs text-muted-foreground">No trips attached yet.</span>'}
              </div>
              ${appliedBlock}
            </div>
          </article>
        `;
      })
      .join("");
  }

  function getTripPhases(entry, rewards) {
    const phases = Array.isArray(rewards?.phases) ? rewards.phases : [];
    const tripId = entry.trip_id;
    const results = [];

    phases.forEach((phase) => {
      if (!Array.isArray(phase.trip_options)) return;
      phase.trip_options.forEach((trip) => {
        if (trip.trip_id === tripId) {
          results.push({ phase, trip });
        }
      });
    });
    return results;
  }

  function renderEntryOptions(entry, rewards) {
    const matches = getTripPhases(entry, rewards);
    if (!matches.length) {
      return "";
    }

    return matches
      .map(({ phase }) => {
        if (phase.unlocked) {
          if (entry.applied_reward && entry.applied_reward.phase_id === phase.id) {
            return `<span class="inline-flex items-center gap-1 rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">
              Applied ${escapeHtml(phase.name || "")}
            </span>`;
          }
          return `<button type="button"
                          class="${APPLY_CLASS}"
                          data-action="apply-reward"
                          data-entry-id="${escapeHtml(entry.id)}"
                          data-phase-id="${escapeHtml(phase.id)}"
                          data-trip-id="${escapeHtml(entry.trip_id)}">
                    Apply ${escapeHtml(phase.name || "")}
                  </button>`;
        }
        return `<span class="${LOCKED_CLASS}" data-entry-locked-option data-phase-id="${escapeHtml(phase.id)}">
                  Unlock at ${escapeHtml(phase.currency || "")} ${escapeHtml(phase.threshold_amount_display || "")}
                </span>`;
      })
      .join("");
  }

  function renderEntryStatus(entry, rewards) {
    if (entry.applied_reward) {
      return `Applied <span class="font-medium text-foreground">${escapeHtml(
        entry.applied_reward.phase_name || ""
      )}</span> · Saved ${escapeHtml(entry.applied_reward.discount_display || "")}`;
    }
    const unlocked = getTripPhases(entry, rewards)
      .filter(({ phase }) => phase.unlocked)
      .map(({ phase }) => phase.name)
      .filter(Boolean);
    if (unlocked.length) {
      return `Unlocked: ${unlocked.join(", ")} reward${unlocked.length === 1 ? "" : "s"} available.`;
    }
    return "";
  }

  function renderEntryRewardActions(entry) {
    if (entry.applied_reward) {
      return `<button type="button"
                      class="${REMOVE_CLASS}"
                      data-action="remove-reward"
                      data-entry-id="${escapeHtml(entry.id)}">
                Remove discount
              </button>`;
    }
    return "";
  }

  function renderEntryCard(entry, summary, config) {
    const rewards = summary.rewards || {};
    const currency = entry.currency || config.currency || "";
    const tripTitle = escapeHtml(entry.trip_title || "");
    const travelDate = entry.travel_date_display
      ? `<li><span class="font-medium text-foreground">Trip date:</span> ${escapeHtml(entry.travel_date_display)}</li>`
      : "";
    const travelerLabel = `<li><span class="font-medium text-foreground">Travelers:</span> ${escapeHtml(
      entry.traveler_label || ""
    )}</li>`;

    const editLink =
      entry.trip_slug && config.tripUrlTemplate
        ? `<a href="${buildTripUrl(config.tripUrlTemplate, entry.trip_slug || "", "#booking-form")}"
               class="trip-action-edit inline-flex items-center gap-1 rounded-full px-3 py-1 font-semibold transition">
             Edit trip
             <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-4 w-4">
               <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5 19.5 10.5M16.5 7.5 8.25 15.75 6 18l2.25-.75L16.5 9" />
             </svg>
           </a>`
        : "";

    const removeForm =
      config.checkoutUrl && config.csrfToken
        ? `<form method="post" action="${config.checkoutUrl}" class="inline-flex">
             <input type="hidden" name="csrfmiddlewaretoken" value="${escapeHtml(config.csrfToken)}">
             <input type="hidden" name="action" value="remove">
             <input type="hidden" name="entry_id" value="${escapeHtml(entry.id)}">
             <button type="submit" class="remove-btn inline-flex items-center gap-1 rounded-full px-3 py-1 font-semibold transition">
               Remove
               <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="h-4 w-4">
                 <path stroke-linecap="round" stroke-linejoin="round" d="M6 18 18 6M6 6l12 12" />
               </svg>
             </button>
           </form>`
        : "";

    const detailLink =
      entry.trip_slug && config.tripUrlTemplate
        ? `<a href="${buildTripUrl(config.tripUrlTemplate, entry.trip_slug || "")}"
               class="trip-details-link text-xs font-semibold uppercase tracking-wide">
             View trip details
           </a>`
        : "";

    const statusHtml = renderEntryStatus(entry, rewards);
    const optionsHtml = renderEntryOptions(entry, rewards);
    const hasRewardContent = (
      Boolean(entry.applied_reward) || (statusHtml && statusHtml.trim()) || (optionsHtml && optionsHtml.trim())
    );
    const rewardBoxClasses = [
      "checkout-trip-rewards",
      "rounded-3xl",
      "border",
      "border-border/60",
      "bg-background/50",
      "p-4",
    ];
    if (!hasRewardContent) {
      rewardBoxClasses.push("hidden");
    }

    const hasDiscount = Number(entry.discount_total_cents || 0) > 0;
    const discountPillClass = entry.applied_reward
      ? "inline-flex items-center gap-1 rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary"
      : "hidden inline-flex items-center gap-1 rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary";

    return `
      <article
        class="checkout-trip-card flex flex-col gap-5 p-6 sm:flex-row sm:items-start sm:justify-between sm:gap-6"
        data-entry
        data-entry-id="${escapeHtml(entry.id)}"
        data-trip-id="${escapeHtml(entry.trip_id)}"
        data-trip-slug="${escapeHtml(entry.trip_slug || "")}"
      >
        <div class="space-y-3">
          <h2 class="checkout-trip-title font-serif text-xl text-foreground">${tripTitle}</h2>
          <ul class="checkout-trip-meta text-sm text-muted-foreground">
            ${travelDate}
            ${travelerLabel}
          </ul>
          <div class="checkout-trip-actions flex flex-wrap gap-3 text-sm">
            ${editLink || ""}
            ${removeForm || ""}
          </div>
          <div class="${rewardBoxClasses.join(" ")}" data-entry-reward-box>
            <div class="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p class="trip-reward-label text-sm font-semibold text-foreground">Rewards</p>
                <p class="trip-reward-status text-xs text-muted-foreground" data-entry-reward-status>${statusHtml}</p>
              </div>
              <div class="flex flex-wrap items-center gap-2" data-entry-reward-actions>
                ${renderEntryRewardActions(entry)}
              </div>
            </div>
            <div class="mt-3 flex flex-wrap gap-2" data-entry-option-list>
              ${optionsHtml}
            </div>
          </div>
        </div>
        <div class="flex flex-col items-end gap-2">
          <span class="trip-price-chip rounded-full bg-primary/10 px-4 py-1 text-sm font-semibold text-primary" data-entry-total>${escapeHtml(
            currency
          )} ${escapeHtml(entry.grand_total_display || "")}</span>
          <span class="trip-price-original text-xs text-muted-foreground line-through ${hasDiscount ? "" : "hidden"}" data-entry-original>${escapeHtml(
            currency
          )} ${escapeHtml(entry.original_grand_total_display || "")}</span>
          <span class="${discountPillClass}" data-entry-discount-pill>
            ${entry.applied_reward ? `Saved ${escapeHtml(entry.applied_reward.discount_display || "")}` : ""}
          </span>
          ${detailLink || ""}
        </div>
      </article>
    `;
  }

  function renderEntriesHtml(summary, config) {
    const entries = Array.isArray(summary.entries) ? summary.entries : [];
    return entries.map((entry) => renderEntryCard(entry, summary, config)).join("");
  }

  function renderQuickAddServices(services) {
    if (!Array.isArray(services) || services.length === 0) {
      return `<p class="quick-add-empty mt-4 text-xs text-muted-foreground" data-quick-add-services-empty>No services available to add right now.</p>`;
    }
    const items = services
      .map(
        (service) => `
        <li class="quick-add-service-item flex items-center justify-between gap-3">
          <span class="quick-add-service-title text-sm font-medium text-foreground">${escapeHtml(service.title || "")}</span>
          <button
            type="button"
            class="quick-add-button inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-semibold transition"
            data-quick-add-trigger
            data-trip-id="${escapeHtml(service.id)}"
            data-trip-slug="${escapeHtml(service.slug || "")}"
          >
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4">
              <path fill-rule="evenodd" d="M10 3.5a.75.75 0 0 1 .75.75v5h5a.75.75 0 0 1 0 1.5h-5v5a.75.75 0 0 1-1.5 0v-5h-5a.75.75 0 0 1 0-1.5h5v-5A.75.75 0 0 1 10 3.5Z" clip-rule="evenodd" />
            </svg>
            Add
          </button>
        </li>
      `
      )
      .join("");
    return `<ul class="mt-4 space-y-3" data-quick-add-services-list>${items}</ul>`;
  }

  function renderQuickAddRecommendations(recommendations) {
    if (!Array.isArray(recommendations) || recommendations.length === 0) {
      return `<p class="quick-add-empty mt-4 text-xs text-muted-foreground" data-quick-add-recommendations-empty>We'll surface suggestions once you add a few trips to your list.</p>`;
    }
    const cards = recommendations.slice(0, 3).map((trip) => {
      const image = trip.image_url
        ? `<img src="${escapeHtml(trip.image_url)}" alt="" class="h-full w-full object-cover" loading="lazy" />`
        : `<div class="quick-add-card-placeholder flex h-full w-full items-center justify-center text-[0.65rem] font-semibold uppercase tracking-wide text-muted-foreground">No image</div>`;
      const tripUrl = tripUrlTemplate ? buildTripUrl(tripUrlTemplate, trip.slug || "") : "#";
      const slugPlain = String(trip.slug || "");
      const dateId = `checkout-quick-add-date-${slugPlain}`;
      const countId = `checkout-quick-add-count-${slugPlain}`;
      return `
        <article class="quick-add-card flex items-stretch gap-4">
          <div class="quick-add-card-media h-24 w-28 flex-none overflow-hidden rounded-xl">
            ${image}
          </div>
          <div class="flex flex-1 flex-col gap-3">
            <div class="space-y-1">
              <p class="quick-add-card-title text-sm font-semibold text-foreground">${escapeHtml(trip.title || "")}</p>
              <p class="quick-add-card-description text-xs text-muted-foreground">${escapeHtml(trip.description || "")}</p>
            </div>
            <div class="quick-add-card-meta flex flex-wrap items-center gap-2 text-xs font-semibold">
              <span class="quick-add-card-price">${escapeHtml(trip.price || "")}</span>
              <span class="quick-add-card-price-note text-[0.65rem] font-medium text-muted-foreground">Price per traveller</span>
              ${
                trip.duration
                  ? `<span class="quick-add-card-duration inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-[0.65rem] text-primary">${escapeHtml(
                      trip.duration
                    )}</span>`
                  : ""
              }
            </div>
            <div class="mt-auto flex flex-wrap items-center justify-end gap-2 text-xs">
              <div class="relative" data-quick-add-container>
                <button
                  type="button"
                  class="quick-add-button inline-flex items-center gap-1 rounded-full px-3 py-1 font-semibold transition"
                  data-quick-add-trigger
                  data-trip-slug="${escapeHtml(trip.slug || "")}"
                  aria-haspopup="dialog"
                  aria-expanded="false"
                >
                  Quick add
                </button>
                <div class="quick-add-popover absolute right-0 z-30 mt-2 hidden w-56 rounded-xl border border-border bg-card p-4 text-left shadow-subtle"
                     data-quick-add-popover
                     role="dialog"
                     aria-label="Quick add trip details"
                     data-state="closed">
                  <div class="space-y-3">
                    <div class="space-y-1">
                      <label for="${escapeHtml(dateId)}" class="text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-muted-foreground">Travel date</label>
                      <input
                        id="${escapeHtml(dateId)}"
                        type="date"
                        name="date"
                        class="w-full rounded-md border border-border/70 bg-background px-2.5 py-2 text-xs font-medium text-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                        data-quick-add-date
                      />
                    </div>
                    <div class="space-y-1">
                      <label for="${escapeHtml(countId)}" class="text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-muted-foreground">Travellers</label>
                      <div class="flex items-center gap-2">
                        <button type="button"
                                class="flex h-8 w-8 items-center justify-center rounded-full border border-border/70 text-xs font-semibold text-muted-foreground transition hover:text-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                                data-quick-add-step="down"
                                aria-label="Decrease travellers">
                          -
                        </button>
                        <input
                          id="${escapeHtml(countId)}"
                          type="number"
                          name="adults"
                          min="1"
                          max="16"
                          value="2"
                          class="h-8 w-12 rounded-md border border-border/70 bg-background text-center text-xs font-semibold text-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                          data-quick-add-count
                        />
                        <button type="button"
                                class="flex h-8 w-8 items-center justify-center rounded-full border border-border/70 text-xs font-semibold text-muted-foreground transition hover:text-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                                data-quick-add-step="up"
                                aria-label="Increase travellers">
                          +
                        </button>
                      </div>
                    </div>
                    <div class="flex items-center justify-end gap-2">
                      <button type="button"
                              class="inline-flex items-center rounded-md border border-border/60 px-2.5 py-1 text-[0.65rem] font-semibold text-muted-foreground transition hover:text-foreground focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                              data-quick-add-cancel>
                        Cancel
                      </button>
                      <button type="button"
                              class="inline-flex items-center rounded-md bg-primary px-2.5 py-1 text-[0.65rem] font-semibold text-primary-foreground transition hover:bg-primary/90 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary"
                              data-quick-add-confirm
                              data-trip-slug="${escapeHtml(trip.slug || "")}">
                        Add trip
                      </button>
                    </div>
                  </div>
                </div>
              </div>
              <a href="${tripUrl}"
                 class="quick-add-link inline-flex items-center gap-1 rounded-full px-3 py-1 font-semibold transition">
                See details
              </a>
            </div>
          </div>
        </article>
      `;
    }).join("");
    return `<div class="mt-4 space-y-4" data-quick-add-recommendations-list>${cards}</div>`;
  }

  function updateQuickAddPanels(payload = {}) {
    if (!quickAddRoot) return;
    closeAllQuickAddPopovers();
    activeQuickAddContainer = null;
    const servicesBody = quickAddRoot.querySelector("[data-quick-add-services-body]");
    const recommendationsBody = quickAddRoot.querySelector("[data-quick-add-recommendations-body]");
    if (servicesBody) {
      servicesBody.innerHTML = renderQuickAddServices(payload.services || []);
    }
    if (recommendationsBody) {
      recommendationsBody.innerHTML = renderQuickAddRecommendations(payload.recommendations || []);
    }
  }

  function updateEntry(entry, rewards) {
    if (!entriesContainer) return;
    const entryEl = entriesContainer.querySelector(`[data-entry-id="${entry.id}"]`);
    if (!entryEl) return;

    const totalEl = entryEl.querySelector("[data-entry-total]");
    const originalEl = entryEl.querySelector("[data-entry-original]");
    const pillEl = entryEl.querySelector("[data-entry-discount-pill]");
    const actionsEl = entryEl.querySelector("[data-entry-reward-actions]");
    const statusEl = entryEl.querySelector("[data-entry-reward-status]");
    const optionsEl = entryEl.querySelector("[data-entry-option-list]");
    const rewardBox = entryEl.querySelector("[data-entry-reward-box]");

    const currency = entry.currency || currentSummary.currency || root.dataset.currency || "";
    setText(totalEl, `${currency} ${entry.grand_total_display}`);

    if (originalEl) {
      const hasDiscount = Number(entry.discount_total_cents || 0) > 0;
      setText(originalEl, `${currency} ${entry.original_grand_total_display}`);
      originalEl.classList.toggle("hidden", !hasDiscount);
    }

    if (pillEl) {
      if (entry.applied_reward) {
        setText(pillEl, `Saved ${entry.applied_reward.discount_display}`);
        pillEl.classList.remove("hidden");
      } else {
        pillEl.classList.add("hidden");
        setText(pillEl, "");
      }
    }

    if (actionsEl) {
      if (entry.applied_reward) {
        actionsEl.innerHTML = `<button type="button"
                                        class="${REMOVE_CLASS}"
                                        data-action="remove-reward"
                                        data-entry-id="${escapeHtml(entry.id)}">
                                  Remove discount
                                </button>`;
      } else {
        actionsEl.innerHTML = "";
      }
    }

    if (statusEl) {
      if (entry.applied_reward) {
        statusEl.innerHTML = `Applied <span class="font-medium text-foreground">${escapeHtml(
          entry.applied_reward.phase_name || ""
        )}</span> · Saved ${escapeHtml(entry.applied_reward.discount_display || "")}`;
      } else {
        const unlocked = getTripPhases(entry, rewards)
          .filter(({ phase }) => phase.unlocked)
          .map(({ phase }) => phase.name)
          .filter(Boolean);
        if (unlocked.length) {
          statusEl.textContent = `Unlocked: ${unlocked.join(", ")} reward${unlocked.length === 1 ? "" : "s"} available.`;
        } else {
          statusEl.textContent = "";
        }
      }
    }

    if (optionsEl) {
      optionsEl.innerHTML = renderEntryOptions(entry, rewards);
    }

    if (rewardBox) {
      rewardBox.classList.toggle("border-primary/60", !!entry.applied_reward);
      rewardBox.classList.toggle("bg-primary/5", !!entry.applied_reward);
      const statusContent = statusEl ? statusEl.textContent.trim() || statusEl.innerHTML.trim() : "";
      const optionsContent = optionsEl ? optionsEl.textContent.trim() : "";
      const hasActions = actionsEl && actionsEl.childElementCount > 0;
      const shouldShow = Boolean(entry.applied_reward) || !!statusContent || !!optionsContent || hasActions;
      rewardBox.classList.toggle("hidden", !shouldShow);
    }
  }

  function updateEntries(summary) {
    if (!entriesContainer) return;
    const entries = Array.isArray(summary.entries) ? summary.entries : [];
    const existingIds = new Set(
      Array.from(entriesContainer.querySelectorAll("[data-entry-id]")).map((node) => node.dataset.entryId)
    );
    const summaryIds = new Set(entries.map((entry) => String(entry.id)));
    const shouldRebuild =
      entries.length !== existingIds.size ||
      entries.some((entry) => !existingIds.has(String(entry.id)));

    if (shouldRebuild) {
      const config = {
        currency: summary.currency || root.dataset.currency || "",
        csrfToken: getCsrfToken(),
        checkoutUrl,
        tripUrlTemplate,
      };
      entriesContainer.innerHTML = renderEntriesHtml(summary, config);
    } else {
      entries.forEach((entry) => updateEntry(entry, summary.rewards));
    }

    const hasEntries = entries.length > 0;
    entriesContainer.classList.toggle("hidden", !hasEntries);
    if (emptyStateEl) {
      emptyStateEl.classList.toggle("hidden", hasEntries);
    }
  }

  function updateSummaryCard(summary) {
    const currency = summary.currency || root.dataset.currency || "";
    setText(summaryCountEl, summary.count);
    if (summaryPreEl) setText(summaryPreEl, `${currency} ${summary.pre_discount_total_display}`);
    if (summaryDiscountEl) setText(summaryDiscountEl, `${currency} ${summary.discount_total_display}`);
    if (summaryTotalEl) setText(summaryTotalEl, `${currency} ${summary.total_display}`);
  }

  function updateRewardsUI(summary) {
    const rewards = summary.rewards || {};
    const phases = Array.isArray(rewards.phases) ? rewards.phases : [];
    const unlockedPhaseIds = Array.isArray(rewards.progress?.unlocked_phase_ids)
      ? rewards.progress.unlocked_phase_ids
      : [];
    const totalPhases = phases.length;
    const unlockedCount = unlockedPhaseIds.length;
    const entriesForRender = summary.entries || [];
    const progressHtml = renderProgressCard(rewards);

    if (progressContainer) {
      progressContainer.innerHTML = progressHtml;
    }
    if (mobileProgressContainer) {
      mobileProgressContainer.innerHTML = progressHtml;
    }
    if (badgeEl) {
      if (!totalPhases) {
        badgeEl.textContent = "No rewards yet";
      } else if (unlockedCount) {
        badgeEl.textContent = `${unlockedCount}/${totalPhases} unlocked`;
      } else {
        badgeEl.textContent = `${totalPhases} available`;
      }
    }
    if (mobileCountEl) {
      if (!totalPhases) {
        mobileCountEl.textContent = "No rewards yet";
      } else {
        mobileCountEl.textContent = `${unlockedCount}/${totalPhases} unlocked`;
      }
    }
    const phaseCardsHtml = renderPhaseCards(rewards, entriesForRender);
    if (phaseList) {
      phaseList.innerHTML = phaseCardsHtml;
    }
    if (mobilePhaseList) {
      mobilePhaseList.innerHTML = phaseCardsHtml;
    }
    if (mobileDetails) {
      const expandedState = mobileDetails.dataset.mobileExpanded === "true";
      setMobileExpanded(expandedState);
    }
    updateEntries(summary);
    updateSummaryCard(summary);
    root.dataset.currency = summary.currency || root.dataset.currency || "";
  }

  function highlightEntryByTripId(tripId) {
    if (!entriesContainer || !tripId) return;
    const entryEl = entriesContainer.querySelector(`[data-entry][data-trip-id="${tripId}"]`);
    if (!entryEl) return;

    entryEl.classList.add("ring-2", "ring-primary", "ring-offset-2");
    entryEl.scrollIntoView({ behavior: "smooth", block: "center" });
    setTimeout(() => {
      entryEl.classList.remove("ring-2", "ring-primary", "ring-offset-2");
    }, 1500);
  }

  function toggleBusy(button, state) {
    if (!button) return;
    button.disabled = !!state;
    button.dataset.loading = state ? "true" : "";
    if (state) {
      button.classList.add("opacity-70");
    } else {
      button.classList.remove("opacity-70");
    }
  }

  async function postJson(url, payload) {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrfToken(),
      },
      body: JSON.stringify(payload),
      credentials: "same-origin",
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      const message = data && data.error ? data.error : "Sorry, we couldn't update that reward.";
      throw new Error(message);
    }
    return data;
  }

  async function handleApply(button) {
    const entryId = button?.dataset?.entryId;
    const phaseId = button?.dataset?.phaseId;
    const tripId = button?.dataset?.tripId;
    if (!entryId || !phaseId || !tripId) return;
    const url = root.dataset.applyUrl;
    if (!url) return;

    toggleBusy(button, true);
    clearAlert();
    try {
      const payload = {
        entry_id: entryId,
        phase_id: Number(phaseId),
        trip_id: Number(tripId),
      };
      const data = await postJson(url, payload);
      if (data && data.cart_summary) {
        currentSummary = data.cart_summary;
        updateSummaryScript(currentSummary);
        updateRewardsUI(currentSummary);
        showAlert("Reward applied to your trip.", false);
      }
    } catch (error) {
      showAlert(error.message || "Unable to apply that reward right now.");
    } finally {
      toggleBusy(button, false);
    }
  }

  async function handleRemove(button) {
    const entryId = button?.dataset?.entryId;
    if (!entryId) return;
    const url = root.dataset.removeUrl;
    if (!url) return;

    toggleBusy(button, true);
    clearAlert();
    try {
      const data = await postJson(url, { entry_id: entryId });
      if (data && data.cart_summary) {
        currentSummary = data.cart_summary;
        updateSummaryScript(currentSummary);
        updateRewardsUI(currentSummary);
        showAlert("Reward removed from this trip.", false);
      }
    } catch (error) {
      showAlert(error.message || "Unable to remove that reward right now.");
    } finally {
      toggleBusy(button, false);
    }
  }

  async function handleQuickAdd(button, options = {}) {
    if (!quickAddRoot) return;
    const opts = options || {};
    const slug = button?.dataset?.tripSlug || opts.slug;
    if (!slug) return;
    if (!quickAddUrlTemplate) return;

    const url = fillSlug(quickAddUrlTemplate, slug);
    if (!url) return;

    const formData = new URLSearchParams();
    formData.append("csrfmiddlewaretoken", getCsrfToken());
    if (opts.date) {
      formData.append("date", opts.date);
    }
    if (opts.adults) {
      formData.append("adults", opts.adults);
    }

    const relatedTrigger =
      opts.relatedTrigger && opts.relatedTrigger !== button ? opts.relatedTrigger : null;
    toggleBusy(button, true);
    if (relatedTrigger) {
      toggleBusy(relatedTrigger, true);
    }
    clearAlert();
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          Accept: "application/json",
        },
        body: formData,
        credentials: "same-origin",
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const message = data && data.error ? data.error : "Unable to update your booking list.";
        throw new Error(message);
      }
      if (data && data.cart_summary) {
        currentSummary = data.cart_summary;
        updateSummaryScript(currentSummary);
        updateRewardsUI(currentSummary);
      }
      if (data && quickAddRoot) {
        updateQuickAddPanels({
          services: data.quick_add_services || [],
          recommendations: data.quick_add_recommendations || [],
        });
      }
      if (data && data.in_cart && data.trip_id) {
        highlightEntryByTripId(data.trip_id);
      }
      if (data && data.toast_message) {
        showAlert(data.toast_message, false);
      }
    } catch (error) {
      showAlert(error.message || "Unable to update your booking list right now.");
    } finally {
      toggleBusy(button, false);
      if (relatedTrigger) {
        toggleBusy(relatedTrigger, false);
      }
    }
  }

  function handlePhaseContainerClick(event) {
    if (event.target.closest("[data-quick-add-trigger]")) {
      return;
    }

    const viewLink = event.target.closest("[data-action='view-trip']");
    if (viewLink) {
      event.preventDefault();
      const slug = viewLink.getAttribute('data-trip-slug');
      if (slug && tripUrlTemplate) {
        window.location.href = buildTripUrl(tripUrlTemplate, slug);
      }
      return;
    }

    const toggle = event.target.closest("[data-reward-phase-toggle]");
    if (toggle) {
      event.preventDefault();
      const article = toggle.closest("[data-reward-phase]");
      if (article) {
        const body = article.querySelector("[data-reward-phase-body]");
        const chevron = toggle.querySelector("[data-chevron]");
        const isOpen = article.dataset.open === "true";
        article.dataset.open = isOpen ? "false" : "true";
        if (body) {
          if (isOpen) {
            body.classList.add("hidden");
          } else {
            body.classList.remove("hidden");
            requestAnimationFrame(() => ensureVisibleWithinPanel(body));
          }
        }
        if (chevron) {
          chevron.classList.toggle("rotate-180", !isOpen);
        }
      }
      return;
    }

    const tripTarget = event.target.closest("[data-reward-trip]");
    if (tripTarget) {
      event.preventDefault();
      const tripId = Number(tripTarget.dataset.tripId);
      if (tripId) {
        highlightEntryByTripId(tripId);
      }
    }
  }

  root.addEventListener("click", handlePhaseContainerClick);
  if (mobileDetails) {
    mobileDetails.addEventListener("click", handlePhaseContainerClick);
  }

  if (entriesContainer) {
    entriesContainer.addEventListener("click", (event) => {
      const applyBtn = event.target.closest("[data-action='apply-reward']");
      if (applyBtn) {
        event.preventDefault();
        handleApply(applyBtn);
        return;
      }
      const removeBtn = event.target.closest("[data-action='remove-reward']");
      if (removeBtn) {
        event.preventDefault();
        handleRemove(removeBtn);
      }
    });
  }

  document.addEventListener("click", (event) => {
    const confirmBtn = event.target.closest("[data-quick-add-confirm]");
    if (confirmBtn) {
      event.preventDefault();
      const container = confirmBtn.closest("[data-quick-add-container]");
      const relatedTrigger = container?.querySelector("[data-quick-add-trigger]") || null;
      const values = extractQuickAddValues(container);
      closeQuickAddPopover(container);
      handleQuickAdd(confirmBtn, {
        date: values.date,
        adults: values.adults,
        relatedTrigger,
      });
      return;
    }

    const cancelBtn = event.target.closest("[data-quick-add-cancel]");
    if (cancelBtn) {
      event.preventDefault();
      const container = cancelBtn.closest("[data-quick-add-container]");
      if (container) {
        closeQuickAddPopover(container);
        const trigger = container.querySelector("[data-quick-add-trigger]");
        if (trigger) {
          trigger.focus();
        }
      }
      return;
    }

    const stepBtn = event.target.closest("[data-quick-add-step]");
    if (stepBtn) {
      event.preventDefault();
      const container = stepBtn.closest("[data-quick-add-container]");
      if (container) {
        const direction = stepBtn.dataset.quickAddStep === "down" ? -1 : 1;
        stepTravelerCount(container, direction);
      }
      return;
    }

    const quickAddBtn = event.target.closest("[data-quick-add-trigger]");
    if (quickAddBtn) {
      event.preventDefault();
      const container = quickAddBtn.closest("[data-quick-add-container]");
      const popover = container?.querySelector("[data-quick-add-popover]");
      if (container && popover) {
        if (popover.dataset.state === "open") {
          closeQuickAddPopover(container);
        } else {
          openQuickAddPopover(container);
        }
      } else {
        handleQuickAdd(quickAddBtn);
      }
      return;
    }

    document.querySelectorAll("[data-quick-add-popover][data-state='open']").forEach((popover) => {
      const container = popover.closest("[data-quick-add-container]");
      if (container && !container.contains(event.target)) {
        closeQuickAddPopover(container);
      }
    });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    document.querySelectorAll("[data-quick-add-popover][data-state='open']").forEach((popover) => {
      const container = popover.closest("[data-quick-add-container]");
      if (container) {
        closeQuickAddPopover(container);
        const trigger = container.querySelector("[data-quick-add-trigger]");
        if (trigger) {
          trigger.focus();
        }
      }
    });
  });

  updateRewardsUI(currentSummary);
})();
