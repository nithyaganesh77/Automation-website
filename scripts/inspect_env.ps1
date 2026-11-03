Write-Host "=== ENVIRONMENT INSPECTION ===" -ForegroundColor Cyan

$os = Get-CimInstance Win32_OperatingSystem
Write-Host "OS: $($os.Caption) $($os.OSArchitecture) (Build $($os.BuildNumber))"

Write-Host "Python Installations:"
py --list

Write-Host "Active Virtualenv Python:"
& "backend\.venv\Scripts\python.exe" --version

Write-Host "Node.js:"
node --version

Write-Host "npm:"
npm --version

Write-Host "Git:"
git --version

Write-Host "Docker CLI:"
docker --version

Write-Host "Docker Compose:"
docker compose version

# Check Docker daemon
try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker Daemon: RUNNING" -ForegroundColor Green
    } else {
        Write-Host "Docker Daemon: NOT RUNNING (Docker Desktop needs to be started if container mode is desired)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Docker Daemon: Error checking" -ForegroundColor Red
}

# Disk space
Write-Host "`nDisk Space:"
Get-PSDrive -PSProvider FileSystem | Select-Object Name, @{Name="FreeGB";Expression={[math]::Round($_.Free/1GB,2)}}, @{Name="UsedGB";Expression={[math]::Round($_.Used/1GB,2)}} | Format-Table -AutoSize

# Ports check
Write-Host "Port Availability Check:"
$ports = @(3000, 3001, 8000, 5432, 6379, 6333, 9000, 9001, 9090)
foreach ($p in $ports) {
    $conn = Get-NetTCPConnection -LocalPort $p -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Host "Port $p : IN USE (PID: $(($conn.OwningProcess -join ', ')))" -ForegroundColor Yellow
    } else {
        Write-Host "Port $p : FREE" -ForegroundColor Green
    }
}

