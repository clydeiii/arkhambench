const CARD_IMAGE_BASE = "https://arkhamdb.com/bundles/cards/";

const state = {
  index: [],
  run: null,
  currentRunName: "",
  stepIndex: 0,
  suppressHash: false,
};

const el = {
  runSelect: document.querySelector("#run-select"),
  first: document.querySelector("#first-step"),
  prev: document.querySelector("#prev-step"),
  next: document.querySelector("#next-step"),
  last: document.querySelector("#last-step"),
  stepLabel: document.querySelector("#step-label"),
  roundSelect: document.querySelector("#round-select"),
  slider: document.querySelector("#step-slider"),
  status: document.querySelector("#status-line"),
  map: document.querySelector("#location-map"),
  scenario: document.querySelector("#scenario-content"),
  events: document.querySelector("#event-ticker"),
  skillTest: document.querySelector("#skill-test"),
  decision: document.querySelector("#decision-content"),
  player: document.querySelector("#player-board"),
  modalBackdrop: document.querySelector("#modal-backdrop"),
  modalTitle: document.querySelector("#modal-title"),
  modalBody: document.querySelector("#modal-body"),
  modalClose: document.querySelector("#modal-close"),
};

const fixedPositions = {
  study: [50, 50],
  hallway: [50, 50],
  attic: [50, 17],
  cellar: [28, 76],
  parlor: [78, 50],
};

// Return to The Gathering: Study and Hallway coexist, plus five new rooms —
// laid out as the house deepens left-to-right (entry -> guest wing -> beyond
// the wall -> the impossible places).
const returnPositions = {
  study: [8, 50],
  guest_hall: [26, 50],
  bedroom: [22, 16],
  bathroom: [22, 84],
  hallway: [46, 50],
  parlor: [66, 50],
  attic: [60, 16],
  cellar: [60, 84],
  field_of_graves: [84, 14],
  ghoul_pits: [84, 86],
};

function scenarioPositions() {
  return String(state.run?.meta?.scenario || "") === "return_to_the_gathering" ? returnPositions : fixedPositions;
}

init().catch((error) => {
  document.body.innerHTML = `<main class="fatal">Unable to load viewer data: ${escapeHtml(error.message)}</main>`;
});

async function init() {
  state.index = await fetchJson("data/index.json");
  populateRunSelect();
  bindControls();

  const hash = readHash();
  const selected = findRun(hash.run) || state.index[0];
  if (!selected) {
    throw new Error("viewer/data/index.json contains no runs");
  }
  await loadRun(selected.name, hash.step || 0);
}

async function fetchJson(path) {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`${path} returned ${response.status}`);
  }
  return response.json();
}

function populateRunSelect() {
  el.runSelect.innerHTML = "";
  for (const row of state.index) {
    const option = document.createElement("option");
    option.value = row.name;
    option.textContent = `${row.name} | seed ${row.seed ?? "?"} | ${row.steps} steps`;
    el.runSelect.append(option);
  }
}

function bindControls() {
  el.runSelect.addEventListener("change", () => loadRun(el.runSelect.value, 0));
  el.first.addEventListener("click", () => setStep(0));
  el.prev.addEventListener("click", () => setStep(state.stepIndex - 1));
  el.next.addEventListener("click", () => setStep(state.stepIndex + 1));
  el.last.addEventListener("click", () => setStep(maxStep()));
  el.slider.addEventListener("input", () => setStep(Number(el.slider.value)));
  el.roundSelect.addEventListener("change", () => setStep(Number(el.roundSelect.value)));
  el.modalClose.addEventListener("click", closeModal);
  el.modalBackdrop.addEventListener("click", (event) => {
    if (event.target === el.modalBackdrop) closeModal();
  });
  document.addEventListener("keydown", (event) => {
    if (!el.modalBackdrop.hidden && event.key === "Escape") {
      closeModal();
      return;
    }
    if (event.target && ["INPUT", "SELECT", "TEXTAREA"].includes(event.target.tagName)) {
      return;
    }
    if (event.key === "ArrowLeft") setStep(state.stepIndex - 1);
    if (event.key === "ArrowRight") setStep(state.stepIndex + 1);
  });
  window.addEventListener("hashchange", async () => {
    if (state.suppressHash) return;
    const hash = readHash();
    if (hash.run && hash.run !== state.currentRunName) {
      await loadRun(hash.run, hash.step || 0);
    } else {
      setStep(hash.step || 0, { updateHash: false });
    }
  });
}

async function loadRun(name, requestedStep) {
  const row = findRun(name);
  if (!row) return;
  state.currentRunName = row.name;
  state.run = await fetchJson(`data/${row.file}`);
  el.runSelect.value = row.name;
  populateRoundSelect();
  setStep(requestedStep, { updateHash: true });
}

