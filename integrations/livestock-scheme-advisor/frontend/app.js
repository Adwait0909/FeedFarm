/* ==========================================================================
   Pashu Yojana Sahayak — frontend logic

   Talks to the FastAPI backend (../backend/app.py) at API_BASE.
   All display text lives in i18n.json; all scheme names and links live in
   schemes.json. Nothing user-visible is hardcoded here.

   IMPORTANT: switching language changes only what is SHOWN. The values sent
   to the backend stay in English, because the model was trained on the
   English category strings in feature_metadata.json.
   ========================================================================== */

const API_BASE = window.API_BASE || "/api/schemes";
const LANG_KEY = "pys.lang";

/* Used only if the backend is unreachable, so the form still fills in. */
const FALLBACK_OPTIONS = {
  district: ["Ahmednagar","Akola","Amravati","Beed","Bhandara","Buldhana","Chandrapur",
    "Chhatrapati Sambhajinagar","Dharashiv","Dhule","Gadchiroli","Gondia","Hingoli","Jalgaon",
    "Jalna","Kolhapur","Latur","Nagpur","Nanded","Nandurbar","Nashik","Palghar","Parbhani",
    "Pune","Raigad","Ratnagiri","Sangli","Satara","Sindhudurg","Solapur","Thane","Wardha",
    "Washim","Yavatmal"],
  breed: ["Buffalo (non-descript)","Crossbred (HF/Jersey)","Dangi","Deccani","Deoni",
    "Desi poultry","Gaolao","Gir","Improved layer/broiler","Kadaknath","Local goat",
    "Local sheep","Madgyal","Osmanabadi","Pandharpuri","Red Kandhari","Sahiwal","Sangamneri"],
  social_category: ["General","OBC","SC","ST"],
  land_holding: ["landless","marginal","small","semi_medium_plus"],
  employment_status: ["bpl","landless_agri_labour","self_employed_farmer","educated_unemployed",
    "shg_member","salaried_or_other"],
  gender: ["female","male"],
  breed_species_map: {
    "Buffalo (non-descript)": "buffalo", "Crossbred (HF/Jersey)": "cattle", "Dangi": "cattle",
    "Deccani": "sheep", "Deoni": "cattle", "Desi poultry": "poultry", "Gaolao": "cattle",
    "Gir": "cattle", "Improved layer/broiler": "poultry", "Kadaknath": "poultry",
    "Local goat": "goat", "Local sheep": "sheep", "Madgyal": "sheep", "Osmanabadi": "goat",
    "Pandharpuri": "buffalo", "Red Kandhari": "cattle", "Sahiwal": "cattle", "Sangamneri": "goat"
  }
};

/* ---------------------------------------------------------------- state -- */
const state = {
  lang: "en",
  i18n: null,
  schemes: null,
  options: FALLBACK_OPTIONS,
  speciesMap: FALLBACK_OPTIONS.breed_species_map,
  selectedFile: null,
  confirmedBreed: null,
  breedConfidence: null,
  breedAlts: [],
  lastResult: null,
  showIneligible: false
};

const $ = (id) => document.getElementById(id);

/* ------------------------------------------------- translation helpers -- */
function t(key) {
  const pack = state.i18n?.[state.lang]?.ui;
  return pack?.[key] ?? state.i18n?.en?.ui?.[key] ?? key;
}

/** Translate a data value (a district, a breed, a category code) for display.
 *  Falls back to the raw value so an unmapped option is still readable. */
function tOpt(group, value) {
  if (value === null || value === undefined || value === "") return "";
  const packs = state.i18n?.[state.lang]?.options;
  const fallback = state.i18n?.en?.options;
  return packs?.[group]?.[value] ?? fallback?.[group]?.[value] ?? value;
}

/** Scheme name in a given language, keyed by the code the backend returns. */
function schemeName(code, lang, apiName) {
  return state.schemes?.[code]?.[lang]?.name ?? apiName ?? code;
}
function schemeDesc(code, lang) {
  return state.schemes?.[code]?.[lang]?.short ?? "";
}
function schemeUrl(code) {
  return state.schemes?.[code]?.url ?? state.schemes?._fallback_url ?? "https://dahd.gov.in/schemes-programmes";
}

