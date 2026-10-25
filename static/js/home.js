/* Farm2Feed home page interactions */
(function () {
  'use strict';
  var root = document.documentElement;
  root.classList.add('js');
  var lang = (document.getElementById('weather-card') || {}).dataset ? document.getElementById('weather-card').dataset.lang : 'en';
  var mr = lang === 'mr';
  function T(en, m) { return mr ? m : en; }

  /* ---------- Text size toggle ---------- */
  var sizeBtn = document.getElementById('text-size-btn');
  function applySize(large) {
    root.classList.toggle('hm-large', large);
    if (sizeBtn) sizeBtn.setAttribute('aria-pressed', String(large));
  }
  try { applySize(localStorage.getItem('f2f-large') === '1'); } catch (e) {}
  if (sizeBtn) sizeBtn.addEventListener('click', function () {
    var large = !root.classList.contains('hm-large');
    applySize(large);
    try { localStorage.setItem('f2f-large', large ? '1' : '0'); } catch (e) {}
  });

  /* ---------- Mobile nav ---------- */
  var burger = document.getElementById('nav-toggle');
  var nav = document.getElementById('hm-nav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      burger.setAttribute('aria-expanded', String(open));
    });
    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) { nav.classList.remove('is-open'); burger.setAttribute('aria-expanded', 'false'); }
    });
  }

  /* ---------- Need chooser tabs ---------- */
  var tabs = Array.prototype.slice.call(document.querySelectorAll('.hm-need-tab'));
  function selectTab(tab, focus) {
    tabs.forEach(function (t) {
      var on = t === tab;
      t.classList.toggle('is-active', on);
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      var panel = document.getElementById(t.getAttribute('aria-controls'));
      if (panel) { panel.hidden = !on; panel.classList.toggle('is-active', on); }
    });
    if (focus) tab.focus();
  }
  tabs.forEach(function (tab, i) {
    tab.addEventListener('click', function () { selectTab(tab); });
    tab.addEventListener('keydown', function (e) {
      var n = null;
      if (e.key === 'ArrowDown' || e.key === 'ArrowRight') n = tabs[(i + 1) % tabs.length];
      if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') n = tabs[(i - 1 + tabs.length) % tabs.length];
      if (n) { e.preventDefault(); selectTab(n, true); }
    });
  });

  /* ---------- Tool filters + search ---------- */
  var cards = Array.prototype.slice.call(document.querySelectorAll('.hm-tool'));
  var filters = Array.prototype.slice.call(document.querySelectorAll('.hm-filter'));
  var empty = document.getElementById('tools-empty');
  var input = document.getElementById('tool-search');
  var hint = document.getElementById('search-hint');
  var activeFilter = 'all';

  function applyFilters() {
    var q = (input && input.value || '').trim().toLowerCase();
    var shown = 0;
    cards.forEach(function (c) {
      var catOk = activeFilter === 'all' || c.dataset.cat === activeFilter;
      var textOk = !q || (c.dataset.keywords || '').toLowerCase().indexOf(q) !== -1 ||
                   c.textContent.toLowerCase().indexOf(q) !== -1;
      var show = catOk && textOk;
      c.hidden = !show;
      c.classList.toggle('is-match', !!q && show);
      if (show) { shown++; c.classList.add('is-in'); }
    });
    if (empty) empty.hidden = shown !== 0;
    if (hint) {
      hint.textContent = q ? (shown
        ? T(shown + ' tool' + (shown > 1 ? 's' : '') + ' found — press Enter to see', shown + ' साधने सापडली — पाहण्यासाठी Enter दाबा')
        : T('Nothing found — try another word', 'काही सापडले नाही — दुसरा शब्द वापरा')) : '';
    }
  }
  filters.forEach(function (f) {
    f.addEventListener('click', function () {
      activeFilter = f.dataset.filter;
      filters.forEach(function (x) { var on = x === f; x.classList.toggle('is-active', on); x.setAttribute('aria-pressed', String(on)); });
      applyFilters();
    });
  });
  if (input) input.addEventListener('input', applyFilters);
  var form = document.getElementById('tool-search-form');
  if (form) form.addEventListener('submit', function (e) {
    e.preventDefault();
    applyFilters();
    var t = document.getElementById('tools');
    if (t) t.scrollIntoView({ behavior: 'smooth', block: 'start' });
    var first = cards.filter(function (c) { return !c.hidden; })[0];
    if (first && input.value.trim()) setTimeout(function () { first.focus({ preventScroll: true }); }, 500);
  });

  /* ---------- Voice navigation + voice search (English & Marathi) ---------- */
  var mic = document.getElementById('voice-btn');
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  var Voice = window.F2FVoice;
  if (mic && SR && Voice) {
    mic.hidden = false;
    var rec = null, pendingNav = null, tried = 0;
    var LANGS = mr ? ['mr-IN', 'en-IN'] : ['en-IN', 'mr-IN'];

    function say(msg) { if (hint) { hint.textContent = msg; } }
    function resolveTarget(target) {
      if (target.path) return document.querySelector('a[href="' + target.path + '"]');
      if (target.contains) return document.querySelector('a[href*="' + target.contains + '"]');
      return null;
    }
    function label(intent) { return mr ? intent.mr : intent.en; }
    function cancelNav() { if (pendingNav) { clearTimeout(pendingNav); pendingNav = null; } }

    function showChoices(options) {
      if (!hint) return;
      hint.textContent = '';
      hint.appendChild(document.createTextNode(T('Did you mean: ', 'तुम्हाला हे म्हणायचे आहे का: ')));
      options.forEach(function (intent, i) {
        var a = document.createElement('a');
        var target = resolveTarget(intent.target);
        a.href = target ? target.getAttribute('href') : '#';
        a.textContent = label(intent);
        a.className = 'hm-voice-choice';
        hint.appendChild(a);
        if (i < options.length - 1) hint.appendChild(document.createTextNode(' · '));
      });
    }

    function fallbackToSearch(text) {
      if (!input || !text) { say(T('Could not understand. Please try again.', 'समजले नाही. कृपया पुन्हा प्रयत्न करा.')); return; }
      input.value = text;
      applyFilters();
      if (form) form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event('submit', { cancelable: true }));
    }

    function handle(result, heard, canRetry) {
      if (result.status === 'blocked') {
        say(T('Voice commands only open pages. They cannot delete, remove or log out. Please use the buttons for that.',
              'आवाजाने फक्त पाने उघडता येतात. हटवणे, काढणे किंवा लॉग आउट बटणांनीच करा.'));
        return;
      }
      if (result.status === 'navigate') {
        var target = resolveTarget(result.intent.target);
        if (!target) { fallbackToSearch(heard); return; }
        say(T('Opening ', 'उघडत आहे: ') + label(result.intent) + '… ' + T('(tap the mic to cancel)', '(रद्द करण्यासाठी माइक दाबा)'));
        var href = target.href;
        var external = target.target === '_blank';
        pendingNav = setTimeout(function () {
          pendingNav = null;
          Voice.go(href, external);
        }, 800);
        return;
      }
      if (result.status === 'choose') { showChoices(result.options); return; }
      // Nothing matched. Listen once more in the other language, then fall back to the tool search box.
      if (canRetry) {
        say(mr ? 'समजले नाही - इंग्रजीत ऐकत आहे…' : 'Did not catch that - listening in Marathi…');
        setTimeout(function () { listen(LANGS[1], false); }, 300);
        return;
      }
      fallbackToSearch(heard);
    }

    function describeError(code) {
      if (code === 'not-allowed' || code === 'service-not-allowed') return T('Microphone access is blocked. Allow it in your browser settings, or type your search.', 'माइक्रोफोन बंद आहे. ब्राउझर सेटिंगमध्ये परवानगी द्या किंवा शब्द टाइप करा.');
      if (code === 'audio-capture') return T('No microphone was found.', 'माइक्रोफोन सापडला नाही.');
      if (code === 'no-speech') return T('I did not hear anything. Tap the mic and try again.', 'काही ऐकू आले नाही. माइक दाबून पुन्हा प्रयत्न करा.');
      if (code === 'network') return T('Speech service is unreachable. Check your internet connection.', 'आवाज सेवा उपलब्ध नाही. इंटरनेट तपासा.');
      return T('Could not hear you. Please try again.', 'ऐकू आले नाही. कृपया पुन्हा प्रयत्न करा.');
    }

    function listen(lang, canRetry) {
      var r = new SR();
      rec = r;
      r.lang = lang;
      r.interimResults = false;
      r.maxAlternatives = 3;
      var gotResult = false;
      mic.classList.add('is-listening');
      say(T('Listening… try “weather”, “scan cow”, “find a vet”', 'ऐकत आहे… म्हणा “हवामान”, “गाय स्कॅन”, “डॉक्टर शोधा”'));
      r.onresult = function (ev) {
        gotResult = true;
        var alts = [];
        for (var i = 0; i < ev.results[0].length; i++) alts.push(ev.results[0][i].transcript);
        var result = Voice ? Voice.interpretAlternatives(alts, resolveTarget) : { status: 'none', options: [] };
        handle(result, alts[0], canRetry);
      };
      r.onerror = function (e) {
        gotResult = true;
        var code = e && e.error;
        if (code === 'language-not-supported' && canRetry) { setTimeout(function () { listen(LANGS[1], false); }, 200); return; }
        if (code === 'aborted') return;
        say(describeError(code));
      };
      r.onend = function () {
        mic.classList.remove('is-listening');
        if (rec === r) rec = null;
        if (!gotResult && hint && hint.textContent.indexOf('Listening') === 0) say(describeError('no-speech'));
      };
      try { r.start(); } catch (e) { mic.classList.remove('is-listening'); rec = null; say(describeError('')); }
    }

    mic.addEventListener('click', function () {
      if (pendingNav) { cancelNav(); say(T('Cancelled.', 'रद्द केले.')); return; }
      if (rec) { rec.stop(); return; }
      listen(LANGS[0], true);
    });
  }

  /* ---------- Weather (Open-Meteo, no key) ---------- */
  var wTemp = document.getElementById('w-temp');
  var wDesc = document.getElementById('w-desc');
  var wRain = document.getElementById('w-rain');
  var wAdv = document.getElementById('w-advice');
  var wPlace = document.getElementById('weather-place');
  var locBtn = document.getElementById('weather-locate');
  var DEFAULT = { lat: 18.5204, lon: 73.8567, name: T('Pune', 'पुणे') };

  var CODES = [
    [[0], 'Clear sky', 'निरभ्र आकाश'], [[1, 2], 'Partly cloudy', 'अंशतः ढगाळ'], [[3], 'Cloudy', 'ढगाळ'],
    [[45, 48], 'Foggy', 'धुके'], [[51, 53, 55, 56, 57], 'Drizzle', 'रिमझिम'],
    [[61, 63, 65, 66, 67, 80, 81, 82], 'Rain', 'पाऊस'], [[71, 73, 75, 77, 85, 86], 'Snow', 'बर्फ'],
    [[95, 96, 99], 'Thunderstorm', 'विजांसह पाऊस']
  ];
  function describe(code) {
    for (var i = 0; i < CODES.length; i++) if (CODES[i][0].indexOf(code) !== -1) return T(CODES[i][1], CODES[i][2]);
    return T('Weather', 'हवामान');
  }
  function advice(temp, rainPct) {
    if (rainPct >= 60) return T('Rain is likely. Avoid spraying, cover harvested produce and keep animals sheltered.', 'पावसाची शक्यता जास्त आहे. फवारणी टाळा, कापलेला माल झाका आणि जनावरे निवाऱ्यात ठेवा.');
    if (temp >= 37) return T('Very hot today. Give animals shade and plenty of clean water; work in the early morning.', 'आज खूप उष्णता आहे. जनावरांना सावली व भरपूर स्वच्छ पाणी द्या; कामे सकाळी लवकर करा.');
    if (temp >= 32) return T('Warm day. Keep water available for animals and irrigate in the evening.', 'उष्ण दिवस. जनावरांसाठी पाणी ठेवा आणि सायंकाळी सिंचन करा.');
    return T('Good conditions for field work today.', 'आज शेतीकामासाठी अनुकूल हवामान आहे.');
  }
  function loadWeather(p) {
    if (!wTemp) return;
    var url = 'https://api.open-meteo.com/v1/forecast?latitude=' + p.lat + '&longitude=' + p.lon +
      '&current=temperature_2m,weather_code&daily=precipitation_probability_max&timezone=auto&forecast_days=1';
    fetch(url).then(function (r) { if (!r.ok) throw 0; return r.json(); }).then(function (d) {
      var t = Math.round(d.current.temperature_2m);
      var rain = (d.daily && d.daily.precipitation_probability_max && d.daily.precipitation_probability_max[0]) || 0;
      wTemp.textContent = t + '°C';
      wDesc.textContent = describe(d.current.weather_code);
      wRain.textContent = T('Rain chance: ', 'पावसाची शक्यता: ') + rain + '%' + (p.name ? ' · ' + p.name : '');
      wAdv.textContent = advice(t, rain);
    }).catch(function () {
      wTemp.textContent = '--°';
      wDesc.textContent = T('Weather unavailable', 'हवामान उपलब्ध नाही');
      wRain.textContent = T('Check your internet connection', 'इंटरनेट जोडणी तपासा');
      wAdv.textContent = '';
    });
  }
  if (wTemp) {
    loadWeather(DEFAULT);
    if (locBtn) locBtn.addEventListener('click', function () {
      if (!navigator.geolocation) { wPlace.textContent = T('Location not supported', 'स्थान समर्थित नाही'); return; }
      wPlace.textContent = T('Finding you…', 'स्थान शोधत आहे…');
      navigator.geolocation.getCurrentPosition(function (pos) {
        wPlace.textContent = T('Your location', 'तुमचे स्थान');
        loadWeather({ lat: pos.coords.latitude.toFixed(3), lon: pos.coords.longitude.toFixed(3), name: T('Your location', 'तुमचे स्थान') });
      }, function () {
        wPlace.textContent = T('Location blocked — showing Pune', 'स्थान बंद — पुणे दाखवत आहे');
      }, { timeout: 8000, maximumAge: 600000 });
    });
  }

  /* ---------- Scroll reveal ---------- */
  var revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); } });
    }, { threshold: 0.12 });
    revealEls.forEach(function (el, i) { el.style.transitionDelay = ((i % 4) * 60) + 'ms'; io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('is-in'); });
  }
})();
