(() => {
  const form = document.getElementById("analyzer-form");
  const input = document.getElementById("french-text");
  const count = document.getElementById("character-count");
  const submit = document.getElementById("analyze-button");
  const label = document.getElementById("analyze-button-label");
  const status = document.getElementById("analyzer-status");
  const errorBox = document.getElementById("analyzer-error");
  const results = document.getElementById("analysis-results");
  const empty = document.getElementById("analyzer-empty");
  const strip = document.getElementById("token-strip");
  const table = document.getElementById("analysis-table-body");
  const inspector = document.getElementById("word-inspector");
  const exampleButtons = [...document.querySelectorAll("[data-example]")];
  let busy = false;
  let data = null;

  const node = (tag, text, className) => {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  };

  const tokenClass = pos => ({ NOUN: "token-noun", PROPN: "token-noun", VERB: "token-verb", AUX: "token-verb", PRON: "token-pron", DET: "token-det", ADJ: "token-adj" }[pos] || "token-other");

  function setBusy(value) {
    busy = value;
    submit.disabled = value;
    input.readOnly = value;
    exampleButtons.forEach(button => { button.disabled = value; });
    label.textContent = value ? "Analyzing…" : "Analyze sentence";
    form.setAttribute("aria-busy", String(value));
  }

  function showError(message) {
    errorBox.textContent = message;
    errorBox.hidden = false;
    status.textContent = "";
  }

  function selectToken(id) {
    const token = data.tokens.find(item => item.id === id);
    if (!token) return;
    strip.querySelectorAll("button").forEach(button => { button.setAttribute("aria-pressed", String(Number(button.dataset.id) === id)); });
    table.querySelectorAll("tr").forEach(row => { row.dataset.selected = String(Number(row.dataset.id) === id); });
    const word = node("div", undefined, "inspector-word");
    const heading = node("h3", token.text);
    heading.lang = "fr";
    word.append(heading, node("p", `Base form: ${token.lemma || "Not identified"}`));
    const details = node("dl", undefined, "inspector-details");
    const relation = token.head_id === token.id ? "Sentence root (no parent word)" : Number.isInteger(token.head_id) ? `“${token.head}” · token ${token.head_id + 1}` : "Not identified";
    [["Word class", token.pos_label], ["Grammatical role", token.dependency_label], ["Related word", relation], ["Available features", token.morphology_label || "No features identified for this token."]].forEach(([term, value]) => {
      const group = node("div");
      group.append(node("dt", term), node("dd", value || "Not identified"));
      details.append(group);
    });
    inspector.replaceChildren(word, details);
  }

  function render(payload) {
    data = payload;
    document.getElementById("analysis-original").textContent = payload.text;
    const summary = payload.summary;
    document.getElementById("analysis-summary").textContent = `${summary.word_count} ${summary.word_count === 1 ? "word" : "words"} · ${summary.token_count} tokens · ${summary.sentence_count} ${summary.sentence_count === 1 ? "sentence" : "sentences"}`;
    strip.replaceChildren();
    table.replaceChildren();
    payload.tokens.forEach(token => {
      const button = node("button", undefined, `grammar-token ${tokenClass(token.pos)}`);
      button.type = "button";
      button.dataset.id = token.id;
      button.setAttribute("aria-pressed", "false");
      button.setAttribute("aria-label", `${token.text}: ${token.pos_label}. Inspect word ${token.id + 1}.`);
      const text = node("span", token.text);
      text.lang = "fr";
      button.append(text, node("span", token.pos_label));
      button.addEventListener("click", () => selectToken(token.id));
      strip.append(button);
      const row = node("tr");
      row.dataset.id = token.id;
      const head = token.head_id === token.id ? "— Root" : Number.isInteger(token.head_id) ? `${token.head} (${token.head_id + 1})` : "—";
      [token.text, token.lemma || "—", token.pos_label, token.dependency_label, head, token.morphology_label || "—"].forEach((value, index) => {
        const cell = node("td", value);
        if (index < 2) cell.lang = "fr";
        row.append(cell);
      });
      table.append(row);
    });
    const notes = document.getElementById("analysis-notes");
    notes.replaceChildren(node("p", "Roles describe dependency relationships. Token numbering includes punctuation; elided forms may be split into separate tokens."));
    (payload.warnings || []).forEach(warning => notes.append(node("p", warning)));
    notes.append(node("p", `Analysis model: ${payload.model}.`));
    empty.hidden = true;
    results.hidden = false;
    if (payload.tokens.length) selectToken(payload.tokens[0].id);
    document.getElementById("results-title").focus({ preventScroll: true });
    results.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "start" });
  }

  input.addEventListener("input", () => {
    count.textContent = `${input.value.length} / 500`;
    input.setCustomValidity("");
    errorBox.hidden = true;
  });

  form.addEventListener("submit", async event => {
    event.preventDefault();
    if (busy) return;
    errorBox.hidden = true;
    const text = input.value.trim();
    if (!text) { input.setCustomValidity("Enter a French sentence first."); input.reportValidity(); return; }
    if (window.location.protocol === "file:") {
      showError("The French analyzer needs its Python backend. Open the deployed Vercel website, or follow the local-server instructions in START_HERE.html.");
      return;
    }
    setBusy(true);
    status.textContent = "Analyzing your sentence. The first request may take a little longer while the language model loads.";
    results.hidden = true;
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 55000);
    try {
      const response = await fetch("/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Accept": "application/json" },
        body: JSON.stringify({ text }),
        signal: controller.signal
      });
      const contentType = response.headers.get("content-type") || "";
      if (!contentType.includes("application/json")) {
        throw new Error(response.status === 404 ? "The Python endpoint was not found. Check that the complete project, including the api folder, was deployed." : "The server could not return an analysis. Please wait a moment and try again.");
      }
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.error && payload.error.message ? payload.error.message : "The sentence could not be analyzed. Please try again.");
      }
      if (!Array.isArray(payload.tokens) || !payload.tokens.length || !payload.summary) throw new Error("The server returned an incomplete analysis. Please try another sentence.");
      render(payload);
      status.textContent = "Analysis complete. Select a word below to explore its details.";
    } catch (error) {
      showError(error.name === "AbortError" ? "The analysis took too long. Please try again; the language model may still be starting." : error.message || "Could not reach the analyzer. Check your connection and try again.");
      empty.hidden = false;
    } finally {
      clearTimeout(timeout);
      setBusy(false);
    }
  });

  exampleButtons.forEach(button => button.addEventListener("click", () => {
    if (busy) return;
    input.value = button.dataset.example;
    input.dispatchEvent(new Event("input"));
    form.requestSubmit();
  }));

  document.getElementById("new-sentence-button").addEventListener("click", () => {
    input.focus();
    input.select();
    form.scrollIntoView({ behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth", block: "center" });
  });
})();
