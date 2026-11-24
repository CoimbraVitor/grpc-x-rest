# Guia Passo a Passo no Minitab — Experimento REST vs. gRPC

Este guia descreve exatamente cada clique que você deve fazer no **Minitab** para reproduzir toda a análise estatística seguindo a árvore de decisão de Sirqueira et al. (`metodos-estatisticos.pdf`), conferir os valores já calculados e salvar os prints para inserir diretamente no relatório em LaTeX (`relatorio/main.tex`).

> **Dica de ouro:** Os menus abaixo estão indicados em **Inglês** (padrão do artigo de referência) e em **Português**, caso seu Minitab esteja traduzido.

---

## 0. Arquivo de Dados Pronto para o Minitab

Use o arquivo Excel já formatado:
- **`results/dados_experimento_minitab.xlsx`**

> **Por que usar o `.xlsx` em vez do `.csv`?**  
> Porque no Excel os números são gravados em formato numérico nativo, evitando qualquer problema de ponto (`.`) vs. vírgula (`,`) decimal no Minitab em Windows PT-BR.

O arquivo `.xlsx` possui abas já preparadas para facilitar cada etapa no Minitab:
1. **`Dados_Empilhados`**: Todas as **8.000 observações** em formato longo (`Arquitetura`, `Payload`, `Latencia_ms`, `Grupo`, etc.).
2. **`Dados_Por_Grupo`**: **1.000 linhas × 8 colunas** (`REST_1KB`, `gRPC_1KB`, `REST_100KB`, `gRPC_100KB`, `REST_1MB`, `gRPC_1MB`, `REST_4MB`, `gRPC_4MB`) — ideal para Normalidade (K-S), Outliers (Grubbs) e Mann-Whitney!
3. **`Payload_1KB`**, **`Payload_100KB`**, **`Payload_1MB`**, **`Payload_4MB`**: Subconjuntos prontos (2.000 linhas cada) para Boxplots e Teste de Levene (2 Variances) comparando REST vs. gRPC em cada tamanho.
4. **`Arq_REST`** e **`Arq_gRPC`**: Subconjuntos prontos (4.000 linhas cada) para o teste de **Kruskal-Wallis** (efeito do tamanho do payload dentro de cada arquitetura).

### Como abrir no Minitab
1. Clique em **`File → Open`** (*Arquivo → Abrir*).
2. Mude o filtro de tipo de arquivo para **Excel (`*.xlsx`)** e selecione `results/dados_experimento_minitab.xlsx`.
3. Na janela que abrir, **marque** `First row contains column names` (*Primeira linha contém nomes das colunas*) e escolha a aba desejada (você pode abrir várias worksheets no mesmo projeto do Minitab!).

---

## Caminho Percorrido na Árvore de Decisão (`metodos-estatisticos.pdf`)

Antes de clicar nos menus, tenha clareza do caminho que nossos dados seguem no fluxograma (Figura 2 do artigo):

1. **A amostra possui mais de 30 valores?**  
   **SIM** ($N = 1.000$ observações por grupo; $8.000$ no total) $\rightarrow$ Usar **Teste de Kolmogorov-Smirnov (K-S)** para verificar normalidade.
2. **A distribuição é normal para todos os valores (grupos)?**  
   **NÃO** (em todos os 8 grupos, $p < 0{,}010 < \alpha = 0{,}05$, pois tempos de resposta de software são assimétricos à direita) $\rightarrow$ **Será necessário utilizar um teste não paramétrico!**
   *(Obs.: Opcionalmente você pode também rodar o Teste de Levene como verificação complementar — ele igualmente retorna $p < 0{,}001$, confirmando heterocedasticidade.)*
3. **Quantos fatores e tratamentos o estudo possui?**
   - **Análise 1 (Comparação entre Arquiteturas por Payload):** 1 fator (`Arquitetura`) com **2 tratamentos** (`REST` e `gRPC`), avaliado em cada tamanho (`1KB`, `100KB`, `1MB`, `4MB`) $\rightarrow$ **Teste de Mann-Whitney**.
   - **Análise 2 (Efeito do Tamanho do Payload por Arquitetura):** 1 fator (`Payload`) com **4 tratamentos** (`1KB`, `100KB`, `1MB`, `4MB`), avaliado separadamente no REST e no gRPC $\rightarrow$ **Teste de Kruskal-Wallis** seguido de **Mann-Whitney par-a-par**.