function populateRoundSelect() {
  el.roundSelect.innerHTML = "";
  const seen = new Set();
  state.run.steps.forEach((step, index) => {
    if (seen.has(step.round)) return;
    seen.add(step.round);
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = String(step.round);
    el.roundSelect.append(option);
  });
}

function findRun(name) {
  return state.index.find((row) => row.name === name || row.file === name);
}

function readHash() {
  const params = new URLSearchParams(location.hash.replace(/^#/, ""));
  return {
    run: params.get("run") || "",
    step: Number(params.get("step") || 0),
  };
}

function writeHash() {
  const params = new URLSearchParams();
  params.set("run", state.currentRunName);
  params.set("step", String(state.stepIndex));
  state.suppressHash = true;
  history.replaceState(null, "", `#${params.toString()}`);
  state.suppressHash = false;
}

function maxStep() {
  return Math.max(0, (state.run?.steps.length || 1) - 1);
}

function setStep(index, options = {}) {
  if (!state.run) return;
  const next = clamp(Number.isFinite(index) ? index : 0, 0, maxStep());
  state.stepIndex = next;
  render();
  if (options.updateHash !== false) writeHash();
}

function render() {
  const step = currentStep();
  const prev = previousStep();
  el.stepLabel.textContent = `step ${state.stepIndex + 1}/${state.run.steps.length}`;
  el.slider.max = String(maxStep());
  el.slider.value = String(state.stepIndex);
  el.status.textContent = step.status || "";
  setRoundSelect(step.round);
  renderMap(step, prev);
  renderScenario(step, prev);
  renderEvents(step);
  renderSkillTest(step);
  renderDecision(step);
  renderPlayer(step, prev);
  el.first.disabled = state.stepIndex === 0;
  el.prev.disabled = state.stepIndex === 0;
  el.next.disabled = state.stepIndex === maxStep();
  el.last.disabled = state.stepIndex === maxStep();
}

function currentStep() {
  return state.run.steps[state.stepIndex];
}

function previousStep() {
  return state.stepIndex > 0 ? state.run.steps[state.stepIndex - 1] : null;
}

function setRoundSelect(round) {
  for (const option of el.roundSelect.options) {
    const optionStep = state.run.steps[Number(option.value)];
    if (optionStep?.round === round) {
      el.roundSelect.value = option.value;
      return;
    }
  }
}

function renderMap(step, prev) {
  const snapshot = step.state;
  const locations = snapshot.locations || {};
  const positions = mapPositions(Object.keys(locations));
  el.map.innerHTML = "";

  // preserveAspectRatio=none makes viewBox percent coords track the CSS
  // percent positions of the absolutely-positioned nodes exactly.
  const svg = svgEl("svg", { viewBox: "0 0 100 100", preserveAspectRatio: "none", class: "map-lines", "aria-hidden": "true" });
  const drawn = new Set();
  for (const location of Object.values(locations)) {
    for (const targetId of location.connections || []) {
      if (!locations[targetId]) continue;
      const key = [location.id, targetId].sort().join("|");
      if (drawn.has(key)) continue;
      drawn.add(key);
      const [x1, y1] = positions[location.id];
      const [x2, y2] = positions[targetId];
      svg.append(svgEl("line", { x1, y1, x2, y2 }));
    }
  }
  el.map.append(svg);

  for (const location of Object.values(locations)) {
    const [x, y] = positions[location.id];
    const node = document.createElement("button");
    node.type = "button";
    node.className = `location-node ${location.revealed ? "revealed" : "unrevealed"} ${changedLocation(prev, location.id) ? "flash" : ""}`;
    node.style.left = `${x}%`;
    node.style.top = `${y}%`;
    node.addEventListener("click", () => openEntityModal(resolveLocation(location.id, snapshot)));

    const card = cardByCode(location.code);
    node.innerHTML = `
      <span class="loc-name">${escapeHtml(location.name || card.name || location.id)}</span>
      <span class="loc-line">shroud <b>${location.revealed ? location.shroud ?? "?" : "?"}</b> | clues <b>${location.clues ?? 0}</b>${card.victory ? ` | VP <b>${card.victory}</b>` : ""}</span>
    `;

    // Location card art: revealed side normally, card back while unrevealed.
    const art = document.createElement("img");
    art.className = "loc-art";
    art.alt = location.name || location.code;
    art.loading = "lazy";
    setCardImage(art, location.code, () => art.classList.add("hidden-art"), !location.revealed);
    node.prepend(art);

    const chips = document.createElement("span");
    chips.className = "loc-chips";
    for (const id of location.attached_instance_ids || []) {
      chips.append(cardThumb(id, snapshot, { chip: true, labelPrefix: "attached" }));
    }
    for (const enemyId of enemyIdsAtLocation(location.id, snapshot)) {
      chips.append(enemyChip(enemyId, snapshot));
    }
    if ((location.investigator_ids || []).includes(snapshot.investigator?.id)) {
      const marker = document.createElement("span");
      marker.className = "investigator-marker";
      marker.textContent = snapshot.investigator.name || "Investigator";
      chips.append(marker);
    }
    node.append(chips);
    el.map.append(node);
  }
}

function mapPositions(ids) {
  const result = {};
  const fixed = scenarioPositions();
  const unknown = ids.filter((id) => !fixed[id]);
  ids.forEach((id) => {
    result[id] = fixed[id] ? [...fixed[id]] : [50, 50];
  });
  unknown.forEach((id, index) => {
    const angle = (Math.PI * 2 * index) / Math.max(unknown.length, 1);
    result[id] = [50 + Math.cos(angle) * 36, 50 + Math.sin(angle) * 34];
  });
  return result;
}

function changedLocation(prev, id) {
  if (!prev) return false;
  const before = prev.state.locations?.[id];
  const after = currentStep().state.locations?.[id];
  return JSON.stringify(before || null) !== JSON.stringify(after || null);
}

function enemyIdsAtLocation(locationId, snapshot) {
  const ids = new Set();
  const location = snapshot.locations?.[locationId];
  for (const id of location?.enemy_ids || []) ids.add(id);
  const investigator = snapshot.investigator || {};
  for (const [id, enemy] of Object.entries(snapshot.enemies || {})) {
    if (enemy.location_id === locationId) ids.add(id);
    if (enemy.engaged_with === investigator.id && investigator.location_id === locationId) ids.add(id);
  }
  return [...ids];
}

function enemyChip(enemyId, snapshot) {
  const enemy = snapshot.enemies?.[enemyId];
  const card = cardByCode(enemy?.card_code);
  const button = document.createElement("button");
  button.type = "button";
  button.className = `enemy-chip ${enemy?.engaged_with ? "engaged" : ""} ${enemy?.exhausted ? "exhausted" : ""}`;
  button.textContent = `${card.name || enemyId} dmg ${enemy?.damage || 0}`;
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    openEntityModal(resolveEnemy(enemyId, snapshot));
  });
  return button;
}

