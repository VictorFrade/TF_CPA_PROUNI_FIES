"""
Script consolidado — todas as correlações do projeto
Avaliação da efetividade do PROUNI e FIES na universalização da educação superior
Fonte: Censo da Educação Superior (INEP), arquivo MICRODADOS_CADASTRO_CURSOS, 2010-2024

Estrutura do script:
  1. Configuração e carga dos dados
  2. Função base — cálculo de evasão por curso (método do fluxo agregado)
  3. Evasão média por modalidade / grau acadêmico / categoria administrativa
  4. Correlações específicas PROUNI e FIES (6 correlações)
  5. Correlações de políticas afirmativas (5 critérios de reserva de vagas)
  6. Correlações estratificadas por setor (público x privado)
  7. Correlações estratificadas por região e esfera administrativa (público)

Requisitos: pandas, numpy, scipy
  pip install pandas numpy scipy --break-system-packages
"""

import pandas as pd
import numpy as np
from scipy import stats

# ═══════════════════════════════════════════════════════════════
# 1. CONFIGURAÇÃO
# ═══════════════════════════════════════════════════════════════

# Diretório onde estão os arquivos MICRODADOS_CADASTRO_CURSOS_AAAA_FILTRADO.csv
DIRETORIO = "." # Caminho varia de acordo com o usuário; ajuste conforme necessário.

# Anos disponíveis (ajuste conforme os arquivos que você tiver)
ANOS = list(range(2009, 2025))

# Chave que identifica um curso de forma única.
# IMPORTANTE: CO_IES + CO_CURSO sozinhos NÃO são únicos — cursos EaD são
# replicados por município de oferta (polo). É necessário incluir
# CO_MUNICIPIO na chave.
CHAVE_CURSO = ["CO_IES", "CO_CURSO", "CO_MUNICIPIO"]

# Tamanho mínimo de alunos na base de cálculo — cursos menores que isso
# geram taxas de evasão instáveis (ex.: 1 ingressante que evade = 100%)
MIN_ALUNOS = 10

# Mapas de tradução de códigos para rótulos legíveis
MAPA_MODALIDADE = {1: "Presencial", 2: "EaD"}
MAPA_GRAU = {1: "Bacharelado", 2: "Licenciatura", 3: "Tecnológico", 4: "N/A"}
MAPA_CATEGORIA = {
    1: "Pública Federal", 2: "Pública Estadual", 3: "Pública Municipal",
    4: "Privada com fins lucrativos", 5: "Privada sem fins lucrativos", 7: "Especial",
}
MAPA_ESFERA_PUBLICA = {1: "Federal", 2: "Estadual", 3: "Municipal"}


def carregar_dados(anos=ANOS, diretorio=DIRETORIO):
    """Carrega todos os arquivos filtrados em um dicionário {ano: DataFrame}."""
    dfs = {}
    for ano in anos:
        caminho = f"{diretorio}/MICRODADOS_CADASTRO_CURSOS_{ano}_FILTRADO.csv"
        dfs[ano] = pd.read_csv(caminho, sep=";", low_memory=False)
    return dfs


def coluna_etnico(df):
    """RVETNICO foi usado até 2023; RVPPI é o equivalente a partir de 2024."""
    return "QT_ING_RVETNICO" if "QT_ING_RVETNICO" in df.columns else "QT_ING_RVPPI"


# ═══════════════════════════════════════════════════════════════
# 2. FUNÇÃO BASE — EVASÃO POR CURSO (método do fluxo agregado)
#
#    TE = 1 - (QT_CONC_t + QT_MAT_t) / (QT_ING_t + QT_MAT_t-1)
# ═══════════════════════════════════════════════════════════════

