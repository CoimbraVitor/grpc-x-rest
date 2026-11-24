# Guia de Coleta Limpa no MacBook (macOS)

Executar o benchmark em ambiente isolado (com todos os aplicativos fechados) é uma excelente prática de **Validade Interna** em Engenharia de Software Experimental, pois reduz o ruído de escalonamento de CPU, picos de *tail latency* e interferência de I/O.

> **Sobre o relógio no macOS:** o código em `internal/clock/clock_other.go` utiliza automaticamente o relógio monotônico de alta resolução do Go no macOS (`mach_absolute_time`), que possui precisão na ordem de **nanossegundos** nativamente (sem a limitação de 0,5 ms do Windows).

---

## 1. Pré-requisitos no MacBook (instale uma única vez)

Abra o **Terminal** no macOS e verifique se Go e Python 3 estão instalados:

```bash
go version
python3 --version
```

Se algum deles não estiver instalado (usando Homebrew):

```bash
# Instalar Go (se necessário)
brew install go

# Instalar bibliotecas Python para gerar a planilha do Minitab e validar os testes
python3 -m pip install --user scipy numpy pandas openpyxl
```

*(Nota: você **não** precisa instalar `protoc` no MacBook, pois os arquivos gerados `proto/benchmarkpb/*.pb.go` já estão commitados no repositório!)*

---

## 2. Checklist de Isolamento do Ambiente (antes de rodar)

Para obter medições limpas e reprodutíveis:

1. **Conecte o MacBook na tomada** (evita modo de economia de energia / redução de clock da CPU).
2. **Desative o Modo Pouca Energia** em *Ajustes do Sistema → Bateria*.
3. **Feche todos os aplicativos abertos** (navegadores, Slack, Discord, VS Code, Docker, Spotify, etc.), mantendo apenas o **Terminal** aberto.
4. **Pause sincronizações em segundo plano** (OneDrive, Google Drive, iCloud Drive, Dropbox, Time Machine).
5. **Ative o modo "Não Perturbe"** (ou desconecte o Wi-Fi durante a coleta, já que o benchmark usa apenas loopback local `127.0.0.1` e não precisa de internet depois que as dependências Go forem baixadas).
6. **Baixe as dependências Go antes de desconectar o Wi-Fi:**
   ```bash
   cd /caminho/para/grpc-x-rest
   go mod download
   ```
7. **Não utilize o computador** durante os ~1 a 2 minutos de execução do script.

---

## 3. Como Executar a Coleta no MacBook

### Opção A — Automática (recomendada)

Dê permissão de execução ao script e rode:

```bash
chmod +x run_benchmark.sh
./run_benchmark.sh 100 1000
```

Isso executa automaticamente:
1. Registra o hardware real do seu MacBook (modelo da CPU, núcleos, RAM, versão do macOS e versão do Go) em `results/ambiente_execucao.txt`.
2. Roda o benchmark **REST (HTTP/1.1 + JSON)** (`100` aquecimento + `1.000` medições × 4 payloads = 4.000 amostras) e salva em `results/raw_rest.csv`.
3. Aguarda 3 segundos de estabilização.
4. Roda o benchmark **gRPC (HTTP/2 + Protobuf)** (`100` aquecimento + `1.000` medições × 4 payloads = 4.000 amostras) e salva em `results/raw_grpc.csv`.
5. Executa `scripts/analyze_and_export.py`, gerando:
   - `results/dados_experimento_minitab.xlsx` — **planilha pronta para abrir no Minitab**;
   - `results/dados_empilhados.csv` e `results/dados_por_grupo.csv`;
   - `results/analise_estatistica_validacao.json` — conferência completa de todos os testes;
   - `results/resumo_tabelas_latex.txt` — **todas as tabelas já prontas em formato LaTeX** com os novos números do seu MacBook para você colar no Overleaf!

---

### Opção B — Passo a Passo Manual (comando por comando)

Se você preferir controlar cada etapa manualmente no Terminal:

```bash
# 1. Conferir especificações da máquina (anote para o Quadro do ambiente no relatório)
sw_vers
sysctl -n machdep.cpu.brand_string
sysctl -n hw.physicalcpu hw.logicalcpu hw.memsize
go version

# 2. Executar o script REST (HTTP/1.1) -> gera results/raw_rest.csv
go run ./cmd/rest_bench -warmup 100 -n 1000

# 3. Executar o script gRPC (HTTP/2) -> gera results/raw_grpc.csv
go run ./cmd/grpc_bench -warmup 100 -n 1000

# 4. Consolidar para o Minitab e gerar tabelas LaTeX atualizadas
python3 ./scripts/analyze_and_export.py
```

*(Dica: você pode testar rapidamente com menos iterações antes da coleta oficial, ex.: `go run ./cmd/rest_bench -warmup 10 -n 50`, e depois rodar a coleta final com `-warmup 100 -n 1000`.)*

---

## 4. Após a Coleta no MacBook: Atualizar Minitab e Overleaf

1. Abra o novo **`results/dados_experimento_minitab.xlsx`** no Minitab e siga o **[GUIA_MINITAB.md](GUIA_MINITAB.md)** para gerar os prints.
2. Abra **`results/resumo_tabelas_latex.txt`** e **`results/ambiente_execucao.txt`**:
   - Copie os dados de hardware do MacBook para o **Quadro 1** do `relatorio/main.tex`;
   - Substitua os números das **Tabelas 1 a 5** e do texto de resultados do `relatorio/main.tex` pelos valores gerados na coleta limpa do MacBook (eles já vêm formatados com vírgula decimal ABNT em `resumo_tabelas_latex.txt`!).
3. Confira se o resultado de normalidade (K-S) e os vencedores por faixa de payload se mantiveram ou mudaram no MacBook — o próprio `resumo_tabelas_latex.txt` já destaca automaticamente qual caminho da árvore de decisão foi seguido e quem venceu cada faixa!
