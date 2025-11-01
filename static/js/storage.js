import { promoteNextDrop, initialiseQueueFromDom } from "./upcoming.js";
import { allDropsLocal, changeStatus } from "./state.js";
// storage.js (v24)
console.log("storage.js v24 loaded");

/* ========================
   Idle / Run Failsafe
======================== */
const FIVE_HOURS = 5 * 60 * 60 * 1000; // 5h in ms

function updateLastActive() {
  localStorage.setItem('lastActive', Date.now().toString());
}

// Safety net: only clear if a run is active AND they were inactive >5h
function clearIfForgotEndShift() {
  const hasActiveRun = localStorage.getItem('runActive') === '1';
  if (!hasActiveRun) return;

  const lastActive = localStorage.getItem('lastActive');
  if (!lastActive) return;

  const inactiveTime = Date.now() - parseInt(lastActive, 10);
  if (inactiveTime > FIVE_HOURS) {
    console.log("No activity for 5+ hours with run active — auto-clearing");
    // full reset of UI cache
    localStorage.clear();
    // be explicit (in case clear() changes later)
    localStorage.removeItem('runActive');
    // Optional: hard reset the DOM so nothing stale lingers
    // location.reload();
  }
}

// Count user activity
window.addEventListener('click', updateLastActive);
window.addEventListener('keydown', updateLastActive);
window.addEventListener('touchstart', updateLastActive);
// If they close the tab quickly, still capture a fresh timestamp
window.addEventListener('beforeunload', updateLastActive);

// Run the safety check on boot, on return, and periodically
document.addEventListener('DOMContentLoaded', clearIfForgotEndShift);
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) clearIfForgotEndShift();
});
setInterval(clearIfForgotEndShift, 5 * 60 * 1000); // every 5 min

/* ========================
   Helpers
======================== */
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

/* ========================
   Queue drain (POST to backend)
======================== */
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

/* ========================
   Timing + queue writes
======================== */
function addDuration(action, key) {
  // Count real actions as activity (keeps the 5h clock honest)
  updateLastActive();

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
      return record; // ignore invalid stop
    }
  }

  setRecord(key, record);
  return record;
}

/* ========================
   DOM swapping (no reload)
======================== */
function swapToDelivered(form, dropIndex) {
  form.innerHTML = `
    <input type="hidden" name="drop_index" value="${dropIndex}">
    <button class="delivered-btn" type="button" name="action" value="stop">Delivered</button>
  `;
}

// function swapToCompleted(form, durationMs) {
//   const card = form.closest(".drop-card");
//   if (!card) return;

//   // We used to mutate the DOM directly. Now UI should be driven by state + render().
//   // So this whole function is no longer used.

//   // form.remove();

//   // if (!card.querySelector(".complete-badge")) {
//   //   const badge = document.createElement("div");
//   //   badge.className = "complete-badge";
//   //   badge.textContent = "Completed ✓";
//   //   card.appendChild(badge);
//   // }

//   // if (!card.querySelector(".drop-elapsed")) {
//   //   const p = document.createElement("p");
//   //   p.className = "drop-elapsed";
//   //   p.innerHTML = `<strong>Total-Time:</strong> ${fmtDuration(durationMs)}`;
//   //   card.appendChild(p);
//   // }
// }


/* ========================
   Rehydrate UI from localStorage
   (so refresh looks right offline)
======================== */

