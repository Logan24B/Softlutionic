param(
    [switch]$AuthorizeAzureCopyCost,
    [switch]$ConfirmReplaceBDsofactur,
    [switch]$CheckOnly,
    [string]$SqlPackageDirectory = 'C:\Program Files\Microsoft SQL Server\170\DAC\bin'
)
$ErrorActionPreference = 'Stop'
throw 'Azure copying is disabled: BDsofactur is now the primary writable database. Reconfigure and review the complete recovery process before using Azure again.'
$root = Split-Path $PSScriptRoot -Parent
$work = Join-Path $root '.recovery'
New-Item $work -ItemType Directory -Force | Out-Null
$identity = [Security.Principal.WindowsIdentity]::GetCurrent().Name
& icacls.exe $work /inheritance:r /grant:r "${identity}:(OI)(CI)F" 'SYSTEM:(OI)(CI)F' | Out-Null
if ($LASTEXITCODE) { throw 'Cannot protect recovery directory' }
$lock = $null
$stage = 'lock'
$azureCopy = $null
$renamed = $false
$stamp = [DateTime]::UtcNow.ToString('yyyyMMddHHmmss') + '_' + ([guid]::NewGuid().ToString('N').Substring(0,8))
$candidate = "BDsofactur_candidate_$stamp"
$previous = "BDsofactur_previous_$stamp"
$bacpac = Join-Path $work "$stamp.bacpac"
$connections = @()
function Connect-Database($server, $database, $azure) {
    $b = New-Object System.Data.SqlClient.SqlConnectionStringBuilder
    $b['Data Source']=$server; $b['Initial Catalog']=$database; $b['Connect Timeout']=30
    $b['Encrypt']=$true; $b['TrustServerCertificate']=(!$azure); $b['Persist Security Info']=$true
    if ($azure) { $b['User ID']='softadmin'; $b['Password']=$script:secret.password }
    else { $b['Integrated Security']=$true }
    $c = New-Object System.Data.SqlClient.SqlConnection $b.ConnectionString
    $c.Open()
    return $c
}
function Query($c, $sql) {
    $cmd=$c.CreateCommand(); $cmd.CommandText=$sql; $cmd.CommandTimeout=7200
    $table=New-Object System.Data.DataTable
    $reader=$cmd.ExecuteReader()
    try { $table.Load($reader) } finally { $reader.Dispose(); $cmd.Dispose() }
    return ,$table
}
function Manifest($c) {
    $tables=Query $c "SELECT s.name AS sn,t.name AS tn FROM sys.tables t JOIN sys.schemas s ON s.schema_id=t.schema_id WHERE t.is_ms_shipped=0 ORDER BY s.name,t.name"
    $result=@{}
    foreach($t in $tables.Rows) {
        $sn=$t.sn.Replace(']',']]'); $tn=$t.tn.Replace(']',']]')
        $r=Query $c "SELECT COUNT_BIG(*) AS n FROM [$sn].[$tn]"
        $result["$($t.sn).$($t.tn)"]=[long]$r.Rows[0].n
    }
    return $result
}
try {
    $lock=[IO.File]::Open((Join-Path $work 'copy.lock'),'OpenOrCreate','ReadWrite','None')
    if(Test-Path (Join-Path $root '.private\recovery-active')) { throw 'Controlled local recovery is active' }
    $stage='credentials'
    $secret=Get-Content (Join-Path $root '.private\azure.json') -Raw | ConvertFrom-Json
    $stage='connections'
    $local=Connect-Database 'localhost\SQLEXPRESS' 'master' $false; $connections+= $local
    $source=Connect-Database 'tcp:sql-softlutionic2.database.windows.net,1433' 'softlutionic-sistema-db' $true; $connections+= $source
    $info=Query $local "SELECT CONVERT(int,SERVERPROPERTY('ProductMajorVersion')) AS major,CONVERT(nvarchar(128),SERVERPROPERTY('Edition')) AS edition"
    if ($info.Rows[0].edition -notlike '*Express*') { throw 'Expected Express' }
    $limit=10GB; if([int]$info.Rows[0].major -ge 17) { $limit=50GB }
    $size=Query $source 'SELECT SUM(CONVERT(bigint,size))*8192 AS bytes FROM sys.database_files WHERE type=0'
    $bytes=[long]$size.Rows[0].bytes
    if($bytes -gt $limit * 0.85) { throw 'Express capacity safety margin exceeded' }
    $paths=Query $local "SELECT CONVERT(nvarchar(4000),SERVERPROPERTY('InstanceDefaultDataPath')) AS p UNION SELECT CONVERT(nvarchar(4000),SERVERPROPERTY('InstanceDefaultLogPath'))"
    foreach($path in @($work)+@($paths.Rows | ForEach-Object {$_.p})) {
        $drive=New-Object IO.DriveInfo ([IO.Path]::GetPathRoot($path))
        if($drive.AvailableFreeSpace -lt ([Math]::Max(5GB,$bytes*5))) { throw 'Insufficient disk space' }
    }
    if($CheckOnly) { $stage='connection-and-capacity-check-passed'; return }
    if(!$AuthorizeAzureCopyCost -or !$ConfirmReplaceBDsofactur) { throw 'Explicit cost and destination authorization required' }
    $stage='load-dacfx'
    Add-Type -Path (Join-Path $SqlPackageDirectory 'Microsoft.SqlServer.Dac.dll')
    # Verify the local destination exists before making a billable Azure resource.
    $destination=Query $local "SELECT name FROM sys.databases WHERE name=N'BDsofactur' AND state_desc='ONLINE'"
    if(!$destination.Rows.Count) { throw 'Expected BDsofactur destination not online' }
    $stage='create-consistent-copy'
    $master=Connect-Database 'tcp:sql-softlutionic2.database.windows.net,1433' 'master' $true; $connections+=$master
    $azureCopy="softlutionic_recovery_$stamp"
    Query $master "CREATE DATABASE [$azureCopy] AS COPY OF [softlutionic-sistema-db]" | Out-Null
    $deadline=[DateTime]::UtcNow.AddHours(2)
    do {
        $state=Query $master "SELECT state_desc FROM sys.databases WHERE name=N'$azureCopy'"
        if($state.Rows.Count -and $state.Rows[0].state_desc -eq 'ONLINE') { break }
        if([DateTime]::UtcNow -gt $deadline) { throw 'Azure copy timeout' }
        Start-Sleep -Seconds 10
    } while($true)
    $copy=Connect-Database 'tcp:sql-softlutionic2.database.windows.net,1433' $azureCopy $true; $connections+=$copy
    $expected=Manifest $copy
    $stage='export'
    $exporter=New-Object Microsoft.SqlServer.Dac.DacServices $copy.ConnectionString
    $exporter.ExportBacpac($bacpac,$azureCopy,$null,$null)
    $stage='import-candidate'
    $importer=New-Object Microsoft.SqlServer.Dac.DacServices $local.ConnectionString
    $package=[Microsoft.SqlServer.Dac.BacPackage]::Load($bacpac)
    try { $importer.ImportBacpac($package,$candidate,[Nullable[Threading.CancellationToken]]$null) } finally { $package.Dispose() }
    $stage='validate-candidate'
    $validation=Connect-Database 'localhost\SQLEXPRESS' $candidate $false
    try {
        $actual=Manifest $validation
        if($actual.Count -ne $expected.Count) { throw 'Table mismatch' }
        foreach($key in $expected.Keys) { if(!$actual.ContainsKey($key) -or $expected[$key] -ne $actual[$key]) { throw 'Row count mismatch' } }
        $check=Query $validation 'DBCC CHECKDB WITH NO_INFOMSGS, ALL_ERRORMSGS'
        if($check.Rows.Count) { throw 'CHECKDB errors' }
        $check=Query $validation 'DBCC CHECKCONSTRAINTS WITH ALL_CONSTRAINTS'
        if($check.Rows.Count) { throw 'Constraint errors' }
    } finally { $validation.Dispose() }
    $stage='promote'
    # Refuse active consumers; never terminate a recovery session or erase a database.
    $active=Query $local "SELECT COUNT(*) AS n FROM sys.dm_exec_sessions WHERE database_id=DB_ID(N'BDsofactur')"
    if([int]$active.Rows[0].n -gt 0) { throw 'Local recovery database has active sessions' }
    Query $local "IF DB_ID(N'BDsofactur') IS NOT NULL BEGIN ALTER DATABASE [BDsofactur] MODIFY NAME=[$previous]; END" | Out-Null
    $renamed=$true
    try { Query $local "ALTER DATABASE [$candidate] MODIFY NAME=[BDsofactur]" | Out-Null }
    catch {
        Query $local "IF DB_ID(N'BDsofactur') IS NULL AND DB_ID(N'$previous') IS NOT NULL ALTER DATABASE [$previous] MODIFY NAME=[BDsofactur]" | Out-Null
        throw
    }
    $stage='success'
    # Keep seven days of completed exports. Never delete SQL databases automatically.
    Get-ChildItem $work -Filter '*.bacpac' | Where-Object {$_.LastWriteTimeUtc -lt [DateTime]::UtcNow.AddDays(-7) -and $_.FullName -ne $bacpac} | Remove-Item
} catch {
    # Do not serialize provider exceptions: they can contain connection strings.
    $sqlErrorNumbers=@()
    $failureType=$_.Exception.GetType().FullName
    $errorDetail=$_.Exception
    while($errorDetail) {
        if($errorDetail -is [Data.SqlClient.SqlException]) {
            $sqlErrorNumbers=@($errorDetail.Errors | ForEach-Object { $_.Number })
        }
        $errorDetail=$errorDetail.InnerException
    }
    Write-Error "Recovery copy failed at stage '$stage'; previous databases retained." -ErrorAction Continue
    $failed=$true
} finally {
    foreach($c in $connections) { $c.Dispose() }
    if($azureCopy) {
        try {
            $cleanup=Connect-Database 'tcp:sql-softlutionic2.database.windows.net,1433' 'master' $true
            try { Query $cleanup "IF DB_ID(N'$azureCopy') IS NOT NULL DROP DATABASE [$azureCopy]" | Out-Null } finally { $cleanup.Dispose() }
        } catch { $cleanupFailed=$true }
    }
    if($lock) {
        $result=@{utc=[DateTime]::UtcNow.ToString('o'); stage=$stage; failed=[bool]$failed; cleanupFailed=[bool]$cleanupFailed; azureCopy=$azureCopy; candidate=$candidate; previous=$previous; identity=$identity; failureType=$failureType; sqlErrorNumbers=@($sqlErrorNumbers)}
        $filename='last-result.json'; if($CheckOnly) { $filename='last-check.json' }
        $result | ConvertTo-Json | Set-Content (Join-Path $work $filename)
        $result | ConvertTo-Json -Compress | Add-Content (Join-Path $work 'history.jsonl')
        $lock.Dispose()
    }
}
if($failed -or $cleanupFailed) { exit 1 }
