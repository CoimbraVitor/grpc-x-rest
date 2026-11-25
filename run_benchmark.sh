#!/usr/bin/env bash
set -euo pipefail

WARMUP="${1:-100}"
ITERATIONS="${2:-1000}"

echo "============================================================"
echo " Experimento REST (HTTP/1.1) vs gRPC (HTTP/2) em Go (macOS)"
echo " Warm-up: ${WARMUP} | Medicoes por cenario: ${ITERATIONS}"
echo "============================================================"

mkdir -p results

OS_NAME="$(uname -s)"
if [[ "$OS_NAME" == "Darwin" ]]; then
  OS_INFO="macOS $(sw_vers -productVersion) (Build $(sw_vers -buildVersion))"
  CPU_INFO="$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo 'Apple Silicon')"
  CORES_PHYS="$(sysctl -n hw.physicalcpu 2>/dev/null || echo '?')"
  CORES_LOG="$(sysctl -n hw.logicalcpu 2>/dev/null || echo '?')"
  RAM_BYTES="$(sysctl -n hw.memsize 2>/dev/null || echo 0)"
  RAM_GB="$(awk -v b="$RAM_BYTES" 'BEGIN { printf "%.2f", b / 1073741824 }')"
else
  OS_INFO="$(uname -sr)"
  CPU_INFO="$(lscpu 2>/dev/null | awk -F: '/Model name/{gsub(/^ +/,"",$2); print $2; exit}' || echo 'N/A')"
  CORES_PHYS="$(nproc 2>/dev/null || echo '?')"
  CORES_LOG="$CORES_PHYS"
  RAM_GB="$(free -b 2>/dev/null | awk '/Mem:/{printf "%.2f", $2/1073741824}' || echo 'N/A')"
fi

GO_VER="$(go version)"
DATE_NOW="$(date '+%Y-%m-%d %H:%M:%S')"

cat <<EOF > results/ambiente_execucao.txt
Data da coleta: ${DATE_NOW}
Sistema Operacional: ${OS_INFO}
Processador: ${CPU_INFO} (${CORES_PHYS} nucleos fisicos / ${CORES_LOG} threads)
Memoria RAM: ${RAM_GB} GB
Versao do Go: ${GO_VER}
Parametros: warmup=${WARMUP}, iterations=${ITERATIONS}
Protocolos: REST (HTTP/1.1, JSON, keep-alive, sem TLS) vs gRPC (HTTP/2, Protobuf, conexao persistente, sem TLS)
Rede: Loopback TCP local (127.0.0.1)
EOF

cat results/ambiente_execucao.txt

echo ""
echo "[1/3] Executando benchmark REST (HTTP/1.1)..."
go run ./cmd/rest_bench -warmup "${WARMUP}" -n "${ITERATIONS}"

# Pausa breve de resfriamento/estabilizacao entre os protocolos
sleep 3

echo ""
echo "[2/3] Executando benchmark gRPC (HTTP/2)..."
go run ./cmd/grpc_bench -warmup "${WARMUP}" -n "${ITERATIONS}"

echo ""
echo "[3/3] Consolidando dados para o Minitab e gerando resumo estatistico..."
if command -v python3 >/dev/null 2>&1; then
  python3 ./scripts/analyze_and_export.py
else
  python ./scripts/analyze_and_export.py
fi

echo ""
echo "Concluido!"
echo "  - Planilha Minitab: results/dados_experimento_minitab.xlsx"
echo "  - Tabelas LaTeX atualizadas: results/resumo_tabelas_latex.txt"
