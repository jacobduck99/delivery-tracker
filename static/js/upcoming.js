
// function initialiseQueueFromDom() {
//     const currentDrop = document.getElementById("current-drop-slot");
//     const upcomingDrops = document.getElementById("upcoming-list");
//     const allDrops = [ ...document.querySelectorAll('.drop-card[id^="drop-"]')];

//     for (let i = 0; i < allDrops.length; i++) {
//         if (i === 0) {
//             currentDrop.append(allDrops[i]);
//         } else {
//             upcomingDrops.append(allDrops[i]);
//         }
//     }

// };

// function promoteNextDrop() {
//   const currentDrop = document.getElementById("current-drop-slot");
//   const upcomingDrops = document.getElementById("upcoming-list");

//   // only promote if current slot is empty
//   if (currentDrop.children.length === 0) {
//     const nextDrop = upcomingDrops.querySelector(".drop-card"); // first drop in upcoming

//     if (nextDrop) {
//       currentDrop.append(nextDrop);
//       console.log("Promoted next drop to current slot!");
//     } else {
//       console.log("No upcoming drops left to promote.");
//     }
//   }
// }

// initialiseQueueFromDom();

