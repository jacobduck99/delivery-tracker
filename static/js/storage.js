// storage.js (v21)
console.log("storage.js v21 loaded");

/* ---------- helpers ---------- */
function keyFor(dropIndex) {
  return `drop-${Number(dropIndex)}`;
}
function getRecord(key) {
  try { return JSON.parse(localStorage.getItem(key) || "{}"); }
  catch { return {}; }
}
function setRecord(key, record) {
  localStorage.setItem(key, JSON.stringify(record));
}
function fmtDuration(ms) {
  if (!Number.isFinite(ms) || ms < 0) return "0:00";
  const s = Math.floor(ms / 1000);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  return h > 0 ? `${h}:${String(m).padStart(2,"0")}:${String(sec).padStart(2,"0")}`
               : `${m}:${String(sec).padStart(2,"0")}`;
}

/* ---------- queue drain ---------- */
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
        setTimeout(drainQueue, 0);
      } else {
        console.warn("Server rejected item:", res);
      }
    })
    .catch((err) => console.warn("Send failed:", err.message || err));
}

/* ---------- timing + queue ---------- */
function addDuration(action, key) {
  const record = getRecord(key);

  if (action === "start") {
    record.start_ts = Date.now();
    delete record.stop_ts;
    delete record.duration_ms;
  } else if (action === "stop") {
    if (typeof record.start_ts === "number") {
      record.stop_ts = Date.now();
      record.duration_ms = record.stop_ts - record.start_ts;

      const queue = JSON.parse(localStorage.getItem("pending_queue_v1") || "[]");
      const drop_index = Number(key.split("-")[1]);
      queue.push({
        drop_index,
        start_ts: record.start_ts,
        stop_ts: record.stop_ts,
        duration_ms: record.duration_ms,
      });
      localStorage.setItem("pending_queue_v1", JSON.stringify(queue));
      if (navigator.onLine) setTimeout(drainQueue, 0);
    } else {
      return record;
    }
  }
  setRecord(key, record);
  return record;
}

/* ---------- DOM swapping (no page reload) ---------- */
function swapToDelivered(form, dropIndex) {
  // Replace current form contents with a Delivered button
  form.innerHTML = `
    <input type="hidden" name="drop_index" value="${dropIndex}">
    <button class="delivered-btn" type="button" name="action" value="stop">Delivered</button>
  `;
}
function swapToCompleted(form, durationMs) {
  const card = form.closest(".drop-card");
  form.remove(); // remove the form row
  const badge = document.createElement("div");
  badge.className = "complete-badge";
  badge.textContent = "Completed ✓";
  card.appendChild(badge);

  // Also show elapsed (client-side)
  const p = document.createElement("p");
  p.className = "drop-elapsed";
  p.innerHTML = `<strong>Total-Time:</strong> ${fmtDuration(durationMs)}`;
  card.appendChild(p);
}

/* ---------- Event delegation for buttons ---------- */
document.addEventListener("click", (e) => {
  const btn = e.target.closest(".arrived-btn, .delivered-btn");
  if (!btn) return;

  e.preventDefault(); // block any form submission
  const form = btn.closest("form");
  if (!form) return;

  const raw = form.querySelector('input[name="drop_index"]');
  if (!raw) return;

  const dropIndex = Number(raw.value);
  if (!Number.isFinite(dropIndex)) return;

  const action = btn.value; // "start" or "stop"
  const key = keyFor(dropIndex);
  const record = addDuration(action, key);

  // Swap UI to the next state without reload
  if (action === "start") {
    swapToDelivered(form, dropIndex);
  } else if (action === "stop") {
    swapToCompleted(form, record?.duration_ms ?? 0);
  }
});

/* ---------- online/offline ---------- */
window.addEventListener("online", () => {
  console.log("online");
  drainQueue();
});
window.addEventListener("offline", () => console.log("offline"));

/* ---------- boot ---------- */
document.addEventListener("DOMContentLoaded", () => {
  // ensure queue key exists
  if (!localStorage.getItem("pending_queue_v1")) {
    localStorage.setItem("pending_queue_v1", "[]");
  }
  // prevent accidental submit on delivery forms (Enter key)
  document.querySelectorAll(".delivery-form").forEach((f) =>
    f.addEventListener("submit", (e) => e.preventDefault())
  );
  // drain any leftovers
  if (navigator.onLine) drainQueue();
});
