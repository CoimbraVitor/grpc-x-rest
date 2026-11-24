# Experimento Estatístico: gRPC (HTTP/2) vs. REST (HTTP/1.1) em Go

Repositório do experimento empírico e da análise estatística conduzida para a disciplina de **Engenharia de Software Experimental**, em continuidade ao Mapeamento Sistemático da Literatura (`mapeamento-sistematico.pdf`) e seguindo a árvore de decisão estatística de Sirqueira et al. (`metodos-estatisticos.pdf`).

## Estrutura do Projeto

- `proto/benchmark.proto` — Contrato Protocol Buffers / gRPC.
- `proto/benchmarkpb/` — Código Go gerado pelo `protoc` (`36.2`).
- `internal/dataset/dataset.go` — Gerador determinístico de payloads estruturados (`1KB`, `100KB`, `1MB`, `4MB`) compartilhado entre REST e gRPC.
- `internal/clock/` — Temporizador monotônico de alta resolução (`QueryPerformanceCounter` no Windows, precisão de ~0,1 µs) para evitar quantização do relógio padrão em requisições rápidas.
- `cmd/rest_bench/main.go` — Script Go do benchmark **REST (HTTP/1.1 + JSON, keep-alive, sem TLS)**.
- `cmd/grpc_bench/main.go` — Script Go do benchmark **gRPC (HTTP/2 + Protocol Buffers, conexão persistente, sem TLS)**.
- `run_benchmark.ps1` / `run_benchmark.sh` — Executam os dois benchmarks em sequência (Windows ou macOS/Linux), registram as especificações de hardware e chamam a consolidação/validação.
- `scripts/analyze_and_export.py` — Consolida os CSVs brutos em `results/dados_experimento_minitab.xlsx` (pronto para abrir no Minitab), valida todos os testes estatísticos e gera `results/resumo_tabelas_latex.txt` pronto para atualizar o Overleaf.
- `results/` — Dados brutos (`raw_rest.csv`, `raw_grpc.csv`), consolidados (`dados_empilhados.csv`, `dados_por_grupo.csv`, `dados_experimento_minitab.xlsx`), especificações da máquina (`ambiente_execucao.txt`), validação (`analise_estatistica_validacao.json`) e tabelas LaTeX (`resumo_tabelas_latex.txt`).
- `GUIA_COLETA_MACBOOK.md` — Checklist de isolamento e passo a passo de coleta limpa no MacBook.
- `GUIA_MINITAB.md` — Passo a passo completo dos menus, prints e interpretações no Minitab.
- `relatorio/` — Projeto LaTeX padrão ABNT (`abntex2cite` + `bibtex`, leve para o Overleaf gratuito: `main.tex` e `referencias.bib`).

## Como Executar Novamente

```powershell
# Rodar os dois scripts separadamente (warm-up 100, N=1000 por payload):
go run ./cmd/rest_bench -warmup 100 -n 1000
go run ./cmd/grpc_bench -warmup 100 -n 1000
python ./scripts/analyze_and_export.py

# Ou rodar tudo de uma vez:
powershell -ExecutionPolicy Bypass -File .\run_benchmark.ps1 -Warmup 100 -Iterations 1000
```

## Resumo dos Resultados Coletados (8.000 observações)

| Payload | REST Mediana (ms) | gRPC Mediana (ms) | Redução Protobuf (bytes) | Mann-Whitney $p$ | Menor Latência |
| :--- | ---: | ---: | ---: | ---: | :--- |
| **1 KB** | 0,1078 | 0,1161 | 30,11% | 0,000035 | **REST** (-7,75%) |
| **100 KB** | 1,1473 | 0,5804 | 29,08% | < 0,0001 | **gRPC** (+49,41%) |
| **1 MB** | 11,9954 | 3,7769 | 29,35% | < 0,0001 | **gRPC** (+68,51%) |
| **4 MB** | 45,1097 | 14,7170 | 29,49% | < 0,0001 | **gRPC** (+67,38%) |

- **Normalidade (Kolmogorov-Smirnov, $N = 1.000 > 30$):** Rejeitada em todos os 8 grupos ($p < 0{,}010$) $\rightarrow$ testes não paramétricos.
- **Efeito do Payload (Kruskal-Wallis):** $H = 3744{,}85$ no REST e $H = 3699{,}40$ no gRPC ($p < 0{,}0001$; todos os 6 pares significativos no pós-teste de Mann-Whitney).
