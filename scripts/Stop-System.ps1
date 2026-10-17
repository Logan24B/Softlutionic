$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$metadata=Join-Path $root '.runtime\server.json'
if(!(Test-Path $metadata)) { throw 'No background server metadata found' }
$server=Get-Content $metadata -Raw | ConvertFrom-Json
$process=Get-CimInstance Win32_Process -Filter "ProcessId=$([int]$server.pid)"
if(!$process) { Write-Output 'Server is already stopped.'; return }
$expected=Join-Path $PSScriptRoot 'serve_local.py'
if(!$process.CommandLine -or !$process.CommandLine.Contains($expected)) { throw 'PID belongs to another process; no process was stopped' }
Stop-Process -Id ([int]$server.pid) -ErrorAction Stop
Write-Output 'Softlutionic server stopped. SQL Server remains running.'
