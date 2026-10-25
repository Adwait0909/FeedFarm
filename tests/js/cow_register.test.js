/* node tests/js/cow_register.test.js <rendered-form.html> <lang>   (the HTML is the real page rendered by Flask) */
const fs = require('fs');
const path = require('path');
const { JSDOM } = require('./_jsdom');
const html = fs.readFileSync(process.argv[2], 'utf8');
const script = fs.readFileSync(path.join(__dirname, '../../static/js/cow_register.js'), 'utf8');
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let failed = 0;
const check = (cond, msg) => { if (!cond) failed++; console.log((cond ? 'PASS ' : 'FAIL ') + msg); };

(async () => {
  const dom = new JSDOM(html.replace(/<script[^>]*src=[^>]*><\/script>/g, ''), { runScripts: 'outside-only', url: 'http://localhost/' });
  const w = dom.window;
  const created = [], revoked = [];
  w.URL.createObjectURL = (f) => { created.push(f.name); return 'blob:test/' + f.name; };
  w.URL.revokeObjectURL = (u) => revoked.push(u);
  w.eval(script);
  const d = w.document, form = d.querySelector('form[data-live-review]');
  const review = (k) => d.querySelector(`[data-review="${k}"]`).textContent;
  const set = (name, value, evt = 'input') => { const el = form.elements[name]; el.value = value; el.dispatchEvent(new w.Event(evt, { bubbles: true })); };

  check(review('cow_name') === '—', 'review starts empty');
  set('cow_name', 'Gauri'); set('breed', 'Gir', 'change'); set('cow_type', 'Dairy', 'change'); set('gender', 'Female', 'change');
  check(review('cow_name') === 'Gauri', 'name appears live');
  check(review('breed') === 'Gir', 'select value (breed) appears live');
  check(review('cow_type') !== '—' && review('gender') !== '—', 'type and gender appear live');
  set('cow_name', '<img src=x onerror=alert(1)>');
  check(d.querySelectorAll('[data-review] img').length === 0, 'typed HTML is shown as text, not injected');
  set('cow_name', '');
  check(review('cow_name') === '—', 'clearing a field clears the review');
  const progress = d.querySelector('[data-review-progress]').textContent;
  check(/\d+\s*(of|\/)\s*\d+/.test(progress), 'completion counter shown: ' + progress);

  // photo
  const input = form.elements['cow_image'];
  const pick = (file) => { Object.defineProperty(input, 'files', { value: [file], configurable: true }); input.dispatchEvent(new w.Event('change', { bubbles: true })); };
  const img = d.querySelector('[data-photo-img]'), err = d.querySelector('[data-photo-error]'), rm = d.querySelector('[data-photo-remove]');
  pick({ name: 'cow.jpg', type: 'image/jpeg', size: 200 * 1024 });
  check(!img.hidden && img.getAttribute('src') === 'blob:test/cow.jpg', 'valid photo is previewed');
  check(d.querySelector('[data-review-photo]').textContent === 'cow.jpg', 'review shows the photo name');
  check(!rm.hidden && /cow.jpg/.test(d.querySelector('[data-photo-name]').textContent), 'name/size and Remove button shown');
  rm.click();
  check(img.hidden && rm.hidden && /No photo|फोटो निवडला/.test(d.querySelector('[data-review-photo]').textContent), 'Remove clears the photo');
  pick({ name: 'cow.gif', type: 'image/gif', size: 1000 });
  check(img.hidden && err.textContent.length > 0, 'wrong file type is rejected with a message: ' + err.textContent);
  pick({ name: 'huge.png', type: 'image/png', size: 5 * 1024 * 1024 });
  check(img.hidden && /4 MB/.test(err.textContent), 'oversize photo is rejected: ' + err.textContent);
  pick({ name: 'ok.png', type: 'image/png', size: 1000 });
  check(!img.hidden && err.textContent === '', 'a valid photo after an error clears the error');
  check(revoked.length >= 1, 'old preview URLs are released');
  console.log(failed ? 'FAILED' : 'all checks passed');
  process.exit(failed ? 1 : 0);
})();