function renderScenario(step, prev) {
  const snapshot = step.state;
  const agenda = snapshot.agenda || {};
  const act = snapshot.act || {};
  const victory = snapshot.victory_display || [];
  el.scenario.innerHTML = "";
  const rows = [
    scenarioCardArt("agenda", agenda, prev),
    panelButton("agenda", `${agenda.name || "Agenda"} ${agenda.doom ?? 0}/${agenda.threshold ?? "?"} doom`, () =>
      openEntityModal(resolveCode(agenda.code, "Agenda"))
    ),
    scenarioCardArt("act", act, prev),
    panelButton("act", `${act.name || "Act"}${act.clues_required != null ? ` | ${act.clues_required} clues` : ""}`, () =>
      openEntityModal(resolveCode(act.code, "Act"))
    ),
    tokenBlock(snapshot.chaos_bag?.tokens || []),
    scenarioReferenceCard(),
    panelButton("victory", `victory display ${victory.length}`, () => openPile("Victory Display", victory, snapshot)),
    countLine("encounter deck", snapshot.encounter_deck_count ?? snapshot.encounter_deck?.length ?? 0, prev, "encounter_deck_count"),
    panelButton("encounter discard", `encounter discard ${(snapshot.encounter_discard || []).length}`, () =>
      openPile("Encounter Discard", snapshot.encounter_discard || [], snapshot)
    )
  ];
  el.scenario.append(...rows.filter(Boolean));
}

function scenarioCardArt(kind, cardState, prev) {
  // Agenda/act card art (landscape cards on arkhamdb); click for the modal.
  const button = document.createElement("button");
  button.type = "button";
  const prevCode = prev?.state?.[kind]?.code;
  button.className = `scenario-art ${prevCode && prevCode !== cardState.code ? "flash" : ""}`;
  button.title = cardState.name || kind;
  const img = document.createElement("img");
  img.alt = cardState.name || kind;
  img.loading = "lazy";
  setCardImage(img, cardState.code, () => button.classList.add("hidden-art"));
  button.append(img);
  button.addEventListener("click", () => openEntityModal(resolveCode(cardState.code, cardState.name || kind)));
  return button;
}

function panelButton(label, text, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "panel-row";
  button.innerHTML = `<span>${escapeHtml(label)}</span><b>${escapeHtml(text)}</b>`;
  button.addEventListener("click", onClick);
  return button;
}

