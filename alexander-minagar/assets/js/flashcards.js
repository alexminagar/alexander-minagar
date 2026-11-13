(() => {
  const grid = document.getElementById("deck-grid");
  if (!grid) return;

  const picker = document.getElementById("deck-picker");
  const studyPanel = document.getElementById("study-panel");
  const completePanel = document.getElementById("complete-panel");
  const error = document.getElementById("deck-error");
  const stage = document.getElementById("study-card");
  const question = document.getElementById("card-question");
  const answer = document.getElementById("card-answer");
  const answerPanel = document.getElementById("answer-panel");
  const note = document.getElementById("card-note");
  const reveal = document.getElementById("reveal-answer");
  const think = document.getElementById("card-think");
  const previous = document.getElementById("previous-card");
  const next = document.getElementById("next-card");
  const announcer = document.getElementById("study-announcer");
  const rawDecks = Array.isArray(window.FLASHCARD_DECKS) ? window.FLASHCARD_DECKS : [];
  const themes = ["film", "french", "web"];
  const symbols = { film: "▤", french: "Aa", web: "</>" };
  const decks = rawDecks.filter(deck => deck && typeof deck.title === "string" && Array.isArray(deck.cards)).map((deck, index) => ({
    id: typeof deck.id === "string" ? deck.id : "deck-" + index,
    title: deck.title,
    description: typeof deck.description === "string" ? deck.description : "A collection of questions to explore.",
    theme: themes.includes(deck.theme) ? deck.theme : "web",
    label: typeof deck.label === "string" ? deck.label : "A little practice",
    cards: deck.cards.filter(card => card && typeof card.question === "string" && card.question.trim() && typeof card.answer === "string" && card.answer.trim()).map((card, cardIndex) => ({ question: card.question, answer: card.answer, note: typeof card.note === "string" ? card.note : "", key: cardIndex }))
  })).filter(deck => deck.cards.length > 0);
  let activeDeck = null;
  let cards = [];
  let position = 0;
  let answerVisible = false;
  let revealedCards = new Set();

  const element = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  };

  const arrowIcon = (pathData = "M5 15 15 5M5 5h10v10") => {
    const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icon.setAttribute("class", "recall-inline-icon");
    icon.setAttribute("viewBox", "0 0 20 20");
    icon.setAttribute("aria-hidden", "true");
    icon.setAttribute("focusable", "false");
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("d", pathData);
    icon.append(path);
    return icon;
  };

  const focusStage = () => stage.focus({ preventScroll: true });

  const renderCard = () => {
    const card = cards[position];
    if (!card) return;
    answerVisible = false;
    question.textContent = card.question;
    answer.textContent = card.answer;
    note.textContent = card.note;
    note.hidden = !card.note;
    answerPanel.hidden = true;
    think.hidden = false;
    reveal.hidden = false;
    reveal.setAttribute("aria-expanded", "false");
    document.getElementById("card-side").textContent = "Question";
    document.getElementById("card-number").textContent = String(position + 1).padStart(2, "0");
    document.getElementById("study-count").textContent = "Card " + (position + 1) + " of " + cards.length;
    const progress = document.getElementById("study-progress");
    progress.max = cards.length;
    progress.value = position + 1;
    progress.setAttribute("aria-valuetext", "Card " + (position + 1) + " of " + cards.length);
    previous.disabled = position === 0;
    next.replaceChildren(document.createTextNode(position === cards.length - 1 ? "Finish deck" : "Next card"), arrowIcon(position === cards.length - 1 ? "m4 10 4 4 8-8" : "m11 5 5 5-5 5M4 10h12"));
    document.getElementById("study-nudge").textContent = "Think first. Reveal when ready.";
    announcer.textContent = "Card " + (position + 1) + " of " + cards.length + ". " + card.question;
    focusStage();
  };

  const shuffleCards = list => {
    const shuffled = list.slice();
    for (let i = shuffled.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    if (shuffled.length > 1 && shuffled.every((card, index) => card.key === list[index].key)) shuffled.push(shuffled.shift());
    return shuffled;
  };

  const beginDeck = (deck, shuffled = false) => {
    if (!deck || !deck.cards.length) return;
    activeDeck = deck;
    cards = shuffled ? shuffleCards(deck.cards) : deck.cards.slice();
    position = 0;
    revealedCards = new Set();
    picker.hidden = true;
    completePanel.hidden = true;
    studyPanel.hidden = false;
    document.getElementById("study-deck-title").textContent = deck.title;
    document.getElementById("study-category").textContent = deck.label;
    document.getElementById("study-order").textContent = (shuffled ? "Shuffled" : "In order") + " · At your pace";
    renderCard();
  };

  const revealAnswer = () => {
    if (!activeDeck || answerVisible || studyPanel.hidden) return;
    answerVisible = true;
    revealedCards.add(cards[position].key);
    answerPanel.hidden = false;
    think.hidden = true;
    reveal.hidden = true;
    reveal.setAttribute("aria-expanded", "true");
    document.getElementById("card-side").textContent = "Question + answer";
    document.getElementById("study-nudge").textContent = "Ready for the next one?";
    announcer.textContent = "Answer: " + cards[position].answer + (cards[position].note ? " " + cards[position].note : "");
    focusStage();
  };

  const finishDeck = () => {
    studyPanel.hidden = true;
    picker.hidden = true;
    completePanel.hidden = false;
    document.getElementById("complete-description").textContent = activeDeck.title + " · You revealed " + revealedCards.size + " of " + cards.length + " answers in this session.";
    document.getElementById("complete-title").focus({ preventScroll: true });
    announcer.textContent = "Deck complete. Choose what to do next.";
  };

  const moveNext = () => {
    if (!activeDeck || studyPanel.hidden) return;
    if (position === cards.length - 1) {
      finishDeck();
      return;
    }
    position += 1;
    renderCard();
  };

  const movePrevious = () => {
    if (!activeDeck || studyPanel.hidden || position === 0) return;
    position -= 1;
    renderCard();
  };

  const chooseDeck = () => {
    studyPanel.hidden = true;
    completePanel.hidden = true;
    picker.hidden = false;
    const target = activeDeck ? Array.from(grid.querySelectorAll("button")).find(button => button.dataset.deckId === activeDeck.id) : null;
    (target || document.getElementById("deck-picker-title")).focus({ preventScroll: true });
    announcer.textContent = "Choose a deck to start a new session.";
  };

  decks.forEach(deck => {
    const button = element("button", "recall-deck recall-deck--" + deck.theme);
    button.type = "button";
    button.dataset.deckId = deck.id;
    button.setAttribute("aria-label", "Study " + deck.title + ", " + deck.cards.length + " cards");
    const top = element("span", "recall-deck-top");
    const symbol = element("span", "recall-deck-symbol", symbols[deck.theme]);
    symbol.setAttribute("aria-hidden", "true");
    top.append(symbol, element("span", "recall-deck-count", deck.cards.length + " cards"));
    const start = element("span", "recall-deck-start");
    const arrow = arrowIcon();
    start.append(element("span", "", "Start studying"), arrow);
    button.append(top, element("span", "recall-deck-title", deck.title), element("span", "recall-deck-description", deck.description), start);
    button.addEventListener("click", () => beginDeck(deck));
    grid.append(button);
  });

  error.hidden = decks.length > 0;
  reveal.addEventListener("click", revealAnswer);
  next.addEventListener("click", moveNext);
  previous.addEventListener("click", movePrevious);
  document.getElementById("change-deck").addEventListener("click", chooseDeck);
  document.getElementById("choose-another").addEventListener("click", chooseDeck);
  document.getElementById("study-again").addEventListener("click", () => beginDeck(activeDeck));
  document.getElementById("shuffle-again").addEventListener("click", () => beginDeck(activeDeck, true));

  stage.addEventListener("keydown", event => {
    if (event.target !== stage || event.altKey || event.ctrlKey || event.metaKey || event.shiftKey || event.repeat) return;
    if (event.key === " " || event.key === "Enter") {
      event.preventDefault();
      revealAnswer();
    } else if (event.key === "ArrowRight") {
      event.preventDefault();
      moveNext();
    } else if (event.key === "ArrowLeft") {
      event.preventDefault();
      movePrevious();
    }
  });
})();
