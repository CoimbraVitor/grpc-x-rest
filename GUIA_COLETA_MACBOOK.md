# Protocolo de Coleta e Reprodutibilidade (macOS)

Este documento descreve o protocolo de isolamento do ambiente e os procedimentos utilizados para executar a coleta experimental em **macOS (Apple Silicon)**, visando preservar a **Validade Interna** do experimento por meio da redução de ruído de escalonamento de CPU, picos de *tail latency* e interferência de I/O.

> **Instrumentação de tempo no macOS:** o pacote `internal/clock/clock_other.go` utiliza o relógio monotônico nativo do Go no macOS (`mach_absolute_time`), oferecendo resolução na ordem de **nanossegundos** para medições sub-milissegundo.

---

## 1. Pré-requisitos

Verifique se o **Go** e o **Python 3** estão disponíveis no ambiente:

```bash
go version
python3 --version
```

Caso seja necessário instalar o Go via Homebrew:

```bash
brew install go
```

Crie um ambiente virtual Python (`.venv`) e instale as bibliotecas utilizadas pelo script de consolidação e validação estatística (`scripts/analyze_and_export.py`):

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install scipy numpy pandas openpyxl
```

*(Observação: não é necessário instalar `protoc`, pois o código Go gerado a partir do contrato `.proto` já está versionado em `proto/benchmarkpb/`.)*

---

## 2. Protocolo de Isolamento do Ambiente

Antes de iniciar a execução dos benchmarks, adotaram-se as seguintes condições de controle:

1. **Alimentação na tomada:** equipamento conectado à fonte de energia para evitar redução dinâmica de clock (*thermal/power throttling*).
2. **Modo Pouca Energia desativado:** configurado em *Ajustes do Sistema → Bateria*.
3. **Encerramento de aplicativos concorrentes:** navegadores, IDEs, clientes de mensageria, containers e reprodutores de mídia encerrados, mantendo apenas o Terminal ativo.
4. **Pausa de serviços de sincronização em segundo plano:** iCloud Drive, OneDrive, Google Drive, Dropbox e Time Machine pausados durante a coleta.
5. **Modo "Não Perturbe" ativo** (e, opcionalmente, Wi-Fi desativado após o download das dependências Go, visto que o experimento opera exclusivamente em *loopback* local `127.0.0.1`).
6. **Pré-carregamento de dependências Go:**
   ```bash
   go mod download
   ```
7. **Sem interação com a máquina** durante toda a execução dos benchmarks (~1 a 2 minutos).

---

## 3. Execução da Coleta

### Opção A — Script Automatizado (`run_benchmark.sh`)

Com o ambiente virtual `.venv` ativado (`source .venv/bin/activate`):

```bash
chmod +x run_benchmark.sh
./run_benchmark.sh 100 1000
```

O script executa sequencialmente:
1. Captura automática das especificações de hardware e software em `results/ambiente_execucao.txt`.
2. Benchmark **REST (HTTP/1.1 + JSON)** — `100` requisições de aquecimento (*warm-up*) + `1.000` medições válidas por payload (`1KB`, `100KB`, `1MB`, `4MB`), totalizando `4.000` observações em `results/raw_rest.csv`.
3. Pausa de 3 segundos para estabilização entre protocolos.
4. Benchmark **gRPC (HTTP/2 + Protocol Buffers)** — `100` requisições de aquecimento + `1.000` medições válidas por payload, totalizando `4.000` observações em `results/raw_grpc.csv`.
5. Consolidação e validação via `scripts/analyze_and_export.py`, gerando:
   - `results/dados_experimento_minitab.xlsx` — planilha estruturada para importação no Minitab;
   - `results/dados_empilhados.csv` e `results/dados_por_grupo.csv` — datasets consolidados em CSV;
   - `results/analise_estatistica_validacao.json` — resultados numéricos de referência de todos os testes estatísticos;
   - `results/resumo_tabelas_latex.txt` — tabelas formatadas em LaTeX (padrão decimal ABNT).

---

### Opção B — Execução Manual Etapa por Etapa

```bash
# 1. Registro das especificações do ambiente
sw_vers
sysctl -n machdep.cpu.brand_string
sysctl -n hw.physicalcpu hw.logicalcpu hw.memsize
go version

# 2. Benchmark REST (HTTP/1.1 + JSON) -> results/raw_rest.csv
go run ./cmd/rest_bench -warmup 100 -n 1000

# 3. Benchmark gRPC (HTTP/2 + Protocol Buffers) -> results/raw_grpc.csv
go run ./cmd/grpc_bench -warmup 100 -n 1000

# 4. Consolidação para o Minitab e geração do resumo estatístico
source .venv/bin/activate
python3 ./scripts/analyze_and_export.py
```

---

## 4. Próxima Etapa — Análise Estatística

Com os arquivos gerados em `results/`, a reprodução dos gráficos e testes de hipótese no Minitab está documentada em **[GUIA_MINITAB.md](GUIA_MINITAB.md)**.
