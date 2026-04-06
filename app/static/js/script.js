/* ============================================================
   FACE CAMERA WIDGET  v4

   Two modes:
     • "capture"  — for registration (click to capture a still)
     • "scan"     — for login (continuous FaceID-style scanning)

   ALL layout styles are inline to avoid CSS conflicts.
   ============================================================ */

'use strict';

class FaceCamera {

    /**
     * @param {string} containerId
     * @param {object} opts
     * @param {string} opts.mode          — "capture" (default) or "scan"
     * @param {function} opts.onScanFrame — async callback(blob) in scan mode
     * @param {number} opts.scanInterval  — ms between scans (default 1500)
     */
    constructor(containerId, opts = {}) {
        this.el = document.getElementById(containerId);
        if (!this.el) return;

        this.mode          = opts.mode || 'capture';
        this.onScanFrame   = opts.onScanFrame || null;
        this.scanInterval  = opts.scanInterval || 1500;

        this.stream        = null;
        this.animFrame     = null;
        this.capturedBlob  = null;
        this._scanTimer    = null;
        this._scanBusy     = false;
        this._scanning     = false;
        this._state        = 'idle';        // idle | live | captured | matched
        this._ledBlink     = null;

        this._render();
    }

    /* ─────────────────────────────────────────────
       RENDER (100% inline styles)
       ───────────────────────────────────────────── */

