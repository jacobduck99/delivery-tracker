
// Create initial state from the DOM
export function allDropsLocal() {

  // Get all drop cards from the page
  const allCards = [...document.querySelectorAll('.drop-card[id^="drop-"]')];

  // Build a fresh array
  const queue = [];

  for (let i = 0; i < allCards.length; i++) {
    const card = allCards[i];

    // Get drop index from DOM attribute
    const dropIndex = Number(card.dataset.dropIndex);

    queue.push({
      dropIndex,
      status: "not_started",
      start_ts: null,
      end_ts: null,
      duration_ms: null
    });
  }

  localStorage.setItem("all_drops", JSON.stringify(queue));
};

