/**
 * app.js — Logique UI et orchestration
 *
 * State minimal : on stocke en variables module — pas de framework nécessaire.
 * Toutes les mutations UI passent par des fonctions dédiées (pattern "UI functions").
 */

// ── État de l'application ────────────────────────────────────────────────────
const state = {
  companyName: "",
  url: "",
  selectedStyle: "modern",
  selectedLang: "fr",
  fullBrochure: "",       // Texte markdown accumulé pendant le stream
  isGenerating: false,
  searchDebounce: null,
};

// ── Références DOM ────────────────────────────────────────────────────────────
const $ = (id) => document.getElementById(id);
const els = {
  companyName:      $("company-name"),
  companyUrl:       $("company-url"),
  searchBtn:        $("search-btn"),
  searchResults:    $("search-results"),
  generateBtn:      $("generate-btn"),
  statusBar:        $("status-bar"),
  statusText:       $("status-text"),
  emptyState:       $("empty-state"),
  brochureContainer:$("brochure-container"),
  brochureRender:   $("brochure-render"),
  brochureCompany:  $("brochure-company-name"),
  sourceUrl:        $("source-url"),
  cursor:           $("cursor"),
  copyBtn:          $("copy-btn"),
  ttsBtn:           $("tts-btn"),
  flyerBtn:         $("flyer-btn"),
  ttsPlayer:        $("tts-player"),
  audioPlayer:      $("audio-player"),
  ttsVoiceLabel:    $("tts-voice-label"),
  flyerContainer:   $("flyer-container"),
  flyerLoading:     $("flyer-loading"),
  flyerImage:       $("flyer-image"),
  flyerPrompt:      $("flyer-prompt"),
  downloadFlyerBtn: $("download-flyer-btn"),
};

// ── Configuration marked.js ────────────────────────────────────────────────────
// marked.js : bibliothèque JavaScript de rendu Markdown → HTML
// On configure renderer custom pour ajouter nos classes CSS
marked.setOptions({
  breaks: true,      // Sauts de ligne simples → <br>
  gfm: true,         // GitHub Flavored Markdown
});

// ── INIT ──────────────────────────────────────────────────────────────────────
function init() {
  // Input company name → activer le bouton
  els.companyName.addEventListener("input", (e) => {
    state.companyName = e.target.value.trim();
    updateGenerateBtn();

    // Auto-search avec debounce de 600ms
    clearTimeout(state.searchDebounce);
    if (state.companyName.length > 2 && !state.url) {
      state.searchDebounce = setTimeout(() => triggerSearch(state.companyName), 600);
    }
  });

  // Input URL
  els.companyUrl.addEventListener("input", (e) => {
    state.url = e.target.value.trim();
    if (state.url) hideSearchResults();
  });

  // Bouton recherche manuelle
  els.searchBtn.addEventListener("click", () => {
    if (state.companyName) triggerSearch(state.companyName);
  });

  // Générer brochure
  els.generateBtn.addEventListener("click", handleGenerate);

  // Style chips
  document.querySelectorAll(".style-chip[data-style]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".style-chip[data-style]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.selectedStyle = btn.dataset.style;
    });
  });

  // Langue TTS chips
  document.querySelectorAll(".style-chip[data-lang]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".style-chip[data-lang]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.selectedLang = btn.dataset.lang;
    });
  });

  // Copier markdown
  els.copyBtn.addEventListener("click", handleCopy);

  // TTS
  els.ttsBtn.addEventListener("click", handleTTS);

  // Flyer
  els.flyerBtn.addEventListener("click", handleFlyer);

  // Download flyer
  els.downloadFlyerBtn.addEventListener("click", handleDownloadFlyer);

  // Fermer dropdown si clic ailleurs
  document.addEventListener("click", (e) => {
    if (!els.searchResults.contains(e.target) && e.target !== els.searchBtn) {
      hideSearchResults();
    }
  });

  // Enter key sur les inputs
  [els.companyName, els.companyUrl].forEach((input) => {
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !state.isGenerating && state.companyName) handleGenerate();
    });
  });
}

