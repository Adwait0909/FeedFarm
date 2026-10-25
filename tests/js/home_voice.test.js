const { JSDOM } = require("./_jsdom");
const fs = require("fs");
// Minimal DOM carrying the real tool links (hrefs copied from the template's tool list).
const links = ["/scan","/register","/animal-health/","/veterinary/","/doctor/login","/farmer/login","/kisaath/weather","/kisaath/crop-calendar","/kisaath/modern-farming","/farmer/schemes/","https://farmer-scheme-app.onrender.com/","https://disease-detectorr-f9b4ee.netlify.app/","/kisaath/marketplace","/dashboard","/kisaath/"]
  .map(h => `<a class="hm-tool" href="${h}" data-keywords="x">${h}</a>`).join("");
function build(lang, scripted) {
  const html = `<div id="weather-card" data-lang="${lang}"></div><form id="tool-search-form"><input id="tool-search"><button type="button" id="voice-btn" hidden></button></form><p id="search-hint"></p><div id="tools-grid">${links}</div><p id="tools-empty" hidden></p>`;
  const dom = new JSDOM(html, { runScripts: "outside-only", url: "http://localhost/" });
  const w = dom.window;
  const started = [];
  w.SpeechRecognition = function () { const self = this; this.start = () => { started.push(this.lang); const next = scripted.shift(); setTimeout(() => next && next(self), 5); }; this.stop = () => {}; };
  w.eval(fs.readFileSync(require("path").join(__dirname, "../../static/js/voice-nav.js"), "utf8"));
  const navs = []; w.F2FVoice.go = (href, ext) => navs.push([href, ext]);
  w.eval(fs.readFileSync(require("path").join(__dirname, "../../static/js/home.js"), "utf8"));
  return { w, started, navs };
}
const result = (...alts) => (rec) => rec.onresult({ results: [alts.map(t => ({ transcript: t }))] });
const error = (code) => (rec) => { rec.onerror({ error: code }); rec.onend(); };
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
(async () => {
  let ok = 0, bad = 0; const check = (c, m) => { c ? ok++ : bad++; console.log((c ? "PASS " : "FAIL ") + m); };
  let t = build("en", [result("what is the weather today")]);
  t.w.document.getElementById("voice-btn").click(); await sleep(1200);
  check(t.navs.length === 1 && t.navs[0][0].endsWith("/kisaath/weather"), "English 'weather' -> /kisaath/weather " + JSON.stringify(t.navs));
  check(t.started[0] === "en-IN", "English page listens in en-IN");
  t = build("mr", [result("गायीचा क्यूआर स्कॅन करा")]);
  t.w.document.getElementById("voice-btn").click(); await sleep(1200);
  check(t.navs.length === 1 && t.navs[0][0].endsWith("/scan"), "Marathi scan -> /scan " + JSON.stringify(t.navs));
  check(t.started[0] === "mr-IN", "Marathi page listens in mr-IN");
  t = build("mr", [result("मार्केटप्लेस उघडा")]); t.w.document.getElementById("voice-btn").click(); await sleep(1200);
  check(t.navs[0] && t.navs[0][0].endsWith("/kisaath/marketplace"), "Marathi marketplace");
  t = build("en", [result("crop disease detection")]); t.w.document.getElementById("voice-btn").click(); await sleep(1200);
  check(t.navs[0] && t.navs[0][0].includes("disease-detectorr") && t.navs[0][1] === false, "external crop-disease link opens (same tab flag false since no target attr)");
  // ambiguity -> choices, no navigation
  t = build("en", [result("schemes")]); t.w.document.getElementById("voice-btn").click(); await sleep(1200);
  const choices = t.w.document.querySelectorAll(".hm-voice-choice");
  check(t.navs.length === 0 && choices.length >= 2, "ambiguous 'schemes' offers " + choices.length + " choices and does not navigate");
  // destructive -> blocked
  t = build("en", [result("delete my cow")]); t.w.document.getElementById("voice-btn").click(); await sleep(1200);
  check(t.navs.length === 0 && /cannot delete/.test(t.w.document.getElementById("search-hint").textContent), "'delete my cow' is refused");
  // unmatched in first language -> retries in the other language and navigates
  t = build("en", [result("hello"), result("हवामान")]); t.w.document.getElementById("voice-btn").click(); await sleep(1500);
  check(t.started.join() === "en-IN,mr-IN" && t.navs[0] && t.navs[0][0].endsWith("/kisaath/weather"), "no match in English -> retry Marathi -> weather (" + t.started.join() + ")");
  // nothing matches twice -> falls back to tool search text
  t = build("en", [result("zzz qqq"), result("zzz qqq")]); t.w.document.getElementById("voice-btn").click(); await sleep(1500);
  check(t.navs.length === 0 && t.w.document.getElementById("tool-search").value === "zzz qqq", "unmatched speech falls back to the search box");
  // microphone denied
  t = build("en", [error("not-allowed")]); t.w.document.getElementById("voice-btn").click(); await sleep(300);
  check(/blocked/.test(t.w.document.getElementById("search-hint").textContent), "microphone denial shows a clear message");
  t = build("mr", [error("no-speech")]); t.w.document.getElementById("voice-btn").click(); await sleep(300);
  check(/ऐकू/.test(t.w.document.getElementById("search-hint").textContent), "Marathi no-speech message");
  // best alternative wins
  t = build("en", [result("blah", "find a vet")]); t.w.document.getElementById("voice-btn").click(); await sleep(1200);
  check(t.navs[0] && t.navs[0][0].endsWith("/veterinary/"), "best recognizer alternative used");
  // cancel pending navigation by tapping the mic again
  t = build("en", [result("weather")]); t.w.document.getElementById("voice-btn").click(); await sleep(100);
  t.w.document.getElementById("voice-btn").click(); await sleep(1000);
  check(t.navs.length === 0, "tapping the mic again cancels a pending navigation");
  // missing destination is never opened
  const t2 = build("en", [result("open marketplace")]); t2.w.document.querySelector('a[href="/kisaath/marketplace"]').remove();
  t2.w.document.getElementById("voice-btn").click(); await sleep(1200);
  check(t2.navs.length === 0, "a destination missing from the page is never opened");
  console.log(`${ok} passed, ${bad} failed`); process.exit(bad ? 1 : 0);
})();