    _render() {
        this.el.innerHTML = '';

        const root = this._div({
            width: '100%', display: 'flex', flexDirection: 'column', gap: '10px',
            fontFamily: "'Inter', system-ui, sans-serif"
        });

        // ── Viewport ──
        this.viewport = this._div({
            position: 'relative', width: '100%', paddingTop: '75%',
            borderRadius: '14px', overflow: 'hidden', background: '#0f172a',
            boxShadow: '0 4px 24px rgba(0,0,0,0.18)'
        });

        // Placeholder
        this.placeholder = this._div({
            position: 'absolute', top: '0', left: '0', width: '100%', height: '100%',
            display: 'flex', flexDirection: 'column', alignItems: 'center',
            justifyContent: 'center', gap: '8px', color: '#64748b', fontSize: '13px', zIndex: '1'
        });
        this.placeholder.innerHTML = `
            <svg width="44" height="44" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="1.5" style="opacity:.35">
                <path d="M23 7l-7 5 7 5V7z"/>
                <rect x="1" y="5" width="15" height="14" rx="2"/>
            </svg>
            <span>${this.mode === 'scan' ? 'Click below to start face scan' : 'Click the button below to start'}</span>`;
        this.viewport.appendChild(this.placeholder);

        // Video
        this.vid = document.createElement('video');
        Object.assign(this.vid.style, {
            position: 'absolute', top: '0', left: '0', width: '100%', height: '100%',
            objectFit: 'cover', transform: 'scaleX(-1)', display: 'none', zIndex: '2'
        });
        this.vid.autoplay = true; this.vid.playsInline = true; this.vid.muted = true;
        this.viewport.appendChild(this.vid);

        // Canvas overlay
        this.cvs = document.createElement('canvas');
        Object.assign(this.cvs.style, {
            position: 'absolute', top: '0', left: '0', width: '100%', height: '100%',
            transform: 'scaleX(-1)', pointerEvents: 'none', zIndex: '3'
        });
        this.ctx = this.cvs.getContext('2d');
        this.viewport.appendChild(this.cvs);

        // Still image (capture mode)
        this.still = document.createElement('img');
        this.still.alt = 'Captured face';
        Object.assign(this.still.style, {
            position: 'absolute', top: '0', left: '0', width: '100%', height: '100%',
            objectFit: 'cover', transform: 'scaleX(-1)', display: 'none', zIndex: '4'
        });
        this.viewport.appendChild(this.still);

        // Success flash overlay (scan mode)
        this.flashOverlay = this._div({
            position: 'absolute', top: '0', left: '0', width: '100%', height: '100%',
            background: 'rgba(34,197,94,0.25)', display: 'none', zIndex: '5',
            transition: 'opacity 0.4s'
        });
        this.viewport.appendChild(this.flashOverlay);

        // HUD
        this.hud = this._div({
            position: 'absolute', bottom: '10px', left: '0', width: '100%',
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px',
            zIndex: '6', pointerEvents: 'none'
        });

        this.statusPill = this._div({
            display: 'inline-flex', alignItems: 'center', gap: '6px',
            background: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(6px)',
            color: '#fff', padding: '5px 16px', borderRadius: '20px',
            fontSize: '12px', fontWeight: '500', whiteSpace: 'nowrap',
            transition: 'all 0.3s'
        });

        this.led = this._div({
            width: '8px', height: '8px', borderRadius: '50%',
            background: '#64748b', flexShrink: '0', transition: 'background 0.3s'
        });

        this.statusText = document.createElement('span');
        this.statusText.textContent = 'Camera off';

        this.statusPill.appendChild(this.led);
        this.statusPill.appendChild(this.statusText);
        this.hud.appendChild(this.statusPill);

        // User name badge (shown on match in scan mode)
        this.matchBadge = this._div({
            display: 'none', alignItems: 'center', gap: '6px',
            background: 'rgba(34,197,94,0.92)', backdropFilter: 'blur(4px)',
            color: '#fff', padding: '6px 18px', borderRadius: '20px',
            fontSize: '13px', fontWeight: '700'
        });
        this.hud.appendChild(this.matchBadge);
        this.viewport.appendChild(this.hud);

        root.appendChild(this.viewport);

        // Error
        this.errEl = this._div({
            display: 'none', background: '#fef2f2', border: '1px solid #fecaca',
            borderRadius: '9px', padding: '9px 13px', fontSize: '12px',
            color: '#dc2626', textAlign: 'center'
        });
        root.appendChild(this.errEl);

        // Controls
        this.btnRow = this._div({
            display: 'flex', justifyContent: 'center', alignItems: 'center',
            gap: '12px', flexWrap: 'wrap'
        });

        if (this.mode === 'scan') {
            this.btnMain = this._button('Scan My Face', {
                padding: '11px 28px', border: 'none', borderRadius: '10px',
                background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
                color: '#fff', fontSize: '14px', fontWeight: '700', cursor: 'pointer',
                fontFamily: 'inherit', transition: 'all .2s ease',
                boxShadow: '0 4px 14px rgba(37,99,235,0.3)'
            });
        } else {
            this.btnMain = this._button('Activate Camera', {
                padding: '11px 28px', border: 'none', borderRadius: '10px',
                background: 'linear-gradient(135deg, #3b82f6, #2563eb)',
                color: '#fff', fontSize: '14px', fontWeight: '700', cursor: 'pointer',
                fontFamily: 'inherit', transition: 'all .2s ease',
                boxShadow: '0 4px 14px rgba(37,99,235,0.3)'
            });
        }
        this.btnMain.addEventListener('click', () => this._onMainClick());

        // Retake / Cancel link
        this.btnSecondary = document.createElement('a');
        this.btnSecondary.href = '#';
        this.btnSecondary.textContent = this.mode === 'scan' ? 'Cancel' : 'Retake photo';
        Object.assign(this.btnSecondary.style, {
            display: 'none', fontSize: '13px', color: '#64748b',
            textDecoration: 'underline', cursor: 'pointer'
        });
        this.btnSecondary.addEventListener('click', (e) => {
            e.preventDefault();
            this._retry();
        });

        this.btnRow.appendChild(this.btnMain);
        this.btnRow.appendChild(this.btnSecondary);
        root.appendChild(this.btnRow);

        this.el.appendChild(root);
    }