def montar_base_evasao(df_at, df_ant, colunas_extra=None):
    """
    Cruza o ano atual (t) com o ano anterior (t-1) pela chave do curso
    e calcula a taxa de evasão agregada. `colunas_extra` permite trazer
    colunas adicionais do ano atual (ex.: modalidade, categoria, região)
    para uso em correlações e segmentações.
    """
    colunas_extra = colunas_extra or []
    cols_at = CHAVE_CURSO + ["QT_ING", "QT_MAT", "QT_CONC"] + colunas_extra
    cols_at = list(dict.fromkeys(cols_at))  # remove duplicatas preservando ordem

    base_at = df_at[cols_at].copy()
    base_ant = df_ant[CHAVE_CURSO + ["QT_MAT"]].rename(columns={"QT_MAT": "QT_MAT_ANT"})
    base_ant = base_ant.merge(df_ant[CHAVE_CURSO + ["QT_CONC"]].rename(columns={"QT_CONC": "QT_CONC_ANT"}), on=CHAVE_CURSO, how="inner")

    cursos = base_at.merge(base_ant, on=CHAVE_CURSO, how="inner")
    cursos["DENOM"] = cursos["QT_MAT_ANT"] - cursos["QT_CONC_ANT"]
    cursos = cursos[cursos["DENOM"] >= MIN_ALUNOS].copy()
    cursos["TE_GERAL"] = 1 - (cursos["QT_MAT"] - cursos["QT_ING"]) / cursos["DENOM"]

    return cursos


# ═══════════════════════════════════════════════════════════════
# 3. EVASÃO MÉDIA POR MODALIDADE / GRAU / CATEGORIA ADMINISTRATIVA
# ═══════════════════════════════════════════════════════════════

def evasao_por_categoria(dfs, anos=None):
    """
    Retorna um DataFrame com a evasão média por ano, segmentada por
    modalidade de ensino, grau acadêmico e categoria administrativa.
    """
    anos = anos or [a for a in ANOS if a - 1 in dfs and a in dfs]
    linhas = []

    for ano_at in anos:
        ano_ant = ano_at - 1
        if ano_ant not in dfs:
            continue

        colunas_extra = ["TP_MODALIDADE_ENSINO", "TP_GRAU_ACADEMICO", "TP_CATEGORIA_ADMINISTRATIVA"]
        cursos = montar_base_evasao(dfs[ano_at], dfs[ano_ant], colunas_extra)

        cursos["MOD"] = cursos["TP_MODALIDADE_ENSINO"].map(MAPA_MODALIDADE)
        cursos["GRAU"] = cursos["TP_GRAU_ACADEMICO"].map(MAPA_GRAU)
        cursos["CAT"] = cursos["TP_CATEGORIA_ADMINISTRATIVA"].map(MAPA_CATEGORIA)

        med_mod = cursos.groupby("MOD")["TE_GERAL"].mean() * 100
        med_grau = cursos.groupby("GRAU")["TE_GERAL"].mean() * 100
        med_cat = cursos.groupby("CAT")["TE_GERAL"].mean() * 100

        linhas.append({
            "ano": ano_at, "N": len(cursos),
            "presencial": med_mod.get("Presencial"), "ead": med_mod.get("EaD"),
            "bacharelado": med_grau.get("Bacharelado"),
            "licenciatura": med_grau.get("Licenciatura"),
            "tecnologico": med_grau.get("Tecnológico"),
            "pub_federal": med_cat.get("Pública Federal"),
            "pub_estadual": med_cat.get("Pública Estadual"),
            "pub_municipal": med_cat.get("Pública Municipal"),
            "priv_lucrativa": med_cat.get("Privada com fins lucrativos"),
            "priv_nao_lucrativa": med_cat.get("Privada sem fins lucrativos"),
        })

    return pd.DataFrame(linhas)


# ═══════════════════════════════════════════════════════════════
# 4. CORRELAÇÕES ESPECÍFICAS PROUNI E FIES
#    [1] %PROUNI x evasão geral   [2] %FIES x evasão geral
#    [3] Evasão PROUNI x evasão geral (mesmo curso)
#    [4] Evasão FIES x evasão geral (mesmo curso)
#    [5] %PROUNI x %FIES (sobreposição)
#    [6] %Financiado total x evasão geral
# ═══════════════════════════════════════════════════════════════

