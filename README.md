# 🦅 SQLHawk

**Created by rV8Cy** &nbsp;|&nbsp; **Version 0.1.0**

📖 این پروژه به فارسی هم مستند شده: [README.fa.md](README.fa.md)

**A multi-language SQL Injection detection scanner built for authorized security testing and bug bounty work.**

SQLHawk crawls a target site, finds every form and URL parameter, and tests each one with three classic SQL injection detection techniques — error-based, boolean-based blind, and time-based blind — then produces a clean, client-ready HTML report you can hand to a site owner or attach to a bug bounty submission.

```
Python  -> crawling, injection logic, reporting, bilingual CLI (Farsi/English)
C       -> fast multi-threaded host/port liveness pre-check
Go      -> optional high-concurrency bulk time-based prober for large target lists
```

Detection works purely over HTTP/HTML, so **it doesn't matter what the target's backend is written in** — PHP, Node.js, Java, Python, Ruby, .NET, Go, etc. all get tested the same way, as long as the vulnerable query itself talks to a SQL database.

## ⚠️ Legal / Ethical Use Only

SQLHawk actively sends test payloads to whatever URL you point it at. **Only use it against:**

- A system **you own**, or
- A target with a **signed penetration testing agreement**, or
- A site with an **official bug bounty program** (e.g. via [HackerOne](https://hackerone.com) or [Bugcrowd](https://bugcrowd.com)) where the target is explicitly in scope.

Scanning a system without authorization is illegal in most countries. The CLI requires you to type `YES` to an authorization prompt before it will run a live scan. **The author(s) accept no responsibility for misuse.**

For practice, use intentionally vulnerable local labs:
- [DVWA](https://github.com/digininja/DVWA)
- [bWAPP](http://www.itsecgames.com/)
- [OWASP Juice Shop](https://github.com/juice-shop/juice-shop)
- [Metasploitable](https://sourceforge.net/projects/metasploitable/)

## Features

- 🌐 **Bilingual CLI** — choose Farsi or English at startup (`Farsi | English ? (F/E)`); every message, prompt, and the HTML report itself switch language accordingly
- 🕷️ **Crawler** — walks the target site (same-domain only, page-limited) collecting forms and URL query parameters
- 💉 **Injector** — tests each field with:
  - Error-based detection (matches DB error signatures for MySQL, PostgreSQL, MSSQL, Oracle, SQLite)
  - Boolean-based blind detection (compares TRUE vs FALSE condition responses)
  - Time-based blind detection (measures response delay from `SLEEP`/`WAITFOR`/`pg_sleep` payloads)
- 🧠 **Analyzer** — fingerprints the likely database engine from error output
- ⚡ **C liveness engine** — multi-threaded TCP connect-check to confirm a host/port is reachable before the (slower) Python crawl starts
- 🚀 **Go bulk prober** (optional) — high-concurrency time-based SQLi re-confirmation across a large list of endpoints at once
- 📄 **HTML report generator** — severity-ranked findings with evidence and remediation advice, generated in Farsi or English, ready to send to a client

## Installation

### 🐧 Linux / macOS

```bash
git clone https://github.com/rV9Cy/SQLHawk.git
cd sqlhawk

# Python dependencies
pip install -r requirements.txt

# Build the optional C liveness engine
cd sqlhawk/engine && gcc -O2 -pthread -o liveness liveness.c && cd ../..

# (optional) build the Go bulk prober
cd sqlhawk/engine_go && go build -o bulkprobe bulkprobe.go && cd ../..

# (optional) install as a system command
pip install -e .
```

### 📱 Termux (Android)

SQLHawk runs fine on Termux since it's pure Python + small C/Go binaries.

```bash
# 1. Update Termux and install what's needed
pkg update && pkg upgrade -y
pkg install python git clang -y
# (optional, only if you want the Go bulk prober too)
pkg install golang -y

# 2. Get the project
git clone https://github.com/rV9Cy/SQLHawk.git
cd sqlhawk

# 3. Python dependencies
pip install -r requirements.txt

# 4. Build the C engine (clang works the same as gcc here)
cd sqlhawk/engine
clang -O2 -pthread -o liveness liveness.c
cd ../..

# 5. Run it (starts interactively — asks Farsi/English, then the link)
python -m sqlhawk.cli

# 6. Open the HTML report (needs Termux:API app + package)
pkg install termux-api -y
termux-open sqlhawk_report.html
```

If you don't have `termux-open`, just move the report to your phone's
`Download` folder (`cp sqlhawk_report.html /sdcard/Download/`, after running
`termux-setup-storage` once) and open it from any file manager/browser.

**About Persian text on Termux:** Termux's terminal doesn't implement the
Unicode bidi/shaping algorithm, so raw Persian text shows up disconnected
and reversed. SQLHawk ships its own small built-in fix for this (no extra
packages needed) that's **on by default**. If you run SQLHawk on a
terminal that already handles Persian correctly (most desktop terminals),
pass `--no-rtl-fix` so it doesn't get double-flipped. The HTML report is
never affected by this — browsers already render Persian correctly on
their own.

## Usage

### Run it like a normal tool (interactive — recommended)

Just run it with no arguments. It clears the screen, asks which language
to use, shows the SQLHawk banner in that language, asks for your
authorization confirmation, then asks you for the link to analyze — and
after each scan, asks if you want to scan another link:

```bash
python -m sqlhawk.cli
```

```
Farsi | English ? (F/E): E

   _____  ____  _      _   _                _
  / ____|/ __ \| |    | | | |              | |
 | (___ | |  | | |    | |_| | __ ___      _| | __
  \___ \| |  | | |    |  _  |/ _` \ \ /\ / / |/ /
  ____) | |__| | |____| | | | (_| |\ V  V /|   <
 |_____/ \___\_\______|_| |_|\__,_| \_/\_/ |_|\_\

        Multi-language Database Vulnerability Scanner  |  v0.1.0
        Creator: rV8Cy

==============================================================
 This tool actively sends test payloads to the target and is
 intended ONLY for authorized targets ...
==============================================================
Type YES to confirm you are authorized to test: YES

Enter the target link to analyze: https://panel.vaslpro.com/
[*] Crawling https://linksite/ (max 25 pages)...
...
[+] Report saved to: sqlhawk_report.html

Analyze another link? (y/n): y

Enter the target link to analyze: _
```

Choosing `F` at the language prompt runs the exact same flow with a
fully Persian screen and a Persian (`dir="rtl"`) HTML report instead.

Add `--no-loop` if you only want to scan one link and exit right after:

```bash
python -m sqlhawk.cli --no-loop
```

`https://panel.linksite.com/` above is just an illustrative example —
only ever enter a link you are actually authorized to test.

### Non-interactive / scripted usage

For CI or repeated automated runs against a pre-approved target, pass
`--url`, `--lang`, and `-y` directly and it skips both prompts:

```bash
python -m sqlhawk.cli --url https://your-authorized-target.com --output report.html --lang en -y
```

Or, if you installed it with `pip install -e .`, run it by name from anywhere (both interactive and scripted forms work the same way):

```bash
sqlhawk
sqlhawk --url https://your-authorized-target.com --output report.html --lang fa -y
```

### Using the Go bulk prober (optional, for large target lists)

Once you have a list of candidate injection points (e.g. from a bigger
crawl or a proxy log), you can re-confirm all of them fast, in parallel:

```bash
cat > targets.txt << EOF
https://your-authorized-target.com/search?id=FUZZ
https://your-authorized-target.com/profile?user=FUZZ&tab=1
EOF

./sqlhawk/engine_go/bulkprobe -file targets.txt -delay 5 -concurrency 20
```

### Options

| Flag | Description | Default |
|---|---|---|
| `--url` | Target base URL (optional - if omitted, the tool asks for it interactively) | — |
| `--output` | Path for the HTML report | `sqlhawk_report.html` |
| `--max-pages` | Max pages to crawl | `25` |
| `--delay` | Seconds used for time-based probes | `5` |
| `-y`, `--yes` | Skip the interactive authorization prompt (for CI/automation on pre-approved targets) | off |
| `--no-banner` | Suppress the ASCII banner / screen clear | off |
| `--no-loop` | Exit after one scan instead of asking for another link (interactive mode loops by default) | off |
| `--lang {fa,en}` | UI language — skips the Farsi/English prompt | — |
| `--no-rtl-fix` | Disable the manual Persian shaping/reordering fix (use on terminals that already render Persian correctly) | off |

### Using the C liveness pre-check (optional)

```python
from sqlhawk.engine.liveness_wrapper import check_ports

check_ports("your-authorized-target.com", [80, 443, 8080])
# {80: True, 443: True, 8080: False}
```

## Project Structure

```
sqlhawk/
├── cli.py                    # main entry point (bilingual)
├── i18n.py                   # English/Persian string tables
├── rtl.py                    # dependency-free Persian shaping/reordering for terminals
├── crawler/
│   └── crawler.py            # form + URL param discovery
├── injector/
│   ├── payloads.py           # detection payload sets
│   └── injector.py           # error/boolean/time-based detection logic
├── analyzer/
│   └── signatures.py         # DB error fingerprinting
├── engine/
│   ├── liveness.c            # fast multi-threaded port checker (C)
│   └── liveness_wrapper.py   # Python bridge to the compiled binary
├── engine_go/
│   └── bulkprobe.go          # concurrent bulk time-based prober (Go)
└── report/
    └── report.py             # HTML report generation (Farsi/English)
```

## Turning this into paid work

1. Sign up on **HackerOne** or **Bugcrowd** and only test programs that explicitly list the target as in-scope.
2. Or approach small businesses directly, explain what you found in general terms, and offer a **written contract** (defined scope, dates, no-damage clause) before running any scan.
3. Use SQLHawk's HTML report as your proof-of-concept writeup — it already includes payload, evidence, and remediation.
4. Never demand payment in exchange for not disclosing a vulnerability publicly — that crosses from bug bounty into extortion and is a crime. Responsible disclosure means reporting the bug, letting them fix it, and getting paid through the program's official bounty/reward process.

## Roadmap Ideas

- [ ] Cookie/session + auth support for scanning behind a login
- [ ] Second-order injection detection
- [ ] NoSQL injection payload set (MongoDB operators)
- [ ] JSON/API endpoint fuzzing (not just HTML forms)
- [ ] PDF report export

## License

MIT — see [LICENSE](LICENSE).


with love rV8Cy & cloude