function rehydrateFromLocal() {
  const completedList = document.getElementById("completed-list");
  if (!completedList) return;

  const allCards = [...document.querySelectorAll('.drop-card[id^="drop-"]')];
  const completed = [];

  // First pass: ensure card UI and collect completed
  for (const card of allCards) {
    const idx = Number(card.id.split("-")[1]);
    if (!Number.isFinite(idx)) continue;

    const rec = getRecord(keyFor(idx));
    const form = card.querySelector(".delivery-form");

    // no local state → leave as is
    if (typeof rec.start_ts !== "number" && typeof rec.stop_ts !== "number") continue;

    if (typeof rec.start_ts === "number" && typeof rec.stop_ts !== "number") {
      if (form && !form.querySelector(".delivered-btn")) swapToDelivered(form, idx);
      continue;
    }

    if (typeof rec.stop_ts === "number") {
      // Ensure completed UI
      if (form) {
        swapToCompleted(form, rec.duration_ms || 0);
      } else {
        if (!card.querySelector(".complete-badge")) {
          const badge = document.createElement("div");
          badge.className = "complete-badge";
          badge.textContent = "Completed ✓";
          card.appendChild(badge);
        }
        if (!card.querySelector(".drop-elapsed")) {
          const p = document.createElement("p");
          p.className = "drop-elapsed";
          p.innerHTML = `<strong>Total-Time:</strong> ${fmtDuration(rec.duration_ms || 0)}`;
          card.appendChild(p);
        }
      }

      completed.push({ card, stop: Number(rec.stop_ts) || 0 });
    }
  }

  // 🔁 FULL REBUILD to enforce order
  // Remove any existing children so server order doesn't persist
  completedList.innerHTML = "";

  // Sort newest→oldest, then append in that order
  completed
    .sort((a, b) => b.stop - a.stop)
    .forEach(({ card }) => {
      const li = document.createElement("li");
      li.appendChild(card);
      completedList.appendChild(li);
    });

    // Empty msg + count
  const emptyMsg = completedList.querySelector(".empty-msg");
  if (emptyMsg && completed.length) emptyMsg.remove();

  const countEl = document.getElementById("completed-count");
  if (countEl) countEl.textContent = String(completedList.querySelectorAll(":scope > li").length);
        promoteNextDrop();
}


/* ========================
   Events
======================== */
// Event delegation for Arrived/Delivered
document.addEventListener("click", (e) => {
  const btn = e.target.closest(".arrived-btn, .delivered-btn");
  if (!btn) return;

  e.preventDefault();

  const form = btn.closest("form");
  if (!form) return;

  const raw = form.querySelector('input[name="drop_index"]');
  if (!raw) return;

  const dropIndex = Number(raw.value);
  if (!Number.isFinite(dropIndex)) return;

  const action = btn.value;  // "start" | "stop"
  const key = keyFor(dropIndex);

  // grab the card BEFORE swapToCompleted removes the form
  const card = form.closest(".drop-card");

  const record = addDuration(action, key);

  if (action === "start") {
    // Mark the run as active the first time they actually start a drop
    localStorage.setItem('runActive', '1');
    swapToDelivered(form, dropIndex);
    changeStatus(dropIndex, "in_progress");
    return;
  }

  if (action === "stop") {
    // avoid double-scheduling
    if (!card || card.dataset.moveScheduled === "1") {
      changeStatus(dropIndex, "completed");
      return;
    }
    card.dataset.moveScheduled = "1";

    // show completed state immediately

    changeStatus(dropIndex, "completed");

    // schedule move into Completed list after 5s
    const completedList = document.getElementById("completed-list");
    setTimeout(() => {
      if (!completedList || !card.isConnected) return;

      // wrap in <li> because completedList is a <ul>
      const li = document.createElement("li");
      li.appendChild(card);
      completedList.prepend(li);

      // remove empty message, bump count
      const emptyMsg = completedList.querySelector(".empty-msg");
      if (emptyMsg) emptyMsg.remove();

      const countEl = document.getElementById("completed-count");
      if (countEl) {
        const n = Number(countEl.textContent || "0");
        countEl.textContent = String(n + 1);
      }

    const currentSlot = document.getElementById("current-drop-slot");
      if (currentSlot && currentSlot.children.length === 0) {
     promoteNextDrop();
}
    }, 3000);
  }
});

function fetchWithTimeout(url, options = {}, timeout = 3000) {
  return Promise.race([
    fetch(url, options),
    new Promise((_, reject) =>
      setTimeout(() => reject(new Error("Timeout")), timeout)
    ),
  ]);
}

