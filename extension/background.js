/* ContentForge — Background service worker (Manifest V3)
 *
 * Handles scoring and comparison requests from popup.js and content.js.
 * Includes retry logic for Render cold starts (~30s), timeout handling,
 * and connection-down detection.
 */

const API_BASE = "https://contentforge-api-lpp9.onrender.com";
const FETCH_TIMEOUT_MS = 35000; // 35s — covers Render free-tier cold start (~30s)
const MAX_RETRIES = 2;
const RETRY_DELAYS_MS = [3000, 8000]; // exponential-ish backoff between retries

// Listen for requests from content script / popup
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === "score") {
    scoreText(msg.text, msg.platform, msg.opts || {})
      .then(sendResponse)
      .catch(err => {
        if (isOfflineError(err)) {
          // Fallback to local heuristic when API is unreachable
          const local = localScore(msg.text, msg.platform);
          sendResponse({ ...local, offline: true, _fallback: true });
        } else {
          sendResponse({ error: err.message, offline: isOfflineError(err) });
        }
      });
    return true; // keep channel open for async response
  }

  if (msg.type === "compare") {
    compareTexts(msg.text_a, msg.text_b, msg.platforms)
      .then(sendResponse)
      .catch(err => sendResponse({ error: err.message, offline: isOfflineError(err) }));
    return true;
  }

  if (msg.type === "suggest") {
    suggestRewrite(msg.text, msg.platform, msg.tone || "engaging")
      .then(sendResponse)
      .catch(err => {
        if (isOfflineError(err)) {
          const fallback = localSuggest(msg.text, msg.platform, msg.tone || "engaging");
          sendResponse({ ...fallback, offline: true, _fallback: true });
        } else {
          sendResponse({ error: err.message, offline: isOfflineError(err) });
        }
      });
    return true;
  }

  if (msg.type === "ping") {
    // Quick health check — /v1/status first, fallback to /health for older deploys.
    pingApi()
      .then(data => sendResponse({ ok: true, version: data.version }))
      .catch(err => sendResponse({ ok: false, error: err.message }));
    return true;
  }

  if (msg.type === "logProof") {
    logProofBundle(msg.payload || {})
      .then(sendResponse)
      .catch(err => sendResponse({ error: err.message, offline: isOfflineError(err) }));
    return true;
  }
});

