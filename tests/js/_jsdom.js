// Finds jsdom: either installed globally / in the project, or inside kisanreact_app/node_modules (Create React App ships it).
const path = require('path');
const candidates = ['jsdom', path.join(__dirname, '../../kisanreact_app/node_modules/jsdom')];
for (const c of candidates) {
  try { module.exports = require(c); return; } catch (e) { /* try next */ }
}
console.log('SKIP: jsdom not found (run "npm ci --legacy-peer-deps" in kisanreact_app first)');
process.exit(77);
