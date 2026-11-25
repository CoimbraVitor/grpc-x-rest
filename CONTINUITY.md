# Documentação Técnica e Decisões Metodológicas

Este documento registra o contexto, as decisões metodológicas e técnicas adotadas, a arquitetura do repositório e o resumo dos resultados da coleta experimental da disciplina de **Engenharia de Software Experimental**.

---

## 1. Contexto e Referências Base

- **Autor:** Vitor de Freitas Coimbra
- **Trabalho prévio:** `mapeamento-sistematico.pdf` — *Desempenho de gRPC e REST em Função do Tamanho do Payload: um mapeamento sistemático da literatura* (10 estudos primários, A01–A10).
  - Lacunas identificadas no mapeamento: divergência sobre inversão de vantagem conforme o tamanho do payload, ausência de controle da versão do HTTP e escassez de testes estatísticos formais (apenas 1 de 10 estudos, Soares e Terra, 2024, aplicou testes de hipótese).
- **Referência estatística:** `metodos-estatisticos.pdf` — Sirqueira *et al.* (2015), *Aplicação de Métodos Estatísticos em Engenharia de Software: teoria e prática* (árvore de decisão da Figura 2 e procedimentos no Minitab).
- **Objetivo:** executar um experimento controlado em Go comparando REST e gRPC, conduzir a análise estatística no **Minitab** seguindo a árvore de decisão de Sirqueira *et al.* e documentar os resultados em relatório LaTeX padrão ABNT (`relatorio/main.tex`).

---

## 2. Decisões Metodológicas e Técnicas

### 2.1 Desenho Experimental
- **Arquiteturas (Fator 1 — 2 tratamentos):** `REST` (HTTP/1.1 + JSON) vs. `gRPC` (HTTP/2 + Protocol Buffers). A inclusão de REST sobre HTTP/2 é registrada em *Ameaças à Validade* e *Trabalhos Futuros*.
- **Tamanhos de Payload (Fator 2 — 4 tratamentos):** `1 KB`, `100 KB`, `1 MB` e `4 MB`.
- **Volume Amostral:** `100` requisições de aquecimento (*warm-up*, descartadas) + **`1.000` medições válidas** por combinação = **`8.000` observações totais** ($2 \times 4 \times 1.000$).
- **Payload Estruturado Determinístico:** definido em `internal/dataset/dataset.go` como coleção de structs `Item` (8 campos tipados: `int64`, 4 `string`, `float64`, `int32`, `bool`), calibrada para ~1 KB (4 itens), ~100 KB (378 itens), ~1 MB (3.845 itens) e ~4 MB (15.348 itens) em JSON, com conteúdo lógico idêntico entre REST e gRPC.
- **Controle de Protocolo:**
  - Conexão TCP persistente em *loopback* local (`127.0.0.1`), sem TLS e sem compressão gzip automática.
  - REST configurado explicitamente para HTTP/1.1 (`ForceAttemptHTTP2: false`, `keep-alive` ativo).
  - gRPC sobre HTTP/2 nativo com `MaxRecvMsgSize` / `MaxSendMsgSize` elevados para **32 MB**.
  - `runtime.GC()` executado antes de cada cenário.

### 2.2 Instrumentação de Tempo (`internal/clock/`)
- **`clock_other.go` (macOS/Linux):** utiliza `time.Now()` / `time.Since()` sobre `mach_absolute_time` (macOS), com resolução monotônica de nanossegundos.
- **`clock_windows.go` (Windows):** utiliza `QueryPerformanceCounter` / `QueryPerformanceFrequency` (`kernel32.dll`), obtendo precisão de ~0,1 µs para evitar quantização em requisições sub-milissegundo.

### 2.3 Estratégia Estatística (Árvore de Decisão de Sirqueira *et al.*)
- **Normalidade:** como $N = 1.000 > 30$ por grupo, aplica-se o **Teste de Kolmogorov-Smirnov (K-S)**. A normalidade foi rejeitada em todos os 8 grupos ($p < 0{,}010$), direcionando a inferência para testes não paramétricos.
- **Outliers:** identificados via teste de Grubbs e critério IQR, mantidos na amostra por representarem *tail latency* legítima (GC e escalonamento do SO), com robustez assegurada por medianas e testes não paramétricos.
- **Testes Inferenciais:**
  1. **Análise 1 — Teste de Mann-Whitney (1 fator, 2 tratamentos):** compara `REST` vs. `gRPC` em cada faixa de payload (`1 KB`, `100 KB`, `1 MB`, `4 MB`).
  2. **Análise 2 — Teste de Kruskal-Wallis + Mann-Whitney par-a-par (1 fator, 4 tratamentos):** avalia o efeito do tamanho do payload dentro de `REST` e dentro de `gRPC`.

### 2.4 Relatório LaTeX (`relatorio/`)
- Modelo ABNT leve baseado em `abntex2cite` + `bibtex` (compatível com Overleaf gratuito).
- Fluxograma vetorial em TikZ (Figura 1) reproduzindo a árvore de decisão de Sirqueira *et al.* com destaque dos caminhos seguidos.
- Macro `\minitabimg` para inclusão das capturas do Minitab em `relatorio/images/` sem quebra de compilação caso alguma imagem ainda não esteja presente.