---

## Etapa 1 — Estatística Descritiva

**Aba usada:** `Dados_Empilhados`

1. Menu: **`Stat → Basic Statistics → Display Descriptive Statistics...`**  
   *(PT-BR: `Estat → Estatísticas Básicas → Exibir Estatísticas Descritivas...`)*
2. Em **Variables** (*Variáveis*): selecione `Latencia_ms`.
3. Em **By variables (optional)** (*Por variáveis*): selecione `Payload` e `Arquitetura`.
4. Clique em **`Statistics...`** (*Estatísticas...*) e marque:
   - `Mean` (Média), `Standard deviation` (Desvio padrão), `Variance` (Variância), `Minimum` (Mínimo), `First quartile` (Q1), `Median` (Mediana), `Third quartile` (Q3), `Maximum` (Máximo), `Range` (Amplitude/Faixa), `IQR` (Intervalo interquartil), `N nonmissing` (N).
5. Clique em **OK** e **OK**.
6. **Print:** Salve o print da tabela gerada na janela Output/Session como **`images/descritiva.png`**.

### Valores esperados para conferência (em ms)
| Grupo | N | Média | Mediana | DP | Mínimo | Q1 | Q3 | Máximo | IQR |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| REST 1KB | 1000 | 0,1252 | 0,1078 | 0,0580 | 0,0758 | 0,1031 | 0,1200 | 0,7338 | 0,0169 |
| gRPC 1KB | 1000 | 0,1910 | 0,1161 | 0,5177 | 0,0631 | 0,0987 | 0,1496 | 10,8796 | 0,0509 |
| REST 100KB | 1000 | 1,2954 | 1,1473 | 0,4034 | 0,9007 | 0,9826 | 1,5322 | 3,2366 | 0,5496 |
| gRPC 100KB | 1000 | 0,6624 | 0,5804 | 0,2272 | 0,4709 | 0,5291 | 0,6966 | 2,6358 | 0,1675 |
| REST 1MB | 1000 | 12,2777 | 11,9954 | 3,7887 | 8,6970 | 11,2088 | 12,7287 | 92,7331 | 1,5199 |
| gRPC 1MB | 1000 | 3,9546 | 3,7769 | 0,6140 | 3,1088 | 3,5567 | 4,1693 | 7,8968 | 0,6127 |
| REST 4MB | 1000 | 49,0201 | 45,1097 | 10,1818 | 38,5877 | 43,6368 | 51,9788 | 160,0186 | 8,3421 |
| gRPC 4MB | 1000 | 15,8239 | 14,7170 | 5,8812 | 12,5693 | 13,8985 | 15,9608 | 140,2882 | 2,0623 |

---

## Etapa 2 — Boxplots (Análise Exploratória)

Como a latência varia de ~0,1 ms (1 KB) até ~45 ms (4 MB), fazer um boxplot separado para cada tamanho de payload deixa a comparação REST vs. gRPC extremamente clara e legível!

**Abas usadas:** `Payload_1KB`, `Payload_100KB`, `Payload_1MB` e `Payload_4MB` (repita para cada uma).

1. Menu: **`Graph → Boxplot...`** *(PT-BR: `Gráfico → Boxplot...`)*.
2. Selecione **`One Y → With Groups`** *(Um Y → Com Grupos)* e clique em **OK**.
3. Em **Graph variables** (*Variáveis gráficas*): selecione `Latencia_ms`.
4. Em **Categorical variables for grouping** (*Variáveis categóricas para agrupamento*): selecione `Arquitetura`.
5. *(Opcional, fica ótimo visualmente)* Clique em **`Data View...`** e marque **`Median connect line`** ou **`Mean symbol`** se quiser igual à Figura 3 do artigo.
6. Clique em **OK**.
7. **Prints:** Clique com o botão direito no gráfico → **`Save Graph As...`** (PNG) e salve como:
   - `images/boxplot_1kb.png`
   - `images/boxplot_100kb.png`
   - `images/boxplot_1mb.png`
   - `images/boxplot_4mb.png`