function countLine(label, value, prev, path) {
  const row = document.createElement("div");
  const fullPath = `state.${path}`;
  row.className = `panel-row static ${changedValue(prev, fullPath, value) ? "flash" : ""}`;
  row.innerHTML = `<span>${escapeHtml(label)}</span><b>${escapeHtml(String(value))}</b>`;
  return row;
}

function tokenBlock(tokens) {
  const wrap = document.createElement("div");
  wrap.className = "chaos-block";
  const title = document.createElement("div");
  title.className = "mini-title";
  title.textContent = `chaos bag (${tokens.length} tokens)`;
  const list = document.createElement("div");
  list.className = "token-list";
  for (const token of tokens) {
    const chip = document.createElement("span");
    chip.className = "chaos-token";
    chip.textContent = token;
    list.append(chip);
  }
  wrap.append(title, list);
  return wrap;
}

function scenarioReferenceCard() {
  const code = state.run?.meta?.scenario_card;
  if (!code) return null;
  const difficulty = String(state.run?.meta?.difficulty || "").toLowerCase();
  const usesBack = difficulty === "hard" || difficulty === "expert";
  const card = cardByCode(code);
  const wrap = document.createElement("div");
  wrap.className = "token-reference";

  const label = document.createElement("div");
  label.className = "mini-title";
  label.textContent = "token effects";

  const button = codeThumb(code, {
    className: "token-reference-thumb",
    imageBack: usesBack,
    title: card.name || "Token effects",
  });

  const note = document.createElement("div");
  note.className = "token-reference-note";
  note.textContent = usesBack ? "Hard/Expert side applies" : "Easy/Standard side applies";

  wrap.append(label, button, note);
  return wrap;
}

function renderEvents(step) {
  el.events.innerHTML = "";
  const snapshot = step.state;
  const events = step.events || [];
  if (!events.length) {
    el.events.textContent = "No events since previous step.";
    return;
  }
  for (const event of events) {
    const line = document.createElement("div");
    line.className = "event-line";
    const message = replaceInstanceTokens(event.message || JSON.stringify(event), snapshot);
    line.innerHTML = `<span>${escapeHtml(event.type || "event")}</span> ${escapeHtml(message)}`;
    el.events.append(line);
  }
}

function renderSkillTest(step) {
  const test = step.state.active_skill_test;
  el.skillTest.hidden = !test;
  el.skillTest.innerHTML = "";
  if (!test) return;
  const committed = test.committed?.length
    ? test.committed.map((id) => instanceDisplayName(id, step.state) || id).join(", ")
    : "none";
  el.skillTest.innerHTML = `
    <b>${escapeHtml(test.skill || "skill")} test</b>
    <span>base ${escapeHtml(String(test.base ?? "?"))}</span>
    <span>difficulty ${escapeHtml(String(test.difficulty ?? "?"))}</span>
    <span>modifier ${escapeHtml(String(test.modifier ?? 0))}</span>
    <span>token ${escapeHtml(test.token ?? "not revealed")}</span>
    <span>committed ${escapeHtml(committed)}</span>
  `;
}

function renderDecision(step) {
  el.decision.innerHTML = "";
  const snapshot = step.state;
  if (!step.decision) {
    const done = document.createElement("div");
    done.className = "no-decision";
    done.textContent = "No pending decision.";
    el.decision.append(done);
    if (state.run.result) {
      el.decision.append(resultBlock(state.run.result));
    }
    return;
  }
  const prompt = document.createElement("div");
  prompt.className = "decision-prompt";
  prompt.textContent = replaceInstanceTokens(step.decision.prompt, snapshot);
  const list = document.createElement("ol");
  list.className = "decision-options";
  step.decision.options.forEach((option, index) => {
    const number = index + 1;
    const item = document.createElement("li");
    const chosen = step.decision.chosen === number;
    item.className = chosen ? "chosen" : "declined";
    item.textContent = replaceInstanceTokens(option, snapshot);
    if (chosen) {
      const mark = document.createElement("span");
      mark.className = "check";
      mark.textContent = " chosen";
      item.append(mark);
    }
    list.append(item);
  });
  el.decision.append(prompt, list);
}

function resultBlock(result) {
  const wrap = document.createElement("div");
  wrap.className = "result-block";
  const summary = result.summary || result.outcome || "Game complete";
  wrap.innerHTML = `
    <h3>Result: ${escapeHtml(summary)}</h3>
    <div class="result-grid">
      <span>outcome <b>${escapeHtml(result.outcome ?? result.resolution ?? "?")}</b></span>
      <span>xp <b>${escapeHtml(String(result.xp ?? "?"))}</b></span>
      <span>trauma <b>${escapeHtml(JSON.stringify(result.trauma || {}))}</b></span>
      <span>score <b>${escapeHtml(String(result.score ?? "?"))}</b></span>
    </div>
    <pre>${escapeHtml(JSON.stringify(result.campaign_log || {}, null, 2))}</pre>
  `;
  return wrap;
}

