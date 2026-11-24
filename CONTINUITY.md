# CONTINUITY.md — Experimento Estatístico gRPC vs. REST

Este documento registra todo o contexto, as decisões metodológicas e técnicas tomadas, o estado atual do repositório e os próximos passos para continuidade do trabalho da disciplina de **Engenharia de Software Experimental** (em preparação para o TCC).

---

## 1. Contexto e Referências Base

- **Autor:** Vitor de Freitas Coimbra
- **Trabalho 1 (já concluído):** `mapeamento-sistematico.pdf` — *Desempenho de gRPC e REST em Função do Tamanho do Payload: um mapeamento sistemático da literatura* (10 estudos primários, A01–A10).
  - Principais lacunas identificadas no mapeamento: divergência sobre inversão de vantagem conforme o tamanho do payload, ausência de controle da versão do HTTP e escassez de testes estatísticos formais (apenas 1 de 10 estudos, A02 — Soares e Terra, 2024, aplicou testes de hipótese).
- **Referência estatística da disciplina:** `metodos-estatisticos.pdf` — Sirqueira *et al.* (2015), *Aplicação de Métodos Estatísticos em Engenharia de Software: teoria e prática*, contendo a árvore de decisão (Figura 2) e o passo a passo no software **Minitab**.
- **Objetivo deste Trabalho 2:** Executar um experimento controlado em Go comparando REST e gRPC com volume robusto de dados, realizar a análise estatística no **Minitab** seguindo a árvore de decisão da disciplina e entregar o relatório em **LaTeX (Overleaf)** no padrão ABNT do Trabalho 1 com prints das saídas do Minitab.

---

## 2. Decisões Metodológicas e Técnicas Tomadas

### 2.1 Desenho Experimental
- **Arquiteturas (Fator 1 — 2 tratamentos):** `REST` (HTTP/1.1 + JSON) vs. `gRPC` (HTTP/2 + Protocol Buffers).
  - *Decisão:* Escolhido o par clássico de 2 arquiteturas para manter simplicidade de implementação e análise, alinhado aos dois scripts Go planejados. A inclusão de REST sobre HTTP/2 ficou registrada em *Ameaças à Validade* e *Trabalhos Futuros* (TCC).
- **Tamanhos de Payload (Fator 2 — 4 tratamentos):** `1 KB`, `100 KB`, `1 MB` e `4 MB`.
  - *Decisão:* Cobre desde payloads muito pequenos até a faixa de transição e megabytes onde a literatura reportou inversões de vantagem.
- **Volume Amostral:** `100` requisições de aquecimento (*warm-up*, descartadas) + **`1.000` medições válidas** por combinação = **`8.000` observações totais** ($2 \times 4 \times 1.000$).
- **Payload Estruturado Realista:** Definido em `internal/dataset/dataset.go` como coleção determinística de structs `Item` (8 campos tipados: `int64`, 4 `string`, `float64`, `int32`, `bool`), calibrada para aproximar o JSON de 1 KB (4 itens), 100 KB (378 itens), 1 MB (3.845 itens) e 4 MB (15.348 itens), com conteúdo lógico idêntico entre REST e gRPC.
- **Controle de Protocolo:**
  - Conexão TCP persistente em *loopback* local (`127.0.0.1`), sem TLS e sem compressão gzip automática em ambos.
  - REST configurado explicitamente para HTTP/1.1 (`ForceAttemptHTTP2: false`, `keep-alive` ativo).
  - gRPC configurado sobre HTTP/2 nativo com `MaxRecvMsgSize` / `MaxSendMsgSize` elevados para **32 MB** (evitando o limite padrão de 4 MB).
  - `runtime.GC()` executado antes de cada cenário.

### 2.2 Instrumentação de Tempo (Descoberta Crítica)
- Na primeira coleta no Windows usando `time.Now()`, constatou-se que o temporizador padrão do Windows quantiza chamadas muito rápidas (1 KB) em múltiplos de ~0,5 ms, produzindo vários zeros artificiais (`0.000000 ms`).
- **Solução implementada (`internal/clock/`):**
  - `clock_windows.go`: usa `QueryPerformanceCounter` / `QueryPerformanceFrequency` (`kernel32.dll`), obtendo precisão de ~0,1 µs.
  - `clock_other.go` (macOS/Linux): usa `time.Now()` / `time.Since()`, que no macOS utiliza `mach_absolute_time` (resolução monotônica de nanossegundos).

