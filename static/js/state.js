
export const state = {
  currentDrop: [],     // holds 0 or 1 id
  upcomingDrops: [],   // ids
  completedDrops: []   // ids
};

// Build state from the DOM once on page load
export function initialiseStateFromDom() {
  const allDrops = [...document.querySelectorAll('.drop-card[id^="drop-"]')];

  state.currentDrop = [];
  state.upcomingDrops = [];
  state.completedDrops = []; // empty at the start

  for (let i = 0; i < allDrops.length; i++) {
    const id = allDrops[i].id;
    if (i === 0) {
      state.currentDrop.push(id);
    } else {
      state.upcomingDrops.push(id);
    }
  }

  render();
}

// Render = update counters + place cards in containers
export function render() {
  const { upcomingDrops, completedDrops } = state;

  const completedCounter = document.getElementById("completed-count");
  if (completedCounter) completedCounter.textContent = String(completedDrops.length);

  const upcomingCounter = document.getElementById("upcoming-count");
  if (upcomingCounter) upcomingCounter.textContent = String(upcomingDrops.length);

  placeCards();  // <-- keep DOM in sync with state here
}

// Complete the current drop and promote the next
export function completeCurrentDrop() {
  const finished = state.currentDrop.shift(); // remove current if present
  if (finished) state.completedDrops.push(finished);

  const next = state.upcomingDrops.shift();   // pull the next upcoming
  if (next) state.currentDrop.push(next);

  render();
  localStorage.setItem("deliveryState", JSON.stringify(state));
}

// Move the actual DOM nodes to match state
export function placeCards() {
  const currentDropContainer   = document.getElementById("current-drop-slot");
  const upcomingDropsContainer = document.getElementById("upcoming-list");
  const completedDropsContainer= document.getElementById("completed-list");

  if (currentDropContainer) {
    currentDropContainer.innerHTML = "";
    for (let id of state.currentDrop) {
      const card = document.getElementById(id);
      if (card) currentDropContainer.append(card);
    }
  }

  if (upcomingDropsContainer) {
    upcomingDropsContainer.innerHTML = "";
    for (let id of state.upcomingDrops) {
      const card = document.getElementById(id);
      if (card) upcomingDropsContainer.append(card);
    }
  }

  if (completedDropsContainer) {
    completedDropsContainer.innerHTML = "";
    for (let id of state.completedDrops) {
      const card = document.getElementById(id);
      if (card) completedDropsContainer.append(card);
    }
  }
} 

function getRecord(key) {
  try { return JSON.parse(localStorage.getItem(key) || "{}"); }
  catch { return {}; }
}

export function addDropsLocal() {
    const allDrops = [...document.querySelectorAll('.drop-card[id^="drop-"]')];
    const queue = JSON.parse(localStorage.getItem("all_drops") || "[]");

    for (const idx of allDrops) {
        const dropIndex = Number(idx.id.split("-")[1]);

        const record = {
            dropIndex: dropIndex,
            status: "not_started"
        };

        queue.push(record);
    }

    localStorage.setItem("all_drops", JSON.stringify(queue));
}
