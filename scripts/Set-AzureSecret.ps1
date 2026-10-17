$ErrorActionPreference = 'Stop'
throw 'Azure configuration is postponed. The application currently uses only local SQL Server with Windows authentication.'
$root = Split-Path $PSScriptRoot -Parent
$dir = Join-Path $root '.private'
New-Item $dir -ItemType Directory -Force | Out-Null
$identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls.exe $dir /inheritance:r /grant:r "${identity}:(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
if ($LASTEXITCODE) { throw 'Cannot secure private directory' }
$secure = Read-Host 'Azure SQL password (hidden)' -AsSecureString
$ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
try {
    $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    @{password=$value} | ConvertTo-Json | Set-Content (Join-Path $dir 'azure.json') -Encoding UTF8
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    $value = $null
}
Write-Host 'Private configuration saved. Run the connection check next.'