---

## Etapa 3 — Análise de Outliers (Teste de Grubbs)

**Aba usada:** `Dados_Por_Grupo`

1. Menu: **`Stat → Basic Statistics → Outlier Test...`**  
   *(PT-BR: `Estat → Estatísticas Básicas → Teste de Outlier...`)*
2. Em **Variables** (*Variáveis*): selecione todas as 8 colunas (`REST_1KB` até `gRPC_4MB`).
3. Em **Method** (*Método*): mantenha **`Grubbs' test`** e nível de significância `0.05` (5%).
4. Clique em **OK**.
5. **Print:** Salve o resultado de texto da saída do Minitab como **`images/outliers_grubbs.png`**.

### O que você vai observar e como explicar ao professor
- Todos os grupos apresentam $p < 0{,}05$ (ex.: REST 100 KB tem $G = 4{,}81$, $p = 0{,}001$; os demais têm $p = 0{,}000$), indicando presença de valores extremos na cauda superior (ex.: `10,88 ms` em gRPC 1 KB; `92,73 ms` em REST 1 MB; `160,02 ms` em REST 4 MB).
- **Decisão metodológica (conforme Sirqueira et al., seção 3):** esses valores **não são erros de coleta ou medição**, mas sim **latência de cauda (*tail latency*)** real causada por pausas do coletor de lixo (*Garbage Collector*) do Go e preempção do escalonador do Windows. Portanto, **mantemos os outliers na amostra** e utilizamos **testes não paramétricos (Mann-Whitney e Kruskal-Wallis)** e **mediana**, que são robustos a valores extremos!

---

## Etapa 4 — Teste de Normalidade (Kolmogorov-Smirnov)

Como $N = 1.000 > 30$ em cada grupo, a árvore de decisão determina o **Teste de Kolmogorov-Smirnov (K-S)**.

**Aba usada:** `Dados_Por_Grupo`

1. Menu: **`Stat → Basic Statistics → Normality Test...`**  
   *(PT-BR: `Estat → Estatísticas Básicas → Teste de Normalidade...`)*
2. Em **Variable** (*Variável*): selecione uma coluna por vez (ex.: `REST_1KB`, depois `gRPC_1KB`, ..., até `gRPC_4MB`).
3. Em **Tests for Normality** (*Testes de Normalidade*): **selecione `Kolmogorov-Smirnov`** (atenção: o padrão do Minitab é Anderson-Darling; lembre-se de trocar para Kolmogorov-Smirnov!).
4. Clique em **OK**.
5. **Prints:** Salve os gráficos de probabilidade (para não poluir o relatório com 8 páginas, você pode salvar todos ou pelo menos os pares principais; o `main.tex` está configurado para aceitar os 4 pares ou um grid compacto com `images/ks_rest_1kb.png`, `images/ks_grpc_1kb.png`, `images/ks_rest_1mb.png`, `images/ks_grpc_1mb.png` — e se quiser colocar os 8, há espaço pronto!).

### Valores esperados no Minitab (K-S)
Em **todos os 8 grupos**, o Minitab exibirá **`P-Value < 0.010`** (estatística `KS` entre `0,135` e `0,403`), levando à **rejeição de $H_0$** (as amostras **não** seguem distribuição normal).

> **Decisão na árvore:** Como a normalidade foi rejeitada ($p < 0{,}05$), seguimos diretamente para o ramo de **testes não paramétricos**!

---

## Etapa 5 (Opcional / Complementar) — Teste de Homocedasticidade (Levene)

Pela árvore de decisão, quando a normalidade já falha, não é obrigatório rodar Levene. Contudo, rodar ao menos um exemplo (ou os 4) enriquece o relatório e confirma que também há **heterocedasticidade**.

**Abas usadas:** `Payload_1KB`, `Payload_100KB`, `Payload_1MB`, `Payload_4MB`

