/* Farm2Feed home page: understand spoken English and Marathi and open the matching EXISTING page.
 *
 * - interpret(text, resolve) is a pure function (unit-tested in tests/voice-nav.test.js).
 *   `resolve(target)` must return a link for a destination or null; a destination whose link is not on the
 *   page is ignored, so a voice command can never open a page that does not exist.
 * - Voice only opens pages. Words that mean delete / remove / log out never navigate anywhere.
 * - Several close matches (for example just "schemes") produce a short list of choices instead of guessing.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.F2FVoice = factory();
}(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  /* weight 3 = unambiguous phrase, 2 = strong word, 1 = weak hint.  Latin phrases match whole words;
     Devanagari phrases match as substrings because Marathi attaches endings to words (गायीची, गाईच्या ...). */
  var INTENTS = [
    { id: 'scan', target: { path: '/scan' }, en: 'Scan a cow QR tag', mr: 'गायीचा QR टॅग स्कॅन करा', phrases: [
      ['scan', 3], ['qr', 3], ['q r', 3], ['qr code', 3], ['barcode', 2], ['cow details', 3], ['cow detail', 3], ['cow information', 3], ['cow info', 3],
      ['cow passport', 3], ['cow profile', 3], ['animal details', 3], ['show cow', 2], ['camera', 1],
      ['स्कॅन', 3], ['क्यूआर', 3], ['क्यू आर', 3], ['गायीची माहिती', 3], ['गाईची माहिती', 3], ['गायीचे तपशील', 3], ['गाईचे तपशील', 3],
      ['गायीचा तपशील', 3], ['गाईचा तपशील', 3], ['तपशील', 2], ['पासपोर्ट', 3], ['गायीची ओळख', 3], ['गाईची ओळख', 3], ['कॅमेरा', 1]] },
    { id: 'register', target: { path: '/register' }, en: 'Register a cow', mr: 'गाय नोंदवा', phrases: [
      ['register cow', 3], ['register a cow', 3], ['cow registration', 3], ['registration', 3], ['register', 2], ['add cow', 3], ['add a cow', 3],
      ['new cow', 3], ['add animal', 2], ['enrol', 2], ['enroll', 2], ['sign up cow', 2],
      ['गाय नोंदवा', 3], ['गाय नोंदणी', 3], ['गाईची नोंदणी', 3], ['गायीची नोंदणी', 3], ['नोंदणी', 3], ['नोंदवा', 3], ['नवीन गाय', 3], ['नवीन गाई', 3],
      ['गाय जोडा', 3], ['गाई जोडा', 3], ['रजिस्टर', 3], ['रजिस्ट्रेशन', 3]] },
    { id: 'animal_health', target: { path: '/animal-health/' }, en: 'Animal health check (photo)', mr: 'जनावर आरोग्य तपासणी (फोटो)', phrases: [
      ['disease detection', 3], ['detect disease', 3], ['animal disease', 3], ['cow disease', 3], ['cattle disease', 3], ['lumpy', 3], ['foot and mouth', 3],
      ['health check', 3], ['sick cow', 3], ['sick animal', 3], ['sick', 2], ['disease', 2], ['illness', 2], ['ill', 1], ['symptoms', 2], ['symptom', 2],
      ['cow health', 2], ['animal health', 3], ['cow is sick', 4], ['cow sick', 4], ['animal is sick', 4], ['my cow is sick', 5], ['photo check', 2], ['upload photo', 1],
      ['गाय आजारी', 4], ['गाई आजारी', 4], ['जनावर आजारी', 4], ['आजारी', 3], ['आजार', 3], ['रोग निदान', 3], ['जनावराचा रोग', 3], ['जनावरांचा रोग', 3], ['रोग', 2], ['लम्पी', 3], ['लंपी', 3], ['लक्षणे', 2],
      ['आरोग्य तपासणी', 3], ['तपासणी', 1], ['जनावराचे आरोग्य', 3], ['गायीचे आरोग्य', 3], ['गाईचे आरोग्य', 3], ['आरोग्य', 2]] },
    { id: 'crop_disease', target: { contains: 'disease-detectorr' }, en: 'Crop disease detection', mr: 'पीक रोग निदान', phrases: [
      ['crop disease', 6], ['plant disease', 6], ['leaf disease', 6], ['leaf', 2], ['plant', 2], ['crop', 1], ['pest', 2],
      ['पीक रोग', 6], ['पिकाचा रोग', 6], ['पिकावरील रोग', 6], ['पिकाचे रोग', 6], ['झाडाचा रोग', 6], ['पानावर रोग', 6], ['पानांवर', 3], ['पानावर', 3], ['पान', 2], ['पाने', 2], ['पिक रोग', 6], ['कीड', 2]] },
    { id: 'vet_finder', target: { path: '/veterinary/' }, en: 'Find a vet nearby', mr: 'जवळचा पशुवैद्य शोधा', phrases: [
      ['find a vet', 3], ['find vet', 3], ['vet nearby', 3], ['nearby vet', 3], ['nearest vet', 3], ['veterinarian', 3], ['veterinary', 3], ['vet', 3],
      ['doctor', 2], ['clinic', 2], ['hospital', 2], ['dispensary', 2], ['contact doctor', 3], ['call doctor', 3], ['talk to doctor', 3], ['doctor contact', 3],
      ['डॉक्टर', 2], ['पशुवैद्य', 3], ['पशुवैद्यकीय', 3], ['दवाखाना', 3], ['दवाखाने', 3], ['रुग्णालय', 2], ['जवळचा डॉक्टर', 3], ['डॉक्टरशी संपर्क', 3],
      ['डॉक्टर संपर्क', 3], ['डॉक्टरला फोन', 3], ['संपर्क', 1], ['वैद्य', 2]] },
    { id: 'vet_login', target: { path: '/doctor/login' }, en: 'Veterinarian login', mr: 'पशुवैद्य लॉगिन', phrases: [
      ['doctor login', 5], ['vet login', 5], ['veterinarian login', 5], ['doctor sign in', 5], ['vet sign in', 5], ['doctor portal', 4],
      ['डॉक्टर लॉगिन', 5], ['पशुवैद्य लॉगिन', 5], ['डॉक्टर लॉग इन', 5], ['डॉक्टर साइन इन', 5]] },
    { id: 'my_farm', target: { path: '/farmer/login' }, en: 'My farm & herd (farmer login)', mr: 'माझे शेत व गोठा (शेतकरी लॉगिन)', phrases: [
      ['my farm', 3], ['my herd', 3], ['my cows', 2], ['my cow', 2], ['farmer login', 5], ['farmer sign in', 5], ['login', 2], ['log in', 2], ['sign in', 2],
      ['help request', 3], ['assistance', 2], ['herd', 2], ['dashboard', 2],
      ['माझे शेत', 3], ['माझी शेती', 3], ['माझ्या गायी', 3], ['माझ्या गाई', 3], ['माझा गोठा', 3], ['गोठा', 3], ['शेतकरी लॉगिन', 5], ['लॉगिन', 2], ['लॉग इन', 2],
      ['मदत विनंती', 3], ['मदतीची विनंती', 3], ['डॅशबोर्ड', 2]] },
    { id: 'weather', target: { path: '/kisaath/weather' }, en: 'Weather', mr: 'हवामान', phrases: [
      ['weather', 3], ['rain', 3], ['rainfall', 3], ['temperature', 3], ['forecast', 3], ['will it rain', 3], ['hot today', 2], ['climate', 2],
      ['हवामान', 3], ['पाऊस', 3], ['पावसाचा', 3], ['तापमान', 3], ['अंदाज', 2], ['ऊन', 1]] },
    { id: 'crop_calendar', target: { path: '/kisaath/crop-calendar' }, en: 'Crop calendar', mr: 'पीक दिनदर्शिका', phrases: [
      ['crop calendar', 4], ['calendar', 3], ['sowing', 3], ['sow', 2], ['harvest', 3], ['season', 2], ['when to plant', 3], ['planting', 2], ['crop plan', 3],
      ['पीक दिनदर्शिका', 4], ['दिनदर्शिका', 3], ['पेरणी', 3], ['कापणी', 3], ['हंगाम', 2], ['पिकाचे नियोजन', 3], ['पीक नियोजन', 3]] },
    { id: 'modern_farming', target: { path: '/kisaath/modern-farming' }, en: 'Modern farming', mr: 'आधुनिक शेती', phrases: [
      ['modern farming', 4], ['modern', 2], ['drip', 3], ['sensor', 3], ['drone', 3], ['hydroponic', 3], ['hydroponics', 3], ['smart farming', 3], ['technology', 2],
      ['आधुनिक शेती', 4], ['आधुनिक', 2], ['ठिबक', 3], ['सेन्सर', 3], ['ड्रोन', 3], ['तंत्रज्ञान', 2]] },
    { id: 'scheme_advisor', target: { path: '/farmer/schemes/' }, en: 'Livestock scheme advisor', mr: 'पशुधन योजना सल्लागार', phrases: [
      ['livestock scheme', 4], ['scheme advisor', 4], ['scheme advisory', 4], ['animal scheme', 3], ['cow scheme', 3], ['dairy scheme', 3], ['subsidy', 2], ['loan', 2], ['scheme', 2], ['schemes', 2],
      ['पशुधन योजना', 4], ['योजना सल्लागार', 4], ['जनावरांची योजना', 3], ['दुग्ध योजना', 3], ['अनुदान', 2], ['कर्ज', 2], ['योजना', 2], ['योजने', 2]] },
    { id: 'gov_schemes', target: { contains: 'farmer-scheme-app' }, en: 'Government schemes', mr: 'सरकारी योजना', phrases: [
      ['government scheme', 4], ['government schemes', 4], ['govt scheme', 4], ['sarkari yojana', 4], ['pm kisan', 4], ['kisan yojana', 3], ['central scheme', 3], ['state scheme', 3], ['scheme', 2], ['schemes', 2],
      ['सरकारी योजना', 4], ['शासकीय योजना', 4], ['किसान योजना', 3], ['पीएम किसान', 4], ['सरकारी', 2], ['योजना', 2], ['योजने', 2]] },
    { id: 'marketplace', target: { path: '/kisaath/marketplace' }, en: 'Marketplace', mr: 'मार्केटप्लेस', phrases: [
      ['marketplace', 4], ['market place', 4], ['market', 3], ['sell', 3], ['buy', 3], ['selling', 3], ['buying', 3], ['produce', 2], ['price', 2], ['prices', 2], ['trade', 2],
      ['मार्केटप्लेस', 4], ['बाजार', 3], ['मार्केट', 3], ['विक्री', 3], ['विकायचे', 3], ['विकायचा', 3], ['खरेदी', 3], ['माल', 2], ['भाव', 2], ['किंमत', 2]] },
    { id: 'all_records', target: { path: '/dashboard' }, en: 'Browse all cow records (vet login)', mr: 'सर्व गायींच्या नोंदी (डॉक्टर लॉगिन)', phrases: [
      ['all cows', 4], ['all cow records', 4], ['cow records', 4], ['cow list', 3], ['registry', 3], ['all records', 3], ['records', 2],
      ['सर्व गायी', 4], ['सर्व गाई', 4], ['गायींच्या नोंदी', 4], ['गाईंच्या नोंदी', 4], ['नोंदी', 2], ['यादी', 2]] },
    { id: 'kisaath', target: { path: '/kisaath/' }, en: 'Kisaath farm tools', mr: 'किसाथ शेती साधने', phrases: [
      ['kisaath', 4], ['kisath', 4], ['kisan saathi', 4], ['kisan sathi', 4], ['farm tools', 3], ['किसाथ', 4], ['किसान साथी', 4], ['शेती साधने', 3]] }
  ];

  /* Words that mean "do something destructive". They never navigate. */
  var BLOCKED = ['delete', 'remove', 'erase', 'destroy', 'wipe', 'cancel account', 'logout', 'log out', 'sign out',
    'पुसा', 'डिलीट', 'काढून टाका', 'काढा', 'नष्ट', 'लॉगआउट', 'लॉग आउट', 'हटवा'];

  var LATIN = /[a-z]/;
  var DEVANAGARI = /[\u0900-\u097F]/;

  function normalize(text) {
    var t = String(text || '').toLowerCase();
    if (t.normalize) t = t.normalize('NFC');
    t = t.replace(/[\u200c\u200d]/g, '');                       // zero-width joiners
    t = t.replace(/[^a-z0-9\u0900-\u097F\s]/g, ' ');             // punctuation, danda, symbols
    return t.replace(/\s+/g, ' ').trim();
  }

  function has(haystack, phrase) {
    var p = normalize(phrase);
    if (!p) return false;
    if (DEVANAGARI.test(p)) return haystack.indexOf(p) !== -1;
    return (' ' + haystack + ' ').indexOf(' ' + p + ' ') !== -1 ||
           // allow simple English plurals / endings: "vets", "cows", "schemes"
           (' ' + haystack + ' ').indexOf(' ' + p + 's ') !== -1;
  }

  function detectLanguage(text) {
    var dev = (String(text).match(/[\u0900-\u097F]/g) || []).length;
    var lat = (String(text).match(/[A-Za-z]/g) || []).length;
    if (dev && !lat) return 'mr';
    if (lat && !dev) return 'en';
    return dev >= lat ? 'mr' : 'en';
  }

  function score(haystack, intent) {
    var total = 0, hits = 0, longest = 0;
    intent.phrases.forEach(function (p) {
      if (has(haystack, p[0])) {
        total += p[1]; hits += 1;
        if (p[0].length > longest) longest = p[0].length;
      }
    });
    // A phrase that is a substring of a longer matched phrase should not count twice.
    var dedup = 0;
    var matched = intent.phrases.filter(function (p) { return has(haystack, p[0]); });
    matched.forEach(function (p) {
      var covered = matched.some(function (q) { return q !== p && normalize(q[0]).indexOf(normalize(p[0])) !== -1 && normalize(q[0]) !== normalize(p[0]); });
      if (!covered) dedup += p[1];
    });
    return dedup || total;
  }

  /* Returns { status: 'navigate'|'choose'|'blocked'|'none', language, intent, options } */
  function interpret(text, resolve) {
    var haystack = normalize(text);
    var language = detectLanguage(text);
    if (!haystack) return { status: 'none', language: language, options: [] };
    for (var i = 0; i < BLOCKED.length; i++) {
      if (has(haystack, BLOCKED[i])) return { status: 'blocked', language: language, options: [] };
    }
    var ranked = [];
    INTENTS.forEach(function (intent) {
      var s = score(haystack, intent);
      if (s > 0 && (!resolve || resolve(intent.target))) ranked.push({ intent: intent, score: s });
    });
    ranked.sort(function (a, b) { return b.score - a.score; });
    if (!ranked.length) return { status: 'none', language: language, options: [] };
    var best = ranked[0], second = ranked[1];
    var margin = best.score - (second ? second.score : 0);
    if (!second && best.score >= 2) {
      return { status: 'navigate', language: language, intent: best.intent, options: [best.intent] };
    }
    if (best.score >= 3 && margin >= 2) {
      return { status: 'navigate', language: language, intent: best.intent, options: [best.intent] };
    }
    if (best.score >= 3 && margin >= 1 && best.score >= 5) {
      return { status: 'navigate', language: language, intent: best.intent, options: [best.intent] };
    }
    return {
      status: 'choose', language: language,
      options: ranked.slice(0, 3).map(function (r) { return r.intent; })
    };
  }

  /* Choose the best reading among several recognizer alternatives (they differ in spelling / language). */
  function interpretAlternatives(alternatives, resolve) {
    var best = null, rank = { navigate: 3, choose: 2, blocked: 4, none: 0 };
    (alternatives || []).forEach(function (text) {
      var r = interpret(text, resolve); r.text = text;
      if (r.status === 'blocked') { best = r; return; }
      if (!best || best.status === 'blocked') { if (!best) best = r; return; }
      if (rank[r.status] > rank[best.status]) best = r;
    });
    return best || { status: 'none', language: 'en', options: [] };
  }

  /* Navigation is a separate function so tests can observe it. */
  function go(href, external) {
    if (external) window.open(href, '_blank', 'noopener'); else window.location.assign(href);
  }

  return { go: go, interpret: interpret, interpretAlternatives: interpretAlternatives, normalize: normalize, detectLanguage: detectLanguage, INTENTS: INTENTS };
}));
