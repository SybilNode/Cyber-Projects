# Changelog

All notable changes to the Network & Vulnerability Scanner, compiled from v1.0 to present.

---

## v2.3

### Changed

- **Full visual redesign — Linux TTY aesthetic** — Commodore 64 purple theme replaced entirely with a phosphor green / pure black palette. Three green shades only: `#00ff41` (bright), `#00c832` (mid), `#005c1a` (dim). No other colours anywhere in the UI.
- **Font changed from Share Tech Mono to VT323** — VT323 is a bitmap-style font that more closely matches a real Linux TTY or VGA console.
- **Bezel and card layout removed** — the centred max-width card with rounded corners, gradient background, and box-shadow is gone. The UI now fills the full viewport width with no container borders, matching a raw terminal session.
- **Input panel redesigned as inline shell arguments** — fields labelled `--target`, `--port-start`, `--port-end`. Inputs have no box border, only an underline. Button reads `[ SCAN ]`.
- **Title bar changed to shell prompt style** — `root@scanner:~# ./network_scan.py` replaces the old `■ NETWORK SCANNER` heading. Badge shows `tty1 | pts/0 | v2.2`.
- **Intro animation updated to Linux boot sequence** — C64-style text replaced with a kernel/dmesg style boot log with timestamped init lines (`[  0.000] Initialising network interfaces...`).
- **Output height fills viewport** — `#terminalOutput` height changed from fixed `480px` to `calc(100vh - 180px)` so the terminal fills the screen regardless of window size.
- **Status messages lowercased** — `IDLE`, `SCANNING...`, `SCAN COMPLETE` changed to `idle`, `scanning...`, `done.` to match Unix convention.
- **Scanline overlay recoloured** — gradient changed from dark purple tint to faint green phosphor tint to complement the new palette.

---

## v2.2

### Added

- **Ghost-in-the-Shell intro animation** — animated typewriter sequence prints to `#terminalOutput` on page load before the user types anything. Character-by-character with randomised timing, newline pauses, and per-character sounds.
- **`newlinePauseMs` option in `typeOut()`** — configurable extra delay after each `\n` for dramatic pacing. Defaults to `0` in manual calls, `160ms` in the intro sequence.
- **`onComplete` callback in `typeOut()`** — optional function called when the typewriter animation finishes. Used by the intro to auto-focus `#target` after the boot sequence completes.
- **Live timestamp in intro text** — generated at page load time so it reflects the actual session start.
- **Dual-path sound triggering in `appendLine()`** — calls `TerminalSFX.playClick()` directly on every appended line in addition to the MutationObserver, ensuring sounds fire reliably on all SSE output.
- **Visual intro starts on page load** — the animation no longer waits for a user gesture. Audio unlocks silently on first interaction and plays normally thereafter.

### Improved

- **Root cause fix: AudioContext not unlocking** — `AudioContext` is now created *inside* the gesture event handler (`unlock()`), not at `init()` time. Browsers require the context to be created or resumed synchronously within a user-gesture call stack.
- **Two-phase buffer loading** — WAV files are fetched as raw `ArrayBuffer`s at `init()` time via `fetch()` (no gesture needed). `decodeAudioData()` is deferred until after the context exists. `.slice(0)` clone prevents the detachment bug on the original buffer.
- **Unlock listeners moved to `window`** — previously attached to `document`; now attached to `window` for broadest gesture capture.
- **`playBuffer()` guard tightened** — now checks `audioCtx.state === 'running'` explicitly before attempting `source.start()`.
- **`typeOut()` uses `observerPaused` flag** — instead of disconnecting and reconnecting the `MutationObserver` (which was racey), the observer checks a boolean flag and skips processing while `typeOut()` is animating.
- **Output element corrected to `#terminalOutput`** — was previously `id="screen"` on a `<div>`, mismatching the selectors in `terminal_sfx.js`. Now `<pre id="terminalOutput">`.
- **`appendLine()` rewritten to use `<span>` children** — previously used `<div>` elements which broke layout inside `<pre>`. Now appends `<span class="line ...">` followed by an explicit newline text node.
- **Cursor managed as a persistent last child** — `ensureCursor()` removes any existing cursor and appends a fresh one at the end of `#terminalOutput` after every write.
- **`TerminalSFX.init()` called with explicit config** — all selectors, sound paths, and throttle values passed explicitly rather than relying on defaults.

### Changed

