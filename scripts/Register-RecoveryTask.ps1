param([switch]$EnableWithPassword)
$ErrorActionPreference='Stop'
throw 'Azure scheduling is disabled while the application uses its local primary database.'
if((Get-TimeZone).Id -ne 'Central America Standard Time') { throw 'Expected Guatemala UTC-6 timezone' }
$name='Softlutionic-AzureToLocal-Daily'
$existing=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
if($existing -and (!$EnableWithPassword -or $existing.State -ne 'Disabled')) { throw 'Task exists; only a disabled task can be activated explicitly' }
$script=Join-Path $PSScriptRoot 'Copy-AzureToLocal.ps1'
$action=New-ScheduledTaskAction -Execute "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -Argument "-NoProfile -NonInteractive -File `"$script`" -AuthorizeAzureCopyCost -ConfirmReplaceBDsofactur" -WorkingDirectory (Split-Path $PSScriptRoot -Parent)
$trigger=New-ScheduledTaskTrigger -Daily -At '00:00'
$settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 6) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$user=[Security.Principal.WindowsIdentity]::GetCurrent().Name
if($EnableWithPassword) {
    if(!(Test-Path "$PSScriptRoot\..\.private\azure.json")) { throw 'Configure Azure secret first' }
    & "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -NonInteractive -File "$PSScriptRoot\Copy-AzureToLocal.ps1" -CheckOnly
    if($LASTEXITCODE -ne 0) { throw 'Connection preflight failed' }
    $result=Get-Content "$PSScriptRoot\..\.recovery\last-result.json" -Raw | ConvertFrom-Json
    if($result.stage -ne 'success' -or $result.failed -or $result.cleanupFailed) { throw 'A successful manual copy and Azure cleanup are required first' }
    $cred=Get-Credential -UserName $user -Message 'Windows execution account (not Azure SQL)'
    if($existing) {
        Set-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -User $user -Password $cred.GetNetworkCredential().Password | Out-Null
        Enable-ScheduledTask -TaskName $name | Out-Null
    } else {
        Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -User $user -Password $cred.GetNetworkCredential().Password | Out-Null
    }
} else {
    $settings.Enabled=$false
    $principal=New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
    Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Settings $settings -Principal $principal | Out-Null
}
Get-ScheduledTask -TaskName $name | Select-Object TaskName,State,@{n='Identity';e={$_.Principal.UserId}},@{n='LogonType';e={$_.Principal.LogonType}}
