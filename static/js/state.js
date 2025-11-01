
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

export function changeStatus(dropIndex, status) {
  // load state
  const all_drops = JSON.parse(localStorage.getItem("all_drops") || "[]");

  // find the correct drop
  const drop = all_drops.find(d => d.dropIndex === dropIndex);
  if (!drop) return;

  // update its status
  drop.status = status;

  // handle timestamps
  if (status === "in_progress") {
    drop.start_ts = Date.now();
  } else if (status === "completed") {
    drop.end_ts = Date.now();
    drop.duration_ms = drop.end_ts - drop.start_ts;
  }

  // save updated state
  localStorage.setItem("all_drops", JSON.stringify(all_drops));
}