async function rapidPost(path, body, retry = 0) {
  if (retry > 0) await new Promise(r => setTimeout(r, RETRY_DELAYS_MS[retry - 1] || 5000));
  let resp;
  try {
    resp = await fetchWithTimeout(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });
  } catch (err) {
    if (retry < MAX_RETRIES) return rapidPost(path, body, retry + 1);
    throw err;
  }

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${resp.status}`);
  }
  return resp.json();
}

async function logProofBundle(payload) {
  const platform = (payload.platform || "tweet").toLowerCase();
  const original = String(payload.original_text || "").trim();
  const revised = String(payload.revised_text || "").trim();
  const postUrl = String(payload.post_url || "").trim();
  const impressions = Math.max(0, Number(payload.impressions || 0));
  const clicks = Math.max(0, Number(payload.clicks || 0));
  const likes = Math.max(0, Number(payload.likes || 0));
  const valuePerClick = Math.max(0, Number(payload.value_per_click || 1.0));
  const revenueAmount = Math.max(0, Number(payload.revenue_amount || 0));

  if (!revised) {
    throw new Error("Missing revised text to log proof");
  }

  const postId = payload.post_id ||
    (postUrl ? `url-${Date.now()}` : `manual-${Date.now()}`);

  const delta = await rapidPost("/v1/record_score_delta", {
    platform,
    original_text: original,
    revised_text: revised,
    suggestions_applied: payload.suggestions_applied || ["extension rewrite"],
    posted: Boolean(postUrl),
    post_url: postUrl,
  });

  const rec = (delta && delta.record) || {};
  const outcome = await rapidPost("/v1/record_publish_outcome", {
    post_id: postId,
    platform,
    score_before: rec.original_score,
    score_after: rec.revised_score,
    engagement: {
      impressions,
      clicks,
      likes,
    },
    value_per_click: valuePerClick,
    url: postUrl,
  });

  let revenue = null;
  if (revenueAmount > 0) {
    revenue = await rapidPost("/v1/record_revenue", {
      post_id: postId,
      platform,
      revenue_amount: revenueAmount,
      revenue_source: payload.revenue_source || "manual",
      currency: payload.currency || "USD",
      notes: payload.notes || "Logged from extension popup",
    });
  }

  return {
    ok: true,
    post_id: postId,
    score_delta: delta?.score_delta,
    estimated_revenue_lift: outcome?.estimated_revenue_lift,
    realized_revenue: revenue?.record?.revenue_amount || 0,
  };
}

async function pingApi() {
  let resp = await fetchWithTimeout(`${API_BASE}/v1/status`, { method: "GET" }, 10000);
  if (resp.status === 404) {
    resp = await fetchWithTimeout(`${API_BASE}/health`, { method: "GET" }, 10000);
  }
  if (!resp.ok) {
    throw new Error(`HTTP ${resp.status}`);
  }
  return resp.json();
}

function isOfflineError(err) {
  const m = (err.message || "").toLowerCase();
  return m.includes("failed to fetch") || m.includes("networkerror") ||
         m.includes("timeout") || m.includes("aborted");
}

async function fetchWithTimeout(url, options, timeoutMs = FETCH_TIMEOUT_MS) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const resp = await fetch(url, { ...options, signal: controller.signal });
    return resp;
  } catch (err) {
    if (err.name === "AbortError") throw new Error("Request timed out — API may be waking up (free tier cold start ~30s). Retrying automatically...");
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

async function scoreText(text, platform, opts, retry = 0) {
  if (retry > 0) await new Promise(r => setTimeout(r, RETRY_DELAYS_MS[retry - 1] || 5000));
  const body = { text, platforms: [platform], ...opts };
  const url = `${API_BASE}/v1/score_multi`;

  let resp;
  try {
    resp = await fetchWithTimeout(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (err) {
    if (retry < MAX_RETRIES) {
      // One retry for cold-start scenarios
      return scoreText(text, platform, opts, retry + 1);
    }
    throw err;
  }

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${resp.status}`);
  }

  const data = await resp.json();
  const result = data.results?.[platform];
  return result || { score: 0, grade: "?", suggestions: [] };
}

async function compareTexts(textA, textB, platforms, retry = 0) {
  if (retry > 0) await new Promise(r => setTimeout(r, RETRY_DELAYS_MS[retry - 1] || 5000));
  let resp;
  try {
    resp = await fetchWithTimeout(`${API_BASE}/v1/compare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text_a: textA, text_b: textB, platforms }),
    });
  } catch (err) {
    if (retry < MAX_RETRIES) {
      return compareTexts(textA, textB, platforms, retry + 1);
    }
    throw err;
  }

  if (resp.status === 404 || resp.status === 405) {
    // Older deployment fallback: compare manually via score_multi
    const p = (platforms && platforms[0]) || "tweet";
    const a = await scoreText(textA, p, {});
    const b = await scoreText(textB, p, {});
    const diff = (a.score || 0) - (b.score || 0);
    return {
      comparisons: {
        [p]: {
          platform: p,
          score_a: a.score || 0,
          score_b: b.score || 0,
          grade_a: a.grade || "D",
          grade_b: b.grade || "D",
          difference: diff,
          winner: diff > 0 ? "A" : diff < 0 ? "B" : "tie",
          a_advantages: (a.suggestions || []).slice(0, 3),
          b_advantages: (b.suggestions || []).slice(0, 3),
        }
      },
      summary: {
        overall_winner: diff > 0 ? "A" : diff < 0 ? "B" : "tie",
        note: "Fallback compare mode was used (legacy API route).",
      },
      _fallback: true,
    };
  }

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${resp.status}`);
  }

  return resp.json();
}

async function suggestRewrite(text, platform, tone, retry = 0) {
  if (retry > 0) await new Promise(r => setTimeout(r, RETRY_DELAYS_MS[retry - 1] || 5000));
  const alias = {
    tweet: "twitter",
    threads: "twitter",
    facebook: "linkedin",
    headline: "twitter",
    youtube: "blog",
    pinterest: "blog",
    ad_copy: "twitter",
    readability: "blog",
  };
  const rewritePlatform = alias[platform] || platform;

  let resp;
  try {
    resp = await fetchWithTimeout(`${API_BASE}/v1/rewrite`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, platform: rewritePlatform, tone }),
    });
  } catch (err) {
    if (retry < MAX_RETRIES) {
      return suggestRewrite(text, platform, tone, retry + 1);
    }
    throw err;
  }

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.error || `HTTP ${resp.status}`);
  }

  const data = await resp.json();
  return {
    rewritten: data.rewritten || "",
    platform: data.platform || platform,
    tone: data.tone || tone,
    char_count: data.char_count,
  };
}