    /* ─────────────────────────────────────────────
       MAIN BUTTON
       ───────────────────────────────────────────── */

    _onMainClick() {
        if (this._state === 'idle') {
            this._startCamera();
        } else if (this._state === 'live' && this.mode === 'capture') {
            this._capture();
        }
    }

    /* ─────────────────────────────────────────────
       START CAMERA
       ───────────────────────────────────────────── */

    async _startCamera() {
        this._clearErr();
        this.btnMain.textContent = 'Starting...';
        this.btnMain.style.opacity = '0.6';
        this.btnMain.style.pointerEvents = 'none';

        try {
            this.stream = await navigator.mediaDevices.getUserMedia({
                video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
                audio: false
            });
        } catch (err) {
            this.btnMain.textContent = this.mode === 'scan' ? 'Scan My Face' : 'Activate Camera';
            this.btnMain.style.opacity = '1';
            this.btnMain.style.pointerEvents = '';
            this._showErr(
                err.name === 'NotAllowedError'
                    ? 'Camera access denied. Please allow permission in your browser.'
                    : 'Camera error: ' + err.message
            );
            return;
        }

        this.vid.srcObject = this.stream;
        await new Promise(r => { this.vid.onloadedmetadata = r; });

        this.cvs.width  = this.vid.videoWidth  || 640;
        this.cvs.height = this.vid.videoHeight || 480;

        this.vid.style.display = 'block';
        this.placeholder.style.display = 'none';

        this._state = 'live';

        if (this.mode === 'scan') {
            // Scan mode: hide button, show cancel, start scan loop
            this.btnMain.style.display = 'none';
            this.btnSecondary.style.display = '';

            this._setLed('#3b82f6', true);
            this.statusText.textContent = 'Scanning...';

            this._drawGuide();
            this._startScanLoop();
        } else {
            // Capture mode: switch button to "Capture Face"
            this.btnMain.textContent = 'Capture Face';
            this.btnMain.style.opacity = '1';
            this.btnMain.style.pointerEvents = '';
            this.btnMain.style.background = 'linear-gradient(135deg, #22c55e, #16a34a)';
            this.btnMain.style.boxShadow = '0 4px 14px rgba(22,163,74,0.3)';

            this._setLed('#22c55e', true);
            this.statusText.textContent = 'Position your face in the frame';

            this._drawGuide();
        }
    }

    /* ─────────────────────────────────────────────
       CAPTURE (capture mode only)
       ───────────────────────────────────────────── */

    _capture() {
        if (!this.stream) return;

        const off = document.createElement('canvas');
        off.width = this.vid.videoWidth; off.height = this.vid.videoHeight;
        off.getContext('2d').drawImage(this.vid, 0, 0);

        off.toBlob(blob => {
            if (!blob) { this._showErr('Capture failed. Try again.'); return; }
            this.capturedBlob = blob;

            this.still.src = URL.createObjectURL(blob);
            this.still.style.display = 'block';
            this._stopStream();
            this.vid.style.display = 'none';
            this.ctx.clearRect(0, 0, this.cvs.width, this.cvs.height);

            this._clearLedBlink();
            this._setLed('#22c55e', false);
            this.statusText.textContent = 'Face captured';

            this.btnMain.style.display = 'none';
            this.btnSecondary.style.display = '';
            this._state = 'captured';

            this.el.dispatchEvent(new CustomEvent('fc:captured', { detail: { blob }, bubbles: true }));
        }, 'image/jpeg', 0.92);
    }

    /* ─────────────────────────────────────────────
       SCAN LOOP (scan mode — FaceID-style)
       ───────────────────────────────────────────── */

    _startScanLoop() {
        this._scanning = true;
        this._doScanTick();
    }