function renderPlayer(step, prev) {
  const snapshot = step.state;
  const investigator = snapshot.investigator || {};
  el.player.innerHTML = "";
  const summary = document.createElement("div");
  summary.className = "player-summary";

  if (investigator.card_code) {
    const investigatorCard = codeThumb(investigator.card_code, {
      className: "investigator-card",
      title: investigator.name || "Investigator",
    });
    summary.append(investigatorCard);
  }

  const summaryLines = document.createElement("div");
  summaryLines.className = "player-summary-lines";

  const stats = document.createElement("div");
  stats.className = "player-stats";
  stats.append(
    statPill(
      investigator.name || "Investigator",
      `${investigator.damage ?? 0}/${investigator.health ?? "?"} dmg`,
      prev,
      "state.investigator.damage",
      investigator.damage ?? 0
    ),
    statPill(
      "horror",
      `${investigator.horror ?? 0}/${investigator.sanity ?? "?"}`,
      prev,
      "state.investigator.horror",
      investigator.horror ?? 0
    ),
    statPill("res", investigator.resources ?? 0, prev, "state.investigator.resources"),
    statPill("clues", investigator.clues ?? 0, prev, "state.investigator.clues"),
    statPill(
      "actions",
      `${investigator.actions_remaining ?? 0}/3`,
      prev,
      "state.investigator.actions_remaining",
      investigator.actions_remaining ?? 0
    ),
    statPill("W/I/C/A", `${investigator.willpower}/${investigator.intellect}/${investigator.combat}/${investigator.agility}`)
  );

  const counts = document.createElement("div");
  counts.className = "pile-counts";
  counts.append(
    pileCount("deck", investigator.deck_count ?? 0),
    pileCount("discard", (investigator.discard || []).length, () => openPile("Player Discard", investigator.discard || [], snapshot), prev, "state.investigator.discard.length")
  );
  summaryLines.append(stats, counts);
  summary.append(summaryLines);

  const play = zoneSection("play area", investigator.play_area || [], snapshot, prev, "play_area");
  const threatIds = [...(investigator.threat_area || []), ...(investigator.engaged_enemies || [])];
  const threat = zoneSection("threat", unique(threatIds), snapshot, prev, "threat_area", { includeEnemies: true });
  const hand = zoneSection("hand", investigator.hand || [], snapshot, prev, "hand", {
    onHeader: () => openPile("Hand", investigator.hand || [], snapshot),
  });
  const zones = document.createElement("div");
  zones.className = "player-zones";
  zones.append(play, threat, hand);
  el.player.append(summary, zones);
}

function statPill(label, value, prev = null, path = "", compareValue = value) {
  const pill = document.createElement("span");
  pill.className = `stat-pill ${path && changedValue(prev, path, compareValue) ? "flash" : ""}`;
  pill.innerHTML = `<span>${escapeHtml(label)}</span><b>${escapeHtml(String(value))}</b>`;
  return pill;
}

function zoneSection(title, ids, snapshot, prev, zoneKey, options = {}) {
  const section = document.createElement("section");
  section.className = "zone-section";
  const header = document.createElement(options.onHeader ? "button" : "div");
  if (options.onHeader) {
    header.type = "button";
    header.addEventListener("click", options.onHeader);
  }
  header.className = "zone-title";
  if (prev && zoneLengthChanged(prev, zoneKey, ids.length)) header.classList.add("flash");
  header.textContent = `${title} (${ids.length})`;
  const cards = document.createElement("div");
  cards.className = "card-row";
  for (const id of ids) {
    const thumb = options.includeEnemies && snapshot.enemies?.[id]
      ? enemyCardThumb(id, snapshot, prev, zoneKey)
      : cardThumb(id, snapshot, { entered: enteredZone(prev, zoneKey, id) });
    cards.append(thumb);
  }
  if (!ids.length) {
    const empty = document.createElement("span");
    empty.className = "empty-zone";
    empty.textContent = "empty";
    cards.append(empty);
  }
  section.append(header, cards);
  return section;
}

function pileCount(label, value, onClick = null, prev = null, path = "") {
  const node = document.createElement(onClick ? "button" : "span");
  if (onClick) {
    node.type = "button";
    node.addEventListener("click", onClick);
  }
  node.className = `pile-count ${path && changedValue(prev, path, value) ? "flash" : ""}`;
  node.innerHTML = `<span>${escapeHtml(label)}</span><b>${escapeHtml(String(value))}</b>`;
  return node;
}

