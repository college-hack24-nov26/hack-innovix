import { toast } from "./main.js";

const drop = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const progress = document.getElementById("upload-progress");
if (drop && fileInput) {
  const send = async (file) => {
    const fd = new FormData();
    fd.append("file", file);
    progress.hidden = false;
    progress.value = 10;
    const res = await fetch("/api/documents/upload", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) { toast(data.error || "Upload failed"); return; }
    progress.value = 70;
    await fetch(`/api/documents/${data.id}/process`, { method: "POST" });
    progress.value = 100;
    toast("Document processed. Please review extracted information.");
    window.location.reload();
  };
  drop.addEventListener("dragover", (e) => { e.preventDefault(); drop.classList.add("active"); });
  drop.addEventListener("drop", (e) => { e.preventDefault(); send(e.dataTransfer.files[0]); });
  fileInput.addEventListener("change", () => send(fileInput.files[0]));
}