1. Menu: **`Stat → Basic Statistics → 2 Variances...`**  
   *(PT-BR: `Estat → Estatísticas Básicas → 2 Variâncias...`)*
2. Selecione **`Both samples are in one column`** (*Ambas as amostras estão em uma coluna*).
   - **Samples** (*Amostras*): `Latencia_ms`
   - **Sample IDs** (*IDs da amostra*): `Arquitetura`
3. Clique em **OK**.
4. Observe o **`Levene's Test P-Value`** no canto superior direito do gráfico: será `0,000` em todos os payloads (em 1 KB, `0,000` / $1{,}8 \times 10^{-5}$), confirmando variâncias desiguais ($p < 0{,}05$).
5. **Print (opcional, recomendado para 1 MB):** salve como **`images/levene_1mb.png`**.

---

## Etapa 6 — Análise 1: REST vs. gRPC por Payload (1 Fator, 2 Tratamentos → Mann-Whitney)

Esta é a análise central do trabalho! Repita os passos abaixo para os **4 tamanhos de payload** (`1KB`, `100KB`, `1MB`, `4MB`).

**Aba usada:** `Dados_Por_Grupo`

1. Menu: **`Stat → Nonparametrics → Mann-Whitney...`**  
   *(PT-BR: `Estat → Não-paramétricos → Mann-Whitney...`)*
2. Para **1 KB**:
   - **First Sample** (*Primeira Amostra*): `REST_1KB`
   - **Second Sample** (*Segunda Amostra*): `gRPC_1KB`
   - **Confidence level**: `95.0`
   - **Alternative**: `not equal` ($\eta_1 \neq \eta_2$)
   - Clique em **OK**.
3. Repita o mesmo procedimento para:
   - `REST_100KB` vs. `gRPC_100KB`
   - `REST_1MB` vs. `gRPC_1MB`
   - `REST_4MB` vs. `gRPC_4MB`
4. **Prints:** Salve o print de cada saída de texto do Minitab como:
   - `images/mw_1kb.png`
   - `images/mw_100kb.png`
   - `images/mw_1mb.png`
   - `images/mw_4mb.png`

### Valores esperados no Minitab (Mann-Whitney)
| Payload | Mediana REST (ms) | Mediana gRPC (ms) | Estimativa $\eta_{\text{REST}} - \eta_{\text{gRPC}}$ (ms) | $W$ | $p$-valor (ajustado) | Conclusão ($\alpha = 0{,}05$) |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| **1 KB** | 0,1078 | 0,1161 | $-0{,}0045$ | 947.049,5 | **0,0000** ($3{,}5 \times 10^{-5}$) | Rejeita $H_0$ (**REST** 7,75% menor) |
| **100 KB** | 1,1473 | 0,5804 | $+0{,}5156$ | 1.454.478,5 | **0,0000** ($< 0{,}0001$) | Rejeita $H_0$ (**gRPC** 49,41% menor) |
| **1 MB** | 11,9954 | 3,7769 | $+8{,}0673$ | 1.500.500,0 | **0,0000** ($< 0{,}0001$) | Rejeita $H_0$ (**gRPC** 68,51% menor) |
| **4 MB** | 45,1097 | 14,7170 | $+30{,}3658$ | 1.496.193,0 | **0,0000** ($< 0{,}0001$) | Rejeita $H_0$ (**gRPC** 67,38% menor) |

---

## Etapa 7 — Análise 2: Efeito do Tamanho do Payload (1 Fator, 4 Tratamentos → Kruskal-Wallis + Mann-Whitney par-a-par)

Esta análise verifica se a variação do tamanho do payload (`1KB`, `100KB`, `1MB`, `4MB`) produz diferença estatisticamente significativa na latência **dentro de cada arquitetura**, exercitando o ramo **"> 2 tratamentos"** da árvore de decisão!

### 7.1 Teste de Kruskal-Wallis
**Abas usadas:** `Arq_REST` (e depois `Arq_gRPC`)

1. Menu: **`Stat → Nonparametrics → Kruskal-Wallis...`**  
   *(PT-BR: `Estat → Não-paramétricos → Kruskal-Wallis...`)*
