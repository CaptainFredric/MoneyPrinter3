/* ContentForge — Popup scoring UI v0.6.0 */

let latestSuggestion = "";
let latestOriginalText = "";
let suggestionHistory = [];
let historyList = null;

document.addEventListener("DOMContentLoaded", () => {
  // --- Elements ---
  const btn        = document.getElementById("scoreBtn");
  const textEl     = document.getElementById("text");
  const platformEl = document.getElementById("platform");
  const resultDiv  = document.getElementById("result");
  const scoreNum   = document.getElementById("scoreNum");
  const gradeText  = document.getElementById("gradeText");
  const qualityGate = document.getElementById("qualityGate");
  const suggList   = document.getElementById("suggList");
  const scoreError = document.getElementById("scoreError");
  const charCount  = document.getElementById("charCount");
  const statusDot  = document.getElementById("statusDot");
  const statusText = document.getElementById("statusText");
  const suggestBtn = document.getElementById("suggestBtn");
  const insertBtn = document.getElementById("insertBtn");
  const toneEl = document.getElementById("tone");
  const assistOutput = document.getElementById("assistOutput");
  const auditSummary = document.getElementById("auditSummary");
  historyList = document.getElementById("historyList");
  const clearHistoryBtn = document.getElementById("clearHistoryBtn");
  const proofPostUrl = document.getElementById("proofPostUrl");
  const proofImpressions = document.getElementById("proofImpressions");
  const proofClicks = document.getElementById("proofClicks");
  const proofLikes = document.getElementById("proofLikes");
  const proofValuePerClick = document.getElementById("proofValuePerClick");
  const proofRevenue = document.getElementById("proofRevenue");
  const logOutcomeBtn = document.getElementById("logOutcomeBtn");
  const proofStatus = document.getElementById("proofStatus");

  loadSuggestionHistory();

  clearHistoryBtn.addEventListener("click", () => {
    suggestionHistory = [];
    chrome.storage.local.set({ cfSuggestionHistory: [] }, renderSuggestionHistory);
  });

  if (proofValuePerClick) proofValuePerClick.value = "1.0";

  // --- API health check on popup open ---
  statusDot.className = "status-dot loading";
  statusText.textContent = "Checking API...";
  chrome.runtime.sendMessage({ type: "ping" }, (resp) => {
    if (chrome.runtime.lastError || !resp) {
      setStatus("error", "Extension error — reload extension");
      return;
    }
    if (resp.ok) {
      setStatus("ok", `API online  ·  v${resp.version || "?"}`);
    } else if (resp.error && resp.error.includes("timed out")) {
      setStatus("loading", "API waking up — first request may be slow");
    } else {
      setStatus("error", "API unreachable — scores may fail");
    }
  });

  function setStatus(state, text) {
    statusDot.className = "status-dot " + state;
    statusText.textContent = text;
  }

  // --- Tab switching ---
  document.querySelectorAll(".tab-btn").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      document.getElementById("tab-score").style.display =
        tab.dataset.tab === "score" ? "block" : "none";
      document.getElementById("tab-compare").style.display =
        tab.dataset.tab === "compare" ? "block" : "none";
    });
  });

  // --- Auto-detect platform from current tab ---
  try {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs || !tabs[0]) return;
      const url = tabs[0].url || "";
      const map = {
        "x.com": "tweet", "twitter.com": "tweet",
        "linkedin.com": "linkedin", "instagram.com": "instagram",
        "facebook.com": "facebook", "threads.net": "threads",
      };
      for (const [host, plat] of Object.entries(map)) {
        if (url.includes(host)) {
          platformEl.value = plat;
          // Also sync compare platform selector
          const cmpP = document.getElementById("cmpPlatform");
          if (cmpP) {
            for (const opt of cmpP.options) {
              if (opt.value === plat) { cmpP.value = plat; break; }
            }
          }
          break;
        }
      }
    });
  } catch (_) { /* no tabs permission in some contexts */ }

  // --- Character counter ---
  textEl.addEventListener("input", () => {
    charCount.textContent = textEl.value.length;
  });

  // --- Score button ---
  btn.addEventListener("click", () => {
    const text = textEl.value.trim();
    if (!text) {
      showError(scoreError, "Type or paste some content first.");
      return;
    }
    hideError(scoreError);
    resultDiv.style.display = "none";

    btn.textContent = "Scoring...";
    btn.disabled = true;

    chrome.runtime.sendMessage(
      { type: "score", text, platform: platformEl.value },
      (resp) => {
        btn.textContent = "Score It";
        btn.disabled = false;

        if (chrome.runtime.lastError || !resp || resp.error) {
          const msg = resp?.error || "Connection error";
          if (resp?.offline || (msg && msg.includes("timed out"))) {
            showError(scoreError,
              `API is waking up (free tier cold start ~30s). ` +
              `Retrying automatically — or <a href="https://captainfredric.github.io/ContentForge/" target="_blank">check status</a>.`
            );
          } else {
            showError(scoreError, escapeHtml(msg));
          }
          return;
        }

        scoreNum.textContent = resp.score;
        scoreNum.style.color = gradeColor(resp.grade);
        gradeText.textContent = resp._fallback
          ? `Grade: ${resp.grade} (offline estimate)`
          : `Grade: ${resp.grade}`;

        // Quality gate badge
        if (resp.quality_gate && qualityGate) {
          qualityGate.textContent = resp.quality_gate;
          qualityGate.className = "quality-gate " + resp.quality_gate.toLowerCase();
          if (resp.operational_risk) {
            qualityGate.textContent += `  ·  Risk: ${resp.operational_risk}`;
          }
          qualityGate.style.display = "inline-block";
        } else if (qualityGate) {
          qualityGate.style.display = "none";
        }

        suggList.innerHTML = "";
        if (resp._note) {
          const li = document.createElement("li");
          li.style.color = "#f59e0b";
          li.textContent = resp._note;
          suggList.appendChild(li);
        }
        (resp.suggestions || []).slice(0, 5).forEach(s => {
          const li = document.createElement("li");
          li.textContent = s;
          suggList.appendChild(li);
        });
        resultDiv.style.display = "block";
      }
    );
  });

  textEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      btn.click();
    }
  });

  suggestBtn.addEventListener("click", () => {
    const text = textEl.value.trim();
    if (!text) {
      showError(scoreError, "Type content first, then ask for a rewrite.");
      return;
    }
    hideError(scoreError);

    suggestBtn.textContent = "Rewriting...";
    suggestBtn.disabled = true;
    insertBtn.disabled = true;
    latestOriginalText = text;

    chrome.runtime.sendMessage(
      { type: "suggest", text, platform: platformEl.value, tone: toneEl.value },
      (resp) => {
        suggestBtn.textContent = "Suggest Rewrite";
        suggestBtn.disabled = false;

        if (chrome.runtime.lastError || !resp || resp.error) {
          showError(scoreError, escapeHtml(resp?.error || "Rewrite failed"));
          return;
        }

        latestSuggestion = (resp.rewritten || "").trim();
        if (!latestSuggestion) {
          showError(scoreError, "Rewrite returned empty text. Try again.");
          return;
        }

        addSuggestionToHistory({
          text: latestSuggestion,
          platform: platformEl.value,
          tone: toneEl.value,
          createdAt: new Date().toISOString(),
        });

        assistOutput.style.display = "block";
        let outputText = latestSuggestion;
        if (resp._fallback && resp._note) outputText += `\n\nNote: ${resp._note}`;
        // Show lift and gate if API returned enriched improve_headline data
        if (resp.lift_percentage) outputText = `[${resp.lift_percentage} lift${resp.quality_gate ? "  ·  " + resp.quality_gate : ""}]\n\n` + outputText;
        assistOutput.textContent = outputText;
        // Audit summary brief
        if (auditSummary) {
          if (resp.audit_summary) {
            auditSummary.textContent = `Audit brief: ${resp.audit_summary}`;
            auditSummary.style.display = "block";
          } else {
            auditSummary.style.display = "none";
          }
        }
        insertBtn.disabled = false;
      }
    );
  });

  insertBtn.addEventListener("click", () => {
    if (!latestSuggestion) return;
    insertBtn.disabled = true;
    insertBtn.textContent = "Inserting...";

    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tabId = tabs?.[0]?.id;
      if (!tabId) {
        showError(scoreError, "No active tab found.");
        insertBtn.disabled = false;
        insertBtn.textContent = "Auto Insert";
        return;
      }

      chrome.tabs.sendMessage(tabId, { type: "insertText", text: latestSuggestion }, (resp) => {
        insertBtn.disabled = false;
        insertBtn.textContent = "Auto Insert";

        if (chrome.runtime.lastError || !resp || !resp.ok) {
          showError(scoreError, "Could not auto-insert on this page. Open a supported composer (X, LinkedIn, Instagram, Threads, Facebook) and try again.");
          return;
        }

        textEl.value = latestSuggestion;
        charCount.textContent = textEl.value.length;

        if (resp.truncated) {
          const limit = resp.maxLength || resp.insertedLength;
          showError(
            scoreError,
            `Inserted with platform limit: ${resp.insertedLength}/${limit} chars (` +
            `original ${resp.originalLength}).`
          );
          textEl.value = latestSuggestion.slice(0, resp.insertedLength);
          charCount.textContent = textEl.value.length;
        } else {
          hideError(scoreError);
        }
      });
    });
  });

  // --- Compare ---
  const cmpBtn    = document.getElementById("compareBtn");
  const cmpResult = document.getElementById("cmpResult");
  const cmpSummary = document.getElementById("cmpSummary");
  const cmpDetail = document.getElementById("cmpDetail");
  const cmpError  = document.getElementById("cmpError");

  cmpBtn.addEventListener("click", () => {
    const textA = document.getElementById("textA").value.trim();
    const textB = document.getElementById("textB").value.trim();
    const plat  = document.getElementById("cmpPlatform").value;
    if (!textA || !textB) {
      showError(cmpError, "Fill in both drafts to compare.");
      return;
    }
    hideError(cmpError);
    cmpResult.style.display = "none";

    cmpBtn.textContent = "Comparing...";
    cmpBtn.disabled = true;

    chrome.runtime.sendMessage(
      { type: "compare", text_a: textA, text_b: textB, platforms: [plat] },
      (resp) => {
        cmpBtn.textContent = "Compare";
        cmpBtn.disabled = false;

        if (chrome.runtime.lastError || !resp || resp.error) {
          const msg = resp?.error || "Connection error";
          if (resp?.offline) {
            showError(cmpError,
              `API unreachable — server may be waking up. Wait 15-30s and retry.`
            );
          } else if (msg.includes("HTTP 405") || msg.includes("HTTP 404")) {
            showError(cmpError, "Compare route unavailable on current deployment. Using fallback mode if possible.");
          } else {
            showError(cmpError, escapeHtml(msg));
          }
          return;
        }

        const comp = resp.comparisons?.[plat];
        if (!comp || comp.error) {
          showError(cmpError, escapeHtml(comp?.error || "Unknown scoring error"));
          return;
        }

        const winner = comp.winner === "tie" ? "Tie!" :
          `${comp.winner === "A" ? "Yours" : "Theirs"} wins!`;
        const winColor = comp.winner === "A" ? "#22c55e" :
          comp.winner === "B" ? "#ef4444" : "#f59e0b";
        cmpSummary.style.color = winColor;
        cmpSummary.textContent = `${winner} (${comp.score_a} vs ${comp.score_b})`;

        let html = `<div style="margin-top:4px">A: ${comp.grade_a} | B: ${comp.grade_b} | diff: ${Math.abs(comp.difference)} pts</div>`;
        if (comp.a_advantages?.length) {
          html += `<div class="strength" style="color:#22c55e">Your strengths:</div>`;
          comp.a_advantages.forEach(a => { html += `<div style="padding-left:8px">\u2022 ${escapeHtml(a)}</div>`; });
        }
        if (comp.b_advantages?.length) {
          html += `<div class="strength" style="color:#ef4444">Their strengths:</div>`;
          comp.b_advantages.forEach(a => { html += `<div style="padding-left:8px">\u2022 ${escapeHtml(a)}</div>`; });
        }
        cmpDetail.innerHTML = html;
        cmpResult.style.display = "block";
      }
    );
  });

  logOutcomeBtn.addEventListener("click", () => {
    const revisedText = (latestSuggestion || textEl.value || "").trim();
    if (!revisedText) {
      proofStatus.textContent = "Generate or select a rewrite first.";
      proofStatus.style.color = "#f59e0b";
      return;
    }

    logOutcomeBtn.disabled = true;
    logOutcomeBtn.textContent = "Logging...";
    proofStatus.textContent = "Recording score delta and outcomes...";
    proofStatus.style.color = "#9ca0c6";

    chrome.runtime.sendMessage({
      type: "logProof",
      payload: {
        platform: platformEl.value,
        original_text: (latestOriginalText || "").trim(),
        revised_text: revisedText,
        post_url: (proofPostUrl.value || "").trim(),
        impressions: Number(proofImpressions.value || 0),
        clicks: Number(proofClicks.value || 0),
        likes: Number(proofLikes.value || 0),
        value_per_click: Number(proofValuePerClick.value || 1),
        revenue_amount: Number(proofRevenue.value || 0),
      },
    }, (resp) => {
      logOutcomeBtn.disabled = false;
      logOutcomeBtn.textContent = "Log Outcome to Proof Dashboard";

      if (chrome.runtime.lastError || !resp || resp.error) {
        proofStatus.textContent = `Failed: ${resp?.error || "connection error"}`;
        proofStatus.style.color = "#ef4444";
        return;
      }

      proofStatus.textContent = `Logged: delta ${resp.score_delta ?? 0}, est lift $${resp.estimated_revenue_lift ?? 0}, realized $${resp.realized_revenue ?? 0}`;
      proofStatus.style.color = "#22c55e";
    });
  });
});

