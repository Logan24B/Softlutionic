param(
    [ValidateRange(1024,65535)][int]$Port=8000,
    [switch]$Background,
    [switch]$OpenFirewall
)
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$python=Join-Path $root '.venv\Scripts\python.exe'
$runtime=Join-Path $root '.runtime'
$private=Join-Path $root '.private'
if(!(Test-Path $python)) { throw 'Prepare .venv and install requirements.txt first' }
if(Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) { throw "Port $Port is already in use; no process was stopped" }
New-Item $runtime,$private -ItemType Directory -Force | Out-Null
$identity=[Security.Principal.WindowsIdentity]::GetCurrent().Name
foreach($dir in @($runtime,$private)) {
    & icacls.exe $dir /inheritance:r /grant:r "${identity}:(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
    if($LASTEXITCODE) { throw 'Cannot protect private runtime files' }
}
Push-Location $root
try {
    & $python -c "from pathlib import Path; import secrets; p=Path('.private/django-secret.key'); p.exists() or p.write_text(secrets.token_urlsafe(64),encoding='utf-8')"
    if($LASTEXITCODE) { throw 'Cannot prepare private signing key' }
    $addresses=@(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.AddressState -eq 'Preferred' -and $_.IPAddress -ne '127.0.0.1' -and $_.IPAddress -notlike '169.254.*'} | Select-Object -ExpandProperty IPAddress)
    $env:SOFTFACTUR_ALLOWED_HOSTS=(@($env:SOFTFACTUR_ALLOWED_HOSTS)+$addresses | Where-Object {$_} | Select-Object -Unique) -join ','
    $env:SOFTFACTUR_DEBUG='false'
    & $python (Join-Path $PSScriptRoot 'check_database.py')
    if($LASTEXITCODE) { throw 'Local SQL connection failed; server was not started' }
    & $python manage.py check
    if($LASTEXITCODE) { throw 'Django validation failed' }
    & $python manage.py collectstatic --noinput
    if($LASTEXITCODE) { throw 'Static asset preparation failed' }
    if($OpenFirewall) {
        $ruleName="Softlutionic-LAN-$Port"
        $rule=Get-NetFirewallRule -Name $ruleName -ErrorAction SilentlyContinue
        if($rule) {
            $filter=$rule | Get-NetFirewallPortFilter
            $address=$rule | Get-NetFirewallAddressFilter
            if($rule.Direction -ne 'Inbound' -or $rule.Action -ne 'Allow' -or $rule.Enabled -ne 'True' -or [string]$rule.Profile -ne 'Private' -or [string]$filter.LocalPort -ne [string]$Port -or [string]$filter.Protocol -ne 'TCP' -or [string]$address.RemoteAddress -ne 'LocalSubnet') { throw 'Existing firewall rule differs; inspect it manually' }
        } else {
            New-NetFirewallRule -Name $ruleName -DisplayName "Softlutionic LAN TCP $Port" -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port -Profile Private -RemoteAddress LocalSubnet | Out-Null
        }
    }
    $urls=@("http://localhost:$Port/")+@($addresses | ForEach-Object {"http://${_}:$Port/"})
    $server=Join-Path $PSScriptRoot 'serve_local.py'
    if($Background) {
        $arguments='"'+$server+'" --host 0.0.0.0 --port '+$Port
        $process=Start-Process -FilePath $python -ArgumentList $arguments -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardOutput (Join-Path $runtime 'server.out.log') -RedirectStandardError (Join-Path $runtime 'server.err.log') -PassThru
        $listener=$null
        for($attempt=0;$attempt -lt 30;$attempt++) {
            Start-Sleep -Milliseconds 500
            $listener=Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
            if($listener) { break }
            if($process.HasExited) { break }
        }
        if(!$listener) { throw 'Server did not start; see .runtime/server.err.log' }
        $owner=Get-CimInstance Win32_Process -Filter "ProcessId=$($listener.OwningProcess)"
        if(!$owner.CommandLine.Contains($server)) { throw 'Unexpected listener; no process was stopped' }
        @{pid=$listener.OwningProcess;port=$Port;urls=$urls;startedUtc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content (Join-Path $runtime 'server.json')
        Write-Output "Running in background as PID $($listener.OwningProcess)."
        $urls | Write-Output
    } else {
        $urls | Write-Output
        Write-Output 'Press Ctrl+C to stop. Keep this window open.'
        & $python $server --host 0.0.0.0 --port $Port
        if($LASTEXITCODE) { throw 'WSGI server failed' }
    }
} finally { Pop-Location }