2. Em **Response** (*Resposta*): selecione `Latencia_ms`.
3. Em **Factor** (*Fator*): selecione `Payload`.
4. Clique em **OK**.
5. Repita usando a aba `Arq_gRPC`.
6. **Prints:** Salve as saídas como:
   - `images/kw_rest.png`
   - `images/kw_grpc.png`

### Valores esperados no Minitab (Kruskal-Wallis)
- **REST:** $H = 3744{,}85$, $DF = 3$, **$p$-valor = 0,000** $\rightarrow$ Rejeita $H_0$!
- **gRPC:** $H = 3699{,}40$, $DF = 3$, **$p$-valor = 0,000** $\rightarrow$ Rejeita $H_0$!

### 7.2 Comparações Pós-Teste (Mann-Whitney par-a-par)
Conforme a Seção 3.4 de `metodos-estatisticos.pdf`, como Kruskal-Wallis rejeitou $H_0$, aplicamos Mann-Whitney entre os pares de tamanhos na aba `Dados_Por_Grupo`:
- Para **REST**: `REST_1KB` vs `REST_100KB`, `REST_100KB` vs `REST_1MB`, `REST_1MB` vs `REST_4MB` (e os demais pares: `1KB vs 1MB`, `1KB vs 4MB`, `100KB vs 4MB`).
- Para **gRPC**: mesmos 6 pares com prefixo `gRPC_`.
- **Resultado esperado:** Em **todos os 6 pares** de ambas as arquiteturas, $p = 0{,}0000 < 0{,}05$ (todas as faixas de payload diferem significativamente entre si!).
- **Print (exemplo ilustrativo):** salve o par adjacente mais próximo (`REST_1MB` vs `REST_4MB` ou `gRPC_1KB` vs `gRPC_100KB`) como **`images/mw_posthoc_exemplo.png`** (ou um mosaico com os pares).

---

## Checklist Final de Prints para Subir no Overleaf

Crie uma pasta chamada **`images/`** dentro do seu projeto no Overleaf (ao lado de `main.tex` e `referencias.bib`) e coloque os prints com exatamente estes nomes:

- [ ] `images/descritiva.png` — Tabela de Estatísticas Descritivas (Etapa 1)
- [ ] `images/boxplot_1kb.png` — Boxplot REST vs gRPC (1 KB)
- [ ] `images/boxplot_100kb.png` — Boxplot REST vs gRPC (100 KB)
- [ ] `images/boxplot_1mb.png` — Boxplot REST vs gRPC (1 MB)
- [ ] `images/boxplot_4mb.png` — Boxplot REST vs gRPC (4 MB)
- [ ] `images/outliers_grubbs.png` — Saída do Outlier Test / Grubbs (Etapa 3)
- [ ] `images/ks_rest_1kb.png` — Teste K-S para REST 1 KB
- [ ] `images/ks_grpc_1kb.png` — Teste K-S para gRPC 1 KB
- [ ] `images/ks_rest_1mb.png` — Teste K-S para REST 1 MB
- [ ] `images/ks_grpc_1mb.png` — Teste K-S para gRPC 1 MB
- [ ] `images/levene_1mb.png` — Teste de Levene (2 Variances) para 1 MB *(complementar)*
- [ ] `images/mw_1kb.png` — Mann-Whitney REST vs gRPC (1 KB)
- [ ] `images/mw_100kb.png` — Mann-Whitney REST vs gRPC (100 KB)
- [ ] `images/mw_1mb.png` — Mann-Whitney REST vs gRPC (1 MB)
- [ ] `images/mw_4mb.png` — Mann-Whitney REST vs gRPC (4 MB)
- [ ] `images/kw_rest.png` — Kruskal-Wallis do efeito do Payload no REST
- [ ] `images/kw_grpc.png` — Kruskal-Wallis do efeito do Payload no gRPC

> **Nota:** O arquivo `relatorio/main.tex` já compila perfeitamente no Overleaf **mesmo antes** de você subir esses prints (ele exibe um quadro informativo onde cada figura irá aparecer). Assim que você fizer upload de cada PNG na pasta `images/`, o LaTeX troca automaticamente o quadro pelo seu print real do Minitab!
