# Guia de Reprodução da Análise Estatística no Minitab

Este documento descreve o procedimento completo utilizado no **Minitab** para conduzir a análise estatística do experimento comparativo entre **REST (HTTP/1.1 + JSON)** e **gRPC (HTTP/2 + Protocol Buffers)**, seguindo a árvore de decisão de Sirqueira *et al.* (`metodos-estatisticos.pdf`), com nível de significância $\alpha = 0{,}05$.

> **Nota sobre idiomas:** os caminhos de menu estão indicados em **Inglês** (padrão do artigo de referência) e em **Português (PT-BR)**.

---

## 1. Conjunto de Dados para Importação no Minitab

Os dados coletados no ambiente de referência (**Apple M3, 16 GB RAM, macOS 15.6.1, Go 1.27.4**, totalizando **8.000 observações**) estão consolidados na planilha:

- **`results/dados_experimento_minitab.xlsx`**

O formato `.xlsx` preserva os valores em tipo numérico nativo, evitando conflitos de separador decimal (`.` vs. `,`) ao importar no Minitab. A planilha está organizada nas seguintes abas:

1. **`Dados_Empilhados`**: todas as **8.000 observações** em formato longo (`Arquitetura`, `Payload`, `Latencia_ms`, `Grupo`, `Wire_Bytes`, etc.).
2. **`Dados_Por_Grupo`**: **1.000 linhas × 8 colunas** (`REST_1KB`, `gRPC_1KB`, `REST_100KB`, `gRPC_100KB`, `REST_1MB`, `gRPC_1MB`, `REST_4MB`, `gRPC_4MB`), estruturada para os testes de Normalidade (K-S), Outliers (Grubbs) e Mann-Whitney.
3. **`Payload_1KB`**, **`Payload_100KB`**, **`Payload_1MB`**, **`Payload_4MB`**: subconjuntos com 2.000 linhas cada para Boxplots e Teste de Levene (*2 Variances*) comparando REST vs. gRPC em cada faixa.
4. **`Arq_REST`** e **`Arq_gRPC`**: subconjuntos com 4.000 linhas cada para o teste de **Kruskal-Wallis** (efeito do tamanho do payload dentro de cada arquitetura).

### Importação no Minitab
1. Acessar **`File → Open`** (*Arquivo → Abrir*).
2. Selecionar o filtro **Excel (`*.xlsx`)** e abrir `results/dados_experimento_minitab.xlsx`.
3. Marcar **`First row contains column names`** (*Primeira linha contém nomes das colunas*) e carregar a aba correspondente a cada etapa.

---

## 2. Caminho na Árvore de Decisão Estatística (`metodos-estatisticos.pdf`)

A seleção dos testes segue integralmente o fluxograma de Sirqueira *et al.* (Figura 2):

1. **A amostra possui mais de 30 valores?**  
   **Sim** ($N = 1.000$ observações por grupo; $8.000$ no total) $\rightarrow$ **Teste de Kolmogorov-Smirnov (K-S)** para avaliação de normalidade.
2. **A distribuição é normal para todos os grupos?**  
   **Não** ($p < 0{,}010 < \alpha = 0{,}05$ em todos os 8 grupos, comportamento esperado em latência de software devido à assimetria à direita) $\rightarrow$ **Testes não paramétricos**.  
   *(Verificação complementar: o Teste de Levene também rejeita homocedasticidade em 1 KB, 100 KB e 1 MB.)*
3. **Quantos fatores e tratamentos o estudo possui?**
   - **Análise 1 (Arquitetura por Payload):** 1 fator (`Arquitetura`) com **2 tratamentos** (`REST` e `gRPC`), avaliado em cada faixa (`1KB`, `100KB`, `1MB`, `4MB`) $\rightarrow$ **Teste de Mann-Whitney**.
   - **Análise 2 (Tamanho do Payload por Arquitetura):** 1 fator (`Payload`) com **4 tratamentos** (`1KB`, `100KB`, `1MB`, `4MB`), avaliado separadamente em REST e em gRPC $\rightarrow$ **Teste de Kruskal-Wallis** seguido de **Mann-Whitney par-a-par**.

---

## 3. Etapa 1 — Estatística Descritiva

**Aba utilizada:** `Dados_Empilhados`

