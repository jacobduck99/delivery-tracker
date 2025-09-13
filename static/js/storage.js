document.querySelectorAll(".arrived-btn, .delivered-btn").forEach(btn => {
  btn.addEventListener("click", (e) => {
    e.preventDefault()

    const form = e.target.closest("form");
    if (!form) return;

    const raw = form.querySelector("input[name='drop_index']");
    if (!raw) return;

    const dropIndex = Number(raw.value);
    if (!Number.isFinite(dropIndex)) return;

    const action = e.target.value; // ensure your buttons have value="start"/"stop"
    const key = keyFor(dropIndex);

    addDuration(action, key);
  });
});


function keyFor(dropIndex) {
     return `drop-${Number(dropIndex)}`; 
}

function getRecord(key) {
    try{
 return JSON.parse(localStorage.getItem(key) || "{}")
    } catch {
        return {}; 
    }
   
};

function setRecord(key, record) {
    localStorage.setItem(key, JSON.stringify(record));
}

function listDropKeys() {
  const results = [];

  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);

    if (key.startsWith("drop-")) {
      const record = getRecord(key);
      results.push({ key, record });
    }
  }

  return results;
}

function removeKey(key) {
    if (typeof key === "string" && key.length > 0) {
      localStorage.removeItem(key);   
    }
}

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
      const drop_index = Number(key.split("-")[1]);  // from "drop-3" -> 3
      queue.push({ drop_index, start_ts: record.start_ts, stop_ts: record.stop_ts, duration_ms: record.duration_ms });
      localStorage.setItem("pending_queue_v1", JSON.stringify(queue));
      if (navigator.onLine) setTimeout(drainQueue, 0);

    } else {
      // optional: mark as invalid or just return early
      return record;
    }
  }

  setRecord(key, record);
  return record;
}

function buildPayloadFromLocal() {
    let records = [];
    const rows = listDropKeys();

    for (const row of rows) {
        const parts = row.key.split("-");
        const numberString = parts[1];
        const drop_index = Number(numberString);

        if (!Number.isFinite(drop_index)) {
            continue;
        }

        let start;
        if (row.record.start_ts != null) {
            start = Number(row.record.start_ts);
        } else {
            start = null;
        }

        let stop;
        if (row.record.stop_ts != null) {
            stop = Number(row.record.stop_ts);
        } else {
            stop = null;
        }

        let duration;
        if (row.record.duration_ms != null && Number(row.record.duration_ms) >= 0) {
            duration = Number(row.record.duration_ms);
        } else {
            duration = null;
        }

        if (start === null && stop === null) {
            continue;
        }

        records.push({
            key: row.key,
            drop_index: drop_index,
            start_ts: start,
            stop_ts: stop,
            duration_ms: duration
        });
    }

    return { records };
}



/* to delete local storage and free up memory when drop done
const dropCards = document.querySelectorAll(".drop-card")
for (const card of dropCards) {
    if (card.querySelector(".drop-elapsed")) {
        localStorage.removeItem(card.id)   
    }
};
*/


function drainQueue() {
  const queue = JSON.parse(localStorage.getItem("pending_queue_v1") || "[]");
  if (queue.length === 0) {
    return; 
  } 

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
      if (res?.ok) {
        queue.shift();
        localStorage.setItem("pending_queue_v1", JSON.stringify(queue));
        setTimeout(drainQueue, 0);
      } else {
        console.warn("Server rejected item:", res);
      }
    })
    .catch((err) => {
      console.warn("Send failed:", err);
    });
}



window.addEventListener("online", (e) => {
    console.log("online");
    drainQueue();
});

window.addEventListener("offline", (e) => {
    console.log("offline");
})