def montar_base_prouni_fies(df_at, df_ant):
    colunas_extra = [
        "QT_ING_PROUNII", "QT_ING_PROUNIP", "QT_MAT_PROUNII", "QT_MAT_PROUNIP",
        "QT_CONC_PROUNII", "QT_CONC_PROUNIP", "QT_ING_FIES", "QT_MAT_FIES", "QT_CONC_FIES",
    ]
    cursos = montar_base_evasao(df_at, df_ant, colunas_extra)

    # Matrícula do ano anterior para PROUNI e FIES (para evasão específica)
    base_ant_extra = df_ant[CHAVE_CURSO + ["QT_MAT_PROUNII", "QT_MAT_PROUNIP", "QT_MAT_FIES"]].rename(
        columns={"QT_MAT_PROUNII": "QT_MAT_PROUNII_ANT", "QT_MAT_PROUNIP": "QT_MAT_PROUNIP_ANT",
                 "QT_MAT_FIES": "QT_MAT_FIES_ANT"}
    )
    cursos = cursos.merge(base_ant_extra, on=CHAVE_CURSO, how="left")

    cursos["ING_PROUNI"] = cursos["QT_ING_PROUNII"] + cursos["QT_ING_PROUNIP"]
    cursos["MAT_PROUNI"] = cursos["QT_MAT_PROUNII"] + cursos["QT_MAT_PROUNIP"]
    cursos["MAT_PROUNI_ANT"] = cursos["QT_MAT_PROUNII_ANT"] + cursos["QT_MAT_PROUNIP_ANT"]
    cursos["CONC_PROUNI"] = cursos["QT_CONC_PROUNII"] + cursos["QT_CONC_PROUNIP"]
    cursos["DENOM_PROUNI"] = cursos["ING_PROUNI"] + cursos["MAT_PROUNI_ANT"]
    cursos["DENOM_FIES"] = cursos["QT_ING_FIES"] + cursos["QT_MAT_FIES_ANT"]

    cursos["PROP_PROUNI"] = np.where(cursos["QT_ING"] > 0, cursos["ING_PROUNI"] / cursos["QT_ING"], np.nan)
    cursos["PROP_FIES"] = np.where(cursos["QT_ING"] > 0, cursos["QT_ING_FIES"] / cursos["QT_ING"], np.nan)

    cursos["TE_PROUNI"] = np.where(
        cursos["DENOM_PROUNI"] >= 5,
        1 - (cursos["CONC_PROUNI"] + cursos["MAT_PROUNI"]) / cursos["DENOM_PROUNI"], np.nan
    )
    cursos["TE_FIES"] = np.where(
        cursos["DENOM_FIES"] >= 5,
        1 - (cursos["QT_CONC_FIES"] + cursos["QT_MAT_FIES"]) / cursos["DENOM_FIES"], np.nan
    )
    return cursos


def correlacoes_prouni_fies(dfs, anos=None):
    """Calcula as 6 correlações PROUNI/FIES para cada par de anos consecutivos."""
    anos = anos or [a for a in ANOS if a - 1 in dfs and a in dfs]
    linhas = []

    for ano_at in anos:
        ano_ant = ano_at - 1
        if ano_ant not in dfs:
            continue

        cursos = montar_base_prouni_fies(dfs[ano_at], dfs[ano_ant])
        entrada = {"ano": ano_at, "N": len(cursos)}

        # [1] %PROUNI x evasão geral
        sub = cursos.dropna(subset=["PROP_PROUNI", "TE_GERAL"])
        entrada["corr_prouni_evasaogeral"] = stats.spearmanr(sub["PROP_PROUNI"], sub["TE_GERAL"])[0] if len(sub) > 2 else None

        # [2] %FIES x evasão geral
        sub = cursos.dropna(subset=["PROP_FIES", "TE_GERAL"])
        entrada["corr_fies_evasaogeral"] = stats.spearmanr(sub["PROP_FIES"], sub["TE_GERAL"])[0] if len(sub) > 2 else None

        # [3] Evasão PROUNI x evasão geral (mesmo curso)
        sub = cursos.dropna(subset=["TE_PROUNI", "TE_GERAL"])
        if len(sub) > 2:
            entrada["corr_evasaoprouni_evasaogeral"] = stats.pearsonr(sub["TE_PROUNI"], sub["TE_GERAL"])[0]
            entrada["evasao_prouni_pct"] = sub["TE_PROUNI"].mean() * 100
        else:
            entrada["corr_evasaoprouni_evasaogeral"] = entrada["evasao_prouni_pct"] = None

        # [4] Evasão FIES x evasão geral (mesmo curso)
        sub = cursos.dropna(subset=["TE_FIES", "TE_GERAL"])
        if len(sub) > 2:
            entrada["corr_evasaofies_evasaogeral"] = stats.pearsonr(sub["TE_FIES"], sub["TE_GERAL"])[0]
            entrada["evasao_fies_pct"] = sub["TE_FIES"].mean() * 100
        else:
            entrada["corr_evasaofies_evasaogeral"] = entrada["evasao_fies_pct"] = None

        # [5] %PROUNI x %FIES (sobreposição de público)
        sub = cursos.dropna(subset=["PROP_PROUNI", "PROP_FIES"])
        entrada["corr_prouni_fies"] = stats.spearmanr(sub["PROP_PROUNI"], sub["PROP_FIES"])[0] if len(sub) > 2 else None

        # [6] %Financiado total (PROUNI+FIES) x evasão geral
        cursos["PROP_FINANC"] = cursos["PROP_PROUNI"].fillna(0) + cursos["PROP_FIES"].fillna(0)
        sub = cursos.dropna(subset=["TE_GERAL"])
        entrada["corr_financtotal_evasaogeral"] = stats.spearmanr(sub["PROP_FINANC"], sub["TE_GERAL"])[0] if len(sub) > 2 else None

        linhas.append(entrada)

    return pd.DataFrame(linhas)


