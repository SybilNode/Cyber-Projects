# Network & Vulnerability Scanner

An educational, transparency-focused tool that demonstrates how **port scanning**, **banner grabbing**, and **basic vulnerability detection** work under the hood. Intended solely for personal cybersecurity learning, debugging, and defensive research.

> **Use only on systems you own and have explicit permission to test.**

---

## Features

- Scans a target IP for open TCP ports across a user-defined range
- Performs banner grabbing to identify exposed service information
- Uses Nmap (`-O -sV --script=vuln`) for OS detection and vulnerability enumeration
- Color-coded CLI output for fast, legible results
- Browser-based GUI with live streaming output via Server-Sent Events (SSE)
- Ghost-in-the-Shell style animated boot sequence with terminal sound effects
- Linux TTY aesthetic — phosphor green on pure black

---

## Project Structure

```
Network-Scanner/
│
├── scanner.py          # CLI entry point
├── app.py              # GUI entry point (Flask)
├── requirements.txt    # Python dependencies
├── static/
│   ├── terminal_sfx.js # Terminal sound effects
│   └── sfx/
│       ├── click1.wav
│       ├── click2.wav
│       ├── click3.wav
│       ├── click4.wav
│       ├── enter.wav
│       └── backspace.wav
├── README.md
└── CHANGELOG.md
```

---

## How It Works

### 1. Port Scanning
`port_scan()` iterates over the user-supplied port range and attempts a TCP connection using `socket.connect_ex()`. A result of `0` means the port is open.

### 2. Banner Grabbing
For each open port, `banner_grab()` connects and reads up to 1024 bytes. Many services expose protocol or version information in this initial response.

### 3. Vulnerability & OS Detection
`vulnerability_scan()` uses the Python Nmap wrapper with:
- `-O` for OS fingerprinting
- `-sV` for service version detection
- `--script=vuln` to run Nmap's vulnerability scripts

Results include hostnames, the top three OS matches with accuracy and device type, and vulnerability entries by severity.

### 4. Scan Orchestration
`network_scan()` ties everything together — port scan, banner grab, vulnerability scan, and formatted output with total duration.

### 5. GUI Mode
`app.py` runs a Flask server on `http://127.0.0.1:5000`. Scan output streams line-by-line in real time. An animated Linux-style boot sequence plays on page load with per-character terminal sound effects.

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/Network-Scanner.git
cd Network-Scanner
```

### 2. Create a virtual environment
```bash
python -m venv .venv
```

### 3. Activate it

**Windows:**
```powershell
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### 4. Install dependencies
```bash
pip install -r requirements.txt
```

### 5. Install Nmap on your system

| OS | Command |
|----|---------|
| Windows | [nmap.org/download.html](https://nmap.org/download.html) |
| Debian / Ubuntu | `sudo apt install nmap` |
| macOS | `brew install nmap` |

> OS detection and vulnerability scanning may require running as Administrator or root.

### 6. Run

**CLI mode:**
```bash
python scanner.py
```

**GUI mode:**
```bash
python app.py
```
Then open `http://127.0.0.1:5000` in your browser.

You will be prompted for a target IP address, starting port, and ending port.

---

## Example Output

```
root@scanner:~# ./network_scan.py

[  0.000] Initialising network interfaces...
[  0.012] Loading nmap engine...
[  0.031] Binding raw socket...
[  0.044] System ready.

──────────────────────────────────────────────────
    HOST INFORMATION
──────────────────────────────────────────────────
    HOSTNAME(S)  : dsldevice

    OS DETECTION :
      1. Linux 4.15 - 5.19
         ACCURACY: 100%   TYPE: general purpose
      2. OpenWrt 21.02 (Linux 5.4)
         ACCURACY: 100%   TYPE: general purpose

──────────────────────────────────────────────────
    VULNERABILITY RESULTS
──────────────────────────────────────────────────
    NO KNOWN VULNERABILITIES DETECTED.

════════════════════════════════════════════════════
SCAN COMPLETE  —  DURATION: 0:04:37
════════════════════════════════════════════════════
```

---

## Legal & Ethical Notice

This project is provided for **educational and defensive purposes only**. You must **never** use it to scan networks, devices, or systems you do not own or lack explicit permission to test.

Unauthorized scanning may violate laws or terms of service. Use responsibly and ethically.