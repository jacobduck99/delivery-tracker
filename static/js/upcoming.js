
export function initialiseQueueFromDom() {
    const currentDrop = document.getElementById("current-drop-slot");
    const upcomingDrops = document.getElementById("upcoming-list");
    const allDrops = [ ...document.querySelectorAll('.drop-card[id^="drop-"]')];
    let counter = 0;

    for (let i = 0; i < allDrops.length; i++) {
        if (i === 0) {
            currentDrop.append(allDrops[i]);
        } else {
            upcomingDrops.append(allDrops[i]);
            counter++;
           
        }
    }
    const countEl = document.getElementById("upcoming-count"); 
    countEl.textContent = `${counter}`;

};

export function promoteNextDrop() {
    const currentDrop = document.getElementById("current-drop-slot");
    const upcomingDrops = document.getElementById("upcoming-list");
    let countEl = document.getElementById("upcoming-count");
    let counter = countEl.textContent;


  // only promote if current slot is empty
  if (currentDrop.children.length === 0) {
    const nextDrop = upcomingDrops.querySelector(".drop-card"); // first drop in upcoming
    
    if (nextDrop) {
    currentDrop.append(nextDrop);
    let count = parseInt(counter, 10);
    const newCount = Math.max(0, count - 1);
    countEl.textContent = String(newCount);  
     if (!countEl) return; // or log and bail

      console.log("Promoted next drop to current slot!");
    } else {
      console.log("No upcoming drops left to promote.");
    }
  }
}

