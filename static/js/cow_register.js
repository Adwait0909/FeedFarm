/* Cow registration forms: photo chooser with preview + live review panel.
 * Works with any <form data-live-review data-lang="en|mr"> that contains:
 *   - elements with data-review="<field name>"   (filled live as the user types)
 *   - [data-review-photo], [data-review-progress]
 *   - a file input named cow_image and a [data-photo-feedback] block
 * Everything is written with textContent / createObjectURL, never innerHTML. */
(function () {
  'use strict';
  var form = document.querySelector('form[data-live-review]');
  if (!form) return;

  var mr = (form.getAttribute('data-lang') || 'en') === 'mr';
  function T(en, marathi) { return mr ? marathi : en; }

  var MAX_BYTES = 4 * 1024 * 1024;
  var ALLOWED = ['image/png', 'image/jpeg'];
  var ALLOWED_EXT = /\.(png|jpe?g)$/i;

  var fileInput = form.querySelector('input[type="file"][name="cow_image"]');
  var feedback = form.querySelector('[data-photo-feedback]');
  var img = feedback && feedback.querySelector('[data-photo-img]');
  var nameBox = feedback && feedback.querySelector('[data-photo-name]');
  var errorBox = feedback && feedback.querySelector('[data-photo-error]');
  var removeBtn = feedback && feedback.querySelector('[data-photo-remove]');
  var reviewPhoto = form.querySelector('[data-review-photo]');
  var progress = form.querySelector('[data-review-progress]');
  var previewUrl = null;

  function fieldValue(name) {
    var el = form.elements[name];
    if (!el) return '';
    if (el.tagName === 'SELECT') {
      var opt = el.options[el.selectedIndex];
      return opt && el.value ? opt.text.trim() : '';
    }
    return (el.value || '').trim();
  }

  function formatSize(bytes) {
    return bytes >= 1048576 ? (bytes / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(bytes / 1024)) + ' KB';
  }

  function updateReview() {
    var nodes = form.querySelectorAll('[data-review]');
    for (var i = 0; i < nodes.length; i++) {
      var value = fieldValue(nodes[i].getAttribute('data-review'));
      nodes[i].textContent = value || '—';
      nodes[i].classList.toggle('is-empty', !value);
    }
    if (progress) {
      var required = form.querySelectorAll('[required]');
      var done = 0;
      for (var j = 0; j < required.length; j++) { if ((required[j].value || '').trim()) done++; }
      progress.textContent = required.length
        ? T(done + ' of ' + required.length + ' required fields completed',
            done + ' / ' + required.length + ' आवश्यक माहिती भरली')
        : '';
      progress.classList.toggle('is-complete', required.length > 0 && done === required.length);
    }
  }

  function clearPhoto(keepError) {
    if (previewUrl) { URL.revokeObjectURL(previewUrl); previewUrl = null; }
    if (img) { img.hidden = true; img.removeAttribute('src'); }
    if (nameBox) nameBox.textContent = '';
    if (removeBtn) removeBtn.hidden = true;
    if (errorBox && !keepError) errorBox.textContent = '';
    if (reviewPhoto) { reviewPhoto.textContent = T('No photo selected', 'फोटो निवडला नाही'); reviewPhoto.classList.add('is-empty'); }
  }

  function showError(message) {
    if (fileInput) fileInput.value = '';
    clearPhoto(true);
    if (errorBox) errorBox.textContent = message;
  }

  function onPhotoChosen() {
    var file = fileInput.files && fileInput.files[0];
    if (errorBox) errorBox.textContent = '';
    if (!file) { clearPhoto(); return; }
    var typeOk = ALLOWED.indexOf(file.type) !== -1 || (!file.type && ALLOWED_EXT.test(file.name));
    if (!typeOk || !ALLOWED_EXT.test(file.name)) {
      showError(T('Only PNG, JPG or JPEG photos can be uploaded.', 'फक्त PNG, JPG किंवा JPEG फोटो अपलोड करता येतात.'));
      return;
    }
    if (file.size > MAX_BYTES) {
      showError(T('This photo is ' + formatSize(file.size) + '. Please choose one under 4 MB.',
                  'हा फोटो ' + formatSize(file.size) + ' आहे. कृपया 4 MB पेक्षा लहान फोटो निवडा.'));
      return;
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(file);
    if (img) {
      img.onerror = function () { showError(T('This file could not be read as an image.', 'ही फाइल फोटो म्हणून वाचता आली नाही.')); };
      img.src = previewUrl;
      img.alt = T('Preview of the selected cow photo', 'निवडलेल्या गायीच्या फोटोचे पूर्वावलोकन');
      img.hidden = false;
    }
    if (nameBox) nameBox.textContent = file.name + ' (' + formatSize(file.size) + ')';
    if (removeBtn) removeBtn.hidden = false;
    if (reviewPhoto) { reviewPhoto.textContent = file.name; reviewPhoto.classList.remove('is-empty'); }
  }

  if (fileInput) fileInput.addEventListener('change', onPhotoChosen);
  if (removeBtn) removeBtn.addEventListener('click', function () { fileInput.value = ''; clearPhoto(); });

  form.addEventListener('input', updateReview);
  form.addEventListener('change', updateReview);
  form.addEventListener('reset', function () { setTimeout(function () { clearPhoto(); updateReview(); }, 0); });

  clearPhoto();
  updateReview();
  if (fileInput && fileInput.files && fileInput.files.length) onPhotoChosen();   // e.g. browser restored the form
})();