/* ---------------------------------------------------------- apply lang -- */
function applyLanguage(lang) {
  state.lang = lang;
  const meta = state.i18n?.[lang]?.meta ?? {};

  document.documentElement.lang = meta.htmlLang || lang;
  document.body.dataset.lang = lang;

  try { localStorage.setItem(LANG_KEY, lang); } catch (e) { /* private mode — fine */ }

  // Toggle button pressed state
  document.querySelectorAll("[data-set-lang]").forEach((btn) => {
    const on = btn.dataset.setLang === lang;
    btn.classList.toggle("is-active", on);
    btn.setAttribute("aria-pressed", String(on));
  });

  // Plain text nodes
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.dataset.i18n);
  });
  // Attributes
  document.querySelectorAll("[data-i18n-aria-label]").forEach((el) => {
    el.setAttribute("aria-label", t(el.dataset.i18nAriaLabel));
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });

  buildAllSelects();
  refreshBreedCard();
  refreshStatusLines();
  if (state.lastResult) renderResults(state.lastResult);
  syncIneligibleToggleLabel();
}

/* ------------------------------------------------------------- selects -- */
/** Options keep their English value; only the label is translated. */
function buildSelect(el, group, values, placeholderKey) {
  if (!el || !Array.isArray(values)) return;
  const previous = el.value;
  el.innerHTML = "";

  const ph = document.createElement("option");
  ph.value = "";
  ph.textContent = t(placeholderKey || "selectPlaceholder");
  el.appendChild(ph);

  values.forEach((v) => {
    const opt = document.createElement("option");
    opt.value = v;                       // English — the backend validates this
    let label = tOpt(group, v);
    if (group === "breed") {
      const sp = state.speciesMap?.[v];
      if (sp) label += ` (${tOpt("species", sp)})`;
    }
    opt.textContent = label;
    el.appendChild(opt);
  });

  if (previous) el.value = previous;     // keep the user's choice across a language switch
}

function buildAllSelects() {
  const o = state.options;
  buildSelect($("district"), "district", o.district);
  buildSelect($("manualBreedSelect"), "breed", o.breed, "breedPlaceholder");
  buildSelect($("socialCategory"), "social_category", o.social_category || FALLBACK_OPTIONS.social_category);
  buildSelect($("landHolding"), "land_holding", o.land_holding || FALLBACK_OPTIONS.land_holding);
  buildSelect($("employmentStatus"), "employment_status", o.employment_status || FALLBACK_OPTIONS.employment_status);
  buildSelect($("gender"), "gender", o.gender || FALLBACK_OPTIONS.gender);
}

/* ------------------------------------------------------------- status -- */
const statusState = { breed: null, form: null };   // { key, tone } or { text, tone }

function setStatus(which, key, tone) {
  statusState[which] = key ? { key, tone } : null;
  refreshStatusLines();
}
function setStatusRaw(which, text, tone) {
  statusState[which] = text ? { text, tone } : null;
  refreshStatusLines();
}
function refreshStatusLines() {
  [["breed", $("breedStatus")], ["form", $("formStatus")]].forEach(([k, el]) => {
    if (!el) return;
    const s = statusState[k];
    if (!s) { el.hidden = true; return; }
    el.textContent = s.text ?? t(s.key);
    el.className = "status" + (s.tone ? ` is-${s.tone}` : "");
    el.hidden = false;
  });
}

/* --------------------------------------------------------------- boot -- */
async function boot() {
  // 1. Language files. Without these the page has no text at all.
  try {
    const [i18nRes, schemesRes] = await Promise.all([
      fetch("i18n.json"),
      fetch("schemes.json")
    ]);
    state.i18n = await i18nRes.json();
    state.schemes = await schemesRes.json();
  } catch (e) {
    document.body.insertAdjacentHTML("afterbegin",
      '<p class="notice">This page loads i18n.json and schemes.json, which a browser will not read from a file:// path. ' +
      'Serve the folder instead: <code>python -m http.server 5500</code>, then open http://localhost:5500</p>');
    console.error("Could not load i18n.json / schemes.json", e);
    return;
  }

  // 2. Remembered language, else Marathi if the browser is set to Marathi.
  let lang = "en";
  try { lang = localStorage.getItem(LANG_KEY) || lang; } catch (e) { /* ignore */ }
  if (!localStorageHas() && (navigator.language || "").toLowerCase().startsWith("mr")) lang = "mr";
  applyLanguage(state.i18n[lang] ? lang : "en");

  // 3. Dropdown values from the backend, so they always match the model.
  try {
    const res = await fetch(`${API_BASE}/`);
    if (res.ok) {
      const data = await res.json();
      const o = data.options || {};
      const merged = { ...FALLBACK_OPTIONS };
      Object.keys(o).forEach((k) => { if (Array.isArray(o[k]) && o[k].length) merged[k] = o[k]; });
      state.options = merged;
      if (data.breed_species_map && Object.keys(data.breed_species_map).length) {
        state.speciesMap = data.breed_species_map;
      }
      buildAllSelects();
    } else {
      showOffline();
    }
  } catch (e) {
    console.warn("Backend not reachable; using the built-in option lists.", e);
    showOffline();
  }

  wireEvents();
}