// =============================================
// Offline fallback: lightweight local scoring
// =============================================
function localScore(text, platform) {
  const len = text.length;
  const words = text.trim().split(/\s+/).filter(Boolean);
  const wordCount = words.length;
  const hasEmoji = /[\p{Emoji_Presentation}\p{Extended_Pictographic}]/u.test(text);
  const hasHashtag = /#\w+/.test(text);
  const hasMention = /@\w+/.test(text);
  const hasUrl = /https?:\/\/\S+/.test(text);
  const hasQuestion = /\?/.test(text);
  const hasCTA = /\b(check out|click|sign up|subscribe|follow|join|grab|get|try|learn more|link in bio|dm me|shop now)\b/i.test(text);
  const excessiveCaps = (text.replace(/[^A-Z]/g, "").length / Math.max(len, 1)) > 0.5 && len > 10;
  const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);

  let score = 50;
  const suggestions = [];

  // Platform-specific ideal lengths
  const ideal = {
    tweet: [40, 200], linkedin: [100, 1300], instagram: [60, 800],
    threads: [40, 300], facebook: [60, 400], tiktok: [30, 150],
    headline: [30, 80], email: [20, 60], youtube: [30, 70],
    pinterest: [50, 300], ad_copy: [30, 150], readability: [100, 3000],
  };
  const [minLen, maxLen] = ideal[platform] || [30, 500];

  if (len < minLen) {
    score -= 15;
    suggestions.push(`Consider adding more detail (${len} chars, aim for ${minLen}+)`);
  } else if (len > maxLen) {
    score -= 10;
    suggestions.push(`A bit long for ${platform} (${len} chars, aim for <${maxLen})`);
  } else {
    score += 10; // good length range
  }

  if (hasEmoji) score += 5;
  else if (["tweet", "instagram", "threads", "tiktok"].includes(platform)) {
    suggestions.push("Try adding an emoji for visual appeal");
  }

  if (hasHashtag) score += 3;
  else if (["instagram", "tiktok", "twitter"].includes(platform)) {
    suggestions.push("Hashtags can boost discoverability");
  }

  if (hasQuestion) score += 4;
  if (hasCTA) score += 6;
  else suggestions.push("Adding a call-to-action can boost engagement");

  if (excessiveCaps) {
    score -= 12;
    suggestions.push("Too many CAPS can feel aggressive — use sparingly");
  }

  if (hasUrl && ["tweet", "linkedin"].includes(platform)) score += 3;
  if (hasMention) score += 2;

  // Sentence variety
  if (sentences.length >= 2) score += 4;

  // Clamp
  score = Math.max(10, Math.min(95, score));

  const grade = score >= 80 ? "A" : score >= 65 ? "B" : score >= 50 ? "C" : score >= 35 ? "D" : "F";

  if (suggestions.length === 0) suggestions.push("Looks solid — try the live API for deeper analysis");

  return {
    score,
    grade,
    suggestions: suggestions.slice(0, 4),
    _note: "Offline estimate — connect to API for full analysis",
  };
}

function localSuggest(text, platform, tone) {
  const cleaned = (text || "").trim();
  const maxByPlatform = {
    tweet: 280,
    twitter: 280,
    linkedin: 700,
    instagram: 2200,
    tiktok: 150,
    email: 500,
    headline: 80,
    youtube: 100,
    facebook: 400,
    threads: 500,
  };
  const maxLen = maxByPlatform[platform] || 500;

  let rewritten = cleaned;
  if (tone === "professional") {
    rewritten = rewritten.replace(/\bi\b/g, "I");
  } else if (tone === "bold") {
    rewritten = rewritten.replace(/\.$/, "");
    if (!/[!?]$/.test(rewritten)) rewritten += ".";
  }

  if (rewritten.length > maxLen) {
    rewritten = rewritten.slice(0, maxLen - 1).trimEnd() + "…";
  }

  return {
    rewritten,
    platform,
    tone,
    char_count: rewritten.length,
    _note: "Offline rewrite estimate — connect to API for stronger suggestions",
  };
}
