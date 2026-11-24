param(
    [int]$Warmup = 100,
    [int]$Iterations = 1000
)

$ErrorActionPreference = "Stop"

# Ensure Go and protoc are in PATH
$env:PATH = "C:\Program Files\Go\bin;$env:USERPROFILE\go\bin;" + $env:PATH

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Experimento REST (HTTP/1.1) vs gRPC (HTTP/2) em Go" -ForegroundColor Cyan
Write-Host " Warm-up: $Warmup | Medicoes por cenario: $Iterations" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# Record hardware & environment specs for replicability (Criterion C1)
New-Item -ItemType Directory -Force -Path "results" | Out-Null
$cpu = (Get-CimInstance Win32_Processor | Select-Object -First 1).Name
$cores = (Get-CimInstance Win32_Processor | Select-Object -First 1).NumberOfCores
$logical = (Get-CimInstance Win32_Processor | Select-Object -First 1).NumberOfLogicalProcessors
$ramGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 2)
$os = (Get-CimInstance Win32_OperatingSystem).Caption
$osVer = (Get-CimInstance Win32_OperatingSystem).Version
$goVer = (go version)

$envInfo = @"
Data da coleta: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Sistema Operacional: $os ($osVer)
Processador: $cpu ($cores nucleos fisicos / $logical threads)
Memoria RAM: $ramGB GB
Versao do Go: $goVer
Parametros: warmup=$Warmup, iterations=$Iterations
Protocolos: REST (HTTP/1.1, JSON, keep-alive, sem TLS) vs gRPC (HTTP/2, Protobuf, conexao persistente, sem TLS)
Rede: Loopback TCP local (127.0.0.1)
"@
$envInfo | Out-File -FilePath "results\ambiente_execucao.txt" -Encoding utf8
Write-Host $envInfo

Write-Host "`n[1/3] Executando benchmark REST (HTTP/1.1)..." -ForegroundColor Yellow
go run ./cmd/rest_bench -warmup $Warmup -n $Iterations

Write-Host "`n[2/3] Executando benchmark gRPC (HTTP/2)..." -ForegroundColor Yellow
go run ./cmd/grpc_bench -warmup $Warmup -n $Iterations

Write-Host "`n[3/3] Consolidando dados para o Minitab e validando estatisticas..." -ForegroundColor Yellow
python ./scripts/analyze_and_export.py

Write-Host "`nConcluido! Abra 'results\dados_experimento_minitab.xlsx' no Minitab." -ForegroundColor Green
