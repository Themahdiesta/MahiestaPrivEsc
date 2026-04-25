<#
.SYNOPSIS
    Pure PowerShell accesschk replacement — no EXE, no /accepteula hang.

.DESCRIPTION
    Checks filesystem and registry write permissions for the current user.
    Drop-in for the common accesschk.exe use-cases in Windows privesc.
    Works on PS 2.0+. No admin required to run checks.

.PARAMETER Mode
    services  — Find writable service binaries + service dirs (DEFAULT)
    path      — Check a specific path/file for write access
    dirs      — Find writable dirs under a root path (like -uwdqs)
    registry  — Check service registry keys for write access
    all       — Run all checks

.PARAMETER Target
    Path to check (used with -Mode path or dirs)

.PARAMETER Recurse
    Recurse into subdirectories when using -Mode dirs

.EXAMPLE
    .\Accesschk.ps1
    .\Accesschk.ps1 -Mode all
    .\Accesschk.ps1 -Mode path -Target "C:\Program Files\App\svc.exe"
    .\Accesschk.ps1 -Mode dirs  -Target "C:\" -Recurse
    .\Accesschk.ps1 -Mode registry
#>
param(
    [ValidateSet('services','path','dirs','registry','all')]
    [string]$Mode = 'services',
    [string]$Target = 'C:\',
    [switch]$Recurse
)

Set-StrictMode -Version 2
$ErrorActionPreference = 'SilentlyContinue'

# ── Colours ───────────────────────────────────────────────────────────────────
function Red($s)    { Write-Host $s -ForegroundColor Red }
function Green($s)  { Write-Host $s -ForegroundColor Green }
function Yellow($s) { Write-Host $s -ForegroundColor Yellow }
function Cyan($s)   { Write-Host $s -ForegroundColor Cyan }
function Gray($s)   { Write-Host $s -ForegroundColor DarkGray }

# ── Core permission checker ───────────────────────────────────────────────────
function Test-WriteAccess {
    param([string]$Path, [switch]$IsReg)

    if ($IsReg) {
        try {
            $key = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey(
                $Path.Replace('HKLM:\','').Replace('HKLM:',''),
                [Microsoft.Win32.RegistryKeyPermissionCheck]::ReadWriteSubTree,
                [System.Security.AccessControl.RegistryRights]::WriteKey
            )
            if ($key) { $key.Close(); return $true }
        } catch {}
        return $false
    }

    # File / directory
    try {
        $acl = Get-Acl -Path $Path -ErrorAction Stop
    } catch {
        return $false
    }

    $id        = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object System.Security.Principal.WindowsPrincipal($id)

    $writeRights = [System.Security.AccessControl.FileSystemRights](
        'Write,Modify,FullControl,WriteData,AppendData,WriteExtendedAttributes,WriteAttributes,TakeOwnership,ChangePermissions'
    )

    foreach ($ace in $acl.Access) {
        if ($ace.AccessControlType -ne 'Allow') { continue }
        try {
            $sid = $ace.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier])
        } catch { continue }
        if (-not $principal.IsInRole($sid)) { continue }
        if ($ace.FileSystemRights -band $writeRights) { return $true }
    }
    return $false
}

# ── Banner ────────────────────────────────────────────────────────────────────
function Show-Banner {
    Cyan "============================================================"
    Cyan "  Accesschk.ps1 — Pure PowerShell Permission Checker"
    Cyan "============================================================"
    $u = [System.Security.Principal.WindowsIdentity]::GetCurrent()
    Yellow "  User   : $($u.Name)"
    $groups = $u.Groups | ForEach-Object {
        try { $_.Translate([System.Security.Principal.NTAccount]).Value } catch { $_.Value }
    }
    Yellow "  Groups : $($groups -join ', ')"
    Cyan "------------------------------------------------------------`n"
}