function localStorageHas() {
  try { return localStorage.getItem(LANG_KEY) !== null; } catch (e) { return false; }
}

function showOffline() {
  const el = $("offlineNotice");
  if (el) { el.textContent = t("offlineNote"); el.hidden = false; }
}

/* -------------------------------------------------------------- events -- */
function wireEvents() {
  document.querySelectorAll("[data-set-lang]").forEach((btn) => {
    btn.addEventListener("click", () => applyLanguage(btn.dataset.setLang));
  });

  const dz = $("dropzone");
  dz.addEventListener("click", () => $("fileInput").click());
  dz.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); $("fileInput").click(); }
  });
  ["dragover", "dragenter"].forEach((ev) =>
    dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.add("is-dragover"); }));
  ["dragleave", "drop"].forEach((ev) =>
    dz.addEventListener(ev, (e) => { e.preventDefault(); dz.classList.remove("is-dragover"); }));
  dz.addEventListener("drop", (e) => {
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  });
  $("fileInput").addEventListener("change", (e) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  });

  $("clearPhotoBtn").addEventListener("click", clearPhoto);
  $("analyzeBtn").addEventListener("click", analyzePhoto);

  $("manualToggleBtn").addEventListener("click", () => {
    const wrap = $("manualBreedWrap");
    wrap.hidden = !wrap.hidden;
    if (!wrap.hidden) $("manualBreedSelect").focus();
  });
  $("manualBreedSelect").addEventListener("change", (e) => {
    if (e.target.value) {
      state.confirmedBreed = e.target.value;
      state.breedConfidence = null;
      state.breedAlts = [];
      refreshBreedCard();
    }
  });

  $("submitBtn").addEventListener("click", submitProfile);

  $("toggleIneligibleBtn").addEventListener("click", () => {
    state.showIneligible = !state.showIneligible;
    $("ineligibleWrap").hidden = !state.showIneligible;
    syncIneligibleToggleLabel();
  });

  $("restartBtn").addEventListener("click", () => {
    clearPhoto();
    state.lastResult = null;
    $("step-results").hidden = true;
    $("step-breed").scrollIntoView({ behavior: "smooth", block: "start" });
  });
}

function syncIneligibleToggleLabel() {
  const btn = $("toggleIneligibleBtn");
  if (btn) btn.textContent = state.showIneligible ? t("hideIneligible") : t("showIneligible");
}

/* --------------------------------------------------------------- photo -- */
function handleFile(file) {
  state.selectedFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    $("previewImg").src = e.target.result;
    $("dropzoneIdle").hidden = true;
    $("dropzonePreview").hidden = false;
  };
  reader.readAsDataURL(file);
  $("analyzeBtn").disabled = false;
  $("clearPhotoBtn").hidden = false;
  setStatus("breed", null);
}

function clearPhoto() {
  state.selectedFile = null;
  state.confirmedBreed = $("manualBreedSelect").value || null;
  state.breedConfidence = null;
  state.breedAlts = [];
  $("fileInput").value = "";
  $("dropzoneIdle").hidden = false;
  $("dropzonePreview").hidden = true;
  $("analyzeBtn").disabled = true;
  $("clearPhotoBtn").hidden = true;
  setStatus("breed", null);
  refreshBreedCard();
}

let csrfTokenPromise = null;
function csrfToken() {
  if (!csrfTokenPromise) {
    csrfTokenPromise = fetch("/csrf-token", { credentials: "same-origin" })
      .then((r) => r.json())
      .then((d) => d.csrf_token)
      .catch(() => { csrfTokenPromise = null; return ""; });
  }
  return csrfTokenPromise;
}

