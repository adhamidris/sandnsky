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
  const alertBox = root.querySelector("[data-rewards-alert]");
  const progressColumn = root.querySelector("[data-reward-progress-column]");
  const phaseList = root.querySelector("[data-reward-phase-list]");

  const summaryCountEl = document.querySelector("[data-summary-count]");
  const summaryPreEl = document.querySelector("[data-summary-pre-discount]");
  const summaryDiscountEl = document.querySelector("[data-summary-discount]");
  const summaryTotalEl = document.querySelector("[data-summary-total]");

  const APPLY_CLASS = "inline-flex items-center gap-1 rounded-full border border-primary/40 bg-background px-3 py-1 text-xs font-semibold text-primary transition hover:bg-primary/10";
  const LOCKED_CLASS = "inline-flex items-center gap-1 rounded-full border border-dashed border-muted px-3 py-1 text-xs font-semibold text-muted-foreground";
  const REMOVE_CLASS = "inline-flex items-center gap-1 rounded-full border border-destructive/40 px-3 py-1 text-xs font-semibold text-destructive transition hover:bg-destructive/10";

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

  function showAlert(message, isError = true) {
    if (!alertBox) return;
    alertBox.textContent = message;
    alertBox.classList.toggle("hidden", false);
    alertBox.classList.toggle("border-destructive/40", isError);
    alertBox.classList.toggle("bg-destructive/10", isError);
    alertBox.classList.toggle("text-destructive", isError);
    alertBox.classList.toggle("border-primary/40", !isError);
    alertBox.classList.toggle("bg-primary/10", !isError);
    alertBox.classList.toggle("text-primary", !isError);
  }

  function clearAlert() {
    if (!alertBox) return;
    alertBox.textContent = "";
    alertBox.classList.add("hidden");
    alertBox.classList.remove("border-primary/40", "bg-primary/10", "text-primary");
    alertBox.classList.add("border-destructive/40", "bg-destructive/10", "text-destructive");
  }

  function renderProgressCard(rewards) {
    const phases = Array.isArray(rewards?.phases) ? rewards.phases : [];
    const progress = rewards?.progress || {};
    const totalCents = Number(progress.total_cents || 0);
    const unlockedIds = Array.isArray(progress.unlocked_phase_ids) ? progress.unlocked_phase_ids : [];
    const nextPhaseId = progress.next_phase_id;
    const remainingDisplay = progress.remaining_to_next_display || "";
    const currency = progress.currency || currentSummary.currency || root.dataset.currency || "";
    const totalDisplay = progress.total_display || "0.00";

    const howItWorksHtml = `
      <div class="rounded-3xl border border-primary/30 bg-gradient-to-br from-primary/10 via-primary/5 to-transparent p-5 text-sm text-muted-foreground">
        <h3 class="text-base font-semibold text-foreground">How it works</h3>
        <ul class="mt-3 space-y-2">
          <li class="flex items-start gap-2"><span class="mt-0.5 h-2 w-2 rounded-full bg-primary"></span><span>Reach each threshold to unlock a new phase of curated trips.</span></li>
          <li class="flex items-start gap-2"><span class="mt-0.5 h-2 w-2 rounded-full bg-primary"></span><span>Apply the reward to one eligible trip and everyone in your group receives the discount.</span></li>
          <li class="flex items-start gap-2"><span class="mt-0.5 h-2 w-2 rounded-full bg-primary"></span><span>Progressive rewards stack, so higher tiers keep the earlier perks.</span></li>
        </ul>
      </div>
    `;

    if (!phases.length) {
      return `
        <div class="rounded-3xl border border-border bg-background/60 p-5 text-sm text-muted-foreground">
          <p class="font-semibold text-foreground">Rewards configuration coming soon.</p>
          <p class="mt-2">Add reward phases in the admin to unlock progressive savings during checkout.</p>
        </div>
        ${howItWorksHtml}
      `;
    }

    const thresholds = phases.map((phase) => Number(phase.threshold_amount_cents || 0));
    const maxThreshold = Math.max(1, ...thresholds, 1);
    const rawProgressPercent = (totalCents / maxThreshold) * 100;
    const progressPercent = Math.min(100, Math.max(0, rawProgressPercent));
    const progressPercentStr = Number(progressPercent.toFixed(3)).toString();

    const dotHtml = phases
      .map((phase) => {
        const percent = Math.min(
          100,
          Math.max(0, ((Number(phase.threshold_amount_cents || 0) / maxThreshold) * 100))
        );
        const percentStr = Number(percent.toFixed(3)).toString();
        const unlocked = phase.unlocked;
        return `
          <div class="absolute top-1/2 -translate-y-1/2 -translate-x-1/2"
               style="left: ${percentStr}%;"
               data-reward-progress-marker
               data-phase-id="${escapeHtml(phase.id)}">
            <span class="block h-3 w-3 rounded-full border-2 ${unlocked ? "border-primary bg-primary" : "border-muted bg-background"}"></span>
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
        const unlocked = phase.unlocked;
        return `
          <div class="absolute left-0 -translate-x-1/2"
               style="left: ${percentStr}%;"
               data-reward-progress-label
               data-phase-id="${escapeHtml(phase.id)}">
            <span class="block font-semibold uppercase tracking-wide ${unlocked ? "text-foreground" : "text-muted-foreground"}">Phase ${escapeHtml(index + 1)}</span>
            <span class="block text-muted-foreground">${escapeHtml(phase.threshold_amount_display || "")}</span>
          </div>
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
    const unlockedCopy = unlockedCount
      ? `${escapeHtml(unlockedCount)} of ${escapeHtml(phases.length)} active phase${phases.length === 1 ? "" : "s"} unlocked.`
      : "Add a little more to begin unlocking 50% off rewards.";

    const progressCard = `
      <div class="rounded-3xl border border-border bg-background/60 p-5">
        <div class="space-y-5">
          <div class="flex flex-col gap-2 sm:flex-row sm:items-baseline sm:justify-between">
            <div>
              <p class="text-xs uppercase tracking-wide text-muted-foreground">Current cart total</p>
              <p class="font-serif text-3xl text-foreground">${escapeHtml(currency)} ${escapeHtml(totalDisplay)}</p>
            </div>
            <div class="text-sm text-muted-foreground sm:max-w-xs">${nextPhaseMessage}</div>
          </div>
          <div>
            <div class="relative">
              <div class="relative h-2 w-full rounded-full bg-muted"
                   data-reward-progress-track
                   data-total-cents="${escapeHtml(totalCents)}"
                   data-max-threshold="${escapeHtml(maxThreshold)}">
                <div class="absolute left-0 top-0 h-full rounded-full bg-primary transition-all"
                     style="width: ${progressPercentStr}%;"
                     data-reward-progress-fill></div>
                ${dotHtml}
              </div>
              <div class="pointer-events-none relative mt-6 h-12 text-center text-[0.65rem] text-muted-foreground">
                ${labelHtml}
              </div>
            </div>
          </div>
          <div class="rounded-2xl bg-primary/10 p-3 text-xs text-primary">
            <p class="font-semibold">Unlocked phases:</p>
            <p class="mt-1">${unlockedCopy}</p>
          </div>
        </div>
      </div>
    `;

    return `${progressCard}${howItWorksHtml}`;
  }

  function renderPhaseCards(rewards, entries) {
    const phases = Array.isArray(rewards?.phases) ? rewards.phases : [];
    const entriesById = new Map();
    (entries || []).forEach((entry) => {
      if (entry && entry.id !== undefined) {
        entriesById.set(String(entry.id), entry);
      }
    });

    return phases
      .map((phase, index) => {
        const unlocked = !!phase.unlocked;
        const appliedTitles = Array.isArray(phase.applied_entry_ids)
          ? phase.applied_entry_ids
              .map((entryId) => entriesById.get(String(entryId)))
              .filter(Boolean)
              .map((entry) => `<li>${escapeHtml(entry.trip_title || "")}</li>`)
          : [];

        const tripButtons = Array.isArray(phase.trip_options)
          ? phase.trip_options
              .map((trip) => {
                const disabled = unlocked ? "" : " disabled";
                const pointer = unlocked ? "" : " pointer-events-none";
                const image = trip.card_image_url
                  ? `<img src="${escapeHtml(trip.card_image_url)}" alt="${escapeHtml(trip.title || "")}" class="h-24 w-full object-cover transition group-hover:scale-105" />`
                  : `<div class="flex h-24 w-full items-center justify-center bg-muted text-xs font-semibold uppercase tracking-wide text-muted-foreground">No image</div>`;
                return `
                  <button type="button"
                          class="group relative overflow-hidden rounded-2xl border border-border bg-background text-left transition focus:outline-none focus:ring-2 focus:ring-primary${pointer}"
                          data-reward-trip
                          data-phase-id="${escapeHtml(phase.id)}"
                          data-trip-id="${escapeHtml(trip.trip_id)}"${disabled}>
                    ${image}
                    <div class="p-3">
                      <p class="text-xs font-semibold text-foreground">${escapeHtml(trip.title || "")}</p>
                    </div>
                  </button>
                `;
              })
              .join("")
          : "";

        const appliedBlock = appliedTitles.length
          ? `
            <div class="mt-4 rounded-2xl bg-primary/10 p-3 text-xs text-primary" data-phase-applied-target>
              <p class="font-semibold">Applied to:</p>
              <ul class="mt-1 space-y-1">${appliedTitles.join("")}</ul>
            </div>
          `
          : "";

        const statusBadge = unlocked
          ? `
            <span class="inline-flex items-center gap-1 rounded-full bg-primary/10 px-3 py-1 text-primary">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-3.5 w-3.5">
                <path fill-rule="evenodd" d="M16.704 5.29a1 1 0 0 1 0 1.414l-6.764 6.764a1 1 0 0 1-1.414 0l-3.53-3.53a1 1 0 0 1 1.414-1.414l2.823 2.823 6.057-6.057a1 1 0 0 1 1.414 0Z" clip-rule="evenodd" />
              </svg>
              Unlocked
            </span>
          `
          : `
            <span class="inline-flex items-center gap-1 rounded-full bg-muted px-3 py-1 text-muted-foreground">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" class="h-3.5 w-3.5">
                <path d="M10 2a5 5 0 0 1 5 5v2h1a1 1 0 0 1 0 2h-1v4a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3V11H4a1 1 0 1 1 0-2h1V7a5 5 0 0 1 5-5Zm-3 7h6V7a3 3 0 1 0-6 0v2Z" />
              </svg>
              Locked
            </span>
          `;

        const summaryCopy = phase.headline
          ? `<p class="mt-2 text-sm font-medium text-foreground">${escapeHtml(phase.headline)}</p>`
          : phase.description
          ? `<p class="mt-2 text-sm text-muted-foreground">${escapeHtml(phase.description)}</p>`
          : "";

        return `
          <article class="rounded-3xl border border-border bg-background/80 p-5 transition${unlocked ? "" : " opacity-50"}"
                   data-reward-phase
                   data-phase-id="${escapeHtml(phase.id)}"
                   data-phase-unlocked="${unlocked ? "true" : "false"}">
            <div class="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
              <div>
                <p class="text-xs uppercase tracking-wide text-muted-foreground">Phase ${escapeHtml(index + 1)}</p>
                <h3 class="font-serif text-xl text-foreground">${escapeHtml(phase.name || "")}</h3>
                <p class="text-sm text-muted-foreground">Unlock at ${escapeHtml(phase.currency || "")} ${escapeHtml(
          phase.threshold_amount_display || ""
        )} · ${escapeHtml(Number(phase.discount_percent || 0).toFixed(0))}% off</p>
              </div>
              <div class="flex items-center gap-2 text-xs font-semibold">${statusBadge}</div>
            </div>
            ${summaryCopy}
            <div class="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3" data-reward-phase-trips>
              ${tripButtons}
            </div>
            ${appliedBlock}
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
      return `<span class="text-xs text-muted-foreground">No rewards available for this trip yet.</span>`;
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
          statusEl.textContent = "No reward applied yet. Choose an unlocked phase below.";
        }
      }
    }

    if (optionsEl) {
      optionsEl.innerHTML = renderEntryOptions(entry, rewards);
    }

    if (rewardBox) {
      rewardBox.classList.toggle("border-primary/60", !!entry.applied_reward);
      rewardBox.classList.toggle("bg-primary/5", !!entry.applied_reward);
    }
  }

  function updateEntries(summary) {
    (summary.entries || []).forEach((entry) => updateEntry(entry, summary.rewards));
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
    if (progressColumn) {
      progressColumn.innerHTML = renderProgressCard(rewards);
    }
    if (phaseList) {
      phaseList.innerHTML = renderPhaseCards(rewards, summary.entries || []);
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
        updateRewardsUI(currentSummary);
        showAlert("Reward removed from this trip.", false);
      }
    } catch (error) {
      showAlert(error.message || "Unable to remove that reward right now.");
    } finally {
      toggleBusy(button, false);
    }
  }

  root.addEventListener("click", (event) => {
    const target = event.target.closest("[data-reward-trip]");
    if (!target) return;
    event.preventDefault();
    const tripId = Number(target.dataset.tripId);
    if (tripId) {
      highlightEntryByTripId(tripId);
    }
  });

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

  updateRewardsUI(currentSummary);
})();
