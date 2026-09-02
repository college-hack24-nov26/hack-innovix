const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const LANG_MAP = { en: "en-IN", hi: "hi-IN", mr: "mr-IN" };

export function speak(text, lang = "en") {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = LANG_MAP[lang] || "en-IN";
  window.speechSynthesis.speak(u);
}

export function createRecognizer({ onResult, onStart, onEnd, onUnavailable, lang = "en" }) {
  if (!SpeechRecognition) {
    onUnavailable?.();
    return null;
  }
  const rec = new SpeechRecognition();
  rec.lang = LANG_MAP[lang] || "en-IN";
  rec.interimResults = false;
  rec.onstart = () => onStart?.();
  rec.onend = () => onEnd?.();
  rec.onresult = (e) => {
    const transcript = Array.from(e.results).map((r) => r[0].transcript).join(" ");
    onResult(transcript);
  };
  rec.onerror = () => onEnd?.();
  return rec;
}
