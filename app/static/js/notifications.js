import { api } from "./main.js";

async function loadNotes() {
  try {
    const data = await api("/api/notifications");
    const el = document.getElementById("note-count");
    if (el) el.textContent = data.items.length;
  } catch (e) { /* ignore */ }
}
loadNotes();