    _doScanTick() {
        if (!this._scanning || !this.stream) return;

        // Wait for previous request to complete
        if (this._scanBusy) {
            this._scanTimer = setTimeout(() => this._doScanTick(), 300);
            return;
        }

        // Capture a frame
        const off = document.createElement('canvas');
        off.width = this.vid.videoWidth; off.height = this.vid.videoHeight;
        off.getContext('2d').drawImage(this.vid, 0, 0);

        off.toBlob(async (blob) => {
            if (!blob || !this._scanning) return;

            this._scanBusy = true;
            try {
                if (this.onScanFrame) {
                    await this.onScanFrame(blob);
                }
            } finally {
                this._scanBusy = false;
            }

            // Schedule next tick
            if (this._scanning) {
                this._scanTimer = setTimeout(() => this._doScanTick(), this.scanInterval);
            }
        }, 'image/jpeg', 0.85);
    }

    stopScanning() {
        this._scanning = false;
        if (this._scanTimer) { clearTimeout(this._scanTimer); this._scanTimer = null; }
    }

    /* ─────────────────────────────────────────────
       STATUS UPDATES (called by external scan handler)
       ───────────────────────────────────────────── */

    setScanStatus(text, state) {
        this.statusText.textContent = text;

        if (state === 'scanning') {
            this._setLed('#3b82f6', true);
        } else if (state === 'no_face') {
            this._setLed('#f59e0b', true);
        } else if (state === 'success') {
            this._clearLedBlink();
            this._setLed('#22c55e', false);
            this.flashOverlay.style.display = 'block';
            this.btnSecondary.style.display = 'none';
        } else if (state === 'error') {
            this._clearLedBlink();
            this._setLed('#ef4444', false);
        }
    }

    showMatchBadge(name) {
        this.matchBadge.textContent = '\u2713 Welcome, ' + name;
        this.matchBadge.style.display = 'inline-flex';
    }

    /* ─────────────────────────────────────────────
       RETRY
       ───────────────────────────────────────────── */

    _retry() {
        this.capturedBlob = null;
        this.stopScanning();
        this._stopStream();

        this.still.src = ''; this.still.style.display = 'none';
        this.vid.style.display = 'none';
        this.placeholder.style.display = '';
        this.flashOverlay.style.display = 'none';
        this.matchBadge.style.display = 'none';
        this.ctx.clearRect(0, 0, this.cvs.width, this.cvs.height);

        this._clearLedBlink();
        this._setLed('#64748b', false);
        this.statusText.textContent = 'Camera off';

        this.btnMain.textContent = this.mode === 'scan' ? 'Scan My Face' : 'Activate Camera';
        this.btnMain.style.display = '';
        this.btnMain.style.background = 'linear-gradient(135deg, #3b82f6, #2563eb)';
        this.btnMain.style.boxShadow = '0 4px 14px rgba(37,99,235,0.3)';
        this.btnSecondary.style.display = 'none';

        this._state = 'idle';
        this._clearErr();

        this.el.dispatchEvent(new CustomEvent('fc:reset', { bubbles: true }));
    }

    /* ─────────────────────────────────────────────
       OVERLAY DRAWING
       ───────────────────────────────────────────── */