async function analyzePhoto() {
  if (!state.selectedFile) return;
  $("analyzeBtn").disabled = true;
  setStatus("breed", "analyzing");

  const form = new FormData();
  form.append("file", state.selectedFile);

  try {
    const res = await fetch(`${API_BASE}/predict/breed`, { method: "POST", headers: { "X-CSRF-Token": await csrfToken() }, body: form });
    if (!res.ok) {
      throw new Error(res.status === 503 ? t("breedModelUnavailable") : t("breedFailNote"));
    }
    const data = await res.json();

    // Low confidence: the photo may show an animal the model was never trained on (a hen, a
    // goat...). Do not pretend to know the breed -- ask the user to pick it by hand.
    if (data.recognized === false || !data.predicted_breed) {
      state.confirmedBreed = null;
      state.breedConfidence = null;
      state.breedAlts = [];
      refreshBreedCard();
      setStatus("breed", "breedUnsureNote", "bad");
      $("manualBreedWrap").hidden = false;
      return;
    }

    state.confirmedBreed = data.predicted_breed;
    state.breedConfidence = data.confidence;
    state.breedAlts = (data.top5 || []).slice(1, 4);
    refreshBreedCard();
    setStatus("breed", "breedOkNote", "ok");
  } catch (e) {
    console.error(e);
    setStatusRaw("breed", e.message || t("breedFailNote"), "bad");
    $("manualBreedWrap").hidden = false;
  } finally {
    $("analyzeBtn").disabled = false;
  }
}

function refreshBreedCard() {
  const card = $("breedResult");
  if (!state.confirmedBreed) { card.hidden = true; return; }

  $("predictedBreed").textContent = tOpt("breed", state.confirmedBreed);

  const sp = state.speciesMap?.[state.confirmedBreed];
  const bits = [];
  if (sp) bits.push(tOpt("species", sp));
  if (state.breedConfidence !== null && state.breedConfidence !== undefined) {
    bits.push(`${(state.breedConfidence * 100).toFixed(1)}%`);
  }
  $("predictedConfidence").textContent = bits.join(" · ");

  const altsWrap = $("breedAltsWrap");
  const alts = $("breedAlts");
  alts.innerHTML = "";
  if (state.breedAlts.length) {
    state.breedAlts.forEach((a) => {
      const s = document.createElement("span");
      s.textContent = `${tOpt("breed", a.breed)} ${(a.confidence * 100).toFixed(0)}%`;
      alts.appendChild(s);
    });
    altsWrap.hidden = false;
  } else {
    altsWrap.hidden = true;
  }

  card.hidden = false;
}

/* -------------------------------------------------------------- submit -- */
async function submitProfile() {
  setStatus("form", null);

  const breed = state.confirmedBreed || $("manualBreedSelect").value;
  if (!breed) {
    setStatus("form", "errNoBreed", "bad");
    return;
  }

  const profile = {
    breed,
    animals_owned: Number($("animalsOwned").value || 0),
    social_category: $("socialCategory").value,
    land_holding: $("landHolding").value,
    employment_status: $("employmentStatus").value,
    gender: $("gender").value,
    district: $("district").value
  };

  if (Object.values(profile).some((v) => v === "" || v === undefined || v === null)) {
    setStatus("form", "errIncomplete", "bad");
    return;
  }

  $("submitBtn").disabled = true;
  setStatus("form", "checking");

  try {
    const res = await fetch(`${API_BASE}/predict/eligibility`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": await csrfToken() },
      body: JSON.stringify(profile)
    });
    if (!res.ok) {
      throw new Error(
        res.status === 401 ? t("errSignIn")
          : res.status === 503 ? t("eligibilityModelUnavailable")
            : t("errGeneric")
      );
    }
    const data = await res.json();
    state.lastResult = data;
    renderResults(data);
    setStatus("form", null);
    $("step-results").hidden = false;
    $("step-results").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (e) {
    console.error(e);
    const offline = e instanceof TypeError;   // fetch itself failed — server is down
    setStatus("form", offline ? "errBackend" : null, "bad");
    if (!offline) setStatusRaw("form", e.message || t("errGeneric"), "bad");
  } finally {
    $("submitBtn").disabled = false;
  }
}

/* ------------------------------------------------------------- results -- */
const ARROW_SVG =
  '<span class="scheme__arrow" aria-hidden="true">' +
  '<svg viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" ' +
  'stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">' +
  '<path d="M7 17 17 7M9 7h8v8"/></svg></span>';