1. Menu: **`Stat → Basic Statistics → Display Descriptive Statistics...`**  
   *(PT-BR: `Estat → Estatísticas Básicas → Exibir Estatísticas Descritivas...`)*
2. **Variables** (*Variáveis*): `Latencia_ms`.
3. **By variables (optional)** (*Por variáveis*): `Payload` e `Arquitetura`.
4. Em **`Statistics...`** (*Estatísticas...*), selecionar: `Mean`, `Standard deviation`, `Variance`, `Minimum`, `First quartile`, `Median`, `Third quartile`, `Maximum`, `Range`, `IQR` e `N nonmissing`.
5. Confirmar em **OK**.
6. Figura associada no relatório: **`images/descritiva.png`**.

### Valores de referência (coleta Apple M3 / macOS 15.6.1, em ms)

| Grupo | N | Média | Mediana | DP | Mínimo | Q1 | Q3 | Máximo | IQR |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| REST 1KB | 1000 | 0,0457 | 0,0405 | 0,0139 | 0,0302 | 0,0378 | 0,0530 | 0,2392 | 0,0151 |
| gRPC 1KB | 1000 | 0,0453 | 0,0403 | 0,0132 | 0,0285 | 0,0363 | 0,0540 | 0,1825 | 0,0177 |
| REST 100KB | 1000 | 0,5108 | 0,4971 | 0,0644 | 0,4303 | 0,4669 | 0,5255 | 0,8532 | 0,0586 |
| gRPC 100KB | 1000 | 0,2035 | 0,1958 | 0,0446 | 0,1854 | 0,1927 | 0,2000 | 0,7885 | 0,0073 |
| REST 1MB | 1000 | 4,7038 | 4,6778 | 0,5308 | 4,3140 | 4,5392 | 4,8066 | 18,8021 | 0,2674 |
| gRPC 1MB | 1000 | 1,7457 | 1,7422 | 0,1419 | 1,3694 | 1,7167 | 1,7753 | 2,3570 | 0,0587 |
| REST 4MB | 1000 | 18,7723 | 18,7834 | 1,2466 | 17,2046 | 18,6120 | 18,9868 | 47,0041 | 0,3748 |
| gRPC 4MB | 1000 | 7,0154 | 6,9928 | 0,6973 | 5,9417 | 6,8828 | 7,2771 | 25,6896 | 0,3943 |

---

## 4. Etapa 2 — Boxplots (Análise Exploratória)

Como a escala de latência varia de ~0,04 ms (1 KB) a ~18,8 ms (4 MB), gera-se um boxplot dedicado para cada tamanho de payload para manter legibilidade visual.

**Abas utilizadas:** `Payload_1KB`, `Payload_100KB`, `Payload_1MB` e `Payload_4MB`.

1. Menu: **`Graph → Boxplot...`** *(PT-BR: `Gráfico → Boxplot...`)*.
2. Selecionar **`One Y → With Groups`** *(Um Y → Com Grupos)* e clicar em **OK**.
3. **Graph variables** (*Variáveis gráficas*): `Latencia_ms`.
4. **Categorical variables for grouping** (*Variáveis categóricas para agrupamento*): `Arquitetura`.
5. *(Opcional)* Em **`Data View...`**, habilitar **`Median connect line`** ou **`Mean symbol`**.
6. Exportar cada gráfico via **`Save Graph As...`** (PNG):
   - `images/boxplot_1kb.png`
   - `images/boxplot_100kb.png`
   - `images/boxplot_1mb.png`
   - `images/boxplot_4mb.png`

---

## 5. Etapa 3 — Análise de Outliers (Teste de Grubbs)

**Aba utilizada:** `Dados_Por_Grupo`

1. Menu: **`Stat → Basic Statistics → Outlier Test...`**  
   *(PT-BR: `Estat → Estatísticas Básicas → Teste de Outlier...`)*
2. **Variables** (*Variáveis*): selecionar as 8 colunas (`REST_1KB` até `gRPC_4MB`).
3. **Method** (*Método*): **`Grubbs' test`**, nível de significância `0.05`.
4. Confirmar em **OK**.
5. Figura associada no relatório: **`images/outliers_grubbs.png`**.