# ═══════════════════════════════════════════════════════════════
# 5. CORRELAÇÕES DE POLÍTICAS AFIRMATIVAS
#    Reserva total, escola pública, social/renda, étnico-racial, PCD
# ═══════════════════════════════════════════════════════════════

CRITERIOS_AFIRMATIVOS = [
    ("QT_ING_RESERVA_VAGA", "reserva_total"),
    ("QT_ING_RVREDEPUBLICA", "escola_publica"),
    ("QT_ING_RVSOCIAL_RF", "social_renda"),
    ("QT_ING_RVPDEF", "pcd"),
]


def montar_base_afirmativas(df_at, df_ant):
    col_et = coluna_etnico(df_at)
    colunas_extra = [c for c, _ in CRITERIOS_AFIRMATIVOS] + [col_et, "TP_CATEGORIA_ADMINISTRATIVA", "NO_REGIAO"]
    cursos = montar_base_evasao(df_at, df_ant, colunas_extra)
    cursos = cursos.rename(columns={col_et: "QT_ING_RVETNICO_PPI"})

    criterios = CRITERIOS_AFIRMATIVOS + [("QT_ING_RVETNICO_PPI", "etnico_racial")]
    for col, label in criterios:
        cursos[f"PROP_{label}"] = np.where(cursos["QT_ING"] > 0, cursos[col] / cursos["QT_ING"], np.nan)

    cursos["SETOR"] = np.where(
        cursos["TP_CATEGORIA_ADMINISTRATIVA"].isin([1, 2, 3]), "Pública",
        np.where(cursos["TP_CATEGORIA_ADMINISTRATIVA"].isin([4, 5]), "Privada", "Outra")
    )
    cursos["ESFERA_PUBLICA"] = cursos["TP_CATEGORIA_ADMINISTRATIVA"].map(MAPA_ESFERA_PUBLICA)
    return cursos


def correlacoes_afirmativas(dfs, anos=None, setor=None):
    """
    Calcula a correlação de Spearman entre proporção de cotistas (por
    critério) e evasão geral do curso, para cada ano.
    `setor`: None (todos os cursos), "Pública" ou "Privada" para filtrar.
    """
    anos = anos or [a for a in ANOS if a - 1 in dfs and a in dfs]
    criterios = CRITERIOS_AFIRMATIVOS + [("QT_ING_RVETNICO_PPI", "etnico_racial")]
    linhas = []

    for ano_at in anos:
        ano_ant = ano_at - 1
        if ano_ant not in dfs:
            continue

        cursos = montar_base_afirmativas(dfs[ano_at], dfs[ano_ant])
        if setor:
            cursos = cursos[cursos["SETOR"] == setor]

        entrada = {"ano": ano_at, "N": len(cursos)}
        for _, label in criterios:
            prop_col = f"PROP_{label}"
            sub = cursos.dropna(subset=[prop_col, "TE_GERAL"])
            if len(sub) > 5 and sub[prop_col].std() > 0:
                entrada[label] = stats.spearmanr(sub[prop_col], sub["TE_GERAL"])[0]
            else:
                entrada[label] = None
        linhas.append(entrada)

    return pd.DataFrame(linhas)


# ═══════════════════════════════════════════════════════════════
# 6. CORRELAÇÃO ESTRATIFICADA POR REGIÃO E ESFERA ADMINISTRATIVA
#    (apenas dentro do setor público, critério "reserva de vagas")
# ═══════════════════════════════════════════════════════════════