    _drawGuide() {
        if (!this.stream) return;

        const w = this.cvs.width, h = this.cvs.height;
        const ctx = this.ctx;
        const t = performance.now() / 1000;

        ctx.clearRect(0, 0, w, h);

        const cx = w / 2, cy = h / 2;
        const rx = w * 0.20, ry = h * 0.33;
        const a  = 0.45 + 0.4 * Math.abs(Math.sin(t * 1.6));

        // Ellipse guide
        ctx.beginPath();
        ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(255, 255, 255, ${a})`;
        ctx.lineWidth   = 2;
        ctx.setLineDash([8, 6]);
        ctx.stroke();
        ctx.setLineDash([]);

        // Corner brackets
        const arm = 14;
        ctx.strokeStyle = `rgba(255, 255, 255, ${Math.min(1, a + 0.2)})`;
        ctx.lineWidth   = 2.5;
        [[cx-rx,cy-ry,1,1],[cx+rx,cy-ry,-1,1],[cx-rx,cy+ry,1,-1],[cx+rx,cy+ry,-1,-1]]
            .forEach(([x,y,dx,dy]) => {
                ctx.beginPath();
                ctx.moveTo(x+dx*arm, y); ctx.lineTo(x, y); ctx.lineTo(x, y+dy*arm);
                ctx.stroke();
            });

        // Scan line (scan mode only)
        if (this.mode === 'scan' && this._scanning) {
            const scanY = cy - ry + (2 * ry) * ((Math.sin(t * 2.2) + 1) / 2);
            ctx.beginPath();
            // Clip scan line to ellipse width at this y-position
            const dy = scanY - cy;
            const xHalf = rx * Math.sqrt(Math.max(0, 1 - (dy*dy) / (ry*ry)));
            ctx.moveTo(cx - xHalf, scanY);
            ctx.lineTo(cx + xHalf, scanY);
            const lineAlpha = 0.5 + 0.4 * Math.abs(Math.sin(t * 3.5));
            ctx.strokeStyle = `rgba(59, 130, 246, ${lineAlpha})`;
            ctx.lineWidth = 2;
            ctx.shadowColor = 'rgba(59, 130, 246, 0.6)';
            ctx.shadowBlur = 8;
            ctx.stroke();
            ctx.shadowBlur = 0;
        }

        this.animFrame = requestAnimationFrame(() => this._drawGuide());
    }

    /* ─────────────────────────────────────────────
       HELPERS
       ───────────────────────────────────────────── */

    _setLed(color, blink) {
        this._clearLedBlink();
        this.led.style.background = color;
        this.led.style.opacity = '1';
        if (blink) {
            this._ledBlink = setInterval(() => {
                this.led.style.opacity = this.led.style.opacity === '0.3' ? '1' : '0.3';
            }, 500);
        }
    }

    _clearLedBlink() {
        if (this._ledBlink) { clearInterval(this._ledBlink); this._ledBlink = null; }
        this.led.style.opacity = '1';
    }

    _showErr(msg) { this.errEl.textContent = msg; this.errEl.style.display = 'block'; }
    _clearErr()   { this.errEl.textContent = ''; this.errEl.style.display = 'none'; }

    _stopStream() {
        if (this.animFrame) { cancelAnimationFrame(this.animFrame); this.animFrame = null; }
        if (this.stream)    { this.stream.getTracks().forEach(t => t.stop()); this.stream = null; }
        this.vid.srcObject = null;
    }

    _div(s)      { const d = document.createElement('div'); Object.assign(d.style, s); return d; }
    _button(t,s) { const b = document.createElement('button'); b.type='button'; b.textContent=t; Object.assign(b.style,s); return b; }
}


/* ============================================================
   FORM INTERCEPTOR (capture mode — for registration)
   ============================================================ */

function attachFaceForm(formId, cameraId, submitBtnId, errorBoxId) {
    const form      = document.getElementById(formId);
    const submitBtn = document.getElementById(submitBtnId);
    const errorBox  = document.getElementById(errorBoxId);
    if (!form) return;

    const cam = new FaceCamera(cameraId, { mode: 'capture' });
    if (submitBtn) submitBtn.disabled = true;

    document.getElementById(cameraId).addEventListener('fc:captured', () => {
        if (submitBtn) submitBtn.disabled = false;
    });
    document.getElementById(cameraId).addEventListener('fc:reset', () => {
        if (submitBtn) submitBtn.disabled = true;
    });

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!cam.capturedBlob) {
            _showFormError(errorBox, 'Please capture your face before submitting.');
            return;
        }

        const data = new FormData(form);
        data.delete('image');
        data.append('image', cam.capturedBlob, 'face.jpg');
        _setSubmitting(submitBtn, true);

        try {
            const res = await fetch(form.action, { method: 'POST', body: data });
            if (res.redirected) { window.location.href = res.url; return; }

            const html = await res.text();
            const doc  = new DOMParser().parseFromString(html, 'text/html');
            const srv  = doc.querySelector('[data-server-error]') || doc.querySelector('.err-box');
            _showFormError(errorBox, srv ? srv.textContent.trim() : 'An error occurred. Try again.');
        } catch (_) {
            _showFormError(errorBox, 'Network error. Check your connection.');
        } finally {
            _setSubmitting(submitBtn, false);
        }
    });
}

function _showFormError(box, msg) {
    if (!box) return;
    box.textContent = msg; box.style.display = 'block';
}
function _setSubmitting(btn, loading) {
    if (!btn) return;
    btn.disabled = loading;
    btn.textContent = loading ? 'Processing...' : (btn.dataset.label || 'Submit');
}


/* ============================================================
   FACE SCAN HANDLER (scan mode — for login)
   Face-only identification: no email needed.
   ============================================================ */

function attachFaceScan(cameraId, errorBoxId) {
    const errorBox = document.getElementById(errorBoxId);

    const cam = new FaceCamera(cameraId, {
        mode: 'scan',
        scanInterval: 1500,
        onScanFrame: async (blob) => {

            cam.setScanStatus('Analyzing...', 'scanning');

            const data = new FormData();
            data.append('frame', blob, 'frame.jpg');

            try {
                const res  = await fetch('/auth/face-scan', { method: 'POST', body: data });
                const json = await res.json();

                switch (json.status) {
                    case 'success':
                        cam.setScanStatus('Identity verified', 'success');
                        cam.showMatchBadge(json.user_name || 'User');
                        cam.stopScanning();
                        setTimeout(() => { window.location.href = json.redirect; }, 900);
                        break;

                    case 'no_face':
                        cam.setScanStatus(json.message, 'no_face');
                        break;

                    case 'scanning':
                        cam.setScanStatus(json.message, 'scanning');
                        break;

                    case 'not_verified':
                        cam.setScanStatus(json.message, 'error');
                        cam.stopScanning();
                        _showFormError(errorBox, json.message);
                        break;
                }
            } catch (_) {
                cam.setScanStatus('Network error', 'error');
            }
        }
    });
}


/* ============================================================
   PAGE INIT
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

    // ── Login: FaceID-style scan (face only, no email) ──
    if (document.getElementById('login-cam')) {
        attachFaceScan('login-cam', 'login-error');
    }

    // ── Register: capture mode ──
    if (document.getElementById('register-form')) {
        attachFaceForm('register-form', 'register-cam', 'register-submit', 'register-error');

        const form = document.getElementById('register-form');
        const pw1  = form.querySelector('[name="password"]');
        const pw2  = form.querySelector('[name="confirm_password"]');
        const err  = document.getElementById('register-error');

        form.addEventListener('submit', (e) => {
            if (pw1 && pw2 && pw1.value !== pw2.value) {
                e.stopImmediatePropagation(); e.preventDefault();
                _showFormError(err, 'Passwords do not match.');
            }
        }, true);
    }

    // ── Admin: create user (capture mode) ──
    if (document.getElementById('admin-create-user-form')) {
        attachFaceForm(
            'admin-create-user-form', 'admin-create-cam',
            'admin-create-submit-btn', 'admin-create-error-box'
        );
    }

    // ── Generic modal toggles ──
    document.querySelectorAll('[data-modal-target]').forEach(btn => {
        btn.addEventListener('click', () => {
            const t = document.getElementById(btn.dataset.modalTarget);
            if (t) t.style.display = 'flex';
        });
    });
    document.querySelectorAll('[data-modal-close]').forEach(btn => {
        btn.addEventListener('click', () => {
            const m = btn.closest('.admin-modal-overlay');
            if (m) m.style.display = 'none';
        });
    });
});