function cardThumb(id, snapshot, options = {}) {
  const entity = resolveEntity(id, snapshot);
  const instance = entity.instance || {};
  const card = entity.card || {};
  const button = document.createElement("button");
  button.type = "button";
  button.className = `${options.chip ? "card-chip" : "card-thumb"} ${options.entered ? "flash" : ""} ${instance.exhausted ? "exhausted" : ""}`;
  button.title = card.name || id;
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    openEntityModal(entity);
  });

  const img = document.createElement("img");
  img.alt = card.name || entity.code || id;
  img.loading = "lazy";
  setCardImage(img, entity.code, () => button.classList.add("image-error"));

  const fallback = document.createElement("span");
  fallback.className = "thumb-fallback";
  fallback.innerHTML = `<b>${escapeHtml(card.name || id)}</b><small>${escapeHtml(cardSummary(card))}</small>`;
  button.append(img, fallback, overlayTokens(instance));
  return button;
}

function codeThumb(code, options = {}) {
  const card = cardByCode(code);
  const button = document.createElement("button");
  button.type = "button";
  button.className = options.className || "card-thumb";
  button.title = options.title || card.name || code;
  button.addEventListener("click", (event) => {
    event.stopPropagation();
    openEntityModal(resolveCode(code, card.name || code));
  });

  const img = document.createElement("img");
  img.alt = card.name || code;
  img.loading = "lazy";
  setCardImage(img, code, () => button.classList.add("image-error"), options.imageBack === true);

  const fallback = document.createElement("span");
  fallback.className = "thumb-fallback";
  fallback.innerHTML = `<b>${escapeHtml(card.name || code)}</b><small>${escapeHtml(cardSummary(card))}</small>`;
  button.append(img, fallback);
  return button;
}

function enemyCardThumb(id, snapshot, prev, zoneKey) {
  const entity = resolveEnemy(id, snapshot);
  const enemy = entity.enemy || {};
  const button = cardThumb(id, snapshot, { entered: enteredZone(prev, zoneKey, id) });
  button.classList.add("enemy-card");
  if (enemy.engaged_with) button.classList.add("engaged");
  return button;
}

function overlayTokens(instance) {
  const wrap = document.createElement("span");
  wrap.className = "overlays";
  for (const [kind, amount] of Object.entries(instance.uses || {})) {
    wrap.append(tokenBadge(`${kind} ${amount}`));
  }
  for (const key of ["damage", "horror", "clues", "doom"]) {
    if (instance[key]) wrap.append(tokenBadge(`${key} ${instance[key]}`));
  }
  if (instance.exhausted) wrap.append(tokenBadge("exhausted"));
  return wrap;
}

function tokenBadge(text) {
  const badge = document.createElement("span");
  badge.className = "overlay-badge";
  badge.textContent = text;
  return badge;
}

function openPile(title, ids, snapshot) {
  el.modalTitle.textContent = title;
  el.modalBody.innerHTML = "";
  const list = document.createElement("div");
  list.className = "pile-list";
  for (const id of ids) {
    list.append(cardThumb(id, snapshot));
  }
  if (!ids.length) {
    const empty = document.createElement("p");
    empty.textContent = "Empty.";
    list.append(empty);
  }
  el.modalBody.append(list);
  el.modalBackdrop.hidden = false;
}

function openEntityModal(entity) {
  const card = entity.card || {};
  el.modalTitle.textContent = card.name || entity.label || entity.id || "Card";
  el.modalBody.innerHTML = "";

  const imageWrap = document.createElement("div");
  imageWrap.className = "modal-images";
  imageWrap.append(
    modalImageSide(entity.code, false, "Front", card),
    modalImageSide(entity.code, true, "Back", card, { optional: true })
  );
  const fallback = document.createElement("div");
  fallback.className = "large-fallback";
  fallback.innerHTML = `<b>${escapeHtml(card.name || entity.code || "Unknown")}</b><span>${escapeHtml(cardSummary(card))}</span>`;
  imageWrap.append(fallback);

  const data = document.createElement("div");
  data.className = "modal-data";
  data.innerHTML = `
    <h3>Engine data</h3>
    <pre>${escapeHtml(JSON.stringify(entity, null, 2))}</pre>
  `;
  el.modalBody.append(imageWrap, data);
  el.modalBackdrop.hidden = false;
}

function modalImageSide(code, back, label, card, options = {}) {
  const side = document.createElement("figure");
  side.className = "modal-image-side";
  const img = document.createElement("img");
  img.alt = `${card.name || code || "Card"} ${label.toLowerCase()}`;
  const caption = document.createElement("figcaption");
  caption.textContent = label;
  setCardImage(img, code, () => {
    if (options.optional) {
      side.remove();
      return;
    }
    side.classList.add("image-error");
    side.closest(".modal-images")?.classList.add("image-error");
  }, back);
  side.append(img, caption);
  return side;
}

function closeModal() {
  el.modalBackdrop.hidden = true;
  el.modalBody.innerHTML = "";
}