def correlacao_reserva_por_regiao(dfs, anos):
    """Correlação reserva_total x evasão, apenas públicas, por região."""
    linhas = []
    for ano_at in anos:
        ano_ant = ano_at - 1
        cursos = montar_base_afirmativas(dfs[ano_at], dfs[ano_ant])
        pub = cursos[cursos["SETOR"] == "Pública"]
        for regiao in sorted(pub["NO_REGIAO"].dropna().unique()):
            sub = pub[pub["NO_REGIAO"] == regiao].dropna(subset=["PROP_reserva_total", "TE_GERAL"])
            if len(sub) > 10 and sub["PROP_reserva_total"].std() > 0:
                r = stats.spearmanr(sub["PROP_reserva_total"], sub["TE_GERAL"])[0]
                linhas.append({
                    "ano": ano_at, "regiao": regiao, "r": r, "N": len(sub),
                    "evasao_media_pct": sub["TE_GERAL"].mean() * 100,
                })
    return pd.DataFrame(linhas)


def correlacao_reserva_por_esfera(dfs, anos):
    """Correlação reserva_total x evasão, apenas públicas, por esfera (Federal/Estadual/Municipal)."""
    linhas = []
    for ano_at in anos:
        ano_ant = ano_at - 1
        cursos = montar_base_afirmativas(dfs[ano_at], dfs[ano_ant])
        pub = cursos[cursos["SETOR"] == "Pública"]
        for esfera in ["Federal", "Estadual", "Municipal"]:
            sub = pub[pub["ESFERA_PUBLICA"] == esfera].dropna(subset=["PROP_reserva_total", "TE_GERAL"])
            if len(sub) > 10 and sub["PROP_reserva_total"].std() > 0:
                r = stats.spearmanr(sub["PROP_reserva_total"], sub["TE_GERAL"])[0]
                linhas.append({
                    "ano": ano_at, "esfera": esfera, "r": r, "N": len(sub),
                    "evasao_media_pct": sub["TE_GERAL"].mean() * 100,
                })
    return pd.DataFrame(linhas)


# ═══════════════════════════════════════════════════════════════
# 7. EXECUÇÃO — rode as funções acima e exporte os resultados
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Carregando dados...")
    dfs = carregar_dados()

    print("\n[3] Evasão por categoria (modalidade, grau, categoria administrativa)")
    df_categoria = evasao_por_categoria(dfs)
    print(df_categoria.to_string(index=False))

    print("\n[4] Correlações PROUNI e FIES")
    df_prouni_fies = correlacoes_prouni_fies(dfs)
    print(df_prouni_fies.to_string(index=False))

    print("\n[5] Correlações de políticas afirmativas — geral")
    df_afirm_geral = correlacoes_afirmativas(dfs)
    print(df_afirm_geral.to_string(index=False))

    print("\n[5b] Correlações de políticas afirmativas — só Pública")
    df_afirm_pub = correlacoes_afirmativas(dfs, setor="Pública")
    print(df_afirm_pub.to_string(index=False))

    print("\n[5c] Correlações de políticas afirmativas — só Privada")
    df_afirm_priv = correlacoes_afirmativas(dfs, setor="Privada")
    print(df_afirm_priv.to_string(index=False))

    print("\n[6a] Correlação reserva de vagas x evasão, públicas, por região (2020-2024)")
    df_regiao = correlacao_reserva_por_regiao(dfs, anos=range(2020, 2025))
    print(df_regiao.to_string(index=False))

    print("\n[6b] Correlação reserva de vagas x evasão, públicas, por esfera (2020-2024)")
    df_esfera = correlacao_reserva_por_esfera(dfs, anos=range(2020, 2025))
    print(df_esfera.to_string(index=False))

    # Exportar tudo
    import os
    os.makedirs("resultados", exist_ok=True)
    df_categoria.to_csv("resultados/evasao_por_categoria.csv", index=False, sep=";")
    df_prouni_fies.to_csv("resultados/correlacoes_prouni_fies.csv", index=False, sep=";")
    df_afirm_geral.to_csv("resultados/correlacoes_afirmativas_geral.csv", index=False, sep=";")
    df_afirm_pub.to_csv("resultados/correlacoes_afirmativas_publica.csv", index=False, sep=";")
    df_afirm_priv.to_csv("resultados/correlacoes_afirmativas_privada.csv", index=False, sep=";")
    df_regiao.to_csv("resultados/correlacao_reserva_por_regiao.csv", index=False, sep=";")
    df_esfera.to_csv("resultados/correlacao_reserva_por_esfera.csv", index=False, sep=";")
    print("\nResultados exportados para ./resultados/")
