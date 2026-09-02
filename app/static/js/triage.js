import { api } from "./main.js";

async function poll() {
  const tbody = document.getElementById("alert-body");
  if (!tbody) return;
  try {
    const data = await api("/api/triage/alerts");
    tbody.innerHTML = data.alerts.map((a) => `
      <tr>
        <td>${a.patient}</td>
        <td>${a.age ?? ""}</td>
        <td>${a.complaint ?? ""}</td>
        <td>${a.message ?? ""}</td>
        <td><span class="badge badge-${a.severity === "EMERGENCY" ? "em" : a.severity === "HIGH" ? "high" : "med"}">${a.severity}</span></td>
        <td>${a.time ?? ""}</td>
        <td>${a.status}</td>
        <td><a href="/doctor/patient/${a.patient_id}">View</a></td>
      </tr>`).join("");
  } catch (e) { /* ignore */ }
}
setInterval(poll, 8000);
poll();