function resolveEntity(id, snapshot) {
  if (snapshot.enemies?.[id]) return resolveEnemy(id, snapshot);
  if (snapshot.card_instances?.[id]) return resolveInstance(id, snapshot);
  if (snapshot.locations?.[id]) return resolveLocation(id, snapshot);
  if (state.run.cards?.[id]) return resolveCode(id, id);
  return { id, code: id, label: id, card: cardByCode(id) };
}

function resolveInstance(id, snapshot) {
  const instance = snapshot.card_instances?.[id] || {};
  return { id, code: instance.card_code, card: cardByCode(instance.card_code), instance };
}

function resolveEnemy(id, snapshot) {
  const enemy = snapshot.enemies?.[id] || {};
  return { id, code: enemy.card_code, card: cardByCode(enemy.card_code), enemy, instance: enemy };
}

function resolveLocation(id, snapshot) {
  const location = snapshot.locations?.[id] || {};
  return { id, code: location.code, card: cardByCode(location.code), location };
}

function resolveCode(code, label) {
  return { id: code, code, label, card: cardByCode(code) };
}

function cardByCode(code) {
  return state.run?.cards?.[code] || {};
}

function replaceInstanceTokens(text, snapshot) {
  return String(text ?? "").replace(/\b[pe]c\d{4}\b/g, (id) => {
    const name = instanceDisplayName(id, snapshot);
    return name ? `${name} (${id})` : id;
  });
}

function instanceDisplayName(id, snapshot) {
  const direct = snapshot.card_instances?.[id] || snapshot.enemies?.[id];
  if (direct?.card_code) return cardByCode(direct.card_code).name || "";
  for (const step of state.run?.steps || []) {
    const stepState = step.state || {};
    const seen = stepState.card_instances?.[id] || stepState.enemies?.[id];
    if (seen?.card_code) return cardByCode(seen.card_code).name || "";
  }
  return "";
}

function cardImageUrl(code, back = false) {
  return `${CARD_IMAGE_BASE}${encodeURIComponent(code || "unknown")}${back ? "b" : ""}.png`;
}

// Image source chain: local cache (viewer/img/, populated by
// scripts/fetch_card_images.py) -> arkhamdb (retried once; it throttles
// bursts) -> caller's text fallback.
function setCardImage(img, code, onFail, back = false) {
  const name = `${encodeURIComponent(code || "unknown")}${back ? "b" : ""}.png`;
  const sources = [`img/${name}`, cardImageUrl(code, back)];
  let attempt = 0;
  img.onerror = () => {
    attempt += 1;
    if (attempt < sources.length) {
      img.src = sources[attempt];
      return;
    }
    if (attempt === sources.length) {
      setTimeout(() => {
        img.src = `${sources[sources.length - 1]}?r=1`;
      }, 1200 + Math.random() * 800);
      return;
    }
    onFail();
  };
  img.src = sources[0];
}

function cardSummary(card) {
  const icons = card.icons
    ? Object.entries(card.icons).filter(([, value]) => value).map(([key, value]) => `${key[0].toUpperCase()}${value}`).join(" ")
    : "";
  const cost = card.cost != null ? `cost ${card.cost}` : "";
  return [card.type_code, cost, icons].filter(Boolean).join(" | ");
}

function changedValue(prev, path, currentValue) {
  if (!prev) return false;
  return JSON.stringify(getPath(prev, path)) !== JSON.stringify(currentValue);
}

function enteredZone(prev, zoneKey, id) {
  if (!prev) return false;
  const before = prev.state.investigator?.[zoneKey] || [];
  return !before.includes(id);
}

function zoneLengthChanged(prev, zoneKey, currentLength) {
  const before = prev.state.investigator?.[zoneKey] || [];
  return before.length !== currentLength;
}

function getPath(root, path) {
  return path.split(".").reduce((value, key) => {
    if (value == null) return undefined;
    if (key === "length") return value.length;
    return value[key];
  }, root);
}

function unique(items) {
  return [...new Set(items)];
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function svgEl(name, attrs) {
  const node = document.createElementNS("http://www.w3.org/2000/svg", name);
  for (const [key, value] of Object.entries(attrs)) {
    node.setAttribute(key, String(value));
  }
  return node;
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
  }[char]));
}

// ---------------------------------------------------------------------------
// Workbench splitters (VSCode model): one 100vh budget; each divider moves the
// boundary between its two neighbors. The map row is flexible (1fr) and
// absorbs whatever the pixel-sized rows release. Sizes persist per browser.

const LAYOUT_KEY = "arkham-viewer-layout";
const LAYOUT_DEFAULTS = { events: 110, decision: 130, player: 230, scenario: 330 };
const LAYOUT_MIN = { events: 56, decision: 64, player: 96, scenario: 220 };
const BENCH_TOP_MIN = 140;