// End Shift modal
document.addEventListener("click", (e) => {
  const endShiftBtn = e.target.closest(".end-shift");
  const modal = document.querySelector(".end-shift-modal");

  if (endShiftBtn) {
    e.preventDefault();
    if (modal) modal.classList.add("show");
    return;
  }

  // Confirm end shift
  if (e.target.closest(".confirm")) {
    e.preventDefault();
    updateLastActive();

    const body = { client_ended_at: new Date().toISOString() };

    const finishLocally = () => {
      localStorage.removeItem("runActive");
      localStorage.clear(); 
      if (modal) modal.classList.remove("show");
      // window.location.href = "/index";
    };

    if (navigator.onLine) {
      fetchWithTimeout("/api/run/end", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        credentials: "same-origin",
        cache: "no-store",
      }, 3000)
        .then((r) => {
          if (!r.ok) throw new Error(`HTTP ${r.status}`);
          return r.json();
        })
        .then((data) => {
          console.log("End run response:", data);
          finishLocally();
        })
        .catch((err) => {
          console.warn("End run failed (timeout or error), queueing:", err.message || err);
          const queue = JSON.parse(localStorage.getItem("pending_queue_v1") || "[]");
          queue.push({ type: "end_run", payload: body });
          localStorage.setItem("pending_queue_v1", JSON.stringify(queue));
          if (modal) modal.classList.remove("show");
        });
    } else {
      // Offline: queue and close modal
      const queue = JSON.parse(localStorage.getItem("pending_queue_v1") || "[]");
      queue.push({ type: "end_run", payload: body });
      localStorage.setItem("pending_queue_v1", JSON.stringify(queue));
      if (modal) modal.classList.remove("show");
    }

    return; // <-- stop after handling confirm
  }

  // Cancel end shift
  if (e.target.closest(".cancel")) {
    if (modal) modal.classList.remove("show");
    return;
  }
});


// Online/offline
window.addEventListener("online", () => {
  console.log("online");
  drainQueue();
});
window.addEventListener("offline", () => {
  console.log("offline");
});

/* ========================
   Boot
======================== */
document.addEventListener("DOMContentLoaded", () => {
  // ensure queue exists
  if (!localStorage.getItem("pending_queue_v1")) {
    localStorage.setItem("pending_queue_v1", "[]");
  }

  // If your template renders drop cards when a run is configured,
  // you can also infer 'runActive' on boot:
  if (document.querySelector('.drop-card')) {
    localStorage.setItem('runActive', '1');
  }

  // prevent accidental submits (Enter key)
  document.querySelectorAll(".delivery-form").forEach((f) =>
    f.addEventListener("submit", (e) => e.preventDefault())
  );

    allDropsLocal();
    initialiseQueueFromDom();     
    promoteNextDrop(); 

  // rebuild UI from local cache
  rehydrateFromLocal();

  // drain any leftovers if online
  if (navigator.onLine) drainQueue();
});

// opening maps 
document.addEventListener("click", (e) => {
  const btn = e.target.closest(".gps-btn");
  if (!btn) return;

  // Don't over-cancel; keep this if it's inside a <form>
  e.preventDefault();

  const input = btn.closest(".gps-section")?.querySelector("input");
  const address = input?.value?.trim();
  if (!address) {
    alert("Please enter an address first!");
    return;
  }

  const encoded = encodeURIComponent(address);

  // Robust Apple detection (covers iPadOS that reports as 'Macintosh')
  const ua = navigator.userAgent || "";
  const isApple =
    /iPhone|iPad|iPod/i.test(ua) ||
    (/\bMacintosh\b/i.test(ua) && navigator.maxTouchPoints > 1);

  // PWA standalone detection
  const isStandalone =
    window.matchMedia?.("(display-mode: standalone)")?.matches ||
    // old iOS
    window.navigator.standalone === true;

  // Map URLs (https for Apple Maps)
  const appleUrl = `https://maps.apple.com/?q=${encoded}`;
  const gmapsUrl = `https://www.google.com/maps/search/?api=1&query=${encoded}`;
  const geoUrl = `geo:0,0?q=${encoded}`; // nice mobile fallback

  const targetUrl = isApple ? appleUrl : gmapsUrl;

  // In standalone PWAs on iOS, prefer same-tab navigation.
  // Elsewhere, a new tab is fine.
  if (isStandalone && isApple) {
    // iOS PWA: _blank can be blocked—use same-tab
    location.href = targetUrl;
  } else {
    // Try geo: first on mobile; if blocked, fall back to web URL
    const tried = window.open(geoUrl, "_blank", "noopener,noreferrer");
    if (!tried) {
      // Popup blocked or desktop—use web URL
      window.open(targetUrl, "_blank", "noopener,noreferrer");
    }
  }
});