// --- Helpers ---
function gradeColor(grade) {
  if (!grade) return "#ef4444";
  const g = grade.charAt(0).toUpperCase();
  if (g === "A") return "#22c55e";
  if (g === "B") return "#3b82f6";
  if (g === "C") return "#f59e0b";
  return "#ef4444";
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function showError(el, html) {
  el.innerHTML = html;
  el.style.display = "block";
}
function hideError(el) {
  el.style.display = "none";
  el.innerHTML = "";
}

function loadSuggestionHistory() {
  chrome.storage.local.get({ cfSuggestionHistory: [] }, (data) => {
    suggestionHistory = Array.isArray(data.cfSuggestionHistory) ? data.cfSuggestionHistory.slice(0, 12) : [];
    renderSuggestionHistory();
  });
}

function addSuggestionToHistory(entry) {
  if (!entry || !entry.text) return;

  // Keep most recent unique drafts at the top.
  suggestionHistory = suggestionHistory.filter((x) => (x?.text || "") !== entry.text);
  suggestionHistory.unshift(entry);
  suggestionHistory = suggestionHistory.slice(0, 12);

  chrome.storage.local.set({ cfSuggestionHistory: suggestionHistory }, renderSuggestionHistory);
}

function renderSuggestionHistory() {
  if (!historyList) return;

  if (!suggestionHistory.length) {
    historyList.innerHTML = '<div class="history-meta">No rewrites yet. Generate one to build your playbook.</div>';
    return;
  }

  historyList.innerHTML = "";
  suggestionHistory.forEach((item, idx) => {
    const wrapper = document.createElement("div");
    wrapper.className = "history-item";

    const ts = item.createdAt ? new Date(item.createdAt) : null;
    const shortTs = ts && !Number.isNaN(ts.valueOf()) ? ts.toLocaleString() : "";
    const meta = document.createElement("div");
    meta.className = "history-meta";
    meta.textContent = `${(item.platform || "unknown").toUpperCase()} · ${item.tone || "engaging"}${shortTs ? ` · ${shortTs}` : ""}`;

    const txt = document.createElement("div");
    txt.className = "history-text";
    txt.textContent = item.text || "";

    const useBtn = document.createElement("button");
    useBtn.className = "history-use";
    useBtn.textContent = "Use this";
    useBtn.addEventListener("click", () => {
      latestSuggestion = item.text || "";
      const assistOutput = document.getElementById("assistOutput");
      const textEl = document.getElementById("text");
      const charCount = document.getElementById("charCount");
      const insertBtn = document.getElementById("insertBtn");
      if (assistOutput) {
        assistOutput.style.display = "block";
        assistOutput.textContent = latestSuggestion;
      }
      if (textEl && charCount) {
        textEl.value = latestSuggestion;
        charCount.textContent = latestSuggestion.length;
      }
      if (insertBtn) {
        insertBtn.disabled = !latestSuggestion;
      }
    });

    wrapper.appendChild(meta);
    wrapper.appendChild(txt);
    wrapper.appendChild(useBtn);
    historyList.appendChild(wrapper);
  });
}