### Interpretação e decisão metodológica
- Todos os oito grupos apresentam $p < 0{,}05$ (`gRPC 1MB`: $G = 4{,}31$, $p = 0{,}015$; demais grupos: $p < 0{,}001$), apontando valores extremos na cauda superior (como `18,80 ms` em REST 1 MB, `47,00 ms` em REST 4 MB e `25,69 ms` em gRPC 4 MB).
- Conforme Sirqueira *et al.* (Seção 3), esses registros representam **latência de cauda (*tail latency*)** legítima do ambiente de execução (pausas do coletor de lixo do Go e escalonamento do sistema operacional), não configurando erros de coleta. Os valores são, portanto, **mantidos na amostra**, utilizando-se medianas e testes não paramétricos robustos a extremos.

---

## 6. Etapa 4 — Teste de Normalidade (Kolmogorov-Smirnov)

Com $N = 1.000 > 30$ em cada grupo, aplica-se o **Teste de Kolmogorov-Smirnov (K-S)**.

**Aba utilizada:** `Dados_Por_Grupo`

1. Menu: **`Stat → Basic Statistics → Normality Test...`**  
   *(PT-BR: `Estat → Estatísticas Básicas → Teste de Normalidade...`)*
2. **Variable** (*Variável*): executar para cada coluna (`REST_1KB` até `gRPC_4MB`).
3. **Tests for Normality** (*Testes de Normalidade*): selecionar **`Kolmogorov-Smirnov`** (alterando o padrão Anderson-Darling do Minitab).
4. Confirmar em **OK**.
5. Figuras associadas no relatório (exemplos representativos): `images/ks_rest_1kb.png`, `images/ks_grpc_1kb.png`, `images/ks_rest_1mb.png` e `images/ks_grpc_1mb.png`.

### Valores de referência (K-S)
Em **todos os 8 grupos**, obtém-se **`P-Value < 0.010`** (estatística $D$ entre `0,175` e `0,372`), rejeitando $H_0$ de normalidade e direcionando a análise para **testes não paramétricos**.

---

## 7. Etapa 5 (Complementar) — Teste de Homocedasticidade (Levene)

Embora a rejeição da normalidade já determine o uso de testes não paramétricos, o teste de Levene é aplicado complementarmente para caracterizar a dispersão entre as arquiteturas.

**Abas utilizadas:** `Payload_1KB`, `Payload_100KB`, `Payload_1MB` e `Payload_4MB`.

1. Menu: **`Stat → Basic Statistics → 2 Variances...`**  
   *(PT-BR: `Estat → Estatísticas Básicas → 2 Variâncias...`)*
2. Selecionar **`Both samples are in one column`** (*Ambas as amostras estão em uma coluna*).
   - **Samples** (*Amostras*): `Latencia_ms`
   - **Sample IDs** (*IDs da amostra*): `Arquitetura`
3. Confirmar em **OK**.
4. **Valores de referência (`Levene's Test P-Value`):** `1 KB`: $p = 0{,}0433$ (heterocedástico); `100 KB`: $p < 0{,}001$ (heterocedástico); `1 MB`: $p < 0{,}001$ (heterocedástico); `4 MB`: $p = 0{,}2690$ (homocedástico).
5. Figura associada no relatório: **`images/levene_1mb.png`**.

---

## 8. Etapa 6 — Análise 1: REST vs. gRPC por Payload (Teste de Mann-Whitney)

Avalia o fator `Arquitetura` (2 tratamentos: REST e gRPC) em cada um dos quatro tamanhos de payload.

**Aba utilizada:** `Dados_Por_Grupo`

1. Menu: **`Stat → Nonparametrics → Mann-Whitney...`**  
   *(PT-BR: `Estat → Não-paramétricos → Mann-Whitney...`)*
2. Configurar cada par com **Confidence level** `95.0` e **Alternative** `not equal` ($\eta_1 \neq \eta_2$):
   - `REST_1KB` vs. `gRPC_1KB` $\rightarrow$ `images/mw_1kb.png`
   - `REST_100KB` vs. `gRPC_100KB` $\rightarrow$ `images/mw_100kb.png`
   - `REST_1MB` vs. `gRPC_1MB` $\rightarrow$ `images/mw_1mb.png`
   - `REST_4MB` vs. `gRPC_4MB` $\rightarrow$ `images/mw_4mb.png`

### Valores de referência (Mann-Whitney)