- **Intro text is `null` by default in config** — built at runtime in `runIntro()` so the timestamp reflects actual interaction time rather than parse time.
- **First-gesture listeners on `window` in inline script** — two `{ once: true }` listeners call `onFirstGesture()` which unlocks audio. Visual intro is driven separately via `DOMContentLoaded`.

### Removed

- **Hardcoded static intro HTML removed from template** — replaced by a single plain-text placeholder that `showIntro()` wipes and replaces with the animated sequence.

---

## v2.1

### Added

- **Terminal sound effects (`terminal_sfx.js`)** — standalone JavaScript file adding Ghost in the Shell / Matrix style typewriter audio to the Flask GUI. Served from `/static/terminal_sfx.js`.
- **Web Audio API integration** — single shared `AudioContext` initialised in suspended state. Resumed only on a real user gesture via `TerminalSFX.unlock()`.
- **Multi-sample click engine** — loads up to four click samples (`click1.wav`–`click4.wav`) from `/static/sfx/` and randomly selects one per keystroke. Dedicated sounds for `enter.wav`, `backspace.wav`, and optional `error.wav`.
- **Per-play audio jitter** — each sound plays with randomised volume (±15%) and playback rate (±3%) for an organic feel.
- **Throttling and rate limiting** — configurable cooldown (default 20ms) and hard cap of 30 sounds/sec. Bulk appends above `bulkThreshold` (default 20 chars) collapse to a single sound.
- **Input typing hooks** — attaches to `#target` via `keydown`. Printable characters → click, Enter → `enter.wav`, Backspace/Delete → `backspace.wav`.
- **MutationObserver output mode** — watches `#terminalOutput` and plays sounds as new text is appended by the SSE stream.
- **`TerminalSFX.typeOut(text, opts)`** — appends text character-by-character with configurable delay and per-character sounds. Pauses the MutationObserver during playback to prevent double-firing.
- **Public API on `window.TerminalSFX`** — `init(configOverride)`, `unlock()`, `typeOut(text, opts)`, `playClick(kind)`. All safe to call regardless of audio lock state.
- **Top-level config object** — all selectors, sound paths, volume levels, jitter ranges, cooldowns, and feature flags in one `DEFAULT_CONFIG` block, overridable at runtime.
- **`/static/sfx/` directory convention** — required files: `click1–4.wav`, `enter.wav`, `backspace.wav`. Optional: `error.wav`. Missing files handled gracefully.

---

## v2.0

### Added

- **Browser-based GUI (`app.py`)** — new Flask server entry point on `http://127.0.0.1:5000`. Accepts the same three inputs as `scanner.py`: target IP, start port, end port.
- **Live streaming output via Server-Sent Events (SSE)** — scan results stream line-by-line in real time as they are produced.
- **Live elapsed timer** — status bar counts up continuously during an active scan.
- **Color-coded terminal output (CLI)** — ANSI color applied across all CLI output: cyan for phases, green for open ports and clean results, yellow for warnings, red for vulnerabilities.
- **Structured section headers and dividers (CLI)** — output divided into clearly labelled sections (Port Scan Results, Host Information, Vulnerability Scan) separated by horizontal dividers.

### Improved

- **OS match formatting** — raw nested dictionary output replaced with a clean numbered list showing the top three OS matches with name, accuracy percentage, and device type.
- **Banner grabbing flow** — banners silently collected into a dictionary, then displayed in a formatted port table. Previously each attempt printed its own interleaved status line.
- **Vulnerability description truncation** — descriptions capped at 120 characters with ellipsis.
- **Scan duration display** — microseconds stripped from elapsed time string (`0:04:37.630867` → `0:04:37`).

### Changed

- **Project structure** — two runnable entry points: `scanner.py` (CLI) and `app.py` (GUI). Both share the same underlying scan functions.
- **Dependencies** — `flask` added for GUI mode. `requests` removed (was imported but unused).
- **Example output in documentation** — updated to reflect new formatted output structure.

### Removed

- **Inline progress noise** — status lines like `"Grabbing banner for target:port…"` no longer appear interleaved with results. Phase progress consolidated into labelled headers.
- **Raw dict dumps** — `print(f"Hostnames: {vuln_info['hostnames']}")` and `print(f"Vulnerabilities: {vuln_info['vulns']}")` replaced with parsed, formatted output functions.

---

## v1.0

Initial release. Single-file CLI scanner (`scanner.py`) with port scanning, banner grabbing, and Nmap-based OS and vulnerability detection. Raw dictionary output. No formatting.