### 2.3 Estratégia Estatística (Árvore de Decisão de Sirqueira *et al.*)
- **Normalidade:** Como $N = 1.000 > 30$ por grupo, aplica-se o **Teste de Kolmogorov-Smirnov (K-S)** (descartando Shapiro-Wilk).
- **Por que caiu em testes não paramétricos:** Benchmarks de latência de software têm piso mínimo físico e cauda longa à direita (GC, escalonamento do SO), violando a normalidade em todos os 8 grupos ($p < 0{,}010$), o que também ocorreu em Soares e Terra (2024). Levene complementar também apontou heterocedasticidade ($p < 0{,}001$).
- **Outliers:** Detectados via Grubbs e critério IQR, porém **mantidos na amostra** conforme orientação de Sirqueira *et al.* (não são erros de coleta, e sim *tail latency* legítima); a robustez é garantida pelo uso de medianas e testes não paramétricos.
- **Por que dois testes inferenciais:**
  1. **Análise 1 — Teste de Mann-Whitney (1 fator, 2 tratamentos):** compara `REST` vs. `gRPC` em cada faixa de payload (`1 KB`, `100 KB`, `1 MB`, `4 MB`) para identificar qual arquitetura vence em cada tamanho.
  2. **Análise 2 — Teste de Kruskal-Wallis + Mann-Whitney par-a-par (1 fator, 4 tratamentos):** compara os 4 tamanhos de payload dentro do `REST` e depois dentro do `gRPC`, comprovando estatisticamente o efeito do tamanho da mensagem e a diferença de escalabilidade.

### 2.4 LaTeX / Overleaf
- **Problema encontrado e corrigido:** A primeira versão usava `biblatex` + `biber` (estourava o *compile time* do plano gratuito do Overleaf) e havia `_` sem `\detokenize` nos placeholders de imagem.
- **Solução final:** Relatório reescrito exatamente no modelo ABNT leve do Trabalho 1 (`abntex2cite` + `bibtex`, cabeçalhos azul claro `RGB{220,230,242}`, `quadro` vs. `table`, `\fonte{}`, `\nota{}`, `\graphicspath{ {./images/} }`), com `abnt-etal-text = "\textit{et al.}"` corrigido.
- **Fluxograma adaptado (Figura 1):** Reproduz o fluxograma original completo da Figura 2 de Sirqueira *et al.* em TikZ vetorial, mantendo ramos descartados em cinza tracejado e destacando em cor os caminhos escolhidos com caixas de justificativa e os nomes exatos dos grupos testados.
- **Macro inteligente `\minitabimg`:** Compila sem erro mesmo antes de subir os prints em `images/` (exibe um quadro indicando o nome exato do PNG esperado e substitui automaticamente assim que o arquivo for enviado ao Overleaf).
- **Compilação verificada localmente:** MiKTeX 25.12 instalado na máquina Windows; `relatorio/main.pdf` compilado com **0 erros** em ~8 segundos (3x `pdflatex` + `bibtex`) e revisado visualmente página por página.

---

## 3. Mapa de Arquivos do Repositório

| Caminho | Função |
| :--- | :--- |
| `proto/benchmark.proto` | Contrato Protocol Buffers / gRPC |
| `proto/benchmarkpb/*.pb.go` | Código Go gerado via `protoc 36.2` (já versionado — não exige `protoc` no MacBook) |
| `internal/dataset/dataset.go` | Gerador determinístico de payloads estruturados (`1KB`, `100KB`, `1MB`, `4MB`) |
| `internal/clock/clock_windows.go` | Temporizador QPC (~0,1 µs) para Windows |
| `internal/clock/clock_other.go` | Temporizador monotônico nativo (`mach_absolute_time`) para macOS/Linux |
| `cmd/rest_bench/main.go` | Benchmark REST (HTTP/1.1 + JSON) -> `results/raw_rest.csv` |
| `cmd/grpc_bench/main.go` | Benchmark gRPC (HTTP/2 + Protobuf) -> `results/raw_grpc.csv` |
| `run_benchmark.ps1` | Orquestrador completo para Windows |
| `run_benchmark.sh` | Orquestrador completo para macOS (MacBook) / Linux |
| `scripts/analyze_and_export.py` | Consolida CSVs, gera Excel para Minitab, valida estatísticas e exporta tabelas LaTeX |
| `results/dados_experimento_minitab.xlsx` | Planilha pronta para abrir no Minitab (9 abas organizadas, sem conflito de vírgula/ponto) |
| `results/dados_empilhados.csv` | Dataset completo empilhado (8.000 linhas) |
| `results/dados_por_grupo.csv` | Dataset por coluna/grupo (1.000 linhas × 8 colunas) |
| `results/ambiente_execucao.txt` | Especificações de hardware/software capturadas automaticamente na coleta |
| `results/analise_estatistica_validacao.json` | Todos os resultados estatísticos numéricos de referência |
| `results/resumo_tabelas_latex.txt` | Linhas de tabelas LaTeX (vírgula ABNT) prontas para colar no `main.tex` após nova coleta |
| `GUIA_COLETA_MACBOOK.md` | Checklist de isolamento e passo a passo de coleta limpa no MacBook |
| `GUIA_MINITAB.md` | Passo a passo detalhado dos menus (EN/PT), prints e checklist de imagens (`images/*.png`) |
| `relatorio/main.tex` | Código-fonte LaTeX ABNT pronto para Overleaf gratuito |
| `relatorio/referencias.bib` | Referências BibTeX (`abntex2cite`, NBR 10520:2023) |
| `relatorio/main.pdf` | Pré-visualização compilada localmente com 0 erros |
| `README.md` | Visão geral e comandos rápidos do projeto |

