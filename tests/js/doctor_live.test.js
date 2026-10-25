const { JSDOM } = require("./_jsdom");
const fs = require("fs");
const html = `<p id="live-status" data-state="ok"><span id="live-status-text"></span><span id="live-demo-note"></span><button id="live-refresh" hidden></button></p>
<span id="stat-follow-up">0</span><span id="stat-vaccination">0</span><span id="stat-requests">0</span>
<section id="cow-section" data-api="/doctor/api/dashboard" data-profile-url="/doctor/cow/__COW__" data-update-url="/doctor/update/__COW__" data-search="" data-request-version="1:a"><div class="empty-state" id="cow-empty"><p>none</p></div></section>`;
function make(fetchImpl) {
  const dom = new JSDOM(html, { runScripts: "outside-only", url: "http://localhost/doctor" });
  const w = dom.window; w.fetch = fetchImpl;
  Object.defineProperty(w.document, "hidden", { value: false, configurable: true });
  w.eval(fs.readFileSync(require("path").join(__dirname, "../../static/js/doctor_live.js"), "utf8"));
  return w;
}
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
(async () => {
  // 1) success path: click refresh -> table rendered, counters updated, XSS-safe
  let calls = [];
  const payload = { follow_up_count: 2, vaccination_count: 3, request_count: 4, request_version: "2:b", demo_count: 1, total: 2,
    cows: [{ cow_id: "COW001", cow_name: "<img src=x onerror=alert(1)>", breed: "Gir", health_status: "Healthy", health_score: 90, next_checkup_date: "2026-10-15", local_cow_number: "C-1", is_demo: true },
           { cow_id: "X/1", cow_name: "Mine", breed: "", health_status: null, health_score: 10, next_checkup_date: null, is_demo: false }] };
  let w = make((url, opts) => { calls.push([url, opts.headers]); return Promise.resolve({ status: 200, ok: true, headers: { get: () => '"e1"' }, json: () => Promise.resolve(payload) }); });
  w.document.getElementById("live-refresh").click(); await sleep(50);
  const rows = w.document.querySelectorAll("#cow-rows tr");
  console.log("rows:", rows.length, "| counters:", ["stat-follow-up","stat-vaccination","stat-requests"].map(i => w.document.getElementById(i).textContent).join(","));
  console.log("no injected <img>:", w.document.querySelectorAll("#cow-rows img").length === 0, "| demo tags:", w.document.querySelectorAll(".demo-tag").length);
  console.log("link encoded:", rows[1].querySelector("a").getAttribute("href"));
  console.log("status:", w.document.getElementById("live-status").dataset.state, "|", w.document.getElementById("live-status-text").textContent);
  console.log("demo note:", w.document.getElementById("live-demo-note").textContent);
  // 2) error path
  w = make(() => Promise.reject(new Error("net")));
  w.document.getElementById("live-refresh").click(); await sleep(50);
  console.log("error state:", w.document.getElementById("live-status").dataset.state, "|", w.document.getElementById("live-status-text").textContent);
  // 3) session expired
  w = make(() => Promise.resolve({ status: 401, ok: false, headers: { get: () => null } }));
  w.document.getElementById("live-refresh").click(); await sleep(50);
  console.log("auth state:", w.document.getElementById("live-status").dataset.state, "| link:", w.document.querySelector("#live-status-text a")?.getAttribute("href"));
  // 4) empty result
  w = make(() => Promise.resolve({ status: 200, ok: true, headers: { get: () => '"e2"' }, json: () => Promise.resolve({ ...payload, cows: [], demo_count: 0 }) }));
  w.document.getElementById("live-refresh").click(); await sleep(50);
  console.log("empty:", w.document.getElementById("cow-empty")?.textContent.trim());
  // 5) 304 keeps content, sends If-None-Match
  calls = [];
  w = make((url, opts) => { calls.push(opts.headers); return calls.length === 1 ? Promise.resolve({ status: 200, ok: true, headers: { get: () => '"e3"' }, json: () => Promise.resolve(payload) }) : Promise.resolve({ status: 304, ok: false, headers: { get: () => null } }); });
  w.document.getElementById("live-refresh").click(); await sleep(50);
  w.document.getElementById("live-refresh").click(); await sleep(50);
  console.log("2nd request If-None-Match:", calls[1]["If-None-Match"], "| rows kept:", w.document.querySelectorAll("#cow-rows tr").length);
  process.exit(0);
})();