# ── MODE: services ────────────────────────────────────────────────────────────
function Check-Services {
    Cyan "`n[+] Checking service binary and directory write access..."
    $svcs = Get-WmiObject Win32_Service | Where-Object { $_.PathName }
    $found = 0

    foreach ($svc in $svcs) {
        $raw = $svc.PathName.Trim('"')
        # Strip args: take everything up to the first space after .exe
        if ($raw -match '^(.*?\.exe)') { $binPath = $matches[1] } else { $binPath = $raw }
        $binPath = $binPath.Trim('"')
        $dirPath = Split-Path $binPath -Parent

        $binWrite = Test-WriteAccess -Path $binPath
        $dirWrite = Test-WriteAccess -Path $dirPath

        if ($binWrite -or $dirWrite) {
            $found++
            Green "  [WRITABLE] $($svc.Name) ($($svc.State))"
            if ($binWrite) { Yellow "    Binary : $binPath  <-- WRITE" }
            else            { Gray   "    Binary : $binPath" }
            if ($dirWrite)  { Yellow "    Dir    : $dirPath  <-- WRITE" }
            else            { Gray   "    Dir    : $dirPath" }
            Write-Host ""
        }
    }

    if ($found -eq 0) { Gray "  No writable service binaries or directories found." }
    else              { Red "  SUMMARY: $found writable service(s) found — check each one above!" }
}

# ── MODE: path ────────────────────────────────────────────────────────────────
function Check-Path {
    param([string]$P)
    Cyan "`n[+] Checking write access: $P"
    if (-not (Test-Path $P)) { Red "  Path does not exist: $P"; return }
    if (Test-WriteAccess -Path $P) {
        Green "  [WRITABLE] $P"
        # Show which ACE grants access
        $acl = Get-Acl $P
        $id  = [System.Security.Principal.WindowsIdentity]::GetCurrent()
        $prin = New-Object System.Security.Principal.WindowsPrincipal($id)
        $wR  = [System.Security.AccessControl.FileSystemRights]'Write,Modify,FullControl,WriteData,TakeOwnership,ChangePermissions'
        foreach ($ace in $acl.Access) {
            if ($ace.AccessControlType -ne 'Allow') { continue }
            try { $sid = $ace.IdentityReference.Translate([System.Security.Principal.SecurityIdentifier]) } catch { continue }
            if ($prin.IsInRole($sid) -and ($ace.FileSystemRights -band $wR)) {
                Yellow "    via: $($ace.IdentityReference) ($($ace.FileSystemRights))"
            }
        }
    } else {
        Red "  [NO WRITE] $P"
    }
}

# ── MODE: dirs ────────────────────────────────────────────────────────────────
function Check-Dirs {
    param([string]$Root, [switch]$R)
    Cyan "`n[+] Scanning for writable directories under: $Root"
    $depth = if ($R) { -Recurse } else { @() }
    $dirs  = Get-ChildItem -Path $Root -Directory -ErrorAction SilentlyContinue @depth |
             Where-Object { $_.FullName -notmatch 'WinSxS|assembly|Microsoft\.NET' }
    $found = 0
    foreach ($d in $dirs) {
        if (Test-WriteAccess -Path $d.FullName) {
            Green "  [W] $($d.FullName)"
            $found++
        }
    }
    if ($found -eq 0) { Gray "  No writable directories found under $Root" }
    else              { Red  "  SUMMARY: $found writable dir(s) found." }
}

# ── MODE: registry ────────────────────────────────────────────────────────────
function Check-Registry {
    Cyan "`n[+] Checking write access on service registry keys..."
    $base = 'HKLM:\SYSTEM\CurrentControlSet\Services'
    $keys = Get-ChildItem -Path $base -ErrorAction SilentlyContinue
    $found = 0
    foreach ($k in $keys) {
        $subPath = $k.Name.Replace('HKEY_LOCAL_MACHINE\','HKLM:\')
        if (Test-WriteAccess -Path $subPath -IsReg) {
            $found++
            Green "  [WRITABLE] $($k.PSChildName)"
            Yellow "    Key: $($k.Name)"
            Write-Host ""
        }
    }
    if ($found -eq 0) { Gray "  No writable service registry keys found." }
    else              { Red  "  SUMMARY: $found writable registry key(s) — can modify service config!" }
}

# ── Entry point ───────────────────────────────────────────────────────────────
Show-Banner

switch ($Mode) {
    'services' { Check-Services }
    'path'     { Check-Path -P $Target }
    'dirs'     { Check-Dirs -Root $Target -R:$Recurse }
    'registry' { Check-Registry }
    'all'      {
        Check-Services
        Check-Dirs -Root 'C:\' -R
        Check-Registry
    }
}

Write-Host ""
Cyan "============================================================"
Cyan "  Done. Use icacls <path> to verify specific ACEs."
Cyan "============================================================"