---

## 4. Estado Atual dos Resultados (Coleta Piloto no Windows)

> **Atenção:** Os dados atualmente em `results/` e no `relatorio/main.tex` foram coletados no Windows 10 (Intel Core i5-8400, 15,96 GB RAM, Go 1.27.4) enquanto o computador estava sendo usado normalmente. O plano é repetir a coleta no **MacBook em ambiente totalmente isolado** para obter a base definitiva.

Resumo da coleta atual (8.000 amostras):
- **Redução de bytes (Protobuf vs. JSON):** 29,08% a 30,11% em todos os payloads.
- **Normalidade (K-S):** Rejeitada em todos os 8 grupos ($p < 0{,}010$).
- **Homocedasticidade (Levene):** Rejeitada em todos os cenários ($p < 0{,}001$).
- **Análise 1 (Mann-Whitney — REST vs. gRPC):**
  - `1 KB`: REST `0,1078 ms` vs. gRPC `0,1161 ms` -> **REST 7,75% mais rápido** ($p = 0{,}000035$)
  - `100 KB`: REST `1,1473 ms` vs. gRPC `0,5804 ms` -> **gRPC 49,41% mais rápido** ($p < 0{,}0001$)
  - `1 MB`: REST `11,9954 ms` vs. gRPC `3,7769 ms` -> **gRPC 68,51% mais rápido** ($p < 0{,}0001$)
  - `4 MB`: REST `45,1097 ms` vs. gRPC `14,7170 ms` -> **gRPC 67,38% mais rápido** ($p < 0{,}0001$)
- **Análise 2 (Kruskal-Wallis — Efeito do Payload):**
  - `REST`: $H = 3.744{,}85$, $DF = 3$, $p < 0{,}0001$ (6/6 pares significativos; crescimento de 418,6× de 1 KB para 4 MB).
  - `gRPC`: $H = 3.699{,}40$, $DF = 3$, $p < 0{,}0001$ (6/6 pares significativos; crescimento de 126,8× de 1 KB para 4 MB).

---

## 5. Próximos Passos (Checklist para Retomada)

- [ ] **1. Coleta limpa no MacBook:** Clonar/atualizar o repositório no MacBook, fechar todos os aplicativos seguindo `GUIA_COLETA_MACBOOK.md` e executar `./run_benchmark.sh 100 1000` (ou rodar os comandos manualmente).
- [ ] **2. Conferir novos resultados:** Verificar `results/ambiente_execucao.txt`, `results/analise_estatistica_validacao.json` e `results/resumo_tabelas_latex.txt` (checar se todos os grupos continuam não normais e se houve alguma mudança nos vencedores por faixa).
- [ ] **3. Executar análise e tirar prints no Minitab:** Abrir o novo `results/dados_experimento_minitab.xlsx` no Minitab, seguir `GUIA_MINITAB.md` e salvar os 17 prints PNG na pasta `images/` com os nomes exatos do checklist.
- [ ] **4. Atualizar o LaTeX com os números definitivos do MacBook:** Atualizar o Quadro 1 (hardware do MacBook), as Tabelas 2–6 e os valores citados no texto/resumo de `relatorio/main.tex` usando `results/resumo_tabelas_latex.txt` (ou enviar os novos resultados para o agente atualizar automaticamente).
- [ ] **5. Compilar versão final no Overleaf:** Subir `relatorio/main.tex`, `relatorio/referencias.bib` e a pasta `images/` com os prints do Minitab no Overleaf e gerar o PDF final para entrega e apresentação.
