import { api, toast } from "./main.js";

const search = document.getElementById("patient-search");
if (search) {
  search.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      window.location.href = `/doctor/patients?q=${encodeURIComponent(search.value)}`;
    }
  });
}

document.querySelectorAll("[data-fhir]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const id = btn.dataset.fhir;
    const data = await api(`/api/fhir/export/${id}`, { method: "POST" });
    toast("FHIR bundle exported (local record).");
    console.info(data);
  });
});
