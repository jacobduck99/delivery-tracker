
document.querySelectorAll(".arrived-btn, .delivered-btn").forEach(btn => {
  btn.addEventListener("click", (e) => {
    const form = e.target.closest("form");
    const dropIndex = form.querySelector("input[name='drop_index']").value;
    const action = e.target.value; // will be "start" or "stop"
    localStorage.setItem(`drop-${dropIndex}`, action);
  });
});





