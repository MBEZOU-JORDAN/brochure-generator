/**
 * api.js — Couche d'abstraction pour tous les appels backend
 *
 * Principe : app.js ne connaît jamais les URLs ni le format des requêtes.
 * Si l'URL backend change, on modifie uniquement ce fichier.
 */

const API_BASE = "http://localhost:8000";

/**
 * searchCompany — Recherche DuckDuckGo via le backend
 * @param {string} query - Nom de l'entreprise
 * @returns {Promise<Array<{title, url, snippet}>>}
 */
async function searchCompany(query) {
  const resp = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}`);
  if (!resp.ok) throw new Error(`Recherche échouée (${resp.status})`);
  const data = await resp.json();
  return data.results;
}

/**
 * streamBrochure — Consomme le flux SSE de génération de brochure
 *
 * SSE via fetch() + ReadableStream (pas EventSource) car EventSource
 * ne supporte pas les requêtes POST nativement.
 *
 * @param {string} companyName
 * @param {string|null} url
 * @param {Object} callbacks - { onStatus, onToken, onDone, onError }
 */
async function streamBrochure(companyName, url, callbacks) {
  const { onStatus, onToken, onDone, onError } = callbacks;

  let resp;
  try {
    resp = await fetch(`${API_BASE}/api/brochure/stream`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ company_name: companyName, url: url || null }),
    });
  } catch (err) {
    onError?.("Impossible de contacter le serveur. Vérifiez que le backend tourne.");
    return;
  }

  if (!resp.ok) {
    const detail = await resp.text();
    onError?.(`Erreur serveur (${resp.status}) : ${detail}`);
    return;
  }

  // Lire le flux SSE
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    // SSE : chaque event est séparé par \n\n
    const parts = buffer.split("\n\n");
    buffer = parts.pop(); // Garder le fragment incomplet

    for (const part of parts) {
      if (!part.startsWith("data: ")) continue;
      const raw = part.slice(6).trim();
      if (!raw) continue;

      let event;
      try {
        event = JSON.parse(raw);
      } catch {
        continue;
      }

      switch (event.type) {
        case "status": onStatus?.(event.message); break;
        case "start":  onStatus?.("✍️ Génération en cours…"); break;
        case "token":  onToken?.(event.content); break;
        case "done":   onDone?.(event.brochure, event.url); break;
        case "error":  onError?.(event.message); break;
      }
    }
  }
}

/**
 * generateTTS — Synthèse vocale via edge-tts
 * @param {string} text
 * @param {string} language - "fr" | "en"
 * @returns {Promise<{audio_base64, voice_used}>}
 */
async function generateTTS(text, language = "fr") {
  const resp = await fetch(`${API_BASE}/api/tts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language }),
  });
  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(err.detail || "TTS échoué");
  }
  return resp.json();
}

/**
 * generateFlyer — Génération d'image FLUX.1-schnell
 * @param {string} brochureText
 * @param {string} companyName
 * @param {string} style - "modern" | "elegant" | "bold" | "minimal"
 * @returns {Promise<{image_base64, prompt_used}>}
 */
async function generateFlyer(brochureText, companyName, style) {
  const resp = await fetch(`${API_BASE}/api/flyer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      brochure_text: brochureText,
      company_name: companyName,
      style,
    }),
  });
  if (!resp.ok) {
    const err = await resp.json();
    throw new Error(err.detail || "Génération du flyer échouée");
  }
  return resp.json();
}
