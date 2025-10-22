
function initialiseQueueFromDom() {
    const currentDrop = document.getElementById("current-drop-slot");
    const upcomingDrops = document.getElementById("upcoming-list");
    const allDrops = [ ...document.querySelectorAll('.drop-card[id^="drop-"]')];

    for (let i = 0; i < allDrops.length; i++) {
        if (i === 0) {
            currentDrop.append(allDrops[i]);
        } else {
            upcomingDrops.append(allDrops[i]);
        }
    }

};

initialiseQueueFromDom();
