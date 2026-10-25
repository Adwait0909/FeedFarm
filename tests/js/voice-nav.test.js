/* Run with:  node tests/voice-nav.test.js   (no dependencies) */
const assert = require('assert');
const V = require('../../static/js/voice-nav.js');

// Every destination exists on the home page, so resolve() accepts all of them.
const all = () => true;
const cases = [
  // [spoken text, expected intent id | 'choose:a,b' | 'blocked' | 'none']
  ['scan a cow QR code', 'scan'], ['I want to scan the QR', 'scan'], ['show cow details', 'scan'], ['cow passport', 'scan'],
  ['गायीचा क्यूआर स्कॅन करा', 'scan'], ['गायीची माहिती दाखवा', 'scan'], ['गाईचे तपशील', 'scan'],
  ['register a new cow', 'register'], ['add cow', 'register'], ['cow registration', 'register'],
  ['नवीन गाय नोंदवा', 'register'], ['गाय नोंदणी करायची आहे', 'register'], ['गाईची नोंदणी', 'register'],
  ['my cow is sick', 'animal_health'], ['check animal disease', 'animal_health'], ['lumpy skin symptoms', 'animal_health'],
  ['माझी गाय आजारी आहे', 'animal_health'], ['जनावराचा आजार तपासा', 'animal_health'], ['लम्पी रोग', 'animal_health'],
  ['crop disease detection', 'crop_disease'], ['leaf disease', 'crop_disease'], ['पिकाचा रोग तपासा', 'crop_disease'], ['पानावर रोग', 'crop_disease'],
  ['find a vet nearby', 'vet_finder'], ['contact doctor', 'vet_finder'], ['I need a veterinarian', 'vet_finder'], ['clinic near me', 'vet_finder'],
  ['जवळचा पशुवैद्य शोधा', 'vet_finder'], ['डॉक्टरशी संपर्क', 'vet_finder'], ['दवाखाना कुठे आहे', 'vet_finder'],
  ['doctor login', 'vet_login'], ['vet sign in', 'vet_login'], ['डॉक्टर लॉगिन', 'vet_login'],
  ['my farm', 'my_farm'], ['farmer login', 'my_farm'], ['my cows', 'my_farm'], ['माझे शेत', 'my_farm'], ['शेतकरी लॉगिन', 'my_farm'], ['माझा गोठा', 'my_farm'],
  ['what is the weather', 'weather'], ['will it rain today', 'weather'], ['हवामान सांगा', 'weather'], ['आज पाऊस पडेल का', 'weather'], ['तापमान किती आहे', 'weather'],
  ['crop calendar', 'crop_calendar'], ['when is harvest', 'crop_calendar'], ['पीक दिनदर्शिका', 'crop_calendar'], ['पेरणी कधी करावी', 'crop_calendar'],
  ['modern farming', 'modern_farming'], ['drip irrigation', 'modern_farming'], ['आधुनिक शेती', 'modern_farming'], ['ठिबक सिंचन', 'modern_farming'],
  ['livestock scheme advisor', 'scheme_advisor'], ['पशुधन योजना', 'scheme_advisor'], ['government schemes', 'gov_schemes'], ['सरकारी योजना', 'gov_schemes'], ['pm kisan', 'gov_schemes'],
  ['schemes', 'choose:scheme_advisor,gov_schemes'], ['योजना', 'choose:scheme_advisor,gov_schemes'],
  ['open marketplace', 'marketplace'], ['I want to sell my produce', 'marketplace'], ['मार्केटप्लेस उघडा', 'marketplace'], ['माल विकायचा आहे', 'marketplace'], ['बाजार भाव', 'marketplace'],
  ['all cow records', 'all_records'], ['सर्व गायींच्या नोंदी', 'all_records'],
  ['kisaath tools', 'kisaath'], ['किसाथ', 'kisaath'],
  // destructive or sensitive words never navigate
  ['delete cow', 'blocked'], ['remove my cow from the registry', 'blocked'], ['गाय डिलीट करा', 'blocked'], ['गाय काढून टाका', 'blocked'], ['log out', 'blocked'], ['लॉगआउट', 'blocked'],
  // nothing usable
  ['', 'none'], ['hello how are you', 'none'], ['नमस्कार', 'none'], ['asdf qwer', 'none'],
];
let failed = 0;
for (const [text, expected] of cases) {
  const r = V.interpret(text, all);
  let actual = r.status === 'navigate' ? r.intent.id : r.status === 'choose' ? 'choose:' + r.options.map(o => o.id).sort().join(',') : r.status;
  if (expected.startsWith('choose:')) expected.split(':')[1] && (actual = r.status === 'choose' ? 'choose:' + r.options.map(o => o.id).filter(id => expected.includes(id)).sort().join(',') : actual);
  const want = expected.startsWith('choose:') ? 'choose:' + expected.split(':')[1].split(',').sort().join(',') : expected;
  if (actual !== want) { failed++; console.log('FAIL', JSON.stringify(text), '->', actual, '(expected', want + ')'); }
}
console.log(`${cases.length - failed}/${cases.length} phrases correct`);

// A destination that is not on the page is never offered.
const noMarket = (t) => !(t.path === '/kisaath/marketplace');
assert.notStrictEqual(V.interpret('open marketplace', noMarket).intent && V.interpret('open marketplace', noMarket).intent.id, 'marketplace');
// Different commands lead to different pages.
const targets = new Set(['scan a qr', 'weather', 'sell produce', 'find a vet', 'crop calendar'].map(t => JSON.stringify(V.interpret(t, all).intent.target)));
assert.strictEqual(targets.size, 5);
// Language detection
assert.strictEqual(V.detectLanguage('गायीची माहिती'), 'mr');
assert.strictEqual(V.detectLanguage('cow details'), 'en');
// Alternatives: the better reading wins; a blocked reading always wins.
assert.strictEqual(V.interpretAlternatives(['gibberish', 'weather forecast'], all).intent.id, 'weather');
assert.strictEqual(V.interpretAlternatives(['weather', 'delete everything'], all).status, 'blocked');
if (failed) process.exit(1);
console.log('voice-nav: all checks passed');
