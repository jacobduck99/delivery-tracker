
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

function pickCurrent(list) {
  return (
    list.find(d => d.status === "in_progress") ||
    list.find(d => d.status === "not_started") ||
    null
  );
}

export function renderCard(record) {
  const { dropIndex, status, duration_ms } = record;

  if (status === "completed") {
    return `
      <article id="drop-${dropIndex}" class="drop-card" data-drop-index="${dropIndex}">
        <h4>Drop ${dropIndex}</h4>
        <div class="complete-badge">Completed ✓</div>
        <p class="drop-elapsed"><strong>Total-Time:</strong> ${fmtDuration(duration_ms || 0)}</p>
      </article>
    `;
  }

  if (status === "in_progress") {
    return `
      <article id="drop-${dropIndex}" class="drop-card" data-drop-index="${dropIndex}">
        <h4>Drop ${dropIndex}</h4>
        <form class="delivery-form">
          <input type="hidden" name="drop_index" value="${dropIndex}">
          <button class="delivered-btn" type="button" name="action" value="stop">Delivered</button>
        </form>
      </article>
    `;
  }

  // not_started
  return `
    <article id="drop-${dropIndex}" class="drop-card" data-drop-index="${dropIndex}">
      <h4>Drop ${dropIndex}</h4>
      <form class="arrival-form">
        <input type="hidden" name="drop_index" value="${dropIndex}">
        <button class="arrived-btn" type="button" name="action" value="start">Arrived / Start</button>
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