---

## 3. Mapa de Arquivos do Repositório

| Caminho | Função |
| :--- | :--- |
| `proto/benchmark.proto` | Contrato Protocol Buffers / gRPC |
| `proto/benchmarkpb/*.pb.go` | Código Go gerado via `protoc 36.2` |
| `internal/dataset/dataset.go` | Gerador determinístico de payloads estruturados (`1KB`, `100KB`, `1MB`, `4MB`) |
| `internal/clock/clock_other.go` | Temporizador monotônico nativo (`mach_absolute_time`) para macOS/Linux |
| `internal/clock/clock_windows.go` | Temporizador QPC (~0,1 µs) para Windows |
| `cmd/rest_bench/main.go` | Benchmark REST (HTTP/1.1 + JSON) -> `results/raw_rest.csv` |
| `cmd/grpc_bench/main.go` | Benchmark gRPC (HTTP/2 + Protobuf) -> `results/raw_grpc.csv` |
| `run_benchmark.sh` / `run_benchmark.ps1` | Orquestradores completos para macOS/Linux e Windows |
| `scripts/analyze_and_export.py` | Consolida CSVs, gera Excel para Minitab, valida estatísticas e exporta tabelas LaTeX |
| `results/dados_experimento_minitab.xlsx` | Planilha estruturada para o Minitab (9 abas) |
| `results/dados_empilhados.csv` | Dataset completo empilhado (8.000 linhas) |
| `results/dados_por_grupo.csv` | Dataset por coluna/grupo (1.000 linhas × 8 colunas) |
| `results/ambiente_execucao.txt` | Especificações de hardware/software capturadas na coleta |
| `results/analise_estatistica_validacao.json` | Resultados estatísticos numéricos de referência |
| `results/resumo_tabelas_latex.txt` | Linhas de tabelas LaTeX formatadas no padrão ABNT |
| `GUIA_COLETA_MACBOOK.md` | Protocolo de isolamento e reprodução da coleta em macOS |
| `GUIA_MINITAB.md` | Procedimento detalhado de reprodução da análise estatística no Minitab |
| `relatorio/main.tex` | Código-fonte LaTeX ABNT do relatório |
| `relatorio/referencias.bib` | Referências BibTeX (`abntex2cite`, NBR 10520:2023) |
| `README.md` | Visão geral e instruções rápidas de execução |

---

## 4. Resumo da Coleta Experimental (Apple M3 / macOS 15.6.1)

Ambiente registrado em `results/ambiente_execucao.txt`: **Apple M3 (8 núcleos físicos / 8 threads)**, **16,00 GB RAM**, **macOS 15.6.1 (Build 24G90)**, **Go 1.27.4 (`darwin/arm64`)**.

- **Redução de bytes (Protobuf vs. JSON):** 29,08% a 30,11% em todos os payloads.
- **Normalidade (K-S):** rejeitada em todos os 8 grupos ($p < 0{,}010$).
- **Homocedasticidade (Levene):** rejeitada em `1 KB` ($p = 0{,}0433$), `100 KB` ($p < 0{,}001$) e `1 MB` ($p < 0{,}001$); não rejeitada em `4 MB` ($p = 0{,}2690$).
- **Análise 1 (Mann-Whitney — REST vs. gRPC):**
  - `1 KB`: REST `0,0405 ms` vs. gRPC `0,0403 ms` -> **gRPC 0,62% menor** ($p = 0{,}0115$; empate técnico em magnitude prática)
  - `100 KB`: REST `0,4971 ms` vs. gRPC `0,1958 ms` -> **gRPC 60,60% menor** ($p < 0{,}0001$)
  - `1 MB`: REST `4,6778 ms` vs. gRPC `1,7422 ms` -> **gRPC 62,76% menor** ($p < 0{,}0001$)
  - `4 MB`: REST `18,7834 ms` vs. gRPC `6,9928 ms` -> **gRPC 62,77% menor** ($p < 0{,}0001$)
- **Análise 2 (Kruskal-Wallis — Efeito do Payload):**
  - `REST`: $H = 3.748{,}29$, $DF = 3$, $p < 0{,}0001$ (6/6 pares significativos; crescimento de 463,8× de 1 KB para 4 MB).
  - `gRPC`: $H = 3.749{,}06$, $DF = 3$, $p < 0{,}0001$ (6/6 pares significativos; crescimento de 173,7× de 1 KB para 4 MB).

---

## 5. Status das Etapas do Projeto

- [x] Implementação dos benchmarks em Go e coleta controlada (8.000 observações em Apple M3 / macOS 15.6.1).
- [x] Consolidação dos dados para o Minitab e validação estatística (`results/`).
- [x] Atualização do relatório LaTeX (`relatorio/main.tex`) e da documentação pública com os resultados definitivos.
- [ ] Geração das capturas de gráficos e tabelas no Minitab (`relatorio/images/*.png`) conforme `GUIA_MINITAB.md`.
- [ ] Compilação final do relatório em PDF no Overleaf com as figuras do Minitab inseridas.