function initWorkbench() {
  const workbench = document.querySelector("#workbench");
  if (!workbench) return;
  const layout = { ...LAYOUT_DEFAULTS, ...readLayout() };
  applyLayout(workbench, layout);

  bindDivider("#div-events", (dy) => boundaryDrag(workbench, layout, "events", dy));
  bindDivider("#div-decision", (dy) => boundaryDrag(workbench, layout, "decision", dy));
  bindDivider("#div-player", (dy) => boundaryDrag(workbench, layout, "player", dy));
  bindDivider("#div-col", (dx) => {
    const maxScenario = Math.max(LAYOUT_MIN.scenario, workbench.clientWidth * 0.6);
    layout.scenario = clamp(layout.scenario - dx, LAYOUT_MIN.scenario, maxScenario);
    applyLayout(workbench, layout);
  });

  function resetTo(defaults) {
    Object.assign(layout, defaults);
    applyLayout(workbench, layout);
    persistLayout(layout);
  }
  for (const id of ["#div-events", "#div-decision", "#div-player", "#div-col"]) {
    document.querySelector(id)?.addEventListener("dblclick", () => resetTo(LAYOUT_DEFAULTS));
  }

  function bindDivider(selector, onDelta) {
    const divider = document.querySelector(selector);
    if (!divider) return;
    const horizontal = divider.classList.contains("divider-col");
    const begin = (startX, startY) => {
      divider.classList.add("dragging");
      let last = { x: startX, y: startY };
      // Window-level listeners with mouse fallbacks: pointer capture on the
      // 5px sash is unreliable (and synthetic/automation input may only send
      // mouse events). Absolute-position deltas make duplicate events no-ops.
      const move = (ev) => {
        const delta = horizontal ? ev.clientX - last.x : ev.clientY - last.y;
        if (delta !== 0) {
          onDelta(delta);
          last = { x: ev.clientX, y: ev.clientY };
        }
        ev.preventDefault();
      };
      const up = () => {
        divider.classList.remove("dragging");
        window.removeEventListener("pointermove", move);
        window.removeEventListener("pointerup", up);
        window.removeEventListener("mousemove", move);
        window.removeEventListener("mouseup", up);
        persistLayout(layout);
      };
      window.addEventListener("pointermove", move);
      window.addEventListener("pointerup", up);
      window.addEventListener("mousemove", move);
      window.addEventListener("mouseup", up);
    };
    divider.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      begin(event.clientX, event.clientY);
    });
    divider.addEventListener("mousedown", (event) => {
      if (event.button !== 0 || divider.classList.contains("dragging")) return;
      event.preventDefault();
      begin(event.clientX, event.clientY);
    });
  }
}

// Each row divider sits directly ABOVE its named row, so dragging it moves that
// row's top boundary: dy > 0 shrinks the row (freed space returns to the
// flexible map row), dy < 0 grows it — taking from the map first (VSCode
// terminal/editor behavior), then cascading into the other fixed rows once the
// map is at its minimum. The sash always tracks the pointer.
const CASCADE = {
  events: ["decision", "player"],
  decision: ["events", "player"],
  player: ["decision", "events"],
};

function boundaryDrag(workbench, layout, row, dy) {
  if (dy > 0) {
    layout[row] = Math.max(LAYOUT_MIN[row], layout[row] - dy);
  } else {
    let need = -dy;
    const pixelRows = ["events", "decision", "player"];
    const dividers = 15;
    const flexNow = workbench.clientHeight - dividers - pixelRows.reduce((sum, k) => sum + layout[k], 0);
    const fromFlex = Math.min(need, Math.max(0, flexNow - BENCH_TOP_MIN));
    layout[row] += fromFlex;
    need -= fromFlex;
    for (const other of CASCADE[row]) {
      if (need <= 0) break;
      const take = Math.min(need, layout[other] - LAYOUT_MIN[other]);
      layout[other] -= take;
      layout[row] += take;
      need -= take;
    }
  }
  applyLayout(workbench, layout);
}

function applyLayout(workbench, layout) {
  workbench.style.setProperty("--h-events", `${Math.round(layout.events)}px`);
  workbench.style.setProperty("--h-decision", `${Math.round(layout.decision)}px`);
  workbench.style.setProperty("--h-player", `${Math.round(layout.player)}px`);
  workbench.style.setProperty("--w-scenario", `${Math.round(layout.scenario)}px`);
}

function readLayout() {
  try {
    return JSON.parse(localStorage.getItem(LAYOUT_KEY) || "{}");
  } catch {
    return {};
  }
}

function persistLayout(layout) {
  try {
    localStorage.setItem(LAYOUT_KEY, JSON.stringify(layout));
  } catch {
    /* private mode etc. — layout just won't persist */
  }
}

initWorkbench();
