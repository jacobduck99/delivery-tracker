
function fmtDuration(ms) {
  if (!Number.isFinite(ms) || ms < 0) return "0:00";
  const s = Math.floor(ms / 1000);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return h > 0
    ? `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`
    : `${m}:${String(sec).padStart(2, "0")}`;
}

export function allDropsLocal() {
  const existing = JSON.parse(localStorage.getItem("all_drops") || "[]");
  if (existing.length) return;
  const allCards = [...document.querySelectorAll('.drop-card[id^="drop-"]')];
  const queue = allCards.map((card) => ({
    dropIndex: Number(card.dataset.dropIndex),
    status: "not_started",
    start_ts: null,
    end_ts: null,
    duration_ms: null
  }));
  localStorage.setItem("all_drops", JSON.stringify(queue));
}

export function changeStatus(dropIndex, status) {
  const all_drops = JSON.parse(localStorage.getItem("all_drops") || "[]");
  const drop = all_drops.find(d => d.dropIndex === dropIndex);
  if (!drop) return;
  drop.status = status;
  if (status === "in_progress") {
    drop.start_ts = Date.now();
  } else if (status === "completed") {
    drop.end_ts = Date.now();
    drop.duration_ms = drop.end_ts - (drop.start_ts || drop.end_ts);
  }
  localStorage.setItem("all_drops", JSON.stringify(all_drops));
}

function drainQueue() {
  if (!navigator.onLine) {
    console.log("skip drain: offline");
    return;
  }
  const queue = JSON.parse(localStorage.getItem("pending_queue_v1") || "[]");
  if (queue.length === 0) return;

  const first = queue[0];

  fetch("/api/drop", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "same-origin",
    cache: "no-store",
    body: JSON.stringify(first),
  })
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      return r.json();
    })
    .then((res) => {
      if (res && res.ok) {
        queue.shift();
        localStorage.setItem("pending_queue_v1", JSON.stringify(queue));
        setTimeout(drainQueue, 0); // drain next
      } else {
        console.warn("Server rejected item:", res);
      }
    })
    .catch((err) => {
      console.warn("Send failed:", err.message || err);
    });
}

export function syncDrops() {
    const localArray = JSON.parse(localStorage.getItem("all_drops") || "[]");
    const copyLocal = [ ...localArray ];
    
    
    const completed = copyLocal.filter(d => d.status === "completed");
    if (completed.length === 0) return; 
    
    const queue = JSON.parse(localStorage.getItem("pending_queue_v1") || "[]");
    
    
    for (const d of completed) {
        const drop_index = Number(d.dropIndex); 
        queue.push({
        drop_index,
        start_ts: d.start_ts,
        stop_ts: d.end_ts,
        duration_ms: d.duration_ms
        });
    }
    
    localStorage.setItem("pending_queue_v1", JSON.stringify(queue));
    if (navigator.onLine) setTimeout(drainQueue, 0);

};

function pickCurrent(list) {
  // If something is running, that's current
  const running = list.find(d => d.status === "in_progress");
  if (running) return running;

  // During the hold window, keep showing the just-completed card
  const held = getActiveHold(list);
  if (held) return held;

  // Otherwise, show the first not_started (or nothing)
  return list.find(d => d.status === "not_started") || null;
}

export function renderCard(record) {
  const { dropIndex, status, duration_ms } = record;

  // Completed
  if (status === "completed") {
    return `
      <article id="drop-${dropIndex}" class="drop-card" data-drop-index="${dropIndex}">
        <h4>Drop ${dropIndex}</h4>

        <div class="gps-section">
          <input type="text" name="address" placeholder="Enter address">
          <button type="button" class="gps-btn">📍 Open in Maps</button>
        </div>

        <div class="complete-badge">Completed ✓</div>
        <p class="drop-elapsed"><strong>Total-Time:</strong> ${fmtDuration(duration_ms || 0)}</p>
      </article>
    `;
  }

  // In Progress
  if (status === "in_progress") {
    return `
      <article id="drop-${dropIndex}" class="drop-card" data-drop-index="${dropIndex}">
        <h4>Drop ${dropIndex}</h4>

        <div class="gps-section">
          <input type="text" name="address" placeholder="Enter address">
          <button type="button" class="gps-btn">📍 Open in Maps</button>
        </div>

        <form class="delivery-form">
          <input type="hidden" name="drop_index" value="${dropIndex}">
          <button class="delivered-btn" type="button" name="action" value="stop">Delivered</button>
        </form>
      </article>
    `;
  }

  // Not Started
  return `
    <article id="drop-${dropIndex}" class="drop-card" data-drop-index="${dropIndex}">
      <h4>Drop ${dropIndex}</h4>

      <div class="gps-section">
        <input type="text" name="address" placeholder="Enter address">
        <button type="button" class="gps-btn">📍 Open in Maps</button>
      </div>

      <form class="arrival-form">
        <input type="hidden" name="drop_index" value="${dropIndex}">
        <button class="arrived-btn" type="button" name="action" value="start">Arrived</button>
      </form>
    </article>
  `;
}


export function render() {
  const list = JSON.parse(localStorage.getItem("all_drops") || "[]");
  const current = pickCurrent(list);
  const completed = list.filter(d => d.status === "completed");
  const upcoming = list.filter(d =>
    d.status === "not_started" && (!current || d.dropIndex !== current.dropIndex)
  );

  const completedCounter = document.getElementById("completed-count");
  const upcomingCounter  = document.getElementById("upcoming-count");
  if (completedCounter) completedCounter.textContent = String(completed.length);
  if (upcomingCounter)  upcomingCounter.textContent  = String(upcoming.length);

  const currentSlot   = document.getElementById("current-drop-slot");
  const upcomingList  = document.getElementById("upcoming-list");
  const completedList = document.getElementById("completed-list");

  if (currentSlot) {
    currentSlot.innerHTML = current ? renderCard(current) : "";
  }
  if (upcomingList) {
    upcomingList.innerHTML =
      (upcoming.length
        ? upcoming.map(r => `<li>${renderCard(r)}</li>`).join("")
        : `<li class="empty-msg">No upcoming drops</li>`);
  }
  if (completedList) {
    completedList.innerHTML =
      (completed.length
        ? completed.map(r => `<li>${renderCard(r)}</li>`).join("")
        : `<li class="empty-msg">No completed drops yet</li>`);
  }
}

export function promoteNextDrop() {
  const list = JSON.parse(localStorage.getItem("all_drops") || "[]");

  // If something is already running → Current stays that.
  if (list.some(d => d.status === "in_progress")) {
    localStorage.removeItem("current_hint");
    return;
  }

  // Otherwise pick the next not_started
  const next = list.find(d => d.status === "not_started");
  if (next) {
    localStorage.setItem("current_hint", String(next.dropIndex));
  } else {
    localStorage.removeItem("current_hint");
  }
}

export function setHold(ms, dropIndex) {
  const until = Date.now() + ms;
  localStorage.setItem("hold_current_until", String(until));
  localStorage.setItem("hold_current_index", String(dropIndex));
}

export function clearHold() {
  localStorage.removeItem("hold_current_until");
  localStorage.removeItem("hold_current_index");
}

export function getActiveHold(list) {
  const until = Number(localStorage.getItem("hold_current_until") || "0");
  if (!Number.isFinite(until)) return null;

  if (Date.now() < until) {
    const idx = Number(localStorage.getItem("hold_current_index") || "0");
    if (!idx) return null;
    return list.find(d => d.dropIndex === idx) || null; // completed record
  } else {
    clearHold();
    return null;
  }
}
