/* ContentForge — Content script: inline scoring badge on social platforms */

(() => {
  "use strict";

  // Platform detection from hostname
  const HOST = location.hostname;
  const PLATFORM = (() => {
    if (HOST.includes("x.com") || HOST.includes("twitter.com")) return "tweet";
    if (HOST.includes("linkedin.com")) return "linkedin";
    if (HOST.includes("instagram.com")) return "instagram";
    if (HOST.includes("threads.net")) return "threads";
    if (HOST.includes("facebook.com")) return "facebook";
    return null;
  })();

  if (!PLATFORM) return;

  // Composer selectors per platform
  const COMPOSER_SELECTORS = {
    tweet: '[data-testid="tweetTextarea_0"], [role="textbox"][data-testid]',
    linkedin: '.ql-editor[contenteditable="true"], div.editor-content [contenteditable="true"]',
    instagram: [
      // DM composer candidates
      'div[role="textbox"][contenteditable="true"][aria-label*="Message" i]',
      'div[contenteditable="true"][aria-label*="message" i]',
      'textarea[aria-label*="Message" i]',
      // Post/reel caption composer candidates
      'textarea[aria-label*="caption" i]',
      'textarea[placeholder*="caption" i]',
      // Generic fallbacks
      'div[contenteditable="true"][role="textbox"]',
      'textarea[aria-label]'
    ],
    threads: 'div[contenteditable="true"][role="textbox"]',
    facebook: 'div[contenteditable="true"][role="textbox"], div[data-contents="true"]',
  };

  const SELECTOR = COMPOSER_SELECTORS[PLATFORM];
  if (!SELECTOR) return;

  const PLATFORM_MAX_CHARS = {
    tweet: 280,
    linkedin: 700,
    instagram: 2200,
    threads: 500,
    facebook: 400,
  };

  let badge = null;
  let debounceTimer = null;
  let scanTimer = null;
  let lastText = "";
  let lastScore = null;
  let scoring = false;

  // -----------------------------------------------------------------------
  // Badge UI
  // -----------------------------------------------------------------------
  function createBadge() {
    if (badge) return badge;
    badge = document.createElement("div");
    badge.id = "cf-score-badge";
    badge.innerHTML = `
      <div class="cf-badge-score">--</div>
      <div class="cf-badge-detail" style="display:none">
        <div class="cf-badge-grade"></div>
        <div class="cf-badge-chars"></div>
        <ul class="cf-badge-suggestions"></ul>
        <div class="cf-badge-brand">ContentForge</div>
      </div>
    `;
    badge.addEventListener("click", () => {
      const detail = badge.querySelector(".cf-badge-detail");
      detail.style.display = detail.style.display === "none" ? "block" : "none";
    });
    document.body.appendChild(badge);
    return badge;
  }

  function updateBadge(score, grade, suggestions) {
    if (!badge) createBadge();
    const scoreEl = badge.querySelector(".cf-badge-score");
    scoreEl.textContent = `${score}`;
    scoreEl.className = "cf-badge-score " + gradeColor(grade);
    badge.querySelector(".cf-badge-grade").textContent = `${grade} — ${PLATFORM}`;
    badge.querySelector(".cf-badge-chars").textContent = `${lastText.length} chars`;
    const ul = badge.querySelector(".cf-badge-suggestions");
    ul.innerHTML = "";
    (suggestions || []).slice(0, 4).forEach(s => {
      const li = document.createElement("li");
      li.textContent = s;
      ul.appendChild(li);
    });
    badge.classList.add("cf-visible");
    scoring = false;
  }

  function showLoading() {
    if (!badge) createBadge();
    badge.querySelector(".cf-badge-score").textContent = "...";
    badge.querySelector(".cf-badge-score").className = "cf-badge-score";
    badge.classList.add("cf-visible");
    scoring = true;
  }

  function hideBadge() {
    if (badge) badge.classList.remove("cf-visible");
  }

  function gradeColor(grade) {
    if (!grade) return "cf-grade-f";
    const g = grade.charAt(0).toUpperCase();
    if (g === "A") return "cf-grade-a";
    if (g === "B") return "cf-grade-b";
    if (g === "C") return "cf-grade-c";
    return "cf-grade-f";
  }

  // -----------------------------------------------------------------------
  // Score via background worker
  // -----------------------------------------------------------------------
  function requestScore(text) {
    showLoading();
    const timeout = setTimeout(() => {
      scoring = false;
      if (badge) {
        badge.querySelector(".cf-badge-score").textContent = "--";
        badge.querySelector(".cf-badge-score").className = "cf-badge-score";
      }
    }, 15000); // 15s timeout for Render cold starts

    chrome.runtime.sendMessage(
      { type: "score", text, platform: PLATFORM },
      (resp) => {
        clearTimeout(timeout);
        if (chrome.runtime.lastError || !resp || resp.error) {
          scoring = false;
          console.warn("[ContentForge]", resp?.error || chrome.runtime.lastError?.message);
          return;
        }
        lastScore = resp;
        updateBadge(resp.score, resp.grade, resp.suggestions);
      }
    );
  }

  // -----------------------------------------------------------------------
  // Observe composer text changes
  // -----------------------------------------------------------------------
  function onTextChange(text) {
    text = text.trim();
    if (text === lastText) return;
    lastText = text;

    if (text.length < 5) {
      hideBadge();
      return;
    }

    if (scoring) return; // don't queue while a request is in flight

    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => requestScore(text), 600);
  }

  // -----------------------------------------------------------------------
  // Attach to composer when it appears
  // -----------------------------------------------------------------------
  function getComposerText(el) {
    if (!el) return "";
    if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") {
      return (el.value || "").trim();
    }
    return (el.innerText || el.textContent || "").trim();
  }

  function attachToComposer(el) {
    if (el.dataset.cfAttached) return;
    el.dataset.cfAttached = "1";

    const observer = new MutationObserver(() => {
      onTextChange(getComposerText(el));
    });
    observer.observe(el, { childList: true, subtree: true, characterData: true });

    el.addEventListener("input", () => {
      onTextChange(getComposerText(el));
    });
  }

  function scanForComposers() {
    const selectors = Array.isArray(SELECTOR) ? SELECTOR : [SELECTOR];
    selectors.forEach(sel => {
      document.querySelectorAll(sel).forEach(attachToComposer);
    });
  }

  function activeComposer() {
    const active = document.activeElement;
    const selectors = Array.isArray(SELECTOR) ? SELECTOR : [SELECTOR];
    if (active && active.matches && selectors.some(sel => active.matches(sel))) {
      return active;
    }
    for (const sel of selectors) {
      const el = document.querySelector(sel);
      if (el) return el;
    }
    return null;
  }

  function truncateAtBoundary(text, maxLen) {
    if (!maxLen || text.length <= maxLen) {
      return { text, truncated: false, originalLength: text.length };
    }
    let clipped = text.slice(0, maxLen).trimEnd();
    const lastSpace = clipped.lastIndexOf(" ");
    if (lastSpace > Math.floor(maxLen * 0.7)) {
      clipped = clipped.slice(0, lastSpace).trimEnd();
    }
    return { text: clipped, truncated: true, originalLength: text.length };
  }

  function writeComposerText(el, text) {
    const incoming = String(text || "");
    const maxLen = PLATFORM_MAX_CHARS[PLATFORM] || 0;
    const result = truncateAtBoundary(incoming, maxLen);
    const value = result.text;

    if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") {
      el.value = value;
    } else if (el.isContentEditable) {
      el.textContent = value;
    }

    const plainEvents = ["input", "change", "keyup", "keydown"];
    plainEvents.forEach(type => {
      try {
        el.dispatchEvent(new Event(type, { bubbles: true }));
      } catch (_) {
        // no-op
      }
    });

    if (el.setSelectionRange && typeof value === "string") {
      const end = value.length;
      try {
        el.setSelectionRange(end, end);
      } catch (_) {
        // no-op
      }
    }

    el.focus();
    return result;
  }

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.type !== "insertText") return;
    const composer = activeComposer();
    if (!composer) {
      sendResponse({ ok: false, error: "No composer found" });
      return;
    }
    const inserted = writeComposerText(composer, msg.text);
    onTextChange(inserted.text || "");
    sendResponse({
      ok: true,
      truncated: inserted.truncated,
      originalLength: inserted.originalLength,
      insertedLength: (inserted.text || "").length,
      maxLength: PLATFORM_MAX_CHARS[PLATFORM] || null,
      platform: PLATFORM,
    });
  });

  // Initial scan + throttled MutationObserver for SPA navigation
  scanForComposers();
  const bodyObserver = new MutationObserver(() => {
    if (scanTimer) return;
    scanTimer = setTimeout(() => { scanTimer = null; scanForComposers(); }, 500);
  });
  bodyObserver.observe(document.body, { childList: true, subtree: true });
})();
