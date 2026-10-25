(function () {
  (function () {
    const statusEl = document.getElementById('qr-reader-status');
    const readerEl = document.getElementById('qr-reader');

    function logDev(msg, obj) {
      if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        console.debug('[qr]', msg, obj || '');
      }
    }

    if (typeof Html5Qrcode === 'undefined') {
      statusEl.textContent = 'Scanner library failed to load. Check your internet connection.';
      logDev('Html5Qrcode not loaded');
      return;
    }

    // prefer element id 'qr-reader' for Html5Qrcode
    const html5QrCode = new Html5Qrcode('qr-reader');
    let active = false;

    function stopScanner() {
      if (active) {
        html5QrCode.stop().then(() => {
          active = false;
          logDev('scanner stopped');
        }).catch(err => logDev('stop error', err));
      }
    }

    function onScanSuccess(decodedText) {
      stopScanner();
      statusEl.textContent = 'QR detected. Opening...';
      logDev('decoded', decodedText);
      const target = decodedText.trim();
      const looksLikeUrl = /^https?:\/\//i.test(target);
      if (looksLikeUrl) {
        window.location.href = target;
      } else {
        window.location.href = '/cow/' + encodeURIComponent(target);
      }
    }

    function onScanFailure(err) {
      // no-op for continuous scanning
    }

    const config = { fps: 10, qrbox: { width: 250, height: 250 } };

    // Check for mediaDevices API and secure context
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      statusEl.textContent = 'Camera not available in this browser.';
      logDev('mediaDevices not available');
      return;
    }

    // enumerate cameras and select environment-facing when possible
    navigator.mediaDevices.enumerateDevices().then(devices => {
      const videoInputs = devices.filter(d => d.kind === 'videoinput');
      logDev('devices', videoInputs);
      let cameraId = null;
      // pick a device labelled with back/rear keywords if available
      for (const d of videoInputs) {
        const label = (d.label || '').toLowerCase();
        if (label.includes('back') || label.includes('rear') || label.includes('environment')) {
          cameraId = d.deviceId; break;
        }
      }
      const constraints = cameraId ? { deviceId: { exact: cameraId } } : { facingMode: { exact: 'environment' } };
      html5QrCode.start(constraints, config, onScanSuccess, onScanFailure).then(() => {
        active = true;
        statusEl.textContent = 'Camera ready — scanning for QR code...';
        logDev('scanner started', { cameraId });
      }).catch(err => {
        // fallback to simple environment facingMode
        html5QrCode.start({ facingMode: 'environment' }, config, onScanSuccess, onScanFailure).then(() => {
          active = true; statusEl.textContent = 'Camera ready — scanning for QR code...';
        }).catch(err2 => {
          statusEl.textContent = 'Could not start the camera. Please allow camera access and use a secure (HTTPS) connection.';
          logDev('start failed', { err, err2 });
        });
      });
    }).catch(err => {
      statusEl.textContent = 'Unable to enumerate cameras.';
      logDev('enumerateDevices failed', err);
    });

    // cleanup on page unload
    window.addEventListener('pagehide', stopScanner);
    window.addEventListener('beforeunload', stopScanner);
  })();
})();