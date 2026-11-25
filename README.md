# Experimento Estatístico: gRPC (HTTP/2) vs. REST (HTTP/1.1) em Go

Repositório do experimento empírico e da análise estatística conduzida para a disciplina de **Engenharia de Software Experimental**, em continuidade ao Mapeamento Sistemático da Literatura (`mapeamento-sistematico.pdf`) e seguindo a árvore de decisão estatística de Sirqueira et al. (`metodos-estatisticos.pdf`).

## Estrutura do Projeto

- `proto/benchmark.proto` — Contrato Protocol Buffers / gRPC.
- `proto/benchmarkpb/` — Código Go gerado pelo `protoc` (`36.2`).
- `internal/dataset/dataset.go` — Gerador determinístico de payloads estruturados (`1KB`, `100KB`, `1MB`, `4MB`) compartilhado entre REST e gRPC.
- `internal/clock/` — Temporizador monotônico de alta resolução (`mach_absolute_time` no macOS/Linux; `QueryPerformanceCounter` no Windows) para evitar quantização do relógio em requisições sub-milissegundo.
- `cmd/rest_bench/main.go` — Script Go do benchmark **REST (HTTP/1.1 + JSON, keep-alive, sem TLS)**.
- `cmd/grpc_bench/main.go` — Script Go do benchmark **gRPC (HTTP/2 + Protocol Buffers, conexão persistente, sem TLS)**.
- `run_benchmark.sh` / `run_benchmark.ps1` — Executam os dois benchmarks em sequência (macOS/Linux ou Windows), registram as especificações de hardware e chamam a consolidação/validação.
- `scripts/analyze_and_export.py` — Consolida os CSVs brutos em `results/dados_experimento_minitab.xlsx`, valida todos os testes estatísticos e gera `results/resumo_tabelas_latex.txt`.
- `results/` — Dados brutos (`raw_rest.csv`, `raw_grpc.csv`), consolidados (`dados_empilhados.csv`, `dados_por_grupo.csv`, `dados_experimento_minitab.xlsx`), especificações da máquina (`ambiente_execucao.txt`), validação (`analise_estatistica_validacao.json`) e tabelas LaTeX (`resumo_tabelas_latex.txt`).
- `GUIA_COLETA_MACBOOK.md` — Protocolo de isolamento do ambiente e reprodução da coleta em macOS.
- `GUIA_MINITAB.md` — Procedimento completo de reprodução da análise estatística no Minitab.
- `CONTINUITY.md` — Documentação técnica das decisões metodológicas e arquitetura do experimento.
- `relatorio/` — Projeto LaTeX padrão ABNT (`abntex2cite` + `bibtex`: `main.tex` e `referencias.bib`).

## Como Executar Novamente

### macOS / Linux

```bash
# 1. Criar ambiente virtual Python e instalar dependências de análise (apenas uma vez):
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install scipy numpy pandas openpyxl

# 2. Baixar dependências Go e executar o experimento completo (warm-up 100, N=1000 por payload):
go mod download
chmod +x run_benchmark.sh
./run_benchmark.sh 100 1000
```

### Windows (PowerShell)

```powershell
# Rodar tudo de uma vez (warm-up 100, N=1000 por payload):
powershell -ExecutionPolicy Bypass -File .\run_benchmark.ps1 -Warmup 100 -Iterations 1000
```

## Resumo dos Resultados Coletados (8.000 observações — Apple M3 / macOS 15.6.1)

Ambiente: **Apple M3 (8 núcleos)**, **16 GB RAM**, **macOS 15.6.1 (Build 24G90)**, **Go 1.27.4 (`darwin/arm64`)**, *loopback* TCP (`127.0.0.1`), sem TLS.

| Payload | REST Mediana (ms) | gRPC Mediana (ms) | Redução Protobuf (bytes) | Mann-Whitney $p$ | Menor Latência |
| :--- | ---: | ---: | ---: | ---: | :--- |
| **1 KB** | 0,0405 | 0,0403 | 30,11% | 0,011455 | **gRPC** (+0,62%) |
| **100 KB** | 0,4971 | 0,1958 | 29,08% | < 0,0001 | **gRPC** (+60,60%) |
| **1 MB** | 4,6778 | 1,7422 | 29,35% | < 0,0001 | **gRPC** (+62,76%) |
| **4 MB** | 18,7834 | 6,9928 | 29,49% | < 0,0001 | **gRPC** (+62,77%) |

- **Normalidade (Kolmogorov-Smirnov, $N = 1.000 > 30$):** Rejeitada em todos os 8 grupos ($p < 0{,}010$) $\rightarrow$ testes não paramétricos.
- **Efeito do Payload (Kruskal-Wallis):** $H = 3.748{,}29$ no REST e $H = 3.749{,}06$ no gRPC ($p < 0{,}0001$; todos os 6 pares significativos no pós-teste de Mann-Whitney).