| Payload | Mediana REST (ms) | Mediana gRPC (ms) | Estimativa $\hat{\eta}_{\text{REST}} - \hat{\eta}_{\text{gRPC}}$ (ms) | $W$ | $p$-valor | Conclusão ($\alpha = 0{,}05$) |
| :--- | ---: | ---: | ---: | ---: | ---: | :--- |
| **1 KB** | 0,0405 | 0,0403 | $+0{,}0008$ | 1.033.151,5 | **0,0115** | Rejeita $H_0$ (**gRPC** 0,62% menor; empate técnico) |
| **100 KB** | 0,4971 | 0,1958 | $+0{,}2992$ | 1.493.842,0 | **< 0,0001** | Rejeita $H_0$ (**gRPC** 60,60% menor) |
| **1 MB** | 4,6778 | 1,7422 | $+2{,}9320$ | 1.500.500,0 | **< 0,0001** | Rejeita $H_0$ (**gRPC** 62,76% menor) |
| **4 MB** | 18,7834 | 6,9928 | $+11{,}7458$ | 1.499.502,0 | **< 0,0001** | Rejeita $H_0$ (**gRPC** 62,77% menor) |

---

## 9. Etapa 7 — Análise 2: Efeito do Tamanho do Payload (Kruskal-Wallis + Pós-Teste)

Avalia o fator `Payload` (4 tratamentos: `1KB`, `100KB`, `1MB`, `4MB`) separadamente em cada arquitetura.

### 9.1 Teste de Kruskal-Wallis
**Abas utilizadas:** `Arq_REST` e `Arq_gRPC`.

1. Menu: **`Stat → Nonparametrics → Kruskal-Wallis...`**  
   *(PT-BR: `Estat → Não-paramétricos → Kruskal-Wallis...`)*
2. **Response** (*Resposta*): `Latencia_ms`.
3. **Factor** (*Fator*): `Payload`.
4. Executar para `Arq_REST` (`images/kw_rest.png`) e `Arq_gRPC` (`images/kw_grpc.png`).

**Valores de referência (Kruskal-Wallis):**
- **REST:** $H = 3.748{,}29$, $DF = 3$, **$p < 0{,}0001$** $\rightarrow$ Rejeita $H_0$.
- **gRPC:** $H = 3.749{,}06$, $DF = 3$, **$p < 0{,}0001$** $\rightarrow$ Rejeita $H_0$.

### 9.2 Pós-Teste (Mann-Whitney par-a-par)
Conforme a Seção 3.4 de `metodos-estatisticos.pdf`, após rejeição de $H_0$ no Kruskal-Wallis, aplicam-se comparações par-a-par com Mann-Whitney na aba `Dados_Por_Grupo` para todos os 6 pares (`1KB vs 100KB`, `1KB vs 1MB`, `1KB vs 4MB`, `100KB vs 1MB`, `100KB vs 4MB`, `1MB vs 4MB`) em REST e em gRPC.

**Resultado de referência:** todos os **6 pares** em ambas as arquiteturas apresentam $p < 0{,}0001$.

---

## 10. Figuras Referenciadas no Relatório LaTeX (`relatorio/main.tex`)

O projeto LaTeX espera as capturas geradas no Minitab no diretório `relatorio/images/` com os seguintes nomes:

- `images/descritiva.png` — Estatísticas Descritivas (Etapa 1)
- `images/boxplot_1kb.png`, `images/boxplot_100kb.png`, `images/boxplot_1mb.png`, `images/boxplot_4mb.png` — Boxplots por payload (Etapa 2)
- `images/outliers_grubbs.png` — Teste de Grubbs (Etapa 3)
- `images/ks_rest_1kb.png`, `images/ks_grpc_1kb.png`, `images/ks_rest_1mb.png`, `images/ks_grpc_1mb.png` — Testes de Normalidade K-S (Etapa 4)
- `images/levene_1mb.png` — Teste de Levene complementar para 1 MB (Etapa 5)
- `images/mw_1kb.png`, `images/mw_100kb.png`, `images/mw_1mb.png`, `images/mw_4mb.png` — Mann-Whitney REST vs. gRPC (Etapa 6)
- `images/kw_rest.png`, `images/kw_grpc.png` — Kruskal-Wallis por arquitetura (Etapa 7)

*(Nota técnica: `relatorio/main.tex` compila mesmo na ausência das imagens, exibindo um quadro de marcação com o nome esperado de cada arquivo até que os PNGs sejam adicionados em `images/`.)*
