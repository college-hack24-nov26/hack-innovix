import { toast } from "./main.js";

const ayush = document.getElementById("ayush-toggle");
if (ayush) {
  ayush.addEventListener("change", () => toast("AYUSH history will be collected in the next interview session."));
}
