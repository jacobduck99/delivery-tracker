document.querySelectorAll(".arrived-btn, .delivered-btn").forEach(btn => {
  btn.addEventListener("click", (e) => {
    const form = e.target.closest("form");
    const dropIndex = form.querySelector("input[name='drop_index']").value;
    const action = e.target.value; // "start" or "stop"
    const key = `drop-${dropIndex}`;

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


function addDuration(action, key) {
    let record = JSON.parse(localStorage.getItem(key) || "{}");

    if (action === "start") {
        record.start_ts = Date.now();
    } else if (action === "stop") {
        record.stop_ts = Date.now();
        record.duration_ms = record.stop_ts - record.start_ts;
    }
    localStorage.setItem(key, JSON.stringify(record));

    return record;

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



/* to delete local storage and free up memory when drop done
const dropCards = document.querySelectorAll(".drop-card")
for (const card of dropCards) {
    if (card.querySelector(".drop-elapsed")) {
        localStorage.removeItem(card.id)   
    }
};
*/

window.addEventListener("online", (e) => {
    
});




