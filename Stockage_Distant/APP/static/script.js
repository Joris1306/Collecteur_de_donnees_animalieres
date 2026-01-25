const grid = document.getElementById("grid");
const toast = document.getElementById("toast");
const btnToggle = document.getElementById("btnToggle");

let listMode = false;

function showToast(msg){
  toast.textContent = msg;
  toast.style.display = "block";
  setTimeout(() => toast.style.display = "none", 3000);
}

// Server-Sent Events for real-time updates
const eventSource = new EventSource('/events');

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  if (data.event === 'new_image') {
    showToast('New image received! Refreshing...');
    setTimeout(() => window.location.reload(), 1500);
  }
};

eventSource.onerror = function(error) {
  console.error('SSE connection error:', error);
  // Automatically reconnects
};

btnToggle.onclick = () => {
  listMode = !listMode;
  grid.style.gridTemplateColumns = listMode ? "1fr" : "";
  showToast(listMode ? "List view enabled" : "Grid view enabled");
};

/* Lightbox */
const lightbox = document.getElementById("lightbox");
const lightboxImg = document.getElementById("lightboxImg");
const lightboxClose = document.getElementById("lightboxClose");

function openLightbox(src){
  lightboxImg.src = src;
  lightbox.classList.add("show");
}

lightboxClose.onclick = () => lightbox.classList.remove("show");
lightbox.onclick = e => e.target === lightbox && lightbox.classList.remove("show");
document.addEventListener("keydown", e => e.key === "Escape" && lightbox.classList.remove("show"));
