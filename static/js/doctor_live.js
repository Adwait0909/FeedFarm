/* Farm2Feed doctor pages: keep real database data current without a manual reload.
 *  - Dashboard: refreshes the three counters and the cow table.
 *  - Assistance page: shows a banner when requests are created, answered or changed.
 * Polls only while the tab is visible and the browser is online; backs off after errors;
 * uses ETag so unchanged data costs a tiny 304 response. */
(function () {
  'use strict';
  var POLL_MS = 30000;
  var MAX_BACKOFF_MS = 300000;

  function fmtTime(d) {
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }

  function Poller(url, onData, onState) {
    var timer = null, etag = null, inflight = false, failures = 0, stopped = false, lastOk = null;
    function delay() { return Math.min(POLL_MS * Math.pow(2, failures), MAX_BACKOFF_MS); }
    function schedule() { if (stopped) return; clearTimeout(timer); timer = setTimeout(function () { run(false); }, delay()); }
    function run(manual) {
      if (stopped || inflight) return;
      if (!manual && (document.hidden || navigator.onLine === false)) { schedule(); return; }
      inflight = true;
      onState('loading', lastOk);
      var headers = { 'Accept': 'application/json' };
      if (etag) headers['If-None-Match'] = etag;
      fetch(url(), { credentials: 'same-origin', headers: headers, cache: 'no-cache' })
        .then(function (r) {
          if (r.status === 304) return null;
          if (r.status === 401) { var e = new Error('auth'); e.auth = true; throw e; }
          if (!r.ok) throw new Error('HTTP ' + r.status);
          etag = r.headers.get('ETag');
          return r.json();
        })
        .then(function (data) {
          failures = 0; lastOk = new Date();
          if (data) onData(data);
          onState('ok', lastOk);
        })
        .catch(function (err) {
          if (err && err.auth) { stopped = true; onState('auth', lastOk); return; }
          failures += 1;
          onState('error', lastOk);
        })
        .then(function () { inflight = false; schedule(); });
    }
    document.addEventListener('visibilitychange', function () { if (!document.hidden) run(false); });
    window.addEventListener('online', function () { failures = 0; run(false); });
    return { refresh: function () { failures = 0; run(true); }, start: schedule };
  }

  /* ---------------- Dashboard ---------------- */
  var section = document.getElementById('cow-section');
  if (section) {
    var statusBox = document.getElementById('live-status');
    var statusText = document.getElementById('live-status-text');
    var demoNote = document.getElementById('live-demo-note');
    var refreshBtn = document.getElementById('live-refresh');
    var tiles = {
      follow_up_count: document.getElementById('stat-follow-up'),
      vaccination_count: document.getElementById('stat-vaccination'),
      request_count: document.getElementById('stat-requests')
    };
    var search = section.dataset.search || '';
    var profileTpl = section.dataset.profileUrl, updateTpl = section.dataset.updateUrl;
    var requestVersion = section.dataset.requestVersion || null;
    var loadedAt = new Date();

    function state(kind, when) {
      statusBox.dataset.state = kind;
      if (refreshBtn) refreshBtn.hidden = false;
      var stamp = when ? fmtTime(when) : fmtTime(loadedAt);
      if (kind === 'loading') statusText.textContent = 'Updating…';
      else if (kind === 'ok') statusText.textContent = 'Live data from the database · updated ' + stamp + '.';
      else if (kind === 'error') statusText.textContent = 'Could not refresh. Showing the data from ' + stamp + '; retrying automatically.';
      else if (kind === 'auth') {
        statusText.textContent = 'Your session has ended, so the data is no longer updating. ';
        var a = document.createElement('a'); a.href = '/doctor/login'; a.textContent = 'Sign in again';
        statusText.appendChild(a);
        if (refreshBtn) refreshBtn.hidden = true;
      }
    }

    function cell(text, className) {
      var td = document.createElement('td');
      if (className) td.className = className;
      td.textContent = text;
      return td;
    }
    function link(href, text) { var a = document.createElement('a'); a.href = href; a.textContent = text; return a; }

    function healthClass(score) { var s = score || 0; return s >= 80 ? 'good' : (s >= 50 ? 'mid' : 'low'); }

    function renderCows(cows) {
      section.textContent = '';
      if (!cows.length) {
        var empty = document.createElement('div'); empty.className = 'empty-state'; empty.id = 'cow-empty';
        var p = document.createElement('p');
        p.textContent = search ? 'No cows match the current search.' : 'No cows have been registered yet.';
        empty.appendChild(p); section.appendChild(empty); return;
      }
      var table = document.createElement('table'); table.className = 'cow-table'; table.id = 'cow-table';
      var head = document.createElement('thead'), hr = document.createElement('tr');
      ['Cow UID', 'Local No.', 'Name', 'Breed', 'Health', 'Next Checkup', 'Actions'].forEach(function (h) {
        var th = document.createElement('th'); th.textContent = h; hr.appendChild(th);
      });
      head.appendChild(hr); table.appendChild(head);
      var body = document.createElement('tbody'); body.id = 'cow-rows';
      cows.forEach(function (cow) {
        var tr = document.createElement('tr');
        tr.appendChild(cell(cow.cow_id, 'mono'));
        tr.appendChild(cell(cow.local_cow_number || '—'));
        var name = cell(cow.cow_name || '');
        if (cow.is_demo) {
          var tag = document.createElement('span'); tag.className = 'demo-tag'; tag.title = 'Demonstration record'; tag.textContent = 'Demo';
          name.appendChild(document.createTextNode(' ')); name.appendChild(tag);
        }
        tr.appendChild(name);
        tr.appendChild(cell(cow.breed || ''));
        var healthTd = document.createElement('td'), pill = document.createElement('span');
        pill.className = 'pill pill-' + healthClass(cow.health_score);
        pill.textContent = cow.health_status || 'Unknown';
        healthTd.appendChild(pill); tr.appendChild(healthTd);
        tr.appendChild(cell(cow.next_checkup_date || '—'));
        var actions = document.createElement('td'); actions.className = 'table-actions';
        var id = encodeURIComponent(cow.cow_id);
        actions.appendChild(link(profileTpl.replace('__COW__', id), 'Profile'));
        actions.appendChild(document.createTextNode(' '));
        actions.appendChild(link(updateTpl.replace('__COW__', id), 'Update'));
        tr.appendChild(actions); body.appendChild(tr);
      });
      table.appendChild(body); section.appendChild(table);
    }

    var poller = Poller(
      function () { return section.dataset.api + (search ? '?q=' + encodeURIComponent(search) : ''); },
      function (d) {
        Object.keys(tiles).forEach(function (k) { if (tiles[k] && d[k] !== undefined) tiles[k].textContent = d[k]; });
        renderCows(d.cows || []);
        demoNote.textContent = d.demo_count
          ? d.demo_count + ' demonstration record' + (d.demo_count === 1 ? '' : 's') + ' included (marked Demo).' : '';
        if (requestVersion !== null && requestVersion !== d.request_version) {
          statusText.setAttribute('data-changed', '1');
        }
        requestVersion = d.request_version;
      },
      state
    );
    if (refreshBtn) { refreshBtn.hidden = false; refreshBtn.addEventListener('click', function () { poller.refresh(); }); }
    state('ok', loadedAt);
    poller.start();
  }

  /* ---------------- Assistance requests ---------------- */
  var banner = document.getElementById('assist-live');
  if (banner) {
    var baseline = banner.dataset.version || null;
    var assist = Poller(
      function () { return banner.dataset.api + '?summary=1'; },
      function (d) {
        if (baseline === null || baseline === '') { baseline = d.request_version; return; }
        if (d.request_version !== baseline) banner.hidden = false;
      },
      function () {}
    );
    assist.start();
  }
})();
