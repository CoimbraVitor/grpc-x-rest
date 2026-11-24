"""
Consolida os CSVs gerados pelos benchmarks em Go (REST e gRPC),
exporta arquivos prontos para importação no Minitab (.csv e .xlsx)
e executa a validação estatística seguindo fielmente a árvore de decisão
de Sirqueira et al. (metodos-estatisticos.pdf).
"""

import json
import math
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats

RESULTS_DIR = Path("results")
PAYLOAD_ORDER = ["1KB", "100KB", "1MB", "4MB"]
ARCH_ORDER = ["REST", "gRPC"]


def grubbs_test(x: np.ndarray, alpha: float = 0.05) -> dict:
    """Two-sided Grubbs' test for a single outlier (matches Minitab Outlier Test)."""
    n = len(x)
    mean = float(np.mean(x))
    std = float(np.std(x, ddof=1))
    if std == 0:
        return {"G": 0.0, "G_crit": 0.0, "p_value": 1.0, "has_outlier": False, "extreme_value": mean}
    abs_dev = np.abs(x - mean)
    idx = int(np.argmax(abs_dev))
    G = float(abs_dev[idx] / std)

    # Critical value
    t_crit = stats.t.ppf(1 - alpha / (2 * n), df=n - 2)
    G_crit = ((n - 1) / math.sqrt(n)) * math.sqrt(t_crit**2 / (n - 2 + t_crit**2))

    # Approximate two-sided p-value (exact upper bound used by Minitab)
    denom = ((n - 1) ** 2 / n) - G**2
    if denom <= 0:
        p_val = 0.0
    else:
        t_stat = math.sqrt((n - 2) * G**2 / denom)
        p_val = min(1.0, 2 * n * float(stats.t.sf(t_stat, df=n - 2)))

    return {
        "G": round(G, 4),
        "G_crit": round(G_crit, 4),
        "p_value": round(p_val, 6),
        "has_outlier": bool(G > G_crit),
        "extreme_value": round(float(x[idx]), 6),
    }


def iqr_outliers(x: np.ndarray) -> dict:
    q1, q3 = np.percentile(x, [25, 75])
    iqr = q3 - q1
    mild_low, mild_high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    ext_low, ext_high = q1 - 3.0 * iqr, q3 + 3.0 * iqr
    mild_count = int(np.sum((x < mild_low) | (x > mild_high)))
    ext_count = int(np.sum((x < ext_low) | (x > ext_high)))
    return {
        "Q1": round(float(q1), 6),
        "Q3": round(float(q3), 6),
        "IQR": round(float(iqr), 6),
        "mild_outliers_1_5_iqr": mild_count,
        "extreme_outliers_3_0_iqr": ext_count,
        "mild_pct": round(100.0 * mild_count / len(x), 2),
        "extreme_pct": round(100.0 * ext_count / len(x), 2),
    }


def ks_normality(x: np.ndarray) -> dict:
    """Kolmogorov-Smirnov normality test (using sample mean and std, as in Minitab)."""
    mean = float(np.mean(x))
    std = float(np.std(x, ddof=1))
    z = (x - mean) / std
    stat, p_std = stats.kstest(z, "norm")
    # Anderson-Darling (Minitab default alternative) for cross-check
    ad_res = stats.anderson(x, dist="norm", method="interpolate")
    # Lilliefors approximation for large N: D_crit(alpha=0.05) ~ 0.886 / sqrt(N)
    n = len(x)
    d_crit_lilliefors_05 = 0.886 / math.sqrt(n)
    return {
        "KS_stat": round(float(stat), 5),
        "KS_p_value_scipy": round(float(p_std), 6),
        "Lilliefors_crit_05": round(float(d_crit_lilliefors_05), 5),
        "normal_at_05": bool(stat < d_crit_lilliefors_05 and p_std > 0.05),
        "AD_stat": round(float(ad_res.statistic), 4),
    }


def describe_array(x: np.ndarray) -> dict:
    q1, med, q3 = np.percentile(x, [25, 50, 75])
    p95, p99 = np.percentile(x, [95, 99])
    return {
        "N": int(len(x)),
        "mean": round(float(np.mean(x)), 6),
        "median": round(float(med), 6),
        "std": round(float(np.std(x, ddof=1)), 6),
        "variance": round(float(np.var(x, ddof=1)), 6),
        "min": round(float(np.min(x)), 6),
        "Q1": round(float(q1), 6),
        "Q3": round(float(q3), 6),
        "max": round(float(np.max(x)), 6),
        "range": round(float(np.max(x) - np.min(x)), 6),
        "IQR": round(float(q3 - q1), 6),
        "P95": round(float(p95), 6),
        "P99": round(float(p99), 6),
    }