// ── RECHERCHE WEB ─────────────────────────────────────────────────────────────
async function triggerSearch(query) {
  try {
    els.searchBtn.innerHTML = `<div class="status-spinner" style="width:14px;height:14px"></div>`;
    const results = await searchCompany(query);

    if (!results.length) {
      hideSearchResults();
      return;
    }

    renderSearchResults(results);
  } catch (err) {
    console.warn("Recherche échouée :", err.message);
  } finally {
    els.searchBtn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>`;
  }
}

function renderSearchResults(results) {
  els.searchResults.innerHTML = "";
  results.forEach((r) => {
    const item = document.createElement("div");
    item.className = "search-item";
    item.setAttribute("role", "option");
    item.innerHTML = `
      <div class="search-item-title">${escapeHtml(r.title)}</div>
      <div class="search-item-url">${escapeHtml(r.url)}</div>
      <div class="search-item-snippet">${escapeHtml(r.snippet)}</div>
    `;
    item.addEventListener("click", () => {
      els.companyUrl.value = r.url;
      state.url = r.url;
      // Auto-fill company name si vide
      if (!state.companyName) {
        els.companyName.value = r.title.split(" — ")[0].split(" - ")[0].trim();
        state.companyName = els.companyName.value;
      }
      hideSearchResults();
      updateGenerateBtn();
    });
    els.searchResults.appendChild(item);
  });
  els.searchResults.classList.remove("hidden");
}

function hideSearchResults() { els.searchResults.classList.add("hidden"); }

// ── GÉNÉRATION BROCHURE ───────────────────────────────────────────────────────
async function handleGenerate() {
  if (state.isGenerating || !state.companyName) return;

  state.isGenerating = true;
  state.fullBrochure = "";

  setGeneratingUI(true);
  showBrochureContainer();
  els.brochureRender.innerHTML = "";
  els.cursor.classList.remove("hidden");
  els.brochureCompany.textContent = state.companyName;
  // Cacher les zones optionnelles d'une précédente génération
  els.ttsPlayer.classList.add("hidden");
  els.flyerContainer.classList.add("hidden");
  els.flyerImage.classList.add("hidden");

  await streamBrochure(state.companyName, state.url || null, {
    onStatus: (msg) => updateStatus(msg),
    onToken: (token) => {
      state.fullBrochure += token;
      // Re-rendre tout le markdown à chaque token
      // marked.parse() est synchrone et très rapide
      els.brochureRender.innerHTML = marked.parse(state.fullBrochure);
    },
    onDone: (brochure, sourceUrl) => {
      state.fullBrochure = brochure || state.fullBrochure;
      els.brochureRender.innerHTML = marked.parse(state.fullBrochure);
      els.cursor.classList.add("hidden");
      if (sourceUrl) els.sourceUrl.textContent = sourceUrl;
      finishGeneration();
    },
    onError: (msg) => {
      showError(msg);
      finishGeneration();
    },
  });
}

function setGeneratingUI(generating) {
  els.generateBtn.disabled = generating;
  els.generateBtn.classList.toggle("loading", generating);
  els.statusBar.classList.toggle("hidden", !generating);
}

function finishGeneration() {
  state.isGenerating = false;
  setGeneratingUI(false);
  els.cursor.classList.add("hidden");
}

function updateStatus(msg) {
  els.statusText.textContent = msg;
}

function showBrochureContainer() {
  els.emptyState.classList.add("hidden");
  els.brochureContainer.classList.remove("hidden");
  els.brochureContainer.classList.add("fade-in");
}

function showError(msg) {
  els.brochureRender.innerHTML = `
    <div style="padding:20px;background:rgba(255,60,60,0.08);border:1px solid rgba(255,60,60,0.2);border-radius:8px;color:#ff6b6b;font-size:0.85rem;">
      ❌ ${escapeHtml(msg)}
    </div>`;
}

// ── COPIER ────────────────────────────────────────────────────────────────────
async function handleCopy() {
  if (!state.fullBrochure) return;
  try {
    await navigator.clipboard.writeText(state.fullBrochure);
    els.copyBtn.textContent = "✓ Copié !";
    setTimeout(() => {
      els.copyBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg> Copier`;
    }, 2000);
  } catch {
    alert("Impossible de copier — utilisez Ctrl+A puis Ctrl+C dans la zone de texte.");
  }
}

// ── TTS ───────────────────────────────────────────────────────────────────────
async function handleTTS() {
  if (!state.fullBrochure) return;

  els.ttsBtn.disabled = true;
  els.ttsBtn.textContent = "Synthèse…";
  els.ttsPlayer.classList.remove("hidden");
  els.ttsVoiceLabel.textContent = "Génération audio en cours…";

  try {
    // Extraire le texte pur (sans markdown) pour une meilleure synthèse
    // On passe le markdown : edge-tts ignore les symboles # * _ bien gérés
    const result = await generateTTS(state.fullBrochure, state.selectedLang);

    // data URL MP3 pour l'élément <audio>
    els.audioPlayer.src = `data:audio/mp3;base64,${result.audio_base64}`;
    els.ttsVoiceLabel.textContent = `Voix : ${result.voice_used}`;
    els.audioPlayer.play();
  } catch (err) {
    els.ttsVoiceLabel.textContent = `Erreur TTS : ${err.message}`;
  } finally {
    els.ttsBtn.disabled = false;
    els.ttsBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg> Écouter`;
  }
}

// ── FLYER ─────────────────────────────────────────────────────────────────────
async function handleFlyer() {
  if (!state.fullBrochure) return;

  els.flyerContainer.classList.remove("hidden");
  els.flyerLoading.classList.remove("hidden");
  els.flyerImage.classList.add("hidden");
  els.flyerPrompt.classList.add("hidden");
  els.flyerBtn.disabled = true;

  // Scroll vers le flyer
  els.flyerContainer.scrollIntoView({ behavior: "smooth", block: "start" });

  try {
    const result = await generateFlyer(state.fullBrochure, state.companyName, state.selectedStyle);

    els.flyerImage.src = `data:image/png;base64,${result.image_base64}`;
    els.flyerImage.classList.remove("hidden");
    els.flyerPrompt.textContent = `Prompt : ${result.prompt_used}`;
    els.flyerPrompt.classList.remove("hidden");
  } catch (err) {
    els.flyerLoading.innerHTML = `<span style="color:#ff6b6b;">❌ ${escapeHtml(err.message)}</span>`;
  } finally {
    els.flyerLoading.classList.add("hidden");
    els.flyerBtn.disabled = false;
  }
}

function handleDownloadFlyer() {
  if (!els.flyerImage.src || els.flyerImage.classList.contains("hidden")) return;
  const a = document.createElement("a");
  a.href = els.flyerImage.src;
  a.download = `flyer-${state.companyName.toLowerCase().replace(/\s+/g, "-")}.png`;
  a.click();
}

// ── UTILITAIRES ───────────────────────────────────────────────────────────────
function updateGenerateBtn() {
  els.generateBtn.disabled = !state.companyName || state.isGenerating;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

// ── DÉMARRAGE ─────────────────────────────────────────────────────────────────
init();