function renderResults(data) {
  const other = state.lang === "en" ? "mr" : "en";

  /* --- top recommendation: the backend returns a scheme code --- */
  const topCode = data.top1_recommendation;
  const hasTop = topCode && state.schemes?.[topCode];
  $("topSchemeName").textContent = hasTop
    ? schemeName(topCode, state.lang)
    : (topCode || t("topPickNone"));
  const rankingNote = data.recommendation_method === "eligibility_confidence_fallback"
    ? t("fallbackRankingNote")
    : "";
  $("topSchemeAlt").textContent = hasTop
    ? [schemeName(topCode, other), rankingNote].filter(Boolean).join(" · ")
    : (rankingNote || "");

  $("eligibleCount").textContent = t("countTemplate")
    .replace("{eligible}", data.eligible_count)
    .replace("{scored}", data.scored_count ?? data.schemes.filter((s) => s.eligibility_status !== "unscored").length)
    .replace("{unscored}", data.unscored_count ?? data.schemes.filter((s) => s.eligibility_status === "unscored").length);

  /* --- the two lists --- */
  const eligible = data.schemes.filter((s) => s.eligibility_status !== "unscored" && s.eligible === true);
  const ineligible = data.schemes.filter((s) => s.eligibility_status !== "unscored" && s.eligible === false);
  const unscored = data.schemes.filter((s) => s.eligibility_status === "unscored");

  const eList = $("eligibleList");
  const iList = $("ineligibleList");
  const uList = $("unscoredList");
  eList.innerHTML = "";
  iList.innerHTML = "";
  uList.innerHTML = "";

  eligible.forEach((s) => eList.appendChild(schemeCard(s, other)));
  ineligible.forEach((s) => iList.appendChild(schemeCard(s, other)));
  unscored.forEach((s) => uList.appendChild(schemeCard(s, other)));

  $("eligibleHeading").hidden = eligible.length === 0;
  $("toggleIneligibleBtn").hidden = ineligible.length === 0;
  $("ineligibleWrap").hidden = !state.showIneligible || ineligible.length === 0;
  $("unscoredWrap").hidden = unscored.length === 0;
  syncIneligibleToggleLabel();
}

function schemeCard(s, otherLang) {
  const card = document.createElement("article");
  const unscored = s.eligibility_status === "unscored";
  card.className = "scheme " + (unscored ? "scheme--no" : (s.eligible ? "scheme--yes" : "scheme--no"));

  const body = document.createElement("div");
  body.className = "scheme__body";

  // tags + eligibility badge
  const top = document.createElement("div");
  top.className = "scheme__top";

  const tags = document.createElement("div");
  tags.className = "scheme__tags";
  if (s.level) {
    const tg = document.createElement("span");
    tg.className = "tag";
    tg.textContent = tOpt("level", s.level);
    tags.appendChild(tg);
  }
  if (s.kind) {
    const tk = document.createElement("span");
    tk.className = "tag tag--kind";
    tk.textContent = tOpt("kind", s.kind);
    tags.appendChild(tk);
  }
  top.appendChild(tags);

  const badge = document.createElement("span");
  badge.className = "badge " + (!unscored && s.eligible ? "badge--yes" : "badge--no");
  badge.textContent = unscored
    ? t("unscoredBadge")
    : (s.eligible ? t("estimatedEligibleBadge") : t("estimatedIneligibleBadge"));
  top.appendChild(badge);
  body.appendChild(top);

  // name in the current language, then the same name in the other language
  const h = document.createElement("h4");
  h.className = "scheme__name";
  h.textContent = schemeName(s.code, state.lang, s.name);
  body.appendChild(h);

  const alt = document.createElement("p");
  alt.className = "scheme__name-alt";
  alt.textContent = schemeName(s.code, otherLang, s.name);
  body.appendChild(alt);

  const desc = schemeDesc(s.code, state.lang);
  if (desc) {
    const p = document.createElement("p");
    p.className = "scheme__desc";
    p.textContent = desc;
    body.appendChild(p);
  }

  card.appendChild(body);

  // the arrow row — opens the scheme's own website
  const link = document.createElement("a");
  link.className = "scheme__link";
  link.href = schemeUrl(s.code);
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.setAttribute("aria-label", `${t("openSiteAria")}: ${schemeName(s.code, state.lang, s.name)}`);
  link.innerHTML = `<span>${t("openSite")}</span>${ARROW_SVG}`;
  card.appendChild(link);

  return card;
}

boot();