def hodges_lehmann_diff(x: np.ndarray, y: np.ndarray) -> float:
    """Point estimate of median(x_i - y_j) matching Minitab Mann-Whitney output."""
    # Exact for n=1000 (1e6 differences fits easily in ~8 MB RAM).
    diffs = x[:, None] - y[None, :]
    return round(float(np.median(diffs)), 6)


def main():
    rest_path = RESULTS_DIR / "raw_rest.csv"
    grpc_path = RESULTS_DIR / "raw_grpc.csv"
    if not rest_path.exists() or not grpc_path.exists():
        raise FileNotFoundError("Execute primeiro os benchmarks REST e gRPC para gerar raw_rest.csv e raw_grpc.csv.")

    df_rest = pd.read_csv(rest_path)
    df_grpc = pd.read_csv(grpc_path)
    df = pd.concat([df_rest, df_grpc], ignore_index=True)

    # Ensure deterministic ordering
    df["payload_label"] = pd.Categorical(df["payload_label"], categories=PAYLOAD_ORDER, ordered=True)
    df["arquitetura"] = pd.Categorical(df["arquitetura"], categories=ARCH_ORDER, ordered=True)
    df = df.sort_values(["payload_label", "arquitetura", "iteracao"]).reset_index(drop=True)

    # 1) Stacked dataset (for Minitab Boxplot With Groups, Descriptive By Variables, Kruskal-Wallis, Levene)
    stacked = df.rename(columns={
        "arquitetura": "Arquitetura",
        "payload_label": "Payload",
        "payload_target_bytes": "Payload_Alvo_Bytes",
        "item_count": "Qtd_Itens",
        "wire_bytes": "Tamanho_Wire_Bytes",
        "iteracao": "Iteracao",
        "latencia_ms": "Latencia_ms",
    })
    stacked["Grupo"] = stacked["Arquitetura"].astype(str) + "_" + stacked["Payload"].astype(str)
    stacked.to_csv(RESULTS_DIR / "dados_empilhados.csv", index=False)

    # 2) Unstacked dataset (columns per group - ideal for Minitab Normality Test, Outlier Test, Mann-Whitney)
    unstacked_cols = {}
    for pl in PAYLOAD_ORDER:
        for arch in ARCH_ORDER:
            sub = df[(df["payload_label"] == pl) & (df["arquitetura"] == arch)].sort_values("iteracao")
            unstacked_cols[f"{arch}_{pl}"] = sub["latencia_ms"].to_numpy()
    df_unstacked = pd.DataFrame(unstacked_cols)
    df_unstacked.to_csv(RESULTS_DIR / "dados_por_grupo.csv", index=False)

    # 3) Scenario summary (wire size comparison)
    summary_rows = []
    for pl in PAYLOAD_ORDER:
        r_sub = df[(df["payload_label"] == pl) & (df["arquitetura"] == "REST")]
        g_sub = df[(df["payload_label"] == pl) & (df["arquitetura"] == "gRPC")]
        r_wire = int(r_sub["wire_bytes"].iloc[0])
        g_wire = int(g_sub["wire_bytes"].iloc[0])
        items = int(r_sub["item_count"].iloc[0])
        reduction_pct = round(100.0 * (1.0 - g_wire / r_wire), 2)
        summary_rows.append({
            "Payload": pl,
            "Qtd_Itens": items,
            "REST_JSON_Bytes": r_wire,
            "gRPC_Protobuf_Bytes": g_wire,
            "Reducao_Tamanho_Protobuf_Pct": reduction_pct,
        })
    df_summary = pd.DataFrame(summary_rows)

    # 4) Export Excel workbook for seamless Minitab import (no decimal separator headaches!)
    xlsx_path = RESULTS_DIR / "dados_experimento_minitab.xlsx"
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        stacked.to_excel(writer, sheet_name="Dados_Empilhados", index=False)
        df_unstacked.to_excel(writer, sheet_name="Dados_Por_Grupo", index=False)
        # Separate sheets per payload for super easy 1-factor 2-treatment analyses in Minitab
        for pl in PAYLOAD_ORDER:
            sub_pl = stacked[stacked["Payload"] == pl][["Arquitetura", "Latencia_ms", "Iteracao"]]
            sub_pl.to_excel(writer, sheet_name=f"Payload_{pl}", index=False)
        # Separate sheets per architecture for 1-factor >2-treatments (effect of payload size)
        for arch in ARCH_ORDER:
            sub_arch = stacked[stacked["Arquitetura"] == arch][["Payload", "Latencia_ms", "Iteracao"]]
            sub_arch.to_excel(writer, sheet_name=f"Arq_{arch}", index=False)
        df_summary.to_excel(writer, sheet_name="Resumo_Wire_Bytes", index=False)

    # 5) Full Statistical Analysis following Sirqueira et al. Decision Tree
    report = {
        "total_observations": int(len(df)),
        "wire_summary": summary_rows,
        "groups": {},
        "comparisons_arch_by_payload": {},
        "comparisons_payload_by_arch": {},
    }

    for pl in PAYLOAD_ORDER:
        for arch in ARCH_ORDER:
            key = f"{arch}_{pl}"
            arr = unstacked_cols[key]
            report["groups"][key] = {
                "descriptive": describe_array(arr),
                "outliers_iqr": iqr_outliers(arr),
                "outliers_grubbs": grubbs_test(arr),
                "normality_ks": ks_normality(arr),
            }

    # Analysis A: 1 Factor (Architecture), 2 Treatments (REST vs gRPC) for each payload size
    for pl in PAYLOAD_ORDER:
        r_arr = unstacked_cols[f"REST_{pl}"]
        g_arr = unstacked_cols[f"gRPC_{pl}"]

        both_normal = (
            report["groups"][f"REST_{pl}"]["normality_ks"]["normal_at_05"]
            and report["groups"][f"gRPC_{pl}"]["normality_ks"]["normal_at_05"]
        )
        lev_stat, lev_p = stats.levene(r_arr, g_arr, center="median")
        homoscedastic = bool(lev_p > 0.05)

        t_stat, t_p = stats.ttest_ind(r_arr, g_arr, equal_var=homoscedastic)
        u_stat, mw_p = stats.mannwhitneyu(r_arr, g_arr, alternative="two-sided")
        # Minitab reports W = sum of ranks of first sample = U + n1*(n1+1)/2
        n1 = len(r_arr)
        w_minitab = float(u_stat + n1 * (n1 + 1) / 2.0)
        hl_diff = hodges_lehmann_diff(r_arr, g_arr)

        med_r = float(np.median(r_arr))
        med_g = float(np.median(g_arr))
        mean_r = float(np.mean(r_arr))
        mean_g = float(np.mean(g_arr))

        winner_median = "gRPC" if med_g < med_r else "REST"
        speedup_median = round(med_r / med_g, 3) if med_g > 0 else None
        pct_diff_median = round(100.0 * (med_r - med_g) / med_r, 2)

        recommended_test = "Teste T (2-Sample t)" if (both_normal and homoscedastic) else "Teste de Mann-Whitney"

        report["comparisons_arch_by_payload"][pl] = {
            "both_normal": both_normal,
            "levene_stat": round(float(lev_stat), 4),
            "levene_p": round(float(lev_p), 6),
            "homoscedastic": homoscedastic,
            "recommended_test": recommended_test,
            "t_test": {"t_stat": round(float(t_stat), 4), "p_value": round(float(t_p), 6)},
            "mann_whitney": {
                "U_stat": round(float(u_stat), 2),
                "W_minitab": round(w_minitab, 1),
                "p_value": round(float(mw_p), 6),
                "hodges_lehmann_REST_minus_gRPC_ms": hl_diff,
            },
            "median_REST_ms": round(med_r, 4),
            "median_gRPC_ms": round(med_g, 4),
            "mean_REST_ms": round(mean_r, 4),
            "mean_gRPC_ms": round(mean_g, 4),
            "winner_by_median": winner_median,
            "ratio_REST_over_gRPC_median": speedup_median,
            "gRPC_reduction_vs_REST_median_pct": pct_diff_median,
        }

    # Analysis B: 1 Factor (Payload Size), 4 Treatments (1KB, 100KB, 1MB, 4MB) within each architecture
    for arch in ARCH_ORDER:
        arrays = [unstacked_cols[f"{arch}_{pl}"] for pl in PAYLOAD_ORDER]
        all_normal = all(report["groups"][f"{arch}_{pl}"]["normality_ks"]["normal_at_05"] for pl in PAYLOAD_ORDER)
        lev_stat, lev_p = stats.levene(*arrays, center="median")
        homoscedastic = bool(lev_p > 0.05)

        f_stat, anova_p = stats.f_oneway(*arrays)
        h_stat, kw_p = stats.kruskal(*arrays)

        recommended_test = "ANOVA One-Way + Tukey" if (all_normal and homoscedastic) else "Kruskal-Wallis + Mann-Whitney par-a-par"

        # Pairwise Mann-Whitney post-hoc
        pairwise = {}
        for i in range(len(PAYLOAD_ORDER)):
            for j in range(i + 1, len(PAYLOAD_ORDER)):
                p1, p2 = PAYLOAD_ORDER[i], PAYLOAD_ORDER[j]
                u_ij, p_ij = stats.mannwhitneyu(arrays[i], arrays[j], alternative="two-sided")
                pairwise[f"{p1}_vs_{p2}"] = {
                    "U_stat": round(float(u_ij), 2),
                    "p_value": round(float(p_ij), 6),
                    "significant_05": bool(p_ij < 0.05),
                }

        report["comparisons_payload_by_arch"][arch] = {
            "all_normal": all_normal,
            "levene_stat": round(float(lev_stat), 4),
            "levene_p": round(float(lev_p), 6),
            "homoscedastic": homoscedastic,
            "recommended_test": recommended_test,
            "anova": {"F_stat": round(float(f_stat), 4), "p_value": round(float(anova_p), 6)},
            "kruskal_wallis": {"H_stat": round(float(h_stat), 4), "df": len(PAYLOAD_ORDER) - 1, "p_value": round(float(kw_p), 6)},
            "pairwise_mann_whitney": pairwise,
        }

    json_out = RESULTS_DIR / "analise_estatistica_validacao.json"
    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    # 6) Export ready-to-paste LaTeX summary (with ABNT decimal commas) for easy update after MacBook run
    def br(val: float, dec: int = 4) -> str:
        return f"{val:.{dec}f}".replace(".", ",")

    def br_int(val: int) -> str:
        return f"{val:,}".replace(",", ".")

    latex_lines = [
        "% ===========================================================================",
        "% RESUMO PRONTO PARA COLAR NO relatorio/main.tex (gerado automaticamente)",
        f"% Total de observacoes: {report['total_observations']}",
        "% ===========================================================================",
        "",
        "% --- TABELA: Estatisticas Descritivas (ms) ---",
    ]
    for pl in PAYLOAD_ORDER:
        for arch in ARCH_ORDER:
            d = report["groups"][f"{arch}_{pl}"]["descriptive"]
            latex_lines.append(
                f"{pl} & {arch} & {br(d['mean'])} & {br(d['median'])} & {br(d['std'])} & "
                f"{br(d['variance'])} & {br(d['min'])} & {br(d['Q1'])} & {br(d['Q3'])} & "
                f"{br(d['max'])} & {br(d['IQR'])} & {br(d['P95'])} \\\\"
            )

    latex_lines += ["", "% --- TABELA: Outliers (Grubbs e IQR) ---"]
    for pl in PAYLOAD_ORDER:
        for arch in ARCH_ORDER:
            gr = report["groups"][f"{arch}_{pl}"]["outliers_grubbs"]
            iq = report["groups"][f"{arch}_{pl}"]["outliers_iqr"]
            p_str = "$< 0,001$" if gr["p_value"] < 0.001 else br(gr["p_value"], 3)
            latex_lines.append(
                f"{pl} & {arch} & {br(gr['G'], 2)} & {p_str} & {br(gr['extreme_value'])} & "
                f"{iq['mild_outliers_1_5_iqr']} ({br(iq['mild_pct'], 1)}\\%) & "
                f"{iq['extreme_outliers_3_0_iqr']} ({br(iq['extreme_pct'], 1)}\\%) \\\\"
            )

    latex_lines += ["", "% --- TABELA: Normalidade (K-S) e Homocedasticidade (Levene) ---"]
    for pl in PAYLOAD_ORDER:
        comp = report["comparisons_arch_by_payload"][pl]
        lev_p_str = "$< 0,001$" if comp["levene_p"] < 0.001 else br(comp["levene_p"], 4)
        for arch in ARCH_ORDER:
            ks = report["groups"][f"{arch}_{pl}"]["normality_ks"]
            ks_p_str = "$< 0,010$" if not ks["normal_at_05"] else "$> 0,050$"
            norm_str = "Sim" if ks["normal_at_05"] else "Não"
            hom_str = "Sim" if comp["homoscedastic"] else "Não"
            latex_lines.append(
                f"{pl} & {arch} & {br(ks['KS_stat'], 3)} & {ks_p_str} & {norm_str} & {lev_p_str} & {hom_str} \\\\"
            )

    latex_lines += ["", "% --- TABELA: Analise 1 - REST vs gRPC por Payload ---"]
    for pl in PAYLOAD_ORDER:
        c = report["comparisons_arch_by_payload"][pl]
        mw = c["mann_whitney"]
        p_str = "$< 0,0001$" if mw["p_value"] < 0.0001 else br(mw["p_value"], 6)
        w_str = f"{mw['W_minitab']:,.1f}".replace(",", "X").replace(".", ",").replace("X", ".")
        sign = "+" if mw["hodges_lehmann_REST_minus_gRPC_ms"] >= 0 else "-"
        hl_abs = br(abs(mw["hodges_lehmann_REST_minus_gRPC_ms"]))
        pct_sign = "+" if c["gRPC_reduction_vs_REST_median_pct"] >= 0 else "-"
        pct_abs = br(abs(c["gRPC_reduction_vs_REST_median_pct"]), 2)
        latex_lines.append(
            f"{pl} & {br(c['median_REST_ms'])} & {br(c['median_gRPC_ms'])} & "
            f"${sign}{hl_abs}$ & {w_str} & {p_str} & ${pct_sign}{pct_abs}\\%$ & "
            f"\\textbf{{{c['winner_by_median']}}} ({c['recommended_test']}) \\\\"
        )

    latex_lines += ["", "% --- TABELA: Analise 2 - Efeito do Payload por Arquitetura ---"]
    for arch in ARCH_ORDER:
        c = report["comparisons_payload_by_arch"][arch]
        kw = c["kruskal_wallis"]
        p_str = "$< 0,0001$" if kw["p_value"] < 0.0001 else br(kw["p_value"], 6)
        h_str = f"{kw['H_stat']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        sig_count = sum(1 for v in c["pairwise_mann_whitney"].values() if v["significant_05"])
        latex_lines.append(
            f"{arch} & {h_str} & {kw['df']} & {p_str} & {sig_count}/6 pares significativos ({c['recommended_test']}) \\\\"
        )

    latex_summary_path = RESULTS_DIR / "resumo_tabelas_latex.txt"
    latex_summary_path.write_text("\n".join(latex_lines) + "\n", encoding="utf-8")

    # Print clean console summary
    print("=" * 72)
    print(f"ANALISE ESTATISTICA CONCLUIDA ({report['total_observations']} observacoes)")
    print("=" * 72)
    print("\n--- Tamanho na Rede (JSON vs Protobuf) ---")
    print(df_summary.to_string(index=False))

    print("\n--- Estatistica Descritiva & Normalidade (K-S) ---")
    for pl in PAYLOAD_ORDER:
        for arch in ARCH_ORDER:
            g = report["groups"][f"{arch}_{pl}"]
            d = g["descriptive"]
            ks = g["normality_ks"]
            gr = g["outliers_grubbs"]
            iq = g["outliers_iqr"]
            print(
                f"{arch:4s} {pl:5s} | Mediana={d['median']:8.4f} ms | Media={d['mean']:8.4f} ms | "
                f"DP={d['std']:7.4f} | IQR={d['IQR']:7.4f} | KS={ks['KS_stat']:.4f} (Normal={ks['normal_at_05']}) | "
                f"Grubbs_p={gr['p_value']:.4f} | IQR_out={iq['mild_outliers_1_5_iqr']} ({iq['mild_pct']}%)"
            )

    print("\n--- Analise 1: REST vs gRPC por Payload (1 Fator, 2 Tratamentos) ---")
    for pl, res in report["comparisons_arch_by_payload"].items():
        print(
            f"Payload {pl:5s} | Teste: {res['recommended_test']:22s} | "
            f"Mediana REST={res['median_REST_ms']:.4f} vs gRPC={res['median_gRPC_ms']:.4f} ms | "
            f"Vencedor={res['winner_by_median']} ({res['gRPC_reduction_vs_REST_median_pct']:+.2f}%) | "
            f"MW p={res['mann_whitney']['p_value']:.6f} | Levene p={res['levene_p']:.6f}"
        )

    print("\n--- Analise 2: Efeito do Payload por Arquitetura (1 Fator, 4 Tratamentos) ---")
    for arch, res in report["comparisons_payload_by_arch"].items():
        print(
            f"Arq {arch:4s} | Teste: {res['recommended_test']} | "
            f"KW H={res['kruskal_wallis']['H_stat']:.2f}, p={res['kruskal_wallis']['p_value']:.6f} | "
            f"Levene p={res['levene_p']:.6f}"
        )

    print(f"\nArquivos exportados em: {RESULTS_DIR.resolve()}")
    print(f"  - {xlsx_path.name} (Abrir direto no Minitab!)")
    print(f"  - dados_empilhados.csv")
    print(f"  - dados_por_grupo.csv")
    print(f"  - {json_out.name}")


if __name__ == "__main__":
    main()
