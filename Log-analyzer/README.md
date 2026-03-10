<h1>Log Analyzer (Educational Cybersecurity & Monitoring Demo)</h1>

<p>
This project is a lightweight, beginner‑friendly log analysis tool designed 
<strong>solely for personal learning, debugging, and defensive security research</strong>.  
It provides a simple interface for loading, filtering, and inspecting log files so you can better understand how applications record events, errors, and system activity.
</p>

<p>
The tool emphasizes <strong>clarity, transparency, and educational value</strong>, making it ideal for students, analysts, and developers who want to explore log formats, detect patterns, or build intuition for incident‑response workflows.
</p>

<p>
This application is <strong>not</strong> intended for intrusion, unauthorized monitoring, or accessing logs you do not own.  
Use it only on systems and data you control.
</p>

<hr />

<h2>Features</h2>

<ul>
  <li>Clean, browser‑based interface for viewing and filtering logs</li>
  <li>Support for large text‑based log files</li>
  <li>Keyword search and real‑time filtering</li>
  <li>Timestamp‑aware sorting (when present in the log format)</li>
  <li>Simple Python backend powered by <code>Flask</code></li>
  <li>Optional standalone Windows executable (no Python required)</li>
  <li>Readable, minimal code suitable for teaching and experimentation</li>
</ul>

<hr />

<h2>Project Structure</h2>

<pre><code>
Log-analyzer/
│
├── app.py               # Flask backend and routing
├── static/              # Frontend assets (CSS, JS)
├── templates/           # HTML templates
├── requirements.txt     # Python dependencies
└── README.md            # Project documentation
</code></pre>

<hr />


# Installation (from source)

## 1. Clone the repository

```bash
git clone https://github.com/zappybird/Log-analyzer.git
cd Log-analyzer
```

## 2. Create a virtual environment

```bash
python -m venv .venv
```

## 3. Activate it (Windows)

```bash
.venv\Scripts\activate
```

## 4. Install dependencies

```bash
pip install -r requirements.txt
```

## 5. Run the app

```bash
python app.py
```

Then open your browser to:

```text
http://127.0.0.1:5000
```

---

### Running the Standalone Executable

A Windows `.exe` version is available under:

### GitHub → Releases

No Python required. Just download and run